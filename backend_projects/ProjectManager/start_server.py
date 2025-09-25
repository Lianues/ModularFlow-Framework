#!/usr/bin/env python3
"""
ProjectManager 统一项目管理面板启动脚本

该脚本负责：
1. 启动API网关服务器（端口8050）
2. 启动项目管理面板前端（端口8080）
3. 提供统一的项目生命周期管理功能
"""

import sys
import os
import json
import time
import threading
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加框架根目录到Python路径
framework_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(framework_root))

try:
    from modules.api_gateway_module import get_api_gateway
    from modules.web_server_module import get_web_server
    from modules.ProjectManager.project_manager_module.project_manager_module import get_project_manager
    from core.services import get_service_manager
    from core.function_registry import get_registry
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print(f"请确保在框架根目录 {framework_root} 下运行此脚本")
    sys.exit(1)


class ProjectManagerBackend:
    """ProjectManager 统一项目管理面板后端管理器"""
    
    def __init__(self):
        self.api_gateway = None
        self.web_server = None
        self.project_manager = None
        self.framework_root = framework_root
        self.project_config = self._get_default_config()
        
        print("🚀 初始化统一项目管理面板...")
        
        # 确保工作目录正确
        os.chdir(self.framework_root)
        
        # 初始化服务管理器
        self.service_manager = get_service_manager()
        print("✓ 服务管理器初始化完成")
        
        # 加载所有模块
        self.load_modules()
        
        # 初始化项目管理器
        self.project_manager = get_project_manager()
        print("✓ 项目管理器初始化完成")
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "project": {
                "name": "ProjectManager",
                "display_name": "统一项目管理面板",
                "version": "2.0.0",
                "description": "用于统一管理前后端项目、端口与生命周期的更高一级控制台",
                "type": "management_console",
                "author": "ModularFlow Team",
                "license": "MIT"
            },
            "backend": {
                "api_gateway": {
                    "enabled": True,
                    "port": 8050,
                    "host": "localhost",
                    "cors_origins": ["http://localhost:8055", "*"],
                    "endpoint": "http://localhost:8050/api/v1"
                },
                "websocket": {
                    "enabled": True,
                    "path": "/ws",
                    "port": 8050
                }
            },
            "frontend": {
                "enabled": True,
                "port": 8055,
                "path": "frontend_projects/ProjectManager",
                "type": "html",
                "dev_command": "python -m http.server 8055",
                "auto_open_browser": True
            }
        }
    
    def load_modules(self):
        """加载必要的模块"""
        try:
            # 加载项目模块
            loaded_count = self.service_manager.load_project_modules()
            print(f"✓ 已加载 {loaded_count} 个模块")
            
            # 使用项目配置初始化API网关和Web服务器
            if self.project_config:
                self.api_gateway = get_api_gateway(project_config=self.project_config)
                
                # 为Web服务器创建前端项目配置
                frontend_config = self._create_frontend_config()
                self.web_server = get_web_server(project_config=frontend_config)
            else:
                # 使用默认配置
                self.api_gateway = get_api_gateway()
                self.web_server = get_web_server()
            
            print("✓ API网关和Web服务器初始化完成")
            
        except Exception as e:
            print(f"❌ 加载模块失败: {e}")
            raise
    
    def _create_frontend_config(self):
        """从项目配置创建前端配置"""
        if not self.project_config:
            return None
        
        project_info = self.project_config.get("project", {})
        frontend_config = self.project_config.get("frontend", {})
        backend_config = self.project_config.get("backend", {})
        api_gateway_config = backend_config.get("api_gateway", {})
        
        # 构建前端项目配置
        return {
            "projects": [
                {
                    "name": project_info.get("name", "ProjectManager"),
                    "display_name": project_info.get("display_name", "统一项目管理面板"),
                    "type": "html",
                    "path": frontend_config.get("path", "frontend_projects/ProjectManager"),
                    "port": frontend_config.get("port", 8080),
                    "api_endpoint": f"http://localhost:{api_gateway_config.get('port', 8050)}/api/v1",
                    "dev_command": frontend_config.get("dev_command", ""),
                    "description": project_info.get("description", "统一项目管理控制台"),
                    "enabled": True
                }
            ],
            "global_config": {
                "cors_origins": api_gateway_config.get("cors_origins", ["*"]),
                "api_base_url": f"http://localhost:{api_gateway_config.get('port', 8050)}",
                "websocket_url": f"ws://localhost:{api_gateway_config.get('port', 8050)}/ws"
            }
        }
    
    def start_api_gateway(self, background=True):
        """启动API网关"""
        try:
            backend_config = self.project_config.get("backend", {})
            api_gateway_config = backend_config.get("api_gateway", {})
            
            if not api_gateway_config.get("enabled", True):
                print("⚠️ API网关在配置中被禁用")
                return False
            
            port = api_gateway_config.get("port", 8050)
            
            print("🌐 启动API网关服务器...")
            self.api_gateway.start_server(background=background)
            print("✅ API网关启动成功")
            print(f"📚 API文档: http://localhost:{port}/docs")
            return True
        except Exception as e:
            print(f"❌ API网关启动失败: {e}")
            return False
    
    def start_frontend_server(self, open_browser=True):
        """启动前端服务器"""
        try:
            project_info = self.project_config.get("project", {})
            frontend_config = self.project_config.get("frontend", {})
            project_name = project_info.get("name", "ProjectManager")
            port = frontend_config.get("port", 8080)
            auto_open = frontend_config.get("auto_open_browser", True) and open_browser
            
            print("⚛️ 启动前端服务器...")
            
            # 使用新的项目管理器启动前端项目
            result = self.project_manager.start_project(project_name, "frontend")
            if result.get("success", False):
                print("✅ 前端服务器启动成功")
                print(f"🌐 管理面板: http://localhost:{port}")
                
                # 自动打开浏览器
                if auto_open:
                    import webbrowser
                    import threading
                    def open_browser_delayed():
                        import time
                        time.sleep(2)
                        try:
                            webbrowser.open(f"http://localhost:{port}")
                            print(f"🌐 浏览器已打开: http://localhost:{port}")
                        except Exception as e:
                            print(f"⚠️ 无法自动打开浏览器: {e}")
                    
                    threading.Thread(target=open_browser_delayed, daemon=True).start()
                
                return True
            else:
                error_msg = result.get("error", "未知错误")
                print(f"❌ 前端服务器启动失败: {error_msg}")
                return False
        except Exception as e:
            print(f"❌ 启动前端服务器失败: {e}")
            return False
    
    def check_services_status(self):
        """检查所有服务状态"""
        print("\n📊 服务状态检查:")
        
        backend_config = self.project_config.get("backend", {})
        api_gateway_config = backend_config.get("api_gateway", {})
        frontend_config = self.project_config.get("frontend", {})
        
        api_port = api_gateway_config.get("port", 8050)
        frontend_port = frontend_config.get("port", 8080)
        
        # 检查API网关
        try:
            import requests
            response = requests.get(f"http://localhost:{api_port}/api/v1/health", timeout=2)
            if response.status_code == 200:
                print("✅ API网关: 运行正常")
            else:
                print("⚠️ API网关: 响应异常")
        except:
            print("❌ API网关: 无法连接")
        
        # 检查前端服务器
        try:
            import requests
            response = requests.get(f"http://localhost:{frontend_port}", timeout=2)
            if response.status_code == 200:
                print("✅ 前端: 运行正常")
            else:
                print("⚠️ 前端: 响应异常")
        except:
            print("❌ 前端: 无法连接")
        
        # 检查项目管理器
        if self.project_manager:
            managed_projects = len(self.project_manager.projects)
            print(f"✅ 项目管理器: 管理 {managed_projects} 个项目")
        else:
            print("❌ 项目管理器: 未初始化")
        
        # 检查注册的函数
        registry = get_registry()
        functions = registry.list_functions()
        project_manager_functions = [f for f in functions if f.startswith('project_manager.')]
        print(f"📝 项目管理函数: {len(project_manager_functions)} 个")
        
        print()
    
    def start_all_services(self):
        """启动所有服务"""
        print("🎯 启动统一项目管理面板完整服务...\n")
        
        # 显示配置信息
        if self.project_config:
            project_info = self.project_config.get("project", {})
            managed_projects = self.project_config.get("managed_projects", [])
            
            print(f"📋 项目: {project_info.get('display_name', '统一项目管理面板')}")
            print(f"📋 版本: {project_info.get('version', '1.0.0')}")
            print(f"📋 描述: {project_info.get('description', '用于统一管理前后端项目、端口与生命周期的更高一级控制台')}")
            print(f"📋 管理项目数: {len(managed_projects)}")
            print()
        
        # 启动API网关 (后台运行)
        if not self.start_api_gateway(background=True):
            return False
        
        # 等待API网关启动
        print("⏳ 等待API网关启动...")
        time.sleep(3)
        
        # 启动前端服务器
        if not self.start_frontend_server(open_browser=True):
            return False
        
        # 等待服务启动
        print("⏳ 等待所有服务启动...")
        time.sleep(3)
        
        # 检查服务状态
        self.check_services_status()
        
        return True
    
    def stop_all_services(self):
        """停止所有服务"""
        print("🛑 停止所有服务...")
        
        try:
            project_info = self.project_config.get("project", {})
            project_name = project_info.get("name", "ProjectManager")
            
            # 首先清理项目管理器（这会停止所有被管理的项目）
            if self.project_manager:
                print("🧹 清理项目管理器...")
                self.project_manager.cleanup()
            
            # 停止前端服务器
            if self.project_manager:
                print("🛑 停止前端服务器...")
                self.project_manager.stop_project(project_name, "frontend")
            
            # 停止API网关
            if self.api_gateway:
                print("🛑 停止API网关...")
                self.api_gateway.stop_server()
            
            # 额外的端口清理检查
            self._force_cleanup_ports()
            
            print("✅ 所有服务已停止")
        
        except Exception as e:
            print(f"⚠️ 停止服务时出现问题: {e}")
    
    def _force_cleanup_ports(self):
        """强制清理占用的端口"""
        try:
            backend_config = self.project_config.get("backend", {})
            frontend_config = self.project_config.get("frontend", {})
            api_gateway_config = backend_config.get("api_gateway", {})
            
            api_port = api_gateway_config.get("port", 8050)
            frontend_port = frontend_config.get("port", 8080)
            
            # 检查并清理占用端口的进程
            import subprocess
            import os
            
            if os.name == 'nt':  # Windows
                for port in [api_port, frontend_port]:
                    try:
                        # 查找占用端口的进程
                        result = subprocess.run(
                            ['netstat', '-ano', '|', 'findstr', f':{port}'],
                            shell=True,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.stdout:
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if 'LISTENING' in line:
                                    parts = line.split()
                                    if len(parts) >= 5:
                                        pid = parts[-1]
                                        try:
                                            # 终止占用端口的进程
                                            subprocess.run(
                                                ['taskkill', '/F', '/PID', pid],
                                                check=False,
                                                capture_output=True
                                            )
                                            print(f"✓ 清理端口 {port} 占用进程 PID: {pid}")
                                        except:
                                            pass
                    except Exception as e:
                        print(f"⚠️ 清理端口 {port} 时出现问题: {e}")
            
        except Exception as e:
            print(f"⚠️ 强制清理端口时出现问题: {e}")


def main():
    """主函数"""
    backend = ProjectManagerBackend()
    
    try:
        # 启动所有服务
        if backend.start_all_services():
            backend_config = backend.project_config.get("backend", {})
            frontend_config = backend.project_config.get("frontend", {})
            api_gateway_config = backend_config.get("api_gateway", {})
            websocket_config = backend_config.get("websocket", {})
            managed_projects = backend.project_config.get("managed_projects", [])
            
            api_port = api_gateway_config.get("port", 8050)
            frontend_port = frontend_config.get("port", 8080)
            websocket_path = websocket_config.get("path", "/ws")
            
            print("🎉 统一项目管理面板启动完成！")
            print("\n📋 可用服务:")
            print(f"  • API网关: http://localhost:{api_port}")
            print(f"  • API文档: http://localhost:{api_port}/docs")
            print(f"  • 管理面板: http://localhost:{frontend_port}")
            print(f"  • WebSocket: ws://localhost:{api_port}{websocket_path}")
            print(f"  • 管理项目数: {len(managed_projects)}")
            
            if managed_projects:
                print(f"\n📁 被管理的项目:")
                for project in managed_projects:
                    print(f"  • {project['name']} ({project['namespace']})")
            
            print("\n💡 管理面板将自动在浏览器中打开")
            print("\n按 Ctrl+C 停止所有服务")
            
            # 保持运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n⏹️ 收到停止信号...")
                backend.stop_all_services()
                print("👋 再见！")
        
        else:
            print("❌ 服务启动失败")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        backend.stop_all_services()
        sys.exit(1)


if __name__ == "__main__":
    main()