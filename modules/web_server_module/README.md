# Web服务器模块

Web服务器模块提供轻量级的Web服务器功能，专门用于前端项目的开发和测试环境。支持多种前端技术栈的开发服务器管理。

## 功能特性

- 🚀 **多项目支持**: 同时管理多个前端项目的开发服务器
- 📁 **静态文件服务**: 为HTML/CSS/JS项目提供静态文件服务器
- 🔧 **开发服务器**: 支持React、Vue、Angular等现代前端框架
- 🌐 **自动浏览器**: 启动项目时自动打开浏览器
- 📊 **状态监控**: 实时监控服务器运行状态和端口使用
- 🔄 **进程管理**: 完整的服务器进程生命周期管理
- ⚙️ **配置驱动**: 通过JSON配置文件管理所有项目设置

## 架构组件

### 1. WebServer 主类
- **职责**: 前端项目和服务器管理的核心控制器
- **特性**: 项目配置加载、服务器生命周期管理、浏览器集成

### 2. DevServer 开发服务器管理器
- **职责**: 管理各种类型的开发服务器进程
- **特性**: 进程监控、状态跟踪、自动重启、端口管理

### 3. StaticFileServer 静态文件服务器
- **职责**: 为静态项目提供HTTP文件服务
- **特性**: 自定义目录、多线程处理、HTTP标准兼容

## 支持的项目类型

### 静态项目 (html/static)
- **描述**: 纯HTML、CSS、JavaScript项目
- **服务器**: 内置Python HTTP服务器
- **特性**: 零配置启动，开发友好

### React项目 (react)
- **描述**: Create React App或自定义React项目
- **服务器**: npm start / yarn start
- **端口**: 默认3000

### Vue项目 (vue)
- **描述**: Vue CLI或Vite驱动的Vue项目
- **服务器**: npm run dev / yarn dev
- **端口**: 默认3001

### Angular项目 (angular)
- **描述**: Angular CLI项目
- **服务器**: ng serve
- **端口**: 默认4200

### Python项目 (python)
- **描述**: Flask、Django或其他Python Web框架
- **服务器**: 自定义或默认Python HTTP服务器

## 配置文件

Web服务器模块使用 `frontend_projects/frontend-projects.json` 进行项目配置：

```json
{
  "projects": [
    {
      "name": "web_admin",
      "display_name": "管理后台",
      "type": "react",
      "path": "frontend_projects/web_admin",
      "port": 3000,
      "api_endpoint": "http://localhost:8050/api/v1",
      "build_command": "npm run build",
      "dev_command": "npm start",
      "description": "基于React的管理后台界面",
      "dependencies": {
        "react": "^18.0.0",
        "axios": "^1.0.0"
      },
      "enabled": true
    }
  ]
}
```

## 使用方法

### 1. 启动Web服务器管理

```python
from modules.web_server_module import get_web_server

# 获取Web服务器实例
server = get_web_server()

# 列出所有项目
projects = server.list_projects()
for project in projects:
    print(f"项目: {project['display_name']} - 状态: {project['server_status']['status']}")
```

### 2. 通过函数注册系统使用

```python
from core.function_registry import get_registered_function

# 启动指定项目
start_project = get_registered_function("web_server.start_project")
result = start_project("SmartTavern", open_browser=True)

# 查看运行中的服务器
get_servers = get_registered_function("web_server.running_servers")
servers = get_servers()
```

### 3. 项目管理操作

```python
server = get_web_server()

# 启动项目
server.start_project("web_admin", open_browser=True)

# 停止项目
server.stop_project("web_admin")

# 重启项目
server.restart_project("web_admin")

# 获取项目详细信息
info = server.get_project_info("web_admin")
```

### 4. 批量操作

```python
# 启动所有启用的项目
results = server.start_all_enabled_projects()

# 停止所有项目
results = server.stop_all_projects()
```

## 项目结构创建

Web服务器模块可以自动创建项目的基础结构：

### HTML项目结构
```
project_name/
├── index.html          # 主页面
├── css/               # 样式文件目录
├── js/                # JavaScript文件目录
└── assets/            # 静态资源目录
```

### React项目结构
```
project_name/
├── package.json       # 项目配置和依赖
├── public/            # 公共资源
├── src/               # 源代码
├── README.md          # 项目文档
└── .gitignore         # Git忽略文件
```

## 注册的函数

以下函数已注册到ModularFlow Framework：

### 项目管理
- `web_server.list_projects` - 列出所有前端项目
- `web_server.start_project` - 启动指定前端项目
- `web_server.stop_project` - 停止指定前端项目
- `web_server.restart_project` - 重启指定前端项目

### 批量操作
- `web_server.start_all` - 启动所有启用的项目
- `web_server.stop_all` - 停止所有项目

### 信息查询
- `web_server.project_info` - 获取项目详细信息
- `web_server.running_servers` - 获取所有运行中的服务器

### 项目结构
- `web_server.create_structure` - 创建项目基础结构

## 服务器状态

每个项目服务器具有以下状态：

- `stopped` - 服务器已停止
- `starting` - 服务器正在启动
- `running` - 服务器运行中
- `error` - 服务器出现错误

## 端口管理

- 每个项目都有独立的端口配置
- 避免端口冲突的自动检测
- 支持动态端口分配（如果默认端口被占用）

## 进程管理

### 进程监控
- 实时跟踪服务器进程状态
- PID管理和进程生命周期控制
- 异常退出检测和日志记录

### 自动清理
- 停止项目时自动终止相关进程
- 资源泄漏防护
- 优雅关闭处理

## 开发工作流

### 典型开发流程

1. **项目配置**: 在 `frontend_projects/frontend-projects.json` 中添加项目配置
2. **结构创建**: 使用 `create_structure` 创建项目基础文件
3. **开发服务器**: 使用 `start_project` 启动开发环境
4. **实时开发**: 自动重载和热更新（取决于项目类型）
5. **测试部署**: 使用 `build_command` 构建生产版本

### 多项目开发

```python
# 同时启动多个项目进行开发
server = get_web_server()

# 启动React管理后台
server.start_project("web_admin")  # http://localhost:3000

# 启动Vue仪表板
server.start_project("vue_dashboard")  # http://localhost:3001

# 启动SmartTavern
server.start_project("SmartTavern")  # http://localhost:6601
```

## 与API网关集成

Web服务器模块与API网关模块无缝集成：

- 前端项目通过配置的 `api_endpoint` 连接后端API
- 支持开发环境的代理设置
- 自动CORS配置处理

## 错误处理

### 常见错误及解决方案

1. **端口被占用**
   - 自动检测并提示端口冲突
   - 建议备用端口或手动修改配置

2. **项目路径不存在**
   - 自动创建项目目录
   - 提供基础文件结构模板

3. **依赖缺失**
   - 检测 `package.json` 和依赖安装状态
   - 提供安装建议和命令

## 性能优化

- **并发处理**: 支持多个服务器同时运行
- **资源监控**: 内存和CPU使用监控
- **缓存优化**: 静态文件缓存控制
- **热重载**: 开发时的快速重载机制

## 扩展支持

### 自定义项目类型

可以通过扩展配置支持新的项目类型：

```python
# 添加新的项目类型支持
custom_project = {
    "name": "custom_app",
    "type": "custom",
    "dev_command": "custom-dev-server --port 5000",
    "port": 5000
}
```

### 中间件支持

未来版本将支持开发服务器中间件：
- 代理中间件
- 认证中间件  
- 日志中间件
- 自定义处理器

## 兼容性

- **操作系统**: Windows, macOS, Linux
- **Python**: 3.8+
- **Node.js**: 14+ (用于前端项目)
- **浏览器**: Chrome, Firefox, Safari, Edge

## 故障排除

### 诊断工具

```python
# 获取详细的项目信息用于诊断
info = server.get_project_info("project_name")
print(f"路径存在: {info['path_exists']}")
print(f"文件数量: {info['files_count']}")
print(f"服务器状态: {info['server_status']}")
```

### 日志查看

Web服务器模块使用标准Python日志系统，可以通过配置日志级别来获取详细的调试信息。