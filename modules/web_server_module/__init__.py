"""
Web服务器模块

提供轻量级的Web服务器功能，用于开发和测试环境。
与API网关模块配合使用，提供完整的前后端服务能力。
"""

from .web_server_module import WebServer, StaticFileServer, DevServer, get_web_server

__version__ = "1.0.0"
__all__ = ["WebServer", "StaticFileServer", "DevServer", "get_web_server"]