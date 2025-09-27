"""
API 封装层：模块能力对外接口 (api/modules)
为 web_server 模块提供统一的 @register_api 注册入口，并在路由层自动添加 '/modules' 前缀。
注意：此层仅作为对外 API 适配，实际实现位于 modules/web_server_module/web_server_module.py
"""

from typing import Any, Dict, Optional
from core.api_registry import register_api
from modules.web_server_module.web_server_module import get_web_server


@register_api(name="web_server.list_projects", outputs=["projects"], description="列出所有前端项目")
def list_frontend_projects(config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    return server.list_projects()


@register_api(name="web_server.start_project", outputs=["result"], description="启动前端项目")
def start_frontend_project(project_name: str, open_browser: bool = True, config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    success = server.start_project(project_name, open_browser)
    return {
        "success": success,
        "project": project_name,
        "message": f"项目 {project_name} {'启动成功' if success else '启动失败'}"
    }


@register_api(name="web_server.stop_project", outputs=["result"], description="停止前端项目")
def stop_frontend_project(project_name: str, config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    success = server.stop_project(project_name)
    return {
        "success": success,
        "project": project_name,
        "message": f"项目 {project_name} {'停止成功' if success else '停止失败'}"
    }


@register_api(name="web_server.restart_project", outputs=["result"], description="重启前端项目")
def restart_frontend_project(project_name: str, config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    success = server.restart_project(project_name)
    return {
        "success": success,
        "project": project_name,
        "message": f"项目 {project_name} {'重启成功' if success else '重启失败'}"
    }


@register_api(name="web_server.start_all", outputs=["results"], description="启动所有启用的前端项目")
def start_all_projects(config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    results = server.start_all_enabled_projects()
    return {
        "results": results,
        "total": len(results),
        "successful": sum(1 for success in results.values() if success)
    }


@register_api(name="web_server.stop_all", outputs=["results"], description="停止所有前端项目")
def stop_all_projects(config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    results = server.stop_all_projects()
    return {
        "results": results,
        "total": len(results),
        "successful": sum(1 for success in results.values() if success)
    }


@register_api(name="web_server.project_info", outputs=["info"], description="获取项目详细信息")
def get_project_information(project_name: str, config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    info = server.get_project_info(project_name)
    return info if info else {"error": f"项目不存在: {project_name}"}


@register_api(name="web_server.running_servers", outputs=["servers"], description="获取所有运行中的服务器")
def get_running_servers(config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    return server.dev_server.list_running_servers()


@register_api(name="web_server.create_structure", outputs=["result"], description="创建项目基础结构")
def create_project_structure(project_name: str, config_path: Optional[str] = None):
    server = get_web_server(config_path=config_path)
    success = server.create_project_structure(project_name)
    return {
        "success": success,
        "project": project_name,
        "message": f"项目结构 {'创建成功' if success else '创建失败'}"
    }


@register_api(name="web_server.load_project_config", outputs=["result"], description="加载项目特定配置")
def load_project_config(project_name: str, project_config_path: str):
    server = get_web_server()
    success = server.load_project_specific_config(project_name, project_config_path)
    return {
        "success": success,
        "project": project_name,
        "message": f"项目配置 {'加载成功' if success else '加载失败'}"
    }