"""
API 封装层：模块能力对外接口 (api/modules)
为 ProjectManager 模块提供统一的 @register_api 注册入口，并在路由层自动添加 '/modules' 前缀。
注意：此层仅作为对外 API 适配，实际实现位于 modules/ProjectManager/project_manager_module/project_manager_module.py
"""

from typing import Any, Dict, Optional
from core.api_registry import register_api
from modules.ProjectManager.project_manager_module.project_manager_module import (
    get_project_manager,
    # 直接复用模块内现有的顶层函数（更复杂的参数处理已在实现层封装）
    import_project as _import_project,
    delete_project as _delete_project,
    update_project_ports as _update_project_ports,
    refresh_projects as _refresh_projects,
    install_project_dependencies as _install_project_dependencies,
    get_project_config_info as _get_project_config_info,
    validate_project_config_script as _validate_project_config_script,
    embed_zip_into_image as _embed_zip_into_image,
    extract_zip_from_image as _extract_zip_from_image,
    import_project_from_image as _import_project_from_image,
)


# 基础项目生命周期

@register_api(name="project_manager.start_project", outputs=["result"], description="启动被管理的项目")
def start_project(project_name: str, component: str = "all") -> Dict[str, Any]:
    manager = get_project_manager()
    return manager.start_project(project_name, component)


@register_api(name="project_manager.stop_project", outputs=["result"], description="停止被管理的项目")
def stop_project(project_name: str, component: str = "all") -> Dict[str, Any]:
    manager = get_project_manager()
    return manager.stop_project(project_name, component)


@register_api(name="project_manager.restart_project", outputs=["result"], description="重启被管理的项目")
def restart_project(project_name: str, component: str = "all") -> Dict[str, Any]:
    manager = get_project_manager()
    return manager.restart_project(project_name, component)


# 项目状态与端口

@register_api(name="project_manager.get_status", outputs=["status"], description="获取项目状态")
def get_status(project_name: Optional[str] = None) -> Dict[str, Any]:
    manager = get_project_manager()
    return manager.get_project_status(project_name)


@register_api(name="project_manager.get_ports", outputs=["ports"], description="获取端口使用情况")
def get_ports() -> Dict[str, Any]:
    manager = get_project_manager()
    return manager.get_port_usage()


@register_api(name="project_manager.health_check", outputs=["health"], description="执行健康检查")
def health_check() -> Dict[str, Any]:
    manager = get_project_manager()
    results = {}
    for name in manager.projects.keys():
        manager._check_project_health(name)
        results[name] = manager.get_project_status(name)
    return results


@register_api(name="project_manager.get_managed_projects", outputs=["projects"], description="获取可管理项目列表")
def get_managed_projects() -> Any:
    # 直接复用实现层函数的逻辑较为复杂，这里可简单组合，也可直接复用实现层已有顶层函数
    # 为保持行为一致，这里复用实现层函数（若未来抽象为 manager 方法，可改为 manager 调用）
    manager = get_project_manager()
    # 直接使用实现层已有的顶层函数以保持输出结构一致
    from modules.ProjectManager.project_manager_module.project_manager_module import get_managed_projects as _get_managed_projects
    return _get_managed_projects()


# 项目导入/删除/配置

@register_api(name="project_manager.import_project", outputs=["result"], description="导入项目（要求根含 modularflow_config.py）")
def import_project(project_archive) -> Dict[str, Any]:
    return _import_project(project_archive)


@register_api(name="project_manager.delete_project", outputs=["result"], description="删除项目")
def delete_project(project_name: str) -> Dict[str, Any]:
    return _delete_project(project_name)


@register_api(name="project_manager.update_ports", outputs=["result"], description="更新项目端口配置")
def update_ports(project_name: str, ports: dict) -> Dict[str, Any]:
    return _update_project_ports(project_name, ports)


@register_api(name="project_manager.refresh_projects", outputs=["result"], description="重新扫描和加载所有项目")
def refresh_projects() -> Dict[str, Any]:
    return _refresh_projects()


@register_api(name="project_manager.install_project", outputs=["result"], description="安装项目依赖")
def install_project(project_name: str) -> Dict[str, Any]:
    return _install_project_dependencies(project_name)


@register_api(name="project_manager.get_project_config", outputs=["config"], description="获取项目配置信息")
def get_project_config(project_name: str) -> Dict[str, Any]:
    return _get_project_config_info(project_name)


@register_api(name="project_manager.validate_config_script", outputs=["result"], description="验证项目配置脚本")
def validate_config_script(project_name: str) -> Dict[str, Any]:
    return _validate_project_config_script(project_name)


# ZIP 嵌入/提取/导入能力（复用实现层）

@register_api(name="project_manager.embed_zip_into_image", outputs=["result"], description="将zip嵌入PNG并返回base64")
def embed_zip_into_image(image, archive) -> Dict[str, Any]:
    return _embed_zip_into_image(image, archive)


@register_api(name="project_manager.extract_zip_from_image", outputs=["result"], description="从PNG提取zip并返回清单")
def extract_zip_from_image(image) -> Dict[str, Any]:
    return _extract_zip_from_image(image)


@register_api(name="project_manager.import_project_from_image", outputs=["result"], description="从PNG反嵌入zip并导入项目")
def import_project_from_image(image) -> Dict[str, Any]:
    return _import_project_from_image(image)