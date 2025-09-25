# 动态项目管理系统

## 概述

ModularFlow Framework 现在支持动态项目发现和管理，不再需要维护静态的项目配置列表。系统会自动扫描 `frontend_projects/` 目录下的所有项目，并通过每个项目根目录下的 `modularflow_config.py` 配置脚本来获取项目信息。

## 🚀 主要特性

### 1. 动态项目发现
- 自动扫描 `frontend_projects/` 目录
- 检测每个子目录中的 `modularflow_config.py` 配置脚本
- 支持多种项目类型：React、Next.js、Vue、HTML等
- 实时项目状态监控和健康检查

### 2. 简化配置脚本
- **关键配置在文件顶部**：端口、项目名称、命令等可直接修改
- **独立运行**：不依赖框架内部结构，保持通用性
- **命令行支持**：支持 `--get-config`、`--install`、`--info` 参数
- **自动回退**：如果没有配置脚本，使用智能默认配置

### 3. 智能端口管理
- 自动端口分配和冲突检测
- 端口注册表防止重复占用
- 支持端口动态更新和范围扫描
- 项目间端口隔离

### 4. 项目导入功能
- 支持从ZIP压缩包导入项目
- 自动解压到 `frontend_projects/` 目录
- 立即发现和注册新导入的项目
- 智能备份现有项目

## 📁 项目结构要求

每个前端项目应该具有以下结构：

```
frontend_projects/
├── your_project_name/
│   ├── modularflow_config.py    # 配置脚本（推荐）
│   ├── package.json             # Node.js项目
│   ├── index.html               # HTML项目
│   └── ... (其他项目文件)
```

## 🔧 简化配置脚本格式

### 新的简化格式（推荐）

```python
#!/usr/bin/env python3
"""
项目配置脚本 - 简化版本
"""

# ===========================================
# 🔧 主要配置 - 可直接修改
# ===========================================

# 端口配置
FRONTEND_PORT = 3000
BACKEND_PORT = 6500
WEBSOCKET_PORT = 6500

# 项目信息
PROJECT_NAME = "MyProject"
DISPLAY_NAME = "我的项目"
PROJECT_TYPE = "nextjs"  # nextjs, react, vue, html

# 运行命令
INSTALL_COMMAND = "npm install"
DEV_COMMAND = "npm run dev"
BUILD_COMMAND = "npm run build"

# ===========================================
# 📋 详细配置 - 一般不需要修改
# ===========================================

import json
import subprocess
import os

class MyProjectConfig:
    """项目配置类"""
    
    def get_project_info(self):
        return {
            "name": PROJECT_NAME,
            "display_name": DISPLAY_NAME,
            "version": "1.0.0",
            "description": f"基于{PROJECT_TYPE}的前端项目",
            "type": PROJECT_TYPE,
            "author": "Your Name",
            "license": "MIT"
        }
    
    def get_runtime_config(self):
        return {
            "port": FRONTEND_PORT,
            "install_command": INSTALL_COMMAND,
            "dev_command": DEV_COMMAND,
            "build_command": BUILD_COMMAND
        }
    
    def get_dependencies(self):
        if PROJECT_TYPE in ["react", "nextjs", "vue"]:
            return {
                "required_tools": ["node", "npm"],
                "optional_tools": ["yarn", "pnpm"],
                "node_version": ">=18.0.0",
                "npm_version": ">=8.0.0"
            }
        else:
            return {
                "required_tools": [],
                "optional_tools": []
            }
    
    def get_api_config(self):
        return {
            "api_endpoint": f"http://localhost:{BACKEND_PORT}/api/v1",
            "websocket_url": f"ws://localhost:{WEBSOCKET_PORT}/ws",
            "cors_origins": [f"http://localhost:{FRONTEND_PORT}"]
        }
    
    def install(self):
        """执行项目安装"""
        if INSTALL_COMMAND:
            try:
                subprocess.run(INSTALL_COMMAND.split(), cwd=os.getcwd(), check=True)
                return True
            except subprocess.CalledProcessError:
                return False
        return True


# 主函数
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description=f"{DISPLAY_NAME} 配置脚本")
    parser.add_argument("--get-config", action="store_true", help="获取配置信息")
    parser.add_argument("--install", action="store_true", help="安装项目")
    parser.add_argument("--info", action="store_true", help="显示项目信息")
    
    args = parser.parse_args()
    config = MyProjectConfig()
    
    if args.get_config:
        print(json.dumps({
            "project": config.get_project_info(),
            "runtime": config.get_runtime_config(),
            "dependencies": config.get_dependencies(),
            "api": config.get_api_config()
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
```

### 调试工具

```bash
# 测试配置脚本
python frontend_projects/your_project/modularflow_config.py --info

# 验证项目发现
python test_project_manager_final.py

# 调试配置加载
python debug_config_loading.py
```