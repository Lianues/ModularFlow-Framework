# Core 方法文档（门面 API）

本文件说明 core 门面提供的所有方法及用法，统一规范“API 优先、门面导入（import core）、端口声明在 modularflow_config.py、SDK 本地客户端使用”。阅读本文件即可，无需深入查看 core 内部脚本。

参考文件：
- [filename](core/__init__.py)
- [filename](core/api_client.py)
- [filename](core/api_registry.py)
- [filename](core/api_gateway.py)
- [filename](core/config/api_config.py)
- [filename](core/services.py)
- [filename](core/project_config_interface.py)

---

## 1) 总览：import core 门面导入

统一通过核心门面使用，不再按文件路径导入模块函数。示例（Python）：

```python
import core

# 使用 SDK 调用任意已注册 API（斜杠路径）
resp = core.call_api("project_manager/get_status",
                     {"project_name": "ProjectManager"},
                     method="GET",
                     namespace="modules")

# 获取注册表与服务管理器
reg = core.get_registry()
svc = core.get_service_manager()

# 获取 API 网关（延迟包装，避免循环依赖）
gateway = core.get_api_gateway()

# 读取统一 API 配置
cfg = core.get_api_config()
print(cfg.base_url, cfg.api_prefix)
```

---

## 2) SDK 本地客户端（ApiClient）

文件：  
- [filename](core/api_client.py)

门面导出：  
- `core.call_api(name, payload=None, method="POST", headers=None, files=None, namespace=None) → Any`  
- `core.get_client(base_url=None, api_prefix=None, timeout=None) → ApiClient`  
- `core.ApiClient`（类，完整控制客户端）

方法说明：
- `call_api(name, payload=None, method="POST", namespace=None)`  
  - 通过斜杠路径调用已注册 API；当 `namespace=None` 时自动尝试 `/api/modules` → `/api/workflow`。
  - `method="GET"` 时，`payload` 作为查询参数；`method="POST"` 时，`payload` 作为 JSON 请求体。
- `get_client(...)`  
  - 获取全局默认客户端（懒初始化），默认从 [filename](core/config/api_config.py) 读取 `base_url=/api_prefix`。
- `ApiClient` 低层方法（直接使用类）：
  - `request(method, path, json=None, params=None, files=None, headers=None) → (status:int, body:Any)`
  - `call(name, payload=None, method="POST", headers=None, files=None, namespace=None) → Any`
  - `call_get(name, params=None, headers=None, namespace=None) → Any`
  - `call_post(name, payload=None, headers=None, files=None, namespace=None) → Any`

示例：
```python
import core

# 直接使用全局客户端
result = core.call_api("web_server/list_projects", {"config_path": None}, method="GET", namespace="modules")

# 自定义客户端（例如指定不同前缀或地址）
client = core.get_client(base_url="http://127.0.0.1:8050", api_prefix="/api", timeout=20)
resp = client.call("project_manager/restart_project",
                   {"project_name": "ProjectManager"},
                   method="POST",
                   namespace="modules")
```

---

## 3) API 注册与注册表（register_api / registry）

文件：  
- [filename](core/api_registry.py)

门面导出：
- `core.register_api(path, input_schema, output_schema, name=None, description="")`（装饰器）  
- `core.get_registry() → FunctionRegistry`  
- `core.get_registered_api(path) → Callable`

装饰器说明：
- `@core.register_api(...)`
  - 参数：
    - `path`: 相对业务路径（斜杠风格，不含 `/api`），例如 `"project_manager/start_project"`
    - `input_schema`: 请求体 JSON Schema
    - `output_schema`: 响应体 JSON Schema
    - `name`: 展示名（建议显式提供；未提供时使用函数名）
    - `description`: 描述
  - 命名空间由注册函数所在文件路径自动确定：
    - 位于 `api/modules/*` → 命名空间为 `modules` → 对外路由前缀 `/api/modules`
    - 位于 `api/workflow/*` → 命名空间为 `workflow` → 对外路由前缀 `/api/workflow`

注册表说明（FunctionRegistry）：
- `get_registry().list_functions() → List[str]` 返回所有已注册的 path
- `get_registry().get_spec(path) → FunctionSpec|None` 获取 API 规范（包含 name/description/path/namespace/input_schema/output_schema）
- `core.get_registered_api(path) → Callable` 获取已注册 API 的可调用对象（按业务 path）

示例：
```python
# 在 api/modules/* 中注册模块 API
import core

@core.register_api(
    name="获取项目信息",
    description="获取项目详细信息",
    path="web_server/project_info",
    input_schema={
        "type": "object",
        "properties": {"project_name": {"type": "string"}},
        "required": ["project_name"]
    },
    output_schema={"type": "object", "additionalProperties": True}
)
def get_project_information(project_name: str):
    ...
```

---

## 4) API 网关（APIGateway）

文件：  
- [filename](core/api_gateway.py)

门面导出：
- `core.get_api_gateway(config=None, config_file=None, project_config=None) → APIGateway`（延迟包装，避免循环依赖）

APIGateway 功能：
- FastAPI 初始化与中间件（logging/error_handling/CORS/限流）
- 自动发现与注册函数为 HTTP 端点（modules/workflow）
- OpenAPI 自动生成（严格基于 JSON Schema）
- WebSocket function_call（斜杠路径）

默认路由规则：
- 对外路径统一为：`/api/{namespace}/{path}`  
  例如 path="web_server/start_project"（位于 `api/modules`） →  
  - `GET /api/modules/web_server/start_project`（便捷调用）  
  - `POST /api/modules/web_server/start_project`

WebSocket 约束：
- function 必须为斜杠路径（例如 `"project_manager/start_project"`）；若包含点号或反斜杠，网关返回错误（FUNCTION_PATH_FORMAT）。

---

## 5) 统一 API 配置（APIConfig）

文件：  
- [filename](core/config/api_config.py)

门面导出：
- `core.get_api_config() → APIConfig`  
  - `APIConfig.base_url`: 默认 `"http://localhost:8050"`  
  - `APIConfig.api_prefix`: 默认 `"/api"`（规范化，前置斜杠、去尾部斜杠）

说明：
- SDK 默认基于此配置构造请求路径与根地址。
- 网关内部也通过此配置统一文档、前缀等。

---

## 6) 统一服务管理器（ServiceManager）

文件：  
- [filename](core/services.py)

门面导出：
- `core.get_service_manager() → UnifiedServiceManager`
- `core.get_current_globals() → Any|None`（兼容旧的 globals 访问；当前可能为 None）

UnifiedServiceManager 功能：
- 动态模块发现（在仓库根 `api/*` 下递归寻址实现文件并导入）
- 服务注册与定位（function/workflow/module/globals）
- 列出已注册服务：`service_manager.list_services(service_type=None)`

---

## 7) 项目配置接口（ProjectConfigInterface）

文件：  
- [filename](core/project_config_interface.py)

门面导出：
- `core.load_project_config(project_path: Path) → ProjectConfigInterface`
- `core.ProjectConfigInterface`（接口类）
- `core.DefaultProjectConfig`（默认实现）
- `core.validate_config_script(config_file: Path) → Dict[str, Any]`

说明：
- 支持两种配置方式：
  1) 类式配置（传统）：定义 `*Config` 结尾的类，提供 `get_project_info/get_runtime_config/get_dependencies/get_api_config` 等
  2) 常量式配置（推荐）：在模块级定义 `FRONTEND_PORT/BACKEND_PORT/WEBSOCKET_PORT` 等常量，框架通过 `SimpleScriptConfig` 适配
- 必须在前端项目根目录提供 `modularflow_config.py` 以供管理器发现与配置。

示例（常量式配置片段）：
```python
# frontend_projects/ProjectManager/modularflow_config.py
FRONTEND_PORT = 8055
BACKEND_PORT = 8050
WEBSOCKET_PORT = 8051
PROJECT_NAME = "ProjectManager"
DEV_COMMAND = "python -m http.server {port}"
```

---

## 8) 模块间调用约束（API 优先）

- 严禁直接 `import` 其他模块的实现（impl）；模块间调用必须走 API 封装层（api/modules/*）或工作流层（api/workflow/*），并使用本地 SDK（core.call_api）。
- 示例（工作流转发模块 API）：
  - `core.call_api("smarttraven/image_binding/get_embedded_files_info", {"image_path": img}, method="GET", namespace="modules")`  
    封装层文件： [filename](api/workflow/image_binding/image_binding.py)

---

## 9) 端口开发注意事项

- 所有“私有端口”（前端/后端/WebSocket）必须在前端项目根的 `modularflow_config.py` 中声明：
  - 必填常量：`FRONTEND_PORT/BACKEND_PORT/WEBSOCKET_PORT`
  - 运行命令常量：`INSTALL_COMMAND/DEV_COMMAND/BUILD_COMMAND`
    - `DEV_COMMAND` 支持 `{port}` 占位符
- 统一端口读取与生成：
  - 网关统一前缀与基地址来自 [filename](core/config/api_config.py)。
  - 项目管理器提供端口使用查询与分配，参考：
    - 端口查询 API：`core.call_api("project_manager/get_ports", None, method="POST", namespace="modules")`  
      封装层： [filename](api/modules/project_manager/project_manager.py)
    - 分配策略与冲突检测： [filename](api/modules/project_manager/impl.py)

---

## 10) WebSocket function_call 约定

- 消息结构示例：
```json
{
  "type": "function_call",
  "function": "project_manager/start_project",
  "params": { "project_name": "ProjectManager" }
}
```
- function 必须为斜杠路径；点式路径或反斜杠将被网关拒绝。实现见： [filename](core/api_gateway.py)

---

## 11) 常见错误与排查

- “Cannot read properties of undefined (reading 'getProjectStatus')”
  - 前端 `window.apiClient` 未初始化；确保按顺序引入 `api.js → main.js` 并调用初始化：
    - 初始化： [filename](frontend_projects/ProjectManager/js/api.js)
    - 就绪守护： [filename](frontend_projects/ProjectManager/js/main.js)
- “函数路径格式错误（FUNCTION_PATH_FORMAT）”
  - 使用了点式路径；应改为斜杠路径：`"project_manager/start_project"`。
- “端口冲突”
  - 检查 `modularflow_config.py` 中端口设置并查看端口查询 API：
    - `core.call_api("project_manager/get_ports", None, method="POST", namespace="modules")`

---

## 12) 开发最佳实践

- 统一使用 `import core` 门面，不硬编码文件路径。
- 模块间调用必须走 API 封装层与工作流层；严禁直接 `import impl`。
- 所有对外 API 必须提供严格的 JSON Schema（input/output）。
- 端口在 `modularflow_config.py` 中声明，后端管理器统一冲突检测与分配。
- WebSocket function_call 使用斜杠路径；点式路径将被拒绝。
- SDK 调用统一斜杠路径；命名空间自动尝试 `modules → workflow`。
- OpenAPI 文档自动生成，严格基于 JSON Schema；文档地址：`/docs`。

如遇到文档与行为不一致，请以上述“API 优先、import core 门面、端口在 modularflow_config.py 声明”的原则为准，并参照上方文件链接进行校验。