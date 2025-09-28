# 开发注意事项（ModularFlow Framework）

本文件为本仓库的开发约束与最佳实践说明，统一规范“API 优先、门面导入（import core）、端口声明在 modularflow_config.py”。

建议所有后端开发者、前端集成者、模块作者遵循以下约定，确保跨模块/跨项目协作的一致性与可维护性。

---

## 1) 门面导入范式（import core）

- 统一通过核心门面使用，不再直接按文件路径导入模块函数。
- 统一范式：
  - Python（SDK 调用）：
    - `result = core.call_api("project_manager/get_status", {"project_name": "ProjectManager"}, method="GET", namespace="modules")`
      见 [python.call_api()](core/api_client.py:227)
  - 获取注册器与服务管理器：
    - `reg = core.get_registry()` 见 [python.get_registry()](core/api_registry.py:133)
    - `svc = core.get_service_manager()` 见 [python.get_service_manager()](core/services.py:204)
  - 获取 API 网关实例（延迟包装，避免循环依赖）：
    - `gateway = core.get_api_gateway()` 见 [python.get_api_gateway()](core/api_gateway.py:831)
  - 读取统一 API 配置：
    - `cfg = core.get_api_config()` 见 [python.get_api_config()](core/config/api_config.py:29)

说明：
- “门面导入”屏蔽了内部文件结构变动，避免硬编码路径与循环依赖。
- 任何涉及跨模块调用，优先通过 core 门面 + API 调用完成。

---

## 2) 模块之间互相调用必须走 API 接口

- 禁止直接 `import` 其他模块的实现层（impl）；模块间调用必须走“API 封装层（api/modules/*）或工作流层（api/workflow/*）”。
- 调用示例（工作流转发模块 API）：
  - `core.call_api("smarttraven/image_binding/get_embedded_files_info", {"image_path": img}, method="GET", namespace="modules")`
    见 [python.api_get_embedded_files_info()](api/workflow/image_binding/image_binding.py:98)

原因：
- 统一契约（JSON Schema）有助于文档生成（OpenAPI）与前后端一致。
- 降低耦合、便于替换实现、支持跨进程/跨服务调用。

---

## 3) 本地客户端（SDK）介绍

- SDK 提供统一 HTTP 调用（自动适配 modules/workflow 命名空间）：
  - `core.call_api(name, payload, method="POST", namespace=None)`：
    - 当 `namespace=None` 时按 `/api/modules` → `/api/workflow` 顺序尝试。
    - 指定命名空间：`namespace="modules"` 或 `namespace="workflow"`。
- 低层方法：
  - [python.ApiClient.request()](core/api_client.py:92) 统一 GET/POST。
  - [python.ApiClient.call_get()](core/api_client.py:167)、[python.ApiClient.call_post()](core/api_client.py:186) 便捷封装。
- SDK 全局客户端：
  - `client: ApiClient = core.get_client()` 见 [python.get_client()](core/api_client.py:216)

示例：
```python
import core

# GET 获取状态
status = core.call_api("project_manager/get_status", {"project_name": "ProjectManager"}, method="GET", namespace="modules")

# POST 启动项目
resp = core.call_api("project_manager/start_project", {"project_name": "ProjectManager", "component": "frontend"}, method="POST", namespace="modules")
```

---

## 4) 核心方法清单（通过 core 门面暴露）

- SDK 与客户端
  - [python.import(core.call_api)](core/__init__.py:12)
  - [python.import(core.get_client)](core/__init__.py:12)
  - [python.import(core.ApiClient)](core/__init__.py:12)
- API 配置
  - [python.import(core.get_api_config)](core/__init__.py:13)
- 注册中心与服务
  - [python.import(core.get_registry)](core/__init__.py:20)
  - [python.import(core.get_registered_api)](core/__init__.py:21)
  - [python.import(core.register_api)](core/__init__.py:22)
  - [python.import(core.get_service_manager)](core/__init__.py:15)
  - [python.import(core.get_current_globals)](core/__init__.py:15)
- API 网关
  - [python.function(core.get_api_gateway)](core/__init__.py:18)（延迟导入包装，避免循环依赖）

---

## 5) 端口开发注意事项

- 所有“私有端口”（前端/后端/WebSocket）必须在项目根的 `modularflow_config.py` 中声明：
  - 必填常量：`FRONTEND_PORT`、`BACKEND_PORT`、`WEBSOCKET_PORT`
  - 运行命令常量：`INSTALL_COMMAND`、`DEV_COMMAND`、`BUILD_COMMAND`
    - `DEV_COMMAND` 支持 `{port}` 占位符。
  - 参考示例： [python.modularflow_config.py](frontend_projects/ProjectManager/modularflow_config.py:1)
- 统一端口读取与生成：
  - 网关统一前缀与基地址由 [python.get_api_config()](core/config/api_config.py:29) 提供（默认 `base_url=http://localhost:8050`，`api_prefix=/api`）。
  - 项目管理模块提供端口使用查询：
    - `core.call_api("project_manager/get_ports", None, method="POST", namespace="modules")`
      见 [python.get_ports()](api/modules/project_manager/project_manager.py:101)
- 端口冲突与分配（后端侧）：
  - 项目管理器内部维护端口注册表并在冲突时偏移，详见：
    - [python.ProjectManager._allocate_port()](api/modules/project_manager/impl.py:155)

---

## 6) API 注册规范（封装层职责）

- 仅在 `api/modules/*` 与 `api/workflow/*` 注册对外 API，统一使用 [python.decorator(core.register_api)](core/__init__.py:22)。
- 内部实现文件（impl.py）仅用于具体逻辑，不直接对外暴露；统一由封装层暴露 API。
- 参考：
  - 模块封装层： [python.image_binding.image_binding.py](api/modules/Smarttraven/image_binding/image_binding.py:1)
  - 工作流封装层： [python.workflow.image_binding.py](api/workflow/image_binding/image_binding.py:1)
  - 项目管理封装层： [python.project_manager.project_manager.py](api/modules/project_manager/project_manager.py:1)
  - 内部实现（供封装层调用）： [python.project_manager.impl.py](api/modules/project_manager/impl.py:1)

---

## 7) WebSocket function_call 约束

- function 名必须为“斜杠路径”；点式与反斜杠将被网关拒绝：
  - 详见 [python.APIGateway._handle_websocket_message()](core/api_gateway.py:676)
- 示例：
```json
{
  "type": "function_call",
  "function": "project_manager/start_project",
  "params": { "project_name": "ProjectManager" }
}
```

---

## 8) 前端调用约定（管理面板）

- 前端 API 客户端读取 `mf_frontend_config.json` 以推导 `baseURL` 与 `apiPrefix`：
  - 见 [javascript.APIClient](frontend_projects/ProjectManager/js/api.js:6)
- 管理面板加载数据前确保客户端已就绪：
  - 见 [javascript.ProjectManagerApp.ensureApiClientReady()](frontend_projects/ProjectManager/js/main.js:289)
- 统一调用：
  - `GET /api/modules/project_manager/get_status` → `window.apiClient.getProjectStatus()`
  - `POST /api/modules/project_manager/start_project` → `window.apiClient.startProject(name)`

---

## 9) 最佳实践清单

- 使用 `import core` 门面，不硬编码文件路径。
- 模块间调用必须走 API，严禁直接 `import impl`。
- 所有对外 API 必须提供严格的 JSON Schema（input/output）。
- 端口在 `modularflow_config.py` 中声明，后端管理器负责冲突检测与分配。
- WebSocket function_call 使用斜杠路径；点式路径将被拒绝。
- SDK 调用统一斜杠路径；命名空间自动尝试 `modules → workflow`。
- 文档与契约来源统一使用 JSON Schema；OpenAPI 自动生成校验。

---

## 10) 常见错误与排查

- “Cannot read properties of undefined (reading 'getProjectStatus')”
  - 前端 `window.apiClient` 未初始化；确保按顺序引入 `api.js → main.js` 并调用
    - [javascript.initApiClient()](frontend_projects/ProjectManager/js/api.js:363)
    - [javascript.ensureApiClientReady()](frontend_projects/ProjectManager/js/main.js:289)
- “函数路径格式错误（FUNCTION_PATH_FORMAT）”
  - 使用了点式路径；应改为斜杠路径：`"project_manager/start_project"`。
- “端口冲突”
  - 检查 `modularflow_config.py` 中端口设置并查看
    - [python.ProjectManager.get_port_usage()](api/modules/project_manager/impl.py:565)
    - 后端日志提示的自动偏移。

---

如遇到文档与行为不一致，请以上述“API 优先、import core 门面、端口在 modularflow_config.py 声明”的原则为准，并参照核心代码链接进行校验。