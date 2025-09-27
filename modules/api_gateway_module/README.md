# API网关模块

API网关模块提供统一的API入口点、路由管理、认证授权和与ModularFlow Framework的深度集成。

## 功能特性

- 🌐 **统一API网关**: 提供单一API入口点，统一管理所有API请求
- 🔄 **自动API发现**: 自动将注册的函数暴露为RESTful API端点
- 🛡️ **中间件支持**: 支持CORS、日志、错误处理等多种中间件
- 📡 **WebSocket支持**: 提供实时双向通信能力
- 📁 **静态文件服务**: 支持前端静态文件托管
- 🔧 **配置驱动**: 通过JSON配置文件灵活配置所有功能
- 📚 **自动文档**: 基于FastAPI自动生成API文档

## 架构组件

### 1. APIGateway 主类
- **职责**: API网关核心管理器，负责应用初始化和服务协调
- **特性**: FastAPI集成、配置管理、服务器生命周期管理

### 2. APIRouter 路由器
- **职责**: API端点注册和路由管理
- **特性**: 端点自动注册、中间件管理、路由优先级控制

### 3. Middleware 中间件系统
- **职责**: 请求/响应处理中间件
- **内置中间件**: CORS、日志记录、错误处理

## 配置文件

API网关使用 `api-config.json` 进行配置：

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8050,
    "debug": true,
    "cors_origins": ["http://localhost:3000"]
  },
  "api": {
    "prefix": "/api",
    "auto_discovery": true,
    "documentation": {
      "enabled": true,
      "url": "/docs"
    }
  },
  "websocket": {
    "enabled": true,
    "path": "/ws"
  },
  "static_files": {
    "enabled": true,
    "directory": "frontend_projects/SmartTavern",
    "url_prefix": "/static"
  }
}
```

## 使用方法

### 1. 启动API网关

```python
from modules.api_gateway_module import get_api_gateway

# 获取API网关实例
gateway = get_api_gateway()

# 启动服务器 (后台运行)
gateway.start_server(background=True)
```

### 2. 通过统一 API 封装层调用

```python
from core.api_client import call_api

# 启动API网关（通过 api/modules 封装）
resp = call_api("api_gateway.start", {"background": True}, namespace="modules")

# 获取网关信息
info = call_api("api_gateway.info", method="GET", namespace="modules")
```

### 3. 添加自定义API端点

```python
gateway = get_api_gateway()

# 添加自定义端点
async def my_custom_handler():
    return {"message": "Hello from custom API"}

gateway.router.add_endpoint(
    "/custom", 
    "GET", 
    my_custom_handler,
    tags=["custom"],
    summary="自定义API端点"
)
```

### 4. WebSocket通信

```javascript
// 前端WebSocket连接
const ws = new WebSocket('ws://localhost:8050/ws');

ws.onopen = function() {
    // 调用注册的函数
    ws.send(JSON.stringify({
        type: 'function_call',
        function: 'some.registered.function',
        params: { key: 'value' }
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('收到响应:', response);
};
```

## 自动API发现

当 `api.auto_discovery` 为 `true` 时，框架仅扫描 `api/*` 目录下通过 `@register_api` 注册的能力，并自动暴露为 RESTful API 端点。

### 能力到API映射规则

- 能力名: `user.get_profile`
- API路径: `/api/modules/user/get_profile`（来源路径位于 `api/modules/...`）
- 支持方法: GET, POST

### 示例（封装层位于 `api/modules/user/user.py`）

```python
from core.api_registry import register_api

@register_api(name="user.get_profile", outputs=["profile"])
def get_user_profile(user_id: int):
    return {"profile": {"user_id": user_id, "name": "用户名", "email": "user@example.com"}}
```

自动生成的API:
- `GET /api/modules/user/get_profile`
- `POST /api/modules/user/get_profile` (带JSON请求体)

## 中间件系统

### 内置中间件

1. **日志中间件**: 记录所有API请求和响应时间
2. **错误处理中间件**: 统一处理异常并返回标准错误格式
3. **CORS中间件**: 处理跨域请求

### 自定义中间件

```python
async def custom_middleware(request: Request, call_next):
    # 请求前处理
    print(f"处理请求: {request.url}")
    
    # 调用下一个中间件/处理器
    response = await call_next(request)
    
    # 响应后处理
    response.headers["X-Custom-Header"] = "CustomValue"
    return response

# 注册中间件
gateway.router.add_middleware("custom", custom_middleware, priority=50)
```

## API端点

### 系统端点

- `GET /api/health` - 健康检查
- `GET /api/info` - API信息和统计
- `GET /docs` - API文档 (Swagger UI)
- `GET /redoc` - API文档 (ReDoc)

### 自动发现端点

所有注册的函数都会自动生成对应的API端点，支持GET和POST方法。

## WebSocket消息格式

### 请求格式

```json
{
  "type": "function_call",
  "function": "function.name",
  "params": {
    "key": "value"
  }
}
```

### 响应格式

```json
{
  "type": "function_result",
  "function": "function.name", 
  "success": true,
  "result": "函数返回值"
}
```

## 静态文件服务

当启用静态文件服务时，可以直接访问前端文件:

- 配置目录: `frontend_projects/SmartTavern`
- 访问URL: `http://localhost:8050/static/index.html`

## 依赖要求

```bash
pip install fastapi uvicorn python-multipart
```

## 集成示例

```python
# 启动完整的API网关服务
from modules.api_gateway_module import get_api_gateway

def main():
    # 获取API网关
    gateway = get_api_gateway()
    
    # 启动服务器
    gateway.start_server()  # 前台运行
    
if __name__ == "__main__":
    main()
```

## 网关管理 API（通过 `api/modules/api_gateway` 封装）

- `POST /api/modules/api_gateway/start` - 启动API网关服务器
- `POST /api/modules/api_gateway/stop` - 停止API网关服务器
- `GET /api/modules/api_gateway/info` - 获取API网关信息
- `POST /api/modules/api_gateway/broadcast` - WebSocket广播消息

## 错误处理

API网关提供统一的错误处理格式:

```json
{
  "error": "错误类型",
  "detail": "详细错误信息",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 性能优化

- 支持异步处理，提高并发性能
- 内置请求/响应缓存机制
- WebSocket连接池管理
- 静态文件缓存控制