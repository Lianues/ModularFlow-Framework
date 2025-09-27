"""
API 封装层：API 网关对外接口 (api/modules)
将 API 网关管理能力以 @register_api 方式统一暴露为 HTTP 端点（带 '/modules' 前缀）。
注意：实际实现位于 modules/api_gateway_module/api_gateway_module.py
"""

from typing import Any, Dict, Optional
from core.api_registry import register_api
from modules.api_gateway_module.api_gateway_module import get_api_gateway


@register_api(name="api_gateway.start", outputs=["result"], description="启动API网关服务器")
def api_gateway_start(background: bool = True, config_file: Optional[str] = None) -> Dict[str, Any]:
    gateway = get_api_gateway(config_file=config_file)
    gateway.start_server(background=background)
    return {"status": "started", "background": background}


@register_api(name="api_gateway.stop", outputs=["result"], description="停止API网关服务器")
def api_gateway_stop() -> Dict[str, Any]:
    gateway = get_api_gateway()
    gateway.stop_server()
    return {"status": "stopped"}


@register_api(name="api_gateway.info", outputs=["info"], description="获取API网关信息")
def api_gateway_info(config_file: Optional[str] = None) -> Dict[str, Any]:
    gateway = get_api_gateway(config_file=config_file)
    return {
        "endpoints": len(gateway.router.get_endpoints()),
        "middlewares": len(gateway.router.get_middlewares()),
        "websocket_connections": len(gateway.websocket_connections),
        "config": gateway.config.__dict__ if gateway.config else None
    }


@register_api(name="api_gateway.broadcast", outputs=["result"], description="向所有WebSocket连接广播消息")
async def api_gateway_broadcast(message: Dict[str, Any]) -> Dict[str, Any]:
    gateway = get_api_gateway()
    await gateway.broadcast_message(message)
    return {"broadcasted": True, "connections": len(gateway.websocket_connections)}