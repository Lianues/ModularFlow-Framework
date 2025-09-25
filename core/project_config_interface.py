#!/usr/bin/env python3
"""
ModularFlow 项目配置接口规范

定义了统一的项目配置脚本接口，所有前端项目的配置脚本都应该遵循这个接口。
配置脚本应该命名为 modularflow_config.py 并放置在项目根目录下。
"""

import json
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class ProjectConfigInterface(ABC):
    """项目配置接口基类"""
    
    @abstractmethod
    def get_project_info(self) -> Dict[str, Any]:
        """
        获取项目基本信息
        
        Returns:
            包含以下字段的字典:
            - name: 项目名称（用于内部标识）
            - display_name: 显示名称
            - version: 版本号
            - description: 项目描述
            - type: 项目类型（react, nextjs, vue, html等）
            - author: 作者
            - license: 许可证
        """
        pass
    
    @abstractmethod
    def get_runtime_config(self) -> Dict[str, Any]:
        """
        获取运行时配置
        
        Returns:
            包含以下字段的字典:
            - port: 默认端口号
            - install_command: 安装命令
            - dev_command: 开发命令
            - build_command: 构建命令
            - test_command: 测试命令（可选）
            - lint_command: 代码检查命令（可选）
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> Dict[str, Any]:
        """
        获取依赖配置
        
        Returns:
            包含以下字段的字典:
            - required_tools: 必需工具列表
            - optional_tools: 可选工具列表（可选）
            - node_version: Node.js版本要求（可选）
            - npm_version: npm版本要求（可选）
            - python_version: Python版本要求（可选）
        """
        pass
    
    @abstractmethod
    def get_api_config(self) -> Dict[str, Any]:
        """
        获取API配置
        
        Returns:
            包含以下字段的字典:
            - api_endpoint: API端点
            - websocket_url: WebSocket URL
            - cors_origins: CORS允许的源列表
        """
        pass
    
    def get_env_config(self) -> Dict[str, Dict[str, str]]:
        """
        获取环境变量配置（可选）
        
        Returns:
            按环境分组的环境变量字典:
            - development: 开发环境变量
            - production: 生产环境变量
        """
        return {}
    
    def check_dependencies(self) -> Dict[str, Any]:
        """
        检查依赖是否满足
        
        Returns:
            检查结果字典:
            - success: 是否成功
            - missing: 缺失的依赖列表
            - warnings: 警告信息列表
        """
        results = {"success": True, "missing": [], "warnings": []}
        dependencies = self.get_dependencies()
        
        for tool in dependencies.get("required_tools", []):
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    results["success"] = False
                    results["missing"].append(tool)
            except (FileNotFoundError, subprocess.TimeoutExpired):
                results["success"] = False
                results["missing"].append(tool)
        
        return results
    
    def install(self) -> bool:
        """
        执行项目安装步骤
        
        Returns:
            是否安装成功
        """
        runtime_config = self.get_runtime_config()
        install_command = runtime_config.get("install_command")
        
        if not install_command:
            return True  # 没有安装命令，认为安装成功
        
        try:
            subprocess.run(install_command.split(), check=True, cwd=Path.cwd())
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        获取完整的项目配置
        
        Returns:
            完整配置字典
        """
        return {
            "project": self.get_project_info(),
            "runtime": self.get_runtime_config(),
            "dependencies": self.get_dependencies(),
            "api": self.get_api_config(),
            "environment": self.get_env_config()
        }


class IndependentConfigWrapper(ProjectConfigInterface):
    """独立配置脚本的包装器"""
    
    def __init__(self, config_instance):
        self.config = config_instance
    
    def get_project_info(self) -> Dict[str, Any]:
        if hasattr(self.config, 'get_project_info'):
            return self.config.get_project_info()
        return {}
    
    def get_runtime_config(self) -> Dict[str, Any]:
        if hasattr(self.config, 'get_runtime_config'):
            return self.config.get_runtime_config()
        return {}
    
    def get_dependencies(self) -> Dict[str, Any]:
        if hasattr(self.config, 'get_dependencies'):
            return self.config.get_dependencies()
        return {"required_tools": [], "optional_tools": []}
    
    def get_api_config(self) -> Dict[str, Any]:
        if hasattr(self.config, 'get_api_config'):
            return self.config.get_api_config()
        return {}
    
    def get_env_config(self) -> Dict[str, Dict[str, str]]:
        if hasattr(self.config, 'get_env_config'):
            return self.config.get_env_config()
        return {}
    
    def check_dependencies(self) -> Dict[str, Any]:
        if hasattr(self.config, 'check_dependencies'):
            return self.config.check_dependencies()
        return super().check_dependencies()
    
    def install(self) -> bool:
        if hasattr(self.config, 'install'):
            return self.config.install()
        return super().install()


class DefaultProjectConfig(ProjectConfigInterface):
    """默认项目配置实现"""
    
    def __init__(self, project_name: str, project_path: Path):
        self.project_name = project_name
        self.project_path = project_path
        self._detect_project_type()
    
    def _detect_project_type(self):
        """自动检测项目类型"""
        if (self.project_path / "package.json").exists():
            try:
                with open(self.project_path / "package.json", 'r', encoding='utf-8') as f:
                    package_json = json.load(f)
                
                dependencies = package_json.get("dependencies", {})
                dev_dependencies = package_json.get("devDependencies", {})
                
                if "next" in dependencies or "next" in dev_dependencies:
                    self.project_type = "nextjs"
                elif "react" in dependencies:
                    self.project_type = "react"
                elif "vue" in dependencies:
                    self.project_type = "vue"
                else:
                    self.project_type = "nodejs"
            except:
                self.project_type = "nodejs"
        elif (self.project_path / "index.html").exists():
            self.project_type = "html"
        else:
            self.project_type = "unknown"
    
    def get_project_info(self) -> Dict[str, Any]:
        return {
            "name": self.project_name,
            "display_name": self.project_name.replace('_', ' ').title(),
            "version": "1.0.0",
            "description": f"基于{self.project_type}的前端项目",
            "type": self.project_type,
            "author": "Unknown",
            "license": "MIT"
        }
    
    def get_runtime_config(self) -> Dict[str, Any]:
        config = {
            "port": 3000,
            "install_command": "",
            "dev_command": "",
            "build_command": "",
        }
        
        if self.project_type in ["react", "nextjs", "vue", "nodejs"]:
            config.update({
                "install_command": "npm install",
                "dev_command": "npm run dev" if self.project_type != "nextjs" else "npm run dev",
                "build_command": "npm run build",
                "test_command": "npm test",
                "lint_command": "npm run lint"
            })
        elif self.project_type == "html":
            config["port"] = 8080
        
        return config
    
    def get_dependencies(self) -> Dict[str, Any]:
        if self.project_type in ["react", "nextjs", "vue", "nodejs"]:
            return {
                "required_tools": ["node", "npm"],
                "optional_tools": ["yarn", "pnpm"],
                "node_version": ">=16.0.0",
                "npm_version": ">=8.0.0"
            }
        else:
            return {
                "required_tools": [],
                "optional_tools": []
            }
    
    def get_api_config(self) -> Dict[str, Any]:
        port = self.get_runtime_config()["port"]
        return {
            "api_endpoint": "http://localhost:8050/api/v1",
            "websocket_url": "ws://localhost:8050/ws",
            "cors_origins": [f"http://localhost:{port}"]
        }


def load_project_config(project_path: Path) -> ProjectConfigInterface:
    """
    加载项目配置
    
    Args:
        project_path: 项目路径
        
    Returns:
        项目配置实例
    """
    config_file = project_path / "modularflow_config.py"
    
    if config_file.exists():
        # 动态导入配置脚本
        import importlib.util
        import sys
        
        spec = importlib.util.spec_from_file_location("project_config", config_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["project_config"] = module
            spec.loader.exec_module(module)
            
            # 查找配置类 - 支持独立配置类（不继承接口）
            config_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    attr_name.endswith('Config') and
                    hasattr(attr, 'get_project_info') and
                    hasattr(attr, 'get_runtime_config')):
                    config_class = attr
                    break
            
            if config_class:
                # 创建配置实例
                config_instance = config_class()
                
                # 如果不是 ProjectConfigInterface 的子类，创建一个包装器
                if not isinstance(config_instance, ProjectConfigInterface):
                    return IndependentConfigWrapper(config_instance)
                else:
                    return config_instance
    
    # 如果没有找到配置脚本或配置类，使用默认配置
    return DefaultProjectConfig(project_path.name, project_path)


def validate_config_script(config_file: Path) -> Dict[str, Any]:
    """
    验证配置脚本是否符合接口规范
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        验证结果
    """
    result = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    if not config_file.exists():
        result["errors"].append("配置文件不存在")
        return result
    
    try:
        # 尝试加载配置
        config = load_project_config(config_file.parent)
        
        # 检查必需方法
        required_methods = [
            "get_project_info",
            "get_runtime_config", 
            "get_dependencies",
            "get_api_config"
        ]
        
        for method in required_methods:
            if not hasattr(config, method):
                result["errors"].append(f"缺少必需方法: {method}")
            else:
                try:
                    getattr(config, method)()
                except Exception as e:
                    result["errors"].append(f"方法 {method} 执行失败: {str(e)}")
        
        if not result["errors"]:
            result["valid"] = True
            
    except Exception as e:
        result["errors"].append(f"加载配置脚本失败: {str(e)}")
    
    return result