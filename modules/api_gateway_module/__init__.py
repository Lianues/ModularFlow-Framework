"""
API网关模块

提供统一的API入口点、路由管理、认证授权和中间件功能。
与ModularFlow Framework的服务管理器和函数注册系统无缝集成。
"""

from .api_gateway_module import (
    APIGateway,
    APIRouter,
    Middleware,
    GatewayConfig,
    get_api_gateway,
    create_api_gateway_for_project
)

__version__ = "1.0.0"
__all__ = [
    "APIGateway",
    "APIRouter",
    "Middleware",
    "GatewayConfig",
    "get_api_gateway",
    "create_api_gateway_for_project"
]