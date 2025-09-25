#!/usr/bin/env python3
"""
ProjectManager 项目配置脚本
"""

# ===========================================
# 🔧 主要配置 - 可直接修改
# ===========================================

# 端口配置
FRONTEND_PORT = 8055
BACKEND_PORT = 8050
WEBSOCKET_PORT = 8051

# 项目信息
PROJECT_NAME = "ProjectManager"
DISPLAY_NAME = "项目管理器"
PROJECT_TYPE = "html"

# 运行命令
INSTALL_COMMAND = "echo 'No installation required for HTML project'"
DEV_COMMAND = "python -m http.server {port}"
BUILD_COMMAND = "echo 'No build required for HTML project'"

# ===========================================
# 📋 详细配置 - 一般不需要修改
# ===========================================

import json
import subprocess
import os


class ProjectManagerConfig:
    """ProjectManager 项目配置"""
    
    def get_project_info(self):
        return {
            "name": PROJECT_NAME,
            "display_name": DISPLAY_NAME,
            "version": "1.0.0",
            "description": "ModularFlow框架的项目管理器前端界面",
            "type": PROJECT_TYPE,
            "author": "ModularFlow Team",
            "license": "MIT"
        }
    
    def get_runtime_config(self):
        return {
            "port": FRONTEND_PORT,
            "install_command": INSTALL_COMMAND,
            "dev_command": f"python -m http.server {FRONTEND_PORT}",
            "build_command": BUILD_COMMAND,
            "static_files": ["index.html", "js/", "css/", "assets/"]
        }
    
    def get_dependencies(self):
        return {
            "required_tools": ["python"],
            "optional_tools": ["nginx", "apache"],
            "python_version": ">=3.7",
            "browser_support": ["Chrome", "Firefox", "Safari", "Edge"]
        }
    
    def get_api_config(self):
        return {
            "api_endpoint": f"http://localhost:{BACKEND_PORT}/api/v1",
            "websocket_url": f"ws://localhost:{WEBSOCKET_PORT}/ws",
            "cors_origins": [f"http://localhost:{FRONTEND_PORT}"]
        }
    
    def get_env_config(self):
        return {
            "development": {
                "API_BASE_URL": f"http://localhost:{BACKEND_PORT}/api/v1",
                "WS_URL": f"ws://localhost:{WEBSOCKET_PORT}/ws",
                "DEBUG": "true"
            },
            "production": {
                "API_BASE_URL": "https://api.modularflow.com/api/v1",
                "WS_URL": "wss://api.modularflow.com/ws",
                "DEBUG": "false"
            }
        }
    
    def install(self):
        """执行项目安装"""
        print(f"🚀 准备 {DISPLAY_NAME}...")
        try:
            # HTML项目通常不需要安装步骤
            print("✅ HTML项目无需安装依赖")
            return True
        except Exception as e:
            print(f"❌ 准备失败: {e}")
            return False


# 主函数
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{DISPLAY_NAME} 配置脚本")
    parser.add_argument("--get-config", action="store_true", help="获取配置信息")
    parser.add_argument("--install", action="store_true", help="安装项目")
    parser.add_argument("--info", action="store_true", help="显示项目信息")
    
    args = parser.parse_args()
    config = ProjectManagerConfig()
    
    if args.get_config:
        print(json.dumps({
            "project": config.get_project_info(),
            "runtime": config.get_runtime_config(),
            "dependencies": config.get_dependencies(),
            "api": config.get_api_config(),
            "environment": config.get_env_config()
        }, indent=2, ensure_ascii=False))
    elif args.install:
        config.install()
    elif args.info:
        info = config.get_project_info()
        print(f"项目: {info['display_name']} ({info['name']})")
        print(f"类型: {info['type']}")
        print(f"端口: {FRONTEND_PORT}")
    else:
        parser.print_help()