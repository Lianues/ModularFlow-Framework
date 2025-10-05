"""
项目管理核心模块
负责统一管理前后端项目的生命周期、端口分配和状态监控
支持动态项目发现和配置脚本自动加载
"""

import json
import base64
import subprocess
import threading
import time
import requests
import psutil
import logging
import os
import shutil
import tempfile
import zipfile
import importlib.util
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
import core

# 配置日志
logger = logging.getLogger(__name__)

def _detect_project_role(project_dir: Path) -> Optional[str]:
    """读取项目标记，区分前端/后端。仅读取 modularflow_config.py 中的 PROJECT_ROLE"""
    try:
        script = project_dir / "modularflow_config.py"
        if not script.exists():
            return None
        spec = importlib.util.spec_from_file_location("modcfg_role", str(script))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        role = getattr(mod, "PROJECT_ROLE", None)
        if isinstance(role, str):
            role = role.strip().lower()
        if role in ("frontend", "backend"):
            return role
        return None
    except Exception:
        return None

def _read_ws_port_from_config(project_dir: Path) -> Optional[int]:
    """读取 modularflow_config.py 中的 WEBSOCKET_PORT，若无则返回 None"""
    try:
        script = project_dir / "modularflow_config.py"
        if not script.exists():
            return None
        spec = importlib.util.spec_from_file_location("modcfg_ws", str(script))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        ws_port = getattr(mod, "WEBSOCKET_PORT", None)
        if isinstance(ws_port, int) and (1024 <= ws_port <= 65535):
            return ws_port
        # 若为字符串数字，尝试转换
        if isinstance(ws_port, str):
            try:
                n = int(ws_port.strip())
                if 1024 <= n <= 65535:
                    return n
            except Exception:
                pass
        return None
    except Exception:
        return None


@dataclass
class ProjectStatus:
    """项目状态信息"""
    name: str
    namespace: str
    project_path: str
    config_script_path: Optional[str] = None
    enabled: bool = True
    frontend_running: bool = False
    backend_running: bool = False
    frontend_port: Optional[int] = None
    backend_port: Optional[int] = None
    frontend_pid: Optional[int] = None
    backend_pid: Optional[int] = None
    start_time: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    errors: List[str] = field(default_factory=list)
    config: Optional[core.ProjectConfigInterface] = None


class ProjectManager:
    """
    统一项目管理器
    
    负责管理所有注册项目的生命周期，包括：
    - 动态项目发现和配置加载
    - 项目启动/停止
    - 端口管理和冲突检测
    - 健康检查
    - 状态监控
    """
    
    def __init__(self):
        self.projects: Dict[str, ProjectStatus] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.health_check_thread: Optional[threading.Thread] = None
        self.health_check_running = False
        self.frontend_projects_path = Path("frontend_projects")
        self.backend_projects_path = Path("backend_projects")
        self.port_registry: Dict[int, str] = {}  # 端口注册表
        
        # 动态发现和加载项目（前端+后端）
        self._discover_and_load_projects()
        self._discover_and_load_backend_projects()
        
        # 启动健康检查
        self._start_health_check()
    
    def _discover_and_load_projects(self):
        """动态发现和加载前端项目"""
        if not self.frontend_projects_path.exists():
            logger.warning(f"⚠️ 前端项目目录不存在: {self.frontend_projects_path}")
            return
        
        discovered_count = 0
        for project_dir in self.frontend_projects_path.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                try:
                    project_status = self._load_project_from_directory(project_dir)
                    if project_status:
                        self.projects[project_status.name] = project_status
                        discovered_count += 1
                        logger.info(f"✓ 发现项目: {project_status.name} ({project_status.project_path})")
                except Exception as e:
                    logger.error(f"❌ 加载项目失败 {project_dir.name}: {e}")
        
        logger.info(f"✓ 动态发现了 {discovered_count} 个前端项目")

    def _discover_and_load_backend_projects(self):
        """动态发现和加载后端项目"""
        if not self.backend_projects_path.exists():
            logger.info(f"ℹ️ 后端项目目录不存在: {self.backend_projects_path}")
            return

        discovered_count = 0
        for project_dir in self.backend_projects_path.iterdir():
            if project_dir.is_dir() and not project_dir.name.startswith('.'):
                try:
                    project_status = self._load_backend_project_from_directory(project_dir)
                    if project_status:
                        # 若名称冲突，优先保留已有（避免覆盖前端同名项目）
                        if project_status.name not in self.projects:
                            self.projects[project_status.name] = project_status
                        else:
                            logger.warning(f"⚠️ 同名项目已存在(可能为前端)：{project_status.name}，跳过后端项目载入")
                        discovered_count += 1
                        logger.info(f"✓ 发现后端项目: {project_status.name} ({project_status.project_path})")
                except Exception as e:
                    logger.error(f"❌ 加载后端项目失败 {project_dir.name}: {e}")
        logger.info(f"✓ 动态发现了 {discovered_count} 个后端项目")

    def _load_backend_project_from_directory(self, project_dir: Path) -> Optional[ProjectStatus]:
        """从目录加载单个后端项目（仅后端端口，前端为空）"""
        project_name = project_dir.name
        try:
            config = core.load_project_config(project_dir)
            project_info = config.get_project_info()
            api_config = config.get_api_config()

            # 检查配置脚本路径
            config_script_path = None
            modularflow_config = project_dir / "modularflow_config.py"
            if modularflow_config.exists():
                config_script_path = str(modularflow_config)

            # 从API配置解析后端端口
            api_endpoint = api_config.get("api_endpoint", "")
            backend_port_from_config = None
            if api_endpoint:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(api_endpoint)
                    if parsed.port:
                        backend_port_from_config = parsed.port
                except Exception:
                    pass

            # 后端端口不再进行动态分配：保持配置中的端口（可能冲突，但不自动调整）
            preferred_backend_port = backend_port_from_config or 8050
            backend_port = preferred_backend_port

            status_obj = ProjectStatus(
                name=project_info.get("name", project_name),
                namespace=project_info.get("name", project_name),
                project_path=str(project_dir),
                config_script_path=config_script_path,
                enabled=True,
                frontend_port=None,   # 后端项目不含前端端口
                backend_port=backend_port,
                config=config
            )
            # 仅更新后端运行标记
            self._update_running_flags(status_obj)
            return status_obj

        except Exception as e:
            logger.error(f"❌ 加载后端项目配置失败 {project_name}: {e}")
            return None
    
    def _load_project_from_directory(self, project_dir: Path) -> Optional[ProjectStatus]:
        """从目录加载单个项目"""
        project_name = project_dir.name
        
        # 加载项目配置
        try:
            config = core.load_project_config(project_dir)
            project_info = config.get_project_info()
            runtime_config = config.get_runtime_config()
            api_config = config.get_api_config()
            
            # 检查配置脚本是否存在
            config_script_path = None
            modularflow_config = project_dir / "modularflow_config.py"
            if modularflow_config.exists():
                config_script_path = str(modularflow_config)
            
            # 分配端口 - 优先使用配置文件中的端口
            frontend_port = self._allocate_port(runtime_config.get("port", 3000), project_name)
            
            # 从API配置中获取后端端口
            api_endpoint = api_config.get("api_endpoint", "")
            backend_port_from_config = None
            if api_endpoint:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(api_endpoint)
                    if parsed.port:
                        backend_port_from_config = parsed.port
                except:
                    pass
            
            # 后端端口不再进行动态分配：保持配置中的端口（可能冲突，但不自动调整）
            # 如果配置中没有端口信息，使用默认值8050
            preferred_backend_port = backend_port_from_config or 8050
            backend_port = preferred_backend_port
            
            # 构建状态对象后，立即探测端口以“实时”确定运行状态（而不是默认False）
            status_obj = ProjectStatus(
                name=project_info["name"],
                namespace=project_info["name"],  # 使用项目名作为命名空间
                project_path=str(project_dir),
                config_script_path=config_script_path,
                enabled=True,
                frontend_port=frontend_port,
                backend_port=backend_port,
                config=config
            )
            # 实时检测（端口探测）
            self._update_running_flags(status_obj)
            return status_obj
            
        except Exception as e:
            logger.error(f"❌ 加载项目配置失败 {project_name}: {e}")
            return None
    
    def _allocate_port(self, preferred_port: int, project_identifier: str) -> int:
        """分配端口，避免冲突"""
        # 如果首选端口可用，直接使用
        if preferred_port not in self.port_registry:
            self.port_registry[preferred_port] = project_identifier
            return preferred_port
        
        # 如果首选端口已被同一项目占用，直接返回
        if self.port_registry.get(preferred_port) == project_identifier:
            return preferred_port
        
        # 寻找可用端口
        for port in range(preferred_port + 1, preferred_port + 100):
            if port not in self.port_registry:
                self.port_registry[port] = project_identifier
                logger.info(f"⚠️ 端口 {preferred_port} 已占用，为 {project_identifier} 分配端口 {port}")
                return port
        
        # 如果找不到可用端口，使用随机端口
        import random
        for _ in range(10):
            port = random.randint(10000, 65535)
            if port not in self.port_registry:
                self.port_registry[port] = project_identifier
                logger.warning(f"⚠️ 无法找到合适端口，为 {project_identifier} 分配随机端口 {port}")
                return port
        
        # 最后的备选方案
        logger.error(f"❌ 无法为 {project_identifier} 分配端口")
        return preferred_port
    
    def _update_running_flags(self, status: ProjectStatus):
        """通过端口探测实时更新运行标记，避免仅初始化时的静态状态"""
        # 探测前端
        frontend_ok = False
        if status.frontend_port:
            try:
                resp = requests.get(f"http://localhost:{status.frontend_port}", timeout=3)
                # 2xx~4xx 视为端口活跃（静态站点返回200，某些服务可能返回404）
                frontend_ok = 200 <= resp.status_code < 500
            except Exception:
                frontend_ok = False
        status.frontend_running = frontend_ok

        # 探测后端（API网关通常提供 /api/health）
        backend_ok = False
        if status.backend_port:
            try:
                resp = requests.get(f"http://localhost:{status.backend_port}/api/health", timeout=3)
                backend_ok = resp.status_code == 200
            except Exception:
                backend_ok = False
        status.backend_running = backend_ok

        # 依据探测结果更新整体健康状态
        if status.frontend_running or status.backend_running:
            status.health_status = "healthy"
        else:
            status.health_status = "unknown"

    def _start_health_check(self):
        """启动健康检查线程"""
        if not self.health_check_running:
            self.health_check_running = True
            self.health_check_thread = threading.Thread(
                target=self._health_check_loop, 
                daemon=True
            )
            self.health_check_thread.start()
            logger.info("✓ 健康检查线程已启动")
    
    def _health_check_loop(self):
        """健康检查循环"""
        while self.health_check_running:
            try:
                for project_name, status in self.projects.items():
                    if status.enabled:
                        self._check_project_health(project_name)
                time.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                time.sleep(10)
    
    def _check_project_health(self, project_name: str):
        """检查单个项目的健康状态"""
        if project_name not in self.projects:
            return
        
        status = self.projects[project_name]
        status.last_health_check = datetime.now()
        status.errors.clear()
        
        # 检查前端健康状态（直接探测端口，不依赖已有运行标记）
        if status.frontend_port:
            frontend_url = f"http://localhost:{status.frontend_port}"
            try:
                response = requests.get(frontend_url, timeout=5)
                if 200 <= response.status_code < 500:
                    status.frontend_running = True
                else:
                    status.errors.append(f"前端响应异常: {response.status_code}")
                    status.frontend_running = False
            except Exception:
                # 连接失败时，不累计错误，仅标记为未运行，避免将整体状态误判为不健康
                status.frontend_running = False
        
        # 检查后端健康状态（直接探测端口，不依赖已有运行标记）
        if status.backend_port:
            try:
                response = requests.get(f"http://localhost:{status.backend_port}/api/health", timeout=5)
                if response.status_code == 200:
                    status.backend_running = True
                else:
                    status.errors.append(f"后端响应异常: {response.status_code}")
                    status.backend_running = False
            except Exception:
                # 连接失败不累计错误，标记为未运行
                status.backend_running = False
        
        # 更新整体健康状态
        if status.errors:
            status.health_status = "unhealthy"
        elif status.frontend_running or status.backend_running:
            status.health_status = "healthy"
        else:
            status.health_status = "unknown"
    
    def _check_command_availability(self, command: str) -> bool:
        """检查命令是否可用"""
        try:
            # 提取命令的第一部分
            cmd_name = command.split()[0]
            return shutil.which(cmd_name) is not None
        except:
            return False
    
    def _execute_command_safely(self, command: str, cwd: str = None, project_name: str = "") -> subprocess.Popen:
        """安全执行命令，处理Windows特殊情况"""
        try:
            # 检查命令是否可用
            if not self._check_command_availability(command):
                raise FileNotFoundError(f"命令不可用: {command.split()[0]}")
            
            # 在Windows上，使用shell=True并设置正确的环境
            env = os.environ.copy()
            
            # 确保PATH包含npm路径
            if "npm" in command and os.name == 'nt':
                # 添加常见的npm路径
                npm_paths = [
                    r"C:\Program Files\nodejs",
                    r"C:\Program Files (x86)\nodejs",
                    os.path.expanduser(r"~\AppData\Roaming\npm")
                ]
                current_path = env.get("PATH", "")
                for npm_path in npm_paths:
                    if os.path.exists(npm_path) and npm_path not in current_path:
                        env["PATH"] = f"{npm_path};{current_path}"
            
            logger.info(f"执行命令: {command} (工作目录: {cwd or '当前目录'})")
            
            # 在Windows上，避免使用PIPE和CREATE_NEW_CONSOLE同时使用
            # 这会导致连接重置错误
            if os.name == 'nt':
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=cwd,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 执行命令失败 {command}: {e}")
            raise
    
    def start_project(self, project_name: str, component: str = "all") -> Dict[str, Any]:
        """
        启动项目
        
        Args:
            project_name: 项目名称
            component: 启动组件 ("frontend", "backend", "all")
        
        Returns:
            启动结果
        """
        if project_name not in self.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = self.projects[project_name]
        if not status.config:
            return {"success": False, "error": f"项目 {project_name} 配置未加载"}
        
        results = {"success": True, "started_components": []}
        
        try:
            # 启动前端
            if component in ["frontend", "all"]:
                runtime_config = status.config.get_runtime_config()
                dev_command = runtime_config.get("dev_command")
                install_command = runtime_config.get("install_command")
                
                if dev_command:
                    project_path = Path(status.project_path)
                    
                    if project_path.exists():
                        # 检查是否需要安装依赖
                        if install_command and self._should_install_dependencies(project_path, status.config):
                            logger.info(f"🔧 检测到 {project_name} 需要安装依赖，正在执行: {install_command}")
                            try:
                                # 执行安装命令
                                install_process = self._execute_install_command(
                                    install_command,
                                    cwd=str(project_path),
                                    project_name=project_name
                                )
                                
                                # 等待安装完成
                                install_process.wait()
                                
                                if install_process.returncode == 0:
                                    logger.info(f"✅ {project_name} 依赖安装成功")
                                    results["dependency_installed"] = True
                                else:
                                    logger.warning(f"⚠️ {project_name} 依赖安装可能有问题，但继续启动")
                                    results["dependency_warning"] = "依赖安装可能有问题"
                                    
                            except Exception as e:
                                logger.warning(f"⚠️ {project_name} 依赖安装失败: {e}，但继续尝试启动")
                                results["dependency_error"] = str(e)
                        
                        logger.info(f"启动 {project_name} 前端: {dev_command}")
                        
                        # 启动前端进程
                        process = self._execute_command_safely(
                            dev_command,
                            cwd=str(project_path),
                            project_name=project_name
                        )
                        
                        self.processes[f"{project_name}_frontend"] = process
                        status.frontend_pid = process.pid
                        status.frontend_running = True
                        status.start_time = datetime.now()
                        results["started_components"].append("frontend")
                        
                        logger.info(f"✓ {project_name} 前端启动成功 (PID: {process.pid})")
                    else:
                        logger.error(f"❌ {project_name} 项目路径不存在: {project_path}")
                        results["success"] = False
                        results["error"] = f"项目路径不存在: {project_path}"
                else:
                    logger.info(f"⚠️ {project_name} 没有配置开发命令，跳过前端启动")
            
            # 启动后端（如果有配置）
            if component in ["backend", "all"]:
                # 这里可以根据需要添加后端启动逻辑
                # 目前大多数前端项目不需要独立的后端启动
                logger.info(f"⚠️ {project_name} 后端启动功能待实现")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 启动项目 {project_name} 失败: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_project(self, project_name: str, component: str = "all") -> Dict[str, Any]:
        """
        停止项目
        
        Args:
            project_name: 项目名称
            component: 停止组件 ("frontend", "backend", "all")
        
        Returns:
            停止结果
        """
        if project_name not in self.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = self.projects[project_name]
        results = {"success": True, "stopped_components": []}
        
        try:
            # 停止后端
            if component in ["backend", "all"]:
                backend_process_key = f"{project_name}_backend"
                if backend_process_key in self.processes:
                    process = self.processes[backend_process_key]
                    try:
                        # 强制终止进程及其子进程
                        self._terminate_process_tree(process)
                        
                        del self.processes[backend_process_key]
                        status.backend_running = False
                        status.backend_pid = None
                        results["stopped_components"].append("backend")
                        
                        logger.info(f"✓ {project_name} 后端已停止")
                    except Exception as e:
                        logger.warning(f"停止 {project_name} 后端时出现问题: {e}")
            
            # 停止前端
            if component in ["frontend", "all"]:
                frontend_process_key = f"{project_name}_frontend"
                if frontend_process_key in self.processes:
                    process = self.processes[frontend_process_key]
                    try:
                        # 强制终止进程及其子进程
                        self._terminate_process_tree(process)
                        
                        del self.processes[frontend_process_key]
                        status.frontend_running = False
                        status.frontend_pid = None
                        results["stopped_components"].append("frontend")
                        
                        logger.info(f"✓ {project_name} 前端已停止")
                    except Exception as e:
                        logger.warning(f"停止 {project_name} 前端时出现问题: {e}")
                
                # 停止控制台（通过 SDK 调用）
                try:
                    import core
                    _ = core.call_api(
                        "web_server/stop_project",
                        {"project_name": project_name},
                        method="POST",
                        namespace="modules"
                    )
                    results["stopped_components"].append("console")
                except Exception as e:
                    logger.warning(f"停止 {project_name} 控制台时出现问题: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 停止项目 {project_name} 失败: {e}")
            return {"success": False, "error": str(e)}
    
    def restart_project(self, project_name: str, component: str = "all") -> Dict[str, Any]:
        """重启项目"""
        stop_result = self.stop_project(project_name, component)
        if not stop_result["success"]:
            return stop_result
        
        # 等待进程完全停止
        time.sleep(3)
        
        return self.start_project(project_name, component)
    
    def get_project_status(self, project_name: str = None) -> Dict[str, Any]:
        """获取项目状态（实时探测端口以更新运行标志与健康状态）"""
        if project_name:
            if project_name not in self.projects:
                return {"error": f"项目 {project_name} 不存在"}
            
            status = self.projects[project_name]
            try:
                self._update_running_flags(status)
            except Exception:
                pass

            return {
                "name": status.name,
                "namespace": status.namespace,
                "enabled": status.enabled,
                "frontend_running": status.frontend_running,
                "backend_running": status.backend_running,
                "frontend_port": status.frontend_port,
                "backend_port": status.backend_port,
                "frontend_pid": status.frontend_pid,
                "backend_pid": status.backend_pid,
                "start_time": status.start_time.isoformat() if status.start_time else None,
                "last_health_check": status.last_health_check.isoformat() if status.last_health_check else None,
                "health_status": status.health_status,
                "errors": status.errors
            }
        else:
            # 返回所有项目状态（逐项实时探测）
            result: Dict[str, Any] = {}
            for name, status in self.projects.items():
                try:
                    self._update_running_flags(status)
                except Exception:
                    pass
                result[name] = {
                    "name": status.name,
                    "namespace": status.namespace,
                    "enabled": status.enabled,
                    "frontend_running": status.frontend_running,
                    "backend_running": status.backend_running,
                    "frontend_port": status.frontend_port,
                    "backend_port": status.backend_port,
                    "health_status": status.health_status,
                    "errors": len(status.errors)
                }
            return result
    
    def get_port_usage(self) -> Dict[str, Any]:
        """获取端口使用情况"""
        port_usage = {}
        
        for project_name, status in self.projects.items():
            project_ports = {}
            
            if status.frontend_port:
                project_ports["frontend"] = {
                    "port": status.frontend_port,
                    "running": status.frontend_running,
                    "pid": status.frontend_pid
                }
            
            if status.backend_port:
                project_ports["backend"] = {
                    "port": status.backend_port,
                    "running": status.backend_running,
                    "pid": status.backend_pid
                }
            
            port_usage[project_name] = project_ports
        
        return port_usage
    
    def _should_install_dependencies(self, project_path: Path, config: core.ProjectConfigInterface) -> bool:
        """检查是否需要安装依赖"""
        try:
            # 检查是否存在 package.json 但没有 node_modules
            if (project_path / "package.json").exists():
                node_modules = project_path / "node_modules"
                if not node_modules.exists():
                    logger.info(f"检测到 package.json 但缺少 node_modules，需要安装依赖")
                    return True
                
                # 检查 node_modules 是否为空或不完整
                if node_modules.exists():
                    try:
                        # 简单检查：如果 node_modules 目录存在但几乎为空，可能需要重新安装
                        contents = list(node_modules.iterdir())
                        if len(contents) < 3:  # 通常至少会有几个基础包
                            logger.info(f"检测到 node_modules 目录不完整，需要安装依赖")
                            return True
                    except Exception:
                        # 如果无法读取 node_modules，假设需要安装
                        return True
            
            # 其他项目类型的依赖检查可以在这里添加
            return False
            
        except Exception as e:
            logger.warning(f"检查依赖时出错: {e}")
            return False
    
    def _execute_install_command(self, command: str, cwd: str = None, project_name: str = "") -> subprocess.Popen:
        """执行安装命令，使用同步方式等待完成"""
        try:
            # 检查命令是否可用
            if not self._check_command_availability(command):
                raise FileNotFoundError(f"命令不可用: {command.split()[0]}")
            
            # 在Windows上，使用shell=True并设置正确的环境
            env = os.environ.copy()
            
            # 确保PATH包含npm路径
            if "npm" in command and os.name == 'nt':
                # 添加常见的npm路径
                npm_paths = [
                    r"C:\Program Files\nodejs",
                    r"C:\Program Files (x86)\nodejs",
                    os.path.expanduser(r"~\AppData\Roaming\npm")
                ]
                current_path = env.get("PATH", "")
                for npm_path in npm_paths:
                    if os.path.exists(npm_path) and npm_path not in current_path:
                        env["PATH"] = f"{npm_path};{current_path}"
            
            logger.info(f"执行安装命令: {command} (工作目录: {cwd or '当前目录'})")
            
            # 对于安装命令，我们需要等待完成，所以使用 PIPE 来捕获输出
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 执行安装命令失败 {command}: {e}")
            raise
    
    def _terminate_process_tree(self, process: subprocess.Popen):
        """终止进程及其所有子进程"""
        try:
            if process.poll() is None:  # 进程仍在运行
                # 在Windows上，尝试终止整个进程树
                if os.name == 'nt':
                    try:
                        # 使用taskkill命令终止进程树
                        subprocess.run(
                            ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                            check=False,
                            capture_output=True
                        )
                        logger.info(f"✓ 使用taskkill终止进程树 PID: {process.pid}")
                    except Exception as e:
                        logger.warning(f"taskkill失败，使用标准方法: {e}")
                        process.terminate()
                        process.wait(timeout=10)
                else:
                    # Unix系统使用进程组终止
                    try:
                        import signal
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                        process.wait(timeout=10)
                    except Exception:
                        process.terminate()
                        process.wait(timeout=10)
        except Exception as e:
            logger.error(f"终止进程树失败: {e}")
            # 最后尝试强制终止
            try:
                process.kill()
            except:
                pass
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 开始清理项目管理器资源...")
        
        # 停止健康检查线程
        self.health_check_running = False
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
            logger.info("✓ 健康检查线程已停止")
        
        # 停止所有进程
        processes_to_clean = list(self.processes.items())
        for process_name, process in processes_to_clean:
            try:
                logger.info(f"🛑 停止进程: {process_name} (PID: {process.pid})")
                self._terminate_process_tree(process)
                logger.info(f"✓ 进程 {process_name} 已停止")
            except Exception as e:
                logger.warning(f"清理进程 {process_name} 时出现问题: {e}")
        
        # 清空进程字典
        self.processes.clear()
        
        # 重置所有项目状态
        for project_name, status in self.projects.items():
            status.frontend_running = False
            status.backend_running = False
            status.frontend_pid = None
            status.backend_pid = None
            status.health_status = "unknown"
        
        logger.info("✅ 项目管理器资源清理完成")


# 全局项目管理器实例
_project_manager_instance = None

def get_project_manager() -> ProjectManager:
    """获取项目管理器单例"""
    global _project_manager_instance
    if _project_manager_instance is None:
        _project_manager_instance = ProjectManager()
    return _project_manager_instance


# 内部实现供 API 层调用（对外 API 暴露统一在 api/modules/project_manager/project_manager.py）

def get_managed_projects():
    """获取可管理项目列表（实时同步文件系统与配置脚本）"""
    manager = get_project_manager()
    projects_list = []

    def _parse_port_from_url(url: str) -> Optional[int]:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.port:
                return int(parsed.port)
            # 未显式端口时返回协议默认端口
            if parsed.scheme in ("http", "ws"):
                return 80
            if parsed.scheme in ("https", "wss"):
                return 443
        except Exception:
            pass
        return None

    # 增量同步：发现新项目目录并加载到管理器（前端）
    try:
        if manager.frontend_projects_path.exists():
            for project_dir in manager.frontend_projects_path.iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    pname = project_dir.name
                    if pname not in manager.projects:
                        ps = manager._load_project_from_directory(project_dir)
                        if ps:
                            manager.projects[ps.name] = ps
    except Exception:
        # 发现异常时忽略，不阻塞后续流程
        pass

    # 增量同步：发现新项目目录并加载到管理器（后端）
    try:
        if manager.backend_projects_path.exists():
            for project_dir in manager.backend_projects_path.iterdir():
                if project_dir.is_dir() and not project_dir.name.startswith('.'):
                    pname = project_dir.name
                    if pname not in manager.projects:
                        ps = manager._load_backend_project_from_directory(project_dir)
                        if ps and (ps.name not in manager.projects):
                            manager.projects[ps.name] = ps
    except Exception:
        # 后端发现异常同样忽略
        pass

    # 实时清理：移除文件系统中已不存在或配置脚本丢失的项目
    for name, status in list(manager.projects.items()):
        try:
            project_dir = Path(status.project_path)
            if not project_dir.exists():
                # 清理端口注册并移除项目
                if status.frontend_port:
                    manager.port_registry.pop(status.frontend_port, None)
                if status.backend_port:
                    manager.port_registry.pop(status.backend_port, None)
                manager.projects.pop(name, None)
                continue
            # 若声明了配置脚本路径但文件已不存在，同样移除
            if status.config_script_path:
                cfg_path = Path(status.config_script_path)
                if not cfg_path.exists():
                    if status.frontend_port:
                        manager.port_registry.pop(status.frontend_port, None)
                    if status.backend_port:
                        manager.port_registry.pop(status.backend_port, None)
                    manager.projects.pop(name, None)
                    continue
        except Exception:
            # 任意异常视作项目无效，移除之
            manager.projects.pop(name, None)
            continue

    # 逐项实时读取配置并构造返回；读取失败时跳过该项目，避免返回过期数据
    for project_name, status in manager.projects.items():
        try:
            current_config = core.load_project_config(Path(status.project_path))
            status.config = current_config

            project_info = current_config.get_project_info()
            runtime_config = current_config.get_runtime_config()
            api_config = current_config.get_api_config()

            # 统一端口映射（优先使用状态端口，其次使用配置端点推断）
            frontend_dev_port = status.frontend_port or runtime_config.get("port")
            api_gateway_port = status.backend_port
            if not api_gateway_port:
                api_endpoint = api_config.get("api_endpoint") if isinstance(api_config, dict) else None
                api_gateway_port = _parse_port_from_url(api_endpoint) if api_endpoint else None
            websocket_port = None
            ws_url = api_config.get("websocket_url") if isinstance(api_config, dict) else None
            if ws_url:
                websocket_port = _parse_port_from_url(ws_url)
            if not websocket_port:
                # 明确走配置中的 WEBSOCKET_PORT，不再回退到后端端口
                websocket_port = _read_ws_port_from_config(Path(status.project_path))

            # 角色标记（优先读取 PROJECT_ROLE，未配置则回退推断）
            role = _detect_project_role(Path(status.project_path))
            project_data = {
                "name": project_info.get("name", project_name),
                "display_name": project_info.get("display_name", project_name),
                "version": project_info.get("version", "1.0.0"),
                "description": project_info.get("description", ""),
                "type": project_info.get("type", "web"),
                "role": role if role else None,
                "enabled": status.enabled,
                "project_path": status.project_path,
                "config_script_path": status.config_script_path,
                "frontend_port": status.frontend_port,
                "backend_port": status.backend_port,
                "runtime": runtime_config,
                "api": api_config,
                # 为前端提供统一 ports 字段
                "ports": {
                    "frontend_dev": frontend_dev_port if frontend_dev_port else "未设置",
                    "api_gateway": api_gateway_port if api_gateway_port else "未设置",
                    "websocket": websocket_port if websocket_port else "未设置"
                }
            }
            projects_list.append(project_data)
        except Exception:
            # 配置读取失败则跳过该项目
            continue

    return projects_list

def import_project(project_archive):
    """导入项目（强化校验：必须包含 modularflow_config.py），失败时清理解压内容"""
    manager = get_project_manager()
    temp_dir = None

    try:
        # 获取上传的文件（二进制或框架上传对象）
        if hasattr(project_archive, 'file'):
            # FastAPI 风格 UploadFile
            file_content = project_archive.file.read()
            filename = getattr(project_archive, 'filename', None) or "project_archive.zip"
        elif hasattr(project_archive, 'name') and hasattr(project_archive, 'read'):
            # Flask 风格 FileStorage
            file_content = project_archive.read()
            filename = getattr(project_archive, 'name', None) or "project_archive.zip"
        else:
            # 直接传递二进制内容
            file_content = project_archive
            filename = "project_archive.zip"
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix="project_import_")
        archive_path = os.path.join(temp_dir, filename)
        
        # 保存压缩包
        with open(archive_path, 'wb') as f:
            f.write(file_content)
        
        # 解压压缩包到临时目录
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)
        
        # 检查解压内容
        extracted_items = list(Path(extract_path).iterdir())
        if not extracted_items:
            # 清理并报错
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "压缩包为空，已取消解压并清理临时文件"}
        
        # 选择项目目录：要求该目录下存在 modularflow_config.py
        project_dir = None
        for item in extracted_items:
            if item.is_dir():
                if (item / "modularflow_config.py").exists():
                    project_dir = item
                    break
        
        if not project_dir:
            # 未发现符合规范的前端项目目录
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "导入失败：未在解压后的前端项目根目录找到 modularflow_config.py，已取消导入并清理临时文件"}
        
        project_name = project_dir.name

        # 校验项目角色标记，避免导入到错误的目录
        role = _detect_project_role(Path(project_dir))
        if role and role != "frontend":
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"导入失败：该压缩包标记为后端项目（PROJECT_ROLE={role}），请选择“后端项目”导入或使用后端导入接口"}
        
        # 复制项目到 frontend_projects 目录
        framework_root = Path(__file__).parent.parent.parent.parent
        target_dir = framework_root / "frontend_projects" / project_name
        
        # 如已存在目标目录，则直接移除旧目录（不生成备份）
        if target_dir.exists():
            shutil.rmtree(str(target_dir), ignore_errors=True)
            logger.info(f"✓ 已移除已存在的项目目录: {target_dir}")
        
        # 拷贝项目
        shutil.copytree(str(project_dir), str(target_dir))
        logger.info(f"✓ 已复制项目到: {target_dir}")
        
        # 重新发现和加载项目
        manager._discover_and_load_projects()
        
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return {
            "success": True,
            "project_name": project_name,
            "message": f"项目 {project_name} 导入成功，已自动发现和注册"
        }
    except Exception as e:
        logger.error(f"导入项目失败: {str(e)}")
        # 失败时尽量清理临时目录
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        return {"success": False, "error": str(e)}

def delete_project(project_name: str):
    """删除项目"""
    manager = get_project_manager()
    
    try:
        # 检查项目是否存在
        if project_name not in manager.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = manager.projects[project_name]
        
        # 首先停止项目
        manager.stop_project(project_name)
        
        framework_root = Path(__file__).parent.parent.parent.parent
        project_path = Path(status.project_path)
        
        # 直接删除项目目录（不生成备份）
        if project_path.exists():
            shutil.rmtree(str(project_path), ignore_errors=True)
            logger.info(f"✓ 已删除项目目录: {project_path}")
        
        # 从端口注册表中移除端口
        if status.frontend_port and status.frontend_port in manager.port_registry:
            del manager.port_registry[status.frontend_port]
        if status.backend_port and status.backend_port in manager.port_registry:
            del manager.port_registry[status.backend_port]
        
        # 从项目列表中移除
        del manager.projects[project_name]
        
        return {
            "success": True,
            "message": f"项目 {project_name} 已删除"
        }
        
    except Exception as e:
        logger.error(f"删除项目失败: {str(e)}")
        return {"success": False, "error": str(e)}

def update_project_ports(project_name: str, ports: dict):
    """更新项目端口配置"""
    manager = get_project_manager()
    
    try:
        # 检查项目是否存在
        if project_name not in manager.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = manager.projects[project_name]
        
        # 获取并验证端口
        frontend_port = ports.get('frontend_dev')
        backend_port = ports.get('api_gateway')
        
        if frontend_port and (frontend_port < 1024 or frontend_port > 65535):
            return {"success": False, "error": "前端端口必须在1024-65535范围内"}
        
        if backend_port and (backend_port < 1024 or backend_port > 65535):
            return {"success": False, "error": "后端端口必须在1024-65535范围内"}
        
        # 检查端口冲突
        if frontend_port and frontend_port in manager.port_registry:
            existing_project = manager.port_registry[frontend_port]
            if existing_project != project_name and existing_project != f"{project_name}_frontend":
                return {"success": False, "error": f"前端端口 {frontend_port} 已被项目 {existing_project} 占用"}
        
        if backend_port and backend_port in manager.port_registry:
            existing_project = manager.port_registry[backend_port]
            if existing_project != project_name and existing_project != f"{project_name}_backend":
                return {"success": False, "error": f"后端端口 {backend_port} 已被项目 {existing_project} 占用"}
        
        # 更新端口注册表
        if status.frontend_port and status.frontend_port in manager.port_registry:
            del manager.port_registry[status.frontend_port]
        if status.backend_port and status.backend_port in manager.port_registry:
            del manager.port_registry[status.backend_port]
        
        # 更新项目状态中的端口
        if frontend_port:
            status.frontend_port = frontend_port
            manager.port_registry[frontend_port] = project_name
        
        if backend_port:
            status.backend_port = backend_port
            manager.port_registry[backend_port] = f"{project_name}_backend"
        
        # 如果项目有配置脚本，尝试更新配置脚本中的端口
        if status.config_script_path:
            try:
                # 这里可以添加更新配置脚本的逻辑
                # 目前只是记录日志
                logger.info(f"项目 {project_name} 的配置脚本路径: {status.config_script_path}")
                logger.info("配置脚本端口更新功能待实现")
            except Exception as e:
                logger.warning(f"更新配置脚本失败: {e}")
        
        return {
            "success": True,
            "message": f"项目 {project_name} 端口配置已更新",
            "ports": {
                "frontend_dev": status.frontend_port,
                "api_gateway": status.backend_port
            }
        }
        
    except Exception as e:
        logger.error(f"更新项目端口配置失败: {str(e)}")
        return {"success": False, "error": str(e)}


def refresh_projects():
    """重新扫描和加载所有项目"""
    manager = get_project_manager()
    
    try:
        # 清空当前项目列表和端口注册表
        old_projects = list(manager.projects.keys())
        manager.projects.clear()
        manager.port_registry.clear()
        
        # 重新发现和加载项目（前端+后端）
        manager._discover_and_load_projects()
        manager._discover_and_load_backend_projects()
        
        new_projects = list(manager.projects.keys())
        
        return {
            "success": True,
            "message": "项目列表已刷新",
            "old_projects": old_projects,
            "new_projects": new_projects,
            "added": [p for p in new_projects if p not in old_projects],
            "removed": [p for p in old_projects if p not in new_projects]
        }
        
    except Exception as e:
        logger.error(f"刷新项目列表失败: {str(e)}")
        return {"success": False, "error": str(e)}


def install_project_dependencies(project_name: str):
    """安装项目依赖"""
    manager = get_project_manager()
    
    try:
        if project_name not in manager.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = manager.projects[project_name]
        if not status.config:
            return {"success": False, "error": f"项目 {project_name} 配置未加载"}
        
        # 检查依赖
        dep_check = status.config.check_dependencies()
        if not dep_check["success"]:
            return {
                "success": False,
                "error": f"依赖检查失败，缺少: {', '.join(dep_check['missing'])}"
            }
        
        # 执行安装
        install_success = status.config.install()
        
        return {
            "success": install_success,
            "message": f"项目 {project_name} {'安装成功' if install_success else '安装失败'}"
        }
        
    except Exception as e:
        logger.error(f"安装项目依赖失败: {str(e)}")
        return {"success": False, "error": str(e)}


def get_project_config_info(project_name: str):
    """获取项目配置信息（实时从配置脚本读取最新内容）"""
    manager = get_project_manager()
    
    try:
        if project_name not in manager.projects:
            return {"error": f"项目 {project_name} 不存在"}
        
        status = manager.projects[project_name]
        # 实时加载配置脚本
        try:
            cfg = core.load_project_config(Path(status.project_path))
            status.config = cfg
            return cfg.get_full_config()
        except Exception:
            # 回退使用已缓存配置
            if status.config:
                return status.config.get_full_config()
            return {"error": f"项目 {project_name} 配置未加载"}
        
    except Exception as e:
        logger.error(f"获取项目配置失败: {str(e)}")
        return {"error": str(e)}


def validate_project_config_script(project_name: str):
    """验证项目配置脚本"""
    manager = get_project_manager()
    
    try:
        if project_name not in manager.projects:
            return {"success": False, "error": f"项目 {project_name} 不存在"}
        
        status = manager.projects[project_name]
        if not status.config_script_path:
            return {"success": False, "error": f"项目 {project_name} 没有配置脚本"}
        
        config_file = Path(status.config_script_path)
        validation_result = core.validate_config_script(config_file)
        
        return {
            "success": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "config_script_path": status.config_script_path
        }
        
    except Exception as e:
        logger.error(f"验证配置脚本失败: {str(e)}")
        return {"success": False, "error": str(e)}
# === 图像绑定扩展：ZIP 嵌入与提取 ===
def embed_zip_into_image(image, archive):
    """将zip压缩包嵌入到PNG图片中，返回嵌入后图片的base64字符串"""
    temp_dir = None
    try:
        # 读取上传对象或二进制
        def read_upload(obj):
            if hasattr(obj, 'file'):
                return obj.file.read(), getattr(obj, 'filename', None)
            elif hasattr(obj, 'read'):
                return obj.read(), getattr(obj, 'name', None)
            elif isinstance(obj, (bytes, bytearray)):
                return obj, None
            else:
                raise ValueError("无效的上传对象")

        image_bytes, image_name = read_upload(image)
        archive_bytes, archive_name = read_upload(archive)

        # 基本校验
        if not image_bytes:
            return {"success": False, "error": "未提供图片数据"}
        if not archive_bytes:
            return {"success": False, "error": "未提供压缩包数据"}

        # 创建临时目录与写入文件
        temp_dir = tempfile.mkdtemp(prefix="embed_zip_")
        img_name = image_name or "input.png"
        zip_name = archive_name or "input.zip"

        # 统一扩展名（若上传名不含扩展）
        if not img_name.lower().endswith(".png"):
            img_name = os.path.splitext(img_name)[0] + ".png"
        if not zip_name.lower().endswith(".zip"):
            zip_name = os.path.splitext(zip_name)[0] + ".zip"

        image_path = os.path.join(temp_dir, img_name)
        archive_path = os.path.join(temp_dir, zip_name)
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        with open(archive_path, "wb") as f:
            f.write(archive_bytes)

        # 通过本地客户端调用模块API进行嵌入
        output_path = os.path.join(temp_dir, f"{os.path.splitext(img_name)[0]}_embedded.png")
        result = core.call_api(
            "smarttraven/image_binding/embed_files_to_image",
            {"image_path": image_path, "file_paths": [archive_path], "output_path": output_path},
            method="POST",
            namespace="modules"
        )
        if not isinstance(result, dict) or not result.get("success"):
            return {"success": False, "error": f"嵌入失败: {result if not isinstance(result, dict) else result.get('message')}"}

        # 读取输出并返回base64
        with open(output_path, "rb") as f:
            out_bytes = f.read()
        img_b64 = base64.b64encode(out_bytes).decode("utf-8")

        return {
            "success": True,
            "filename": os.path.basename(output_path),
            "image_base64": img_b64
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def extract_zip_from_image(image):
    """从PNG图片中提取嵌入的zip文件，返回zip的临时路径与文件清单"""
    temp_dir = None
    try:
        def read_upload(obj):
            if hasattr(obj, 'file'):
                return obj.file.read(), getattr(obj, 'filename', None)
            elif hasattr(obj, 'read'):
                return obj.read(), getattr(obj, 'name', None)
            elif isinstance(obj, (bytes, bytearray)):
                return obj, None
            else:
                raise ValueError("无效的上传对象")

        image_bytes, image_name = read_upload(image)
        if not image_bytes:
            return {"success": False, "error": "未提供图片数据"}

        temp_dir = tempfile.mkdtemp(prefix="extract_zip_")
        img_name = image_name or "input.png"
        if not img_name.lower().endswith(".png"):
            img_name = os.path.splitext(img_name)[0] + ".png"
        image_path = os.path.join(temp_dir, img_name)
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # 通过本地客户端调用模块API进行提取
        result = core.call_api(
            "smarttraven/image_binding/extract_files_from_image",
            {"image_path": image_path, "output_dir": temp_dir},
            method="POST",
            namespace="modules"
        )
        if not isinstance(result, dict) or not result.get("success"):
            return {"success": False, "error": f"提取失败: {result if not isinstance(result, dict) else result.get('message')}"}
        extracted = result.get("files", [])

        # 查找zip文件
        zip_file_info = None
        for fi in extracted:
            n = fi.get("name", "")
            if n.lower().endswith(".zip"):
                zip_file_info = fi
                break

        if not zip_file_info:
            return {"success": False, "error": "图片内未发现zip文件"}

        return {
            "success": True,
            "zip_path": zip_file_info.get("path"),
            "files": extracted
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # 不在finally删除，因为调用方可能需要读取zip_path；此函数仅返回路径供后续使用
        # 若需要自动清理，可在后续流程完成后清理
        pass


def import_project_from_image(image):
    """从PNG图片反嵌入zip并导入项目（要求项目根含 modularflow_config.py）"""
    manager = get_project_manager()
    temp_dir = None
    try:
        def read_upload(obj):
            if hasattr(obj, 'file'):
                return obj.file.read(), getattr(obj, 'filename', None)
            elif hasattr(obj, 'read'):
                return obj.read(), getattr(obj, 'name', None)
            elif isinstance(obj, (bytes, bytearray)):
                return obj, None
            else:
                raise ValueError("无效的上传对象")

        image_bytes, image_name = read_upload(image)
        if not image_bytes:
            return {"success": False, "error": "未提供图片数据"}

        temp_dir = tempfile.mkdtemp(prefix="import_from_image_")
        img_name = image_name or "input.png"
        if not img_name.lower().endswith(".png"):
            img_name = os.path.splitext(img_name)[0] + ".png"
        image_path = os.path.join(temp_dir, img_name)
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # 通过本地客户端调用模块API进行反嵌入提取
        result = core.call_api(
            "smarttraven/image_binding/extract_files_from_image",
            {"image_path": image_path, "output_dir": temp_dir},
            method="POST",
            namespace="modules"
        )
        if not isinstance(result, dict) or not result.get("success"):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"提取失败: {result if not isinstance(result, dict) else result.get('message')}"}
        extracted = result.get("files", [])

        # 找zip
        zip_file_info = None
        for fi in extracted:
            n = fi.get("name", "")
            if n.lower().endswith(".zip"):
                zip_file_info = fi
                break

        if not zip_file_info:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "图片中未找到项目压缩包(zip)"}

        zip_path = zip_file_info.get("path")
        if not zip_path or not os.path.exists(zip_path):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "提取的zip路径无效"}

        # 解压zip
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 选择项目目录（必须含 modularflow_config.py）
        extracted_items = list(Path(extract_path).iterdir())
        project_dir = None
        for item in extracted_items:
            if item.is_dir() and (item / "modularflow_config.py").exists():
                project_dir = item
                break

        if not project_dir:
            # 清理并报错
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "导入失败：未在解压后的前端项目根目录找到 modularflow_config.py"}

        project_name = project_dir.name

        # 校验项目角色标记，避免导入到错误的目录
        role = _detect_project_role(Path(project_dir))
        if role and role != "frontend":
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"导入失败：该压缩包标记为后端项目（PROJECT_ROLE={role}），请选择“后端项目”导入或使用后端导入接口"}

        # 复制到 frontend_projects
        framework_root = Path(__file__).parent.parent.parent.parent
        target_dir = framework_root / "frontend_projects" / project_name
        if target_dir.exists():
            # 直接移除旧目录（不生成备份）
            shutil.rmtree(str(target_dir), ignore_errors=True)
            logger.info(f"✓ 已移除已存在的项目目录: {target_dir}")

        shutil.copytree(str(project_dir), str(target_dir))
        logger.info(f"✓ 已复制项目到: {target_dir}")

        # 重新发现和加载
        manager._discover_and_load_projects()

        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

        return {
            "success": True,
            "project_name": project_name,
            "message": f"项目 {project_name} 已通过图片反嵌入并导入"
        }
    except Exception as e:
        logger.error(f"从图片导入项目失败: {str(e)}")
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        return {"success": False, "error": str(e)}

# 新增：导入后端项目（zip）
def import_backend_project(project_archive):
    """导入后端项目（要求根含 modularflow_config.py），复制到 backend_projects，失败时清理临时文件"""
    manager = get_project_manager()
    temp_dir = None
    try:
        # 获取上传文件内容与文件名
        if hasattr(project_archive, 'file'):
            file_content = project_archive.file.read()
            filename = getattr(project_archive, 'filename', None) or "backend_project.zip"
        elif hasattr(project_archive, 'name') and hasattr(project_archive, 'read'):
            file_content = project_archive.read()
            filename = getattr(project_archive, 'name', None) or "backend_project.zip"
        else:
            file_content = project_archive
            filename = "backend_project.zip"

        # 临时目录与保存
        temp_dir = tempfile.mkdtemp(prefix="backend_import_")
        archive_path = os.path.join(temp_dir, filename)
        with open(archive_path, 'wb') as f:
            f.write(file_content)

        # 解压
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_path)

        # 选择项目目录（要求 modularflow_config.py）
        extracted_items = list(Path(extract_path).iterdir())
        project_dir = None
        for item in extracted_items:
            if item.is_dir() and (item / "modularflow_config.py").exists():
                project_dir = item
                break

        if not project_dir:
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "导入失败：未在解压后的后端项目根目录找到 modularflow_config.py，已取消导入并清理临时文件"}

        project_name = project_dir.name

        # 校验项目角色标记，避免导入到错误的目录
        role = _detect_project_role(Path(project_dir))
        if role and role != "backend":
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"导入失败：该压缩包标记为前端项目（PROJECT_ROLE={role}），请选择“前端项目”导入或使用前端导入接口"}

        # 复制到 backend_projects
        framework_root = Path(__file__).parent.parent.parent.parent
        target_dir = framework_root / "backend_projects" / project_name
        if target_dir.exists():
            shutil.rmtree(str(target_dir), ignore_errors=True)
            logger.info(f"✓ 已移除已存在的后端项目目录: {target_dir}")

        shutil.copytree(str(project_dir), str(target_dir))
        logger.info(f"✓ 已复制后端项目到: {target_dir}")

        # 重新发现（前端+后端）
        try:
            manager._discover_and_load_projects()
            manager._discover_and_load_backend_projects()
        except Exception:
            pass

        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": True,
            "project_name": project_name,
            "message": f"后端项目 {project_name} 导入成功，已复制到 backend_projects"
        }
    except Exception as e:
        logger.error(f"导入后端项目失败: {str(e)}")
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        return {"success": False, "error": str(e)}

# 新增：从图片导入后端项目
def import_backend_project_from_image(image):
    """从PNG图片反嵌入zip并导入后端项目（要求项目根含 modularflow_config.py），复制到 backend_projects"""
    manager = get_project_manager()
    temp_dir = None
    try:
        def read_upload(obj):
            if hasattr(obj, 'file'):
                return obj.file.read(), getattr(obj, 'filename', None)
            elif hasattr(obj, 'read'):
                return obj.read(), getattr(obj, 'name', None)
            elif isinstance(obj, (bytes, bytearray)):
                return obj, None
            else:
                raise ValueError("无效的上传对象")

        image_bytes, image_name = read_upload(image)
        if not image_bytes:
            return {"success": False, "error": "未提供图片数据"}

        temp_dir = tempfile.mkdtemp(prefix="backend_import_from_image_")
        img_name = image_name or "input.png"
        if not img_name.lower().endswith(".png"):
            img_name = os.path.splitext(img_name)[0] + ".png"
        image_path = os.path.join(temp_dir, img_name)
        with open(image_path, "wb") as f:
            f.write(image_bytes)

        # 反嵌入提取
        result = core.call_api(
            "smarttraven/image_binding/extract_files_from_image",
            {"image_path": image_path, "output_dir": temp_dir},
            method="POST",
            namespace="modules"
        )
        if not isinstance(result, dict) or not result.get("success"):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"提取失败: {result if not isinstance(result, dict) else result.get('message')}"}
        extracted = result.get("files", [])

        # 找zip
        zip_file_info = None
        for fi in extracted:
            n = fi.get("name", "")
            if n.lower().endswith(".zip"):
                zip_file_info = fi
                break

        if not zip_file_info:
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "图片中未找到项目压缩包(zip)"}

        zip_path = zip_file_info.get("path")
        if not zip_path or not os.path.exists(zip_path):
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "提取的zip路径无效"}

        # 解压zip
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

        # 选择后端项目目录（必须含 modularflow_config.py）
        extracted_items = list(Path(extract_path).iterdir())
        project_dir = None
        for item in extracted_items:
            if item.is_dir() and (item / "modularflow_config.py").exists():
                project_dir = item
                break

        if not project_dir:
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": "导入失败：未在解压后的后端项目根目录找到 modularflow_config.py"}

        project_name = project_dir.name

        # 校验项目角色标记，避免导入到错误的目录
        role = _detect_project_role(Path(project_dir))
        if role and role != "backend":
            shutil.rmtree(extract_path, ignore_errors=True)
            shutil.rmtree(temp_dir, ignore_errors=True)
            return {"success": False, "error": f"导入失败：该压缩包标记为前端项目（PROJECT_ROLE={role}），请选择“前端项目”导入或使用前端导入接口"}

        # 复制到 backend_projects
        framework_root = Path(__file__).parent.parent.parent.parent
        target_dir = framework_root / "backend_projects" / project_name
        if target_dir.exists():
            shutil.rmtree(str(target_dir), ignore_errors=True)
            logger.info(f"✓ 已移除已存在的后端项目目录: {target_dir}")

        shutil.copytree(str(project_dir), str(target_dir))
        logger.info(f"✓ 已复制后端项目到: {target_dir}")

        # 重新发现（前端+后端）
        try:
            manager._discover_and_load_projects()
            manager._discover_and_load_backend_projects()
        except Exception:
            pass

        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "success": True,
            "project_name": project_name,
            "message": f"后端项目 {project_name} 已通过图片反嵌入并导入"
        }
    except Exception as e:
        logger.error(f"从图片导入后端项目失败: {str(e)}")
        try:
            if temp_dir and os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        return {"success": False, "error": str(e)}