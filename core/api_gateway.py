"""
API网关模块（核心层 - core）

提供统一的API入口、路由管理、中间件处理和与ModularFlow Framework的集成。
支持RESTful API、WebSocket连接和自动API发现功能。
该模块不再硬编码任何配置，所有配置都从项目配置文件中读取。
"""

import json
import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import threading

try:
    from fastapi import FastAPI, HTTPException, Request, Response, WebSocket
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.websockets import WebSocketDisconnect
    from starlette.websockets import WebSocketState
    import uvicorn
except ImportError:
    FastAPI = None
    WebSocketDisconnect = None
    WebSocketState = None
    print("⚠️ FastAPI未安装，请运行: pip install fastapi uvicorn")

import core

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APIEndpoint:
    """API端点定义"""
    path: str
    method: str
    handler: Callable
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    description: str = ""
    response_model: Optional[Any] = None


@dataclass 
class MiddlewareConfig:
    """中间件配置"""
    name: str
    handler: Callable
    priority: int = 0
    enabled: bool = True


@dataclass
class GatewayConfig:
    """API网关配置"""
    # 服务器配置
    host: str = "0.0.0.0"
    port: int = 8050
    debug: bool = True
    
    # API配置
    api_prefix: str = "/api"
    auto_discovery: bool = True
    
    # 文档配置
    docs_enabled: bool = True
    docs_url: str = "/docs"
    
    # WebSocket配置
    websocket_enabled: bool = True
    websocket_path: str = "/ws"
    
    # 静态文件配置
    static_files_enabled: bool = False
    static_directory: str = ""
    static_url_prefix: str = "/static"
    
    # CORS配置
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    
    # 安全与治理配置
    auth_enabled: bool = False
    rate_limit_enabled: bool = False
    rate_limit_per_minute: int = 120

    # 其他配置
    title: str = "ModularFlow API Gateway"
    description: str = "统一API网关 - 集成ModularFlow Framework"
    version: str = "1.0.0"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GatewayConfig':
        """从字典创建配置对象"""
        # 提取嵌套配置
        server_config = data.get("server", {})
        api_config = data.get("api", {})
        websocket_config = data.get("websocket", {})
        static_config = data.get("static_files", {})
        docs_config = api_config.get("documentation", {})
        
        return cls(
            # 服务器配置
            host=server_config.get("host", "0.0.0.0"),
            port=server_config.get("port", 8050),
            debug=server_config.get("debug", True),
            cors_origins=server_config.get("cors_origins", ["*"]),
            
            # API配置
            api_prefix=api_config.get("prefix", "/api"),
            auto_discovery=api_config.get("auto_discovery", True),
            
            # 文档配置
            docs_enabled=docs_config.get("enabled", True),
            docs_url=docs_config.get("url", "/docs"),
            
            # WebSocket配置
            websocket_enabled=websocket_config.get("enabled", True),
            websocket_path=websocket_config.get("path", "/ws"),
            
            # 静态文件配置
            static_files_enabled=static_config.get("enabled", False),
            static_directory=static_config.get("directory", ""),
            static_url_prefix=static_config.get("url_prefix", "/static"),
            
            # 应用配置
            title=data.get("title", "ModularFlow API Gateway"),
            description=data.get("description", "统一API网关 - 集成ModularFlow Framework"),
            version=data.get("version", "1.0.0")
        )


class APIRouter:
    """API路由器 - 管理API端点注册和路由"""
    
    def __init__(self):
        self.endpoints: List[APIEndpoint] = []
        self.middlewares: List[MiddlewareConfig] = []
        
    def add_endpoint(self, path: str, method: str, handler: Callable, **kwargs):
        """添加API端点"""
        endpoint = APIEndpoint(
            path=path,
            method=method.upper(),
            handler=handler,
            **kwargs
        )
        self.endpoints.append(endpoint)
        logger.info(f"✓ 注册API端点: {method.upper()} {path}")
        
    def add_middleware(self, name: str, handler: Callable, priority: int = 0):
        """添加中间件"""
        middleware = MiddlewareConfig(
            name=name,
            handler=handler,
            priority=priority
        )
        self.middlewares.append(middleware)
        # 按优先级排序
        self.middlewares.sort(key=lambda m: m.priority, reverse=True)
        logger.info(f"✓ 注册中间件: {name} (优先级: {priority})")
        
    def get_endpoints(self) -> List[APIEndpoint]:
        """获取所有端点"""
        return self.endpoints
        
    def get_middlewares(self) -> List[MiddlewareConfig]:
        """获取所有中间件"""
        return [m for m in self.middlewares if m.enabled]


class Middleware:
    """中间件基类和预定义中间件"""
    
    @staticmethod
    async def cors_middleware(request: Request, call_next):
        """CORS中间件"""
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
    
    @staticmethod
    async def logging_middleware(request: Request, call_next):
        """日志中间件"""
        start_time = datetime.now()
        logger.info(f"📨 {request.method} {request.url}")
        
        response = await call_next(request)
        
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"📤 {response.status_code} - {process_time:.4f}s")
        
        return response
    
    @staticmethod
    async def error_handling_middleware(request: Request, call_next):
        """错误处理中间件"""
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"❌ API错误: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error_code": "INTERNAL_ERROR", "message": "Internal Server Error", "detail": str(e)}
            )

    @staticmethod
    async def auth_middleware(request: Request, call_next):
        """基础鉴权中间件（示例：要求 Authorization 头）"""
        path = str(request.url.path)
        # 放行基础系统端点
        if path.endswith("/health") or path.endswith("/info"):
            return await call_next(request)
        auth = request.headers.get("Authorization")
        if not auth:
            return JSONResponse(status_code=401, content={"error_code": "UNAUTHORIZED", "message": "缺少Authorization头"})
        return await call_next(request)

    # 简易限流存储（内存）
    _rate_store: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    async def rate_limit_middleware(request: Request, call_next):
        """基础限流中间件（每IP每分钟限次）"""
        try:
            client_ip = request.client.host if request.client else "unknown"
            now_minute = datetime.now().strftime("%Y%m%d%H%M")
            key = f"{client_ip}:{now_minute}"
            record = Middleware._rate_store.get(key, {"count": 0})
            record["count"] += 1
            Middleware._rate_store[key] = record
            # 默认限流阈值（如需读取配置，可在此扩展）
            limit = 120
            if record["count"] > limit:
                return JSONResponse(status_code=429, content={"error_code": "RATE_LIMITED", "message": "请求过于频繁"})
        except Exception as e:
            logger.warning(f"限流中间件异常: {e}")
        return await call_next(request)


class APIGateway:
    """
    API网关主类
    
    提供完整的API网关功能，包括：
    - FastAPI应用初始化和配置
    - 自动API发现和注册
    - 中间件管理
    - WebSocket支持
    - 静态文件服务
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None, config_file: Optional[str] = None, project_config: Optional[Dict[str, Any]] = None):
        """
        初始化API网关
        
        Args:
            config: 直接传入的网关配置
            config_file: 配置文件路径
            project_config: 项目配置字典
        """
        self.app = None
        self.router = APIRouter()
        self.config = None
        self.websocket_connections = []
        self._server_thread = None
        self._server = None
        
        # 加载配置
        self._load_config(config, config_file, project_config)
        
        # 初始化FastAPI应用
        if FastAPI and self.config:
            self._init_fastapi()
            self._setup_default_middlewares()
            self._setup_default_routes()
    
    def _load_config(self, config: Optional[GatewayConfig] = None, config_file: Optional[str] = None, project_config: Optional[Dict[str, Any]] = None):
        """加载API配置"""
        if config:
            # 直接使用传入的配置
            self.config = config
            logger.info("✓ 使用直接传入的配置")
            return
        
        if project_config:
            # 从项目配置中提取API网关配置
            backend_config = project_config.get("backend", {})
            api_gateway_config = backend_config.get("api_gateway", {})
            
            if api_gateway_config.get("enabled", True):
                # 构建网关配置
                gateway_dict = self._extract_gateway_config_from_project(project_config)
                self.config = GatewayConfig.from_dict(gateway_dict)
                logger.info("✓ 从项目配置加载API网关配置")
                return
        
        if config_file:
            config_path = Path(config_file)
        else:
            # 尝试多个可能的配置文件位置
            possible_paths = [
                "api-config.json",
                "config/api-config.json", 
                "backend_projects/api-config.json"
            ]
            
            config_path = None
            for path in possible_paths:
                if Path(path).exists():
                    config_path = Path(path)
                    break
        
        if config_path and config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self.config = GatewayConfig.from_dict(config_data)
                logger.info(f"✓ 从文件加载API配置: {config_path}")
            except Exception as e:
                logger.error(f"❌ 加载API配置文件失败: {e}")
                self.config = GatewayConfig()
                logger.info("⚠️ 使用默认API配置")
        else:
            self.config = GatewayConfig()
            logger.info("⚠️ 使用默认API配置")
    
    def _extract_gateway_config_from_project(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """从项目配置中提取API网关配置"""
        project_info = project_config.get("project", {})
        backend_config = project_config.get("backend", {})
        api_gateway_config = backend_config.get("api_gateway", {})
        websocket_config = backend_config.get("websocket", {})
        
        prefix = core.get_api_config().api_prefix
        return {
            "title": f"{project_info.get('display_name', 'ModularFlow')} API Gateway",
            "description": project_info.get("description", "API网关服务"),
            "version": project_info.get("version", "1.0.0"),
            "server": {
                "host": "0.0.0.0",
                "port": api_gateway_config.get("port", 8050),
                "debug": True,
                "cors_origins": api_gateway_config.get("cors_origins", ["*"])
            },
            "api": {
                "prefix": prefix,
                "auto_discovery": True,
                "documentation": {
                    "enabled": True,
                    "url": "/docs"
                }
            },
            "websocket": {
                "enabled": websocket_config.get("enabled", True),
                "path": websocket_config.get("path", "/ws")
            },
            "static_files": {
                "enabled": False,
                "directory": "",
                "url_prefix": "/static"
            }
        }
    
    def _init_fastapi(self):
        """初始化FastAPI应用"""
        if not FastAPI or not self.config:
            return
            
        self.app = FastAPI(
            title=self.config.title,
            description=self.config.description,
            version=self.config.version,
            docs_url=self.config.docs_url if self.config.docs_enabled else None
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        logger.info("✓ FastAPI应用初始化完成")
    
    def _setup_default_middlewares(self):
        """设置默认中间件"""
        # 基础中间件
        self.router.add_middleware("logging", Middleware.logging_middleware, priority=100)
        self.router.add_middleware("error_handling", Middleware.error_handling_middleware, priority=90)
        # 注册到 FastAPI 应用
        if self.app:
            for m in self.router.get_middlewares():
                self.app.middleware("http")(m.handler)
    
    def _setup_default_routes(self):
        """设置默认路由"""
        # 健康检查端点
        self.router.add_endpoint(
            "/health", 
            "GET", 
            self._health_check_handler,
            tags=["system"],
            summary="健康检查"
        )
        
        # API信息端点
        self.router.add_endpoint(
            "/info",
            "GET", 
            self._api_info_handler,
            tags=["system"],
            summary="API信息"
        )
        
        # 注册所有端点到FastAPI
        if self.app:
            self._register_endpoints_to_fastapi()
    
    async def _health_check_handler(self):
        """健康检查处理器"""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    async def _api_info_handler(self):
        """API信息处理器"""
        service_manager = core.get_service_manager()
        services = service_manager.list_services()
        
        return {
            "title": self.config.title if self.config else "ModularFlow API Gateway",
            "version": self.config.version if self.config else "1.0.0", 
            "endpoints": len(self.router.get_endpoints()),
            "middlewares": len(self.router.get_middlewares()),
            "services": {k: len(v) for k, v in services.items()},
            "websocket_connections": len(self.websocket_connections)
        }
    
    def _register_endpoints_to_fastapi(self):
        """将路由器中的端点注册到FastAPI应用"""
        if not self.app or not self.config:
            return
            
        for endpoint in self.router.get_endpoints():
            full_path = f"{self.config.api_prefix}{endpoint.path}"
            
            if endpoint.method == "GET":
                self.app.get(full_path, tags=endpoint.tags, summary=endpoint.summary)(endpoint.handler)
            elif endpoint.method == "POST":
                self.app.post(full_path, tags=endpoint.tags, summary=endpoint.summary)(endpoint.handler)
            elif endpoint.method == "PUT":
                self.app.put(full_path, tags=endpoint.tags, summary=endpoint.summary)(endpoint.handler)
            elif endpoint.method == "DELETE":
                self.app.delete(full_path, tags=endpoint.tags, summary=endpoint.summary)(endpoint.handler)

        # 基于注册表构建 OpenAPI（仅展示 api/* 层能力，按新规范）
        try:
            registry = core.get_registry()
            paths = {}
            for path in registry.list_functions():
                spec = registry.get_spec(path)
                if not spec:
                    continue
                full_path = f"{self.config.api_prefix}/{spec.namespace}/{spec.path}"
                paths.setdefault(full_path, {})
                # GET 仅用于便捷调用（不携带请求体）
                paths[full_path]["get"] = {
                    "summary": f"{spec.description or 'API 调用'}",
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": spec.output_schema or {"type": "object"}}}
                        }
                    }
                }
                # POST 使用严格请求体 Schema
                paths[full_path]["post"] = {
                    "summary": f"{spec.description or 'API 调用'}",
                    "requestBody": {
                        "required": True if spec.input_schema and spec.input_schema.get("required") else False,
                        "content": {
                            "application/json": {"schema": spec.input_schema or {"type": "object"}}
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {"application/json": {"schema": spec.output_schema or {"type": "object"}}}
                        }
                    }
                }
            self.app.openapi_schema = {
                "openapi": "3.0.0",
                "info": {"title": self.config.title, "version": self.config.version},
                "paths": paths
            }
            self.app.openapi = lambda: self.app.openapi_schema
        except Exception as e:
            logger.warning(f"⚠️ 构建OpenAPI失败: {e}")
    
    def discover_and_register_functions(self):
        """自动发现并注册函数作为API端点（新规范）"""
        if not self.config or not self.config.auto_discovery:
            return

        registry = core.get_registry()
        for path in registry.list_functions():
            try:
                func = core.get_registered_api(path)
                spec = registry.get_spec(path)
                if not func or not spec:
                    continue

                api_path = f"/{spec.namespace}/{spec.path}"

                # 创建API处理器（基于 JSON Schema 的简单校验）
                def create_handler(fn=func, _spec=spec):
                    async def handler(request: Request = None):
                        try:
                            data = {}
                            content_type = ""
                            method = "GET"
                            body_bytes = b""

                            if request:
                                method = request.method.upper()
                                content_type = (request.headers.get("content-type", "") or "").lower()
                                body_bytes = await request.body()

                            expected_props = list((_spec.input_schema or {}).get("properties", {}).keys())
                            required_inputs = list((_spec.input_schema or {}).get("required", []) or [])

                            def to_snake(s: str) -> str:
                                out = []
                                for ch in s:
                                    if ch.isupper():
                                        out.append('_')
                                        out.append(ch.lower())
                                    else:
                                        out.append(ch)
                                return ''.join(out).lstrip('_')

                            if method == "POST":
                                if "multipart/form-data" in content_type:
                                    form = await request.form()
                                    mapped = {}
                                    for k, v in form.items():
                                        k2 = to_snake(k)
                                        if not expected_props or k2 in expected_props:
                                            mapped[k2] = v
                                    data = mapped
                                elif "application/json" in content_type:
                                    data = await request.json() if body_bytes else {}
                                else:
                                    # 原始体：仅在单参数且必填时映射
                                    if body_bytes and len(required_inputs) == 1:
                                        data = {required_inputs[0]: body_bytes}
                                    else:
                                        data = {}
                            else:
                                # GET：从查询参数获取
                                q = dict(request.query_params) if request else {}
                                if q:
                                    mapped = {}
                                    for k, v in q.items():
                                        k2 = to_snake(k)
                                        if not expected_props or k2 in expected_props:
                                            mapped[k2] = v
                                    data = mapped

                            # 必填校验
                            missing = [k for k in required_inputs if k not in (data or {})]
                            if missing:
                                return JSONResponse(status_code=400, content={
                                    "error_code": "MISSING_REQUIRED",
                                    "message": "缺少必填字段",
                                    "missing": missing
                                })

                            # 协程/同步统一调用
                            import inspect as _ins
                            if _ins.iscoroutinefunction(fn):
                                result = await fn(**(data or {}))
                            else:
                                loop = asyncio.get_running_loop()
                                result = await loop.run_in_executor(None, (lambda: fn(**(data or {})) if data else fn()))
                            return result
                        except Exception as e:
                            return {"error": str(e)}
                    return handler

                handler = create_handler()

                # 注册为API端点 (支持GET和POST)
                self.router.add_endpoint(
                    api_path,
                    "GET",
                    handler,
                    tags=["functions"],
                    summary=f"{spec.description or 'API 调用'}"
                )
                self.router.add_endpoint(
                    api_path,
                    "POST",
                    handler,
                    tags=["functions"],
                    summary=f"{spec.description or 'API 调用'}"
                )

                logger.info(f"✓ 自动注册函数API: {spec.namespace}:{spec.path} -> {api_path}")

            except Exception as e:
                logger.error(f"❌ 注册函数API失败 {path}: {e}")
    
    def setup_websocket(self):
        """设置WebSocket支持"""
        if not self.app or not self.config or not self.config.websocket_enabled:
            return
            
        @self.app.websocket(self.config.websocket_path)
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.websocket_connections.append(websocket)
            logger.info(f"✓ WebSocket连接建立: {len(self.websocket_connections)}个活跃连接")
            
            try:
                while True:
                    try:
                        # 接收消息
                        data = await websocket.receive_text()
                        message = json.loads(data)
                        
                        # 处理消息
                        response = await self._handle_websocket_message(message)
                        
                        # 发送响应
                        await websocket.send_text(json.dumps(response))
                        
                    except (WebSocketDisconnect, ConnectionResetError, ConnectionAbortedError):
                        # WebSocket连接断开或重置
                        break
                    except Exception as e:
                        logger.error(f"❌ WebSocket消息处理错误: {e}")
                        # 尝试发送错误响应
                        try:
                            # 检查WebSocket状态
                            if websocket.client_state != WebSocketState.DISCONNECTED:
                                error_response = {
                                    "type": "error",
                                    "error": "消息处理失败",
                                    "detail": str(e)
                                }
                                await websocket.send_text(json.dumps(error_response))
                            else:
                                break
                        except:
                            # 如果发送错误响应也失败，则断开连接
                            break
                    
            except Exception as e:
                logger.error(f"❌ WebSocket错误: {e}")
            finally:
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
                logger.info(f"✓ WebSocket连接断开: {len(self.websocket_connections)}个活跃连接")
    
    async def _handle_websocket_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理WebSocket消息（新规范：函数路径必须为斜杠风格）"""
        try:
            msg_type = message.get("type", "ping")
            
            if msg_type == "ping":
                return {"type": "pong", "timestamp": datetime.now().isoformat()}
            elif msg_type == "function_call":
                # 斜杠路径，禁止点式与反斜杠
                func_path = message.get("function", "") or ""
                params = message.get("params", {}) or {}
                
                if "." in func_path or "\\" in func_path:
                    return {
                        "type": "function_result",
                        "function": func_path,
                        "success": False,
                        "error": "FUNCTION_PATH_FORMAT",
                        "message": "函数路径必须为斜杠形式（例如 'project_manager/start_project'），不再支持点式名称"
                    }
                
                try:
                    func = core.get_registered_api(func_path)
                except Exception:
                    func = None
                
                if func:
                    result = func(**params) if params else func()
                    return {
                        "type": "function_result",
                        "function": func_path,
                        "success": True,
                        "result": result
                    }
                else:
                    return {
                        "type": "function_result",
                        "function": func_path,
                        "success": False,
                        "error": f"函数不存在: {func_path}"
                    }
            else:
                return {"type": "error", "error": f"不支持的消息类型: {msg_type}"}
                
        except Exception as e:
            return {"type": "error", "error": str(e)}
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """广播消息给所有WebSocket连接"""
        if not self.websocket_connections:
            return
            
        message_text = json.dumps(message)
        disconnected = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message_text)
            except:
                disconnected.append(websocket)
        
        # 移除断开的连接
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)
    
    def setup_static_files(self):
        """设置静态文件服务"""
        if not self.app or not self.config or not self.config.static_files_enabled:
            return
            
        if not self.config.static_directory:
            logger.warning("⚠️ 静态文件目录未配置")
            return
            
        static_path = Path(self.config.static_directory)
        if static_path.exists():
            self.app.mount(self.config.static_url_prefix, StaticFiles(directory=str(static_path)), name="static")
            logger.info(f"✓ 静态文件服务: {self.config.static_url_prefix} -> {self.config.static_directory}")
        else:
            logger.warning(f"⚠️ 静态文件目录不存在: {self.config.static_directory}")
    
    def start_server(self, background: bool = False):
        """启动API服务器"""
        if not self.app or not self.config:
            logger.error("❌ FastAPI未初始化或配置缺失，无法启动服务器")
            return
        
        # 完成所有设置
        self.discover_and_register_functions()
        self.setup_websocket()
        self.setup_static_files()
        self._register_endpoints_to_fastapi()  # 重新注册以包含自动发现的端点
        
        if background:
            # 后台运行
            def run_server():
                try:
                    import uvicorn
                    config = uvicorn.Config(
                        self.app,
                        host=self.config.host,
                        port=self.config.port,
                        log_level="info"
                    )
                    self._server = uvicorn.Server(config)
                    asyncio.run(self._server.serve())
                except Exception as e:
                    logger.error(f"❌ API服务器运行异常: {e}")
            
            self._server_thread = threading.Thread(target=run_server, daemon=True)
            self._server_thread.start()
            logger.info(f"🚀 API服务器后台启动: http://{self.config.host}:{self.config.port}")
        else:
            # 前台运行
            logger.info(f"🚀 API服务器启动: http://{self.config.host}:{self.config.port}")
            uvicorn.run(self.app, host=self.config.host, port=self.config.port, log_level="info", reload=self.config.debug)
    
    def stop_server(self):
        """停止API服务器"""
        try:
            # 停止uvicorn服务器
            if self._server:
                self._server.should_exit = True
                if hasattr(self._server, 'force_exit'):
                    self._server.force_exit = True
                logger.info("✓ API服务器停止信号已发送")
            
            # 等待服务器线程结束
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=10)
                if self._server_thread.is_alive():
                    logger.warning("⚠️ API服务器线程未能在10秒内停止")
                else:
                    logger.info("✓ API服务器线程已停止")
            
            # 清理WebSocket连接
            if self.websocket_connections:
                logger.info(f"🧹 清理 {len(self.websocket_connections)} 个WebSocket连接")
                self.websocket_connections.clear()
            
            # 重置状态
            self._server = None
            self._server_thread = None
            
            logger.info("🛑 API服务器已完全停止")
            
        except Exception as e:
            logger.error(f"❌ 停止API服务器时出现异常: {e}")


# 全局API网关实例
_api_gateway_instance = None

def get_api_gateway(
    config: Optional[GatewayConfig] = None, 
    config_file: Optional[str] = None, 
    project_config: Optional[Dict[str, Any]] = None
) -> APIGateway:
    """获取API网关单例"""
    global _api_gateway_instance
    if _api_gateway_instance is None:
        _api_gateway_instance = APIGateway(config=config, config_file=config_file, project_config=project_config)
    return _api_gateway_instance

def create_api_gateway_for_project(project_config_path: str) -> APIGateway:
    """为特定项目创建API网关实例"""
    project_config_file = Path(project_config_path)
    if project_config_file.exists():
        try:
            with open(project_config_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
            return APIGateway(project_config=project_config)
        except Exception as e:
            logger.error(f"❌ 加载项目配置失败: {e}")
    
    return APIGateway()


if __name__ == "__main__":
    # 直接运行时启动API网关
    gateway = get_api_gateway()
    gateway.start_server()