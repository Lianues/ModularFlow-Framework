# ModularFlow 统一项目管理面板（ProjectManager）与图片嵌入导入/导出

本仓库提供一个基于 ModularFlow-Framework 的统一项目管理面板，包含：
- 后端 API 网关（FastAPI）与 Web 服务器管理
- 前端“项目管理面板”站点（静态 HTML）
- 前端项目的导入/删除/端口管理/依赖安装/启动与停止
- 将前端项目压缩包（zip）嵌入 PNG 图片导出，以及从图片中反嵌入并导入项目

核心代码参考：
- 后端入口脚本：[backend_projects/ProjectManager/start_server.py](backend_projects/ProjectManager/start_server.py)
- API 网关模块（核心）：[core/api_gateway.py](core/api_gateway.py)
- Web 服务器模块：[api/modules/web_server/web_server.py](api/modules/web_server/web_server.py)
- 项目管理器主模块：[api/modules/project_manager/impl.py](api/modules/project_manager/impl.py)
- 图片绑定模块：[api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
- 项目管理前端（静态站点）：[frontend_projects/ProjectManager/index.html](frontend_projects/ProjectManager/index.html)、[frontend_projects/ProjectManager/js/api.js](frontend_projects/ProjectManager/js/api.js)、[frontend_projects/ProjectManager/js/main.js](frontend_projects/ProjectManager/js/main.js)

示例 Next.js 项目（可由管理面板管理并示范导入/导出流程）：
- [frontend_projects/manosaba_ai/package.json](frontend_projects/manosaba_ai/package.json)

依赖清单：
- Python 依赖：[requirements.txt](requirements.txt)

UI 风格规范：
- [ui美化规范.md](ui美化规范.md)

---

## 功能特性概览

- 前端项目统一管理（发现、状态查看、启动/停止、端口配置、依赖安装）
- 一键导入前端项目（zip）
  - 安全校验：必须在解压后的前端项目根目录发现 `modularflow_config.py`，否则直接失败并清理解压内容
- 将项目 zip 嵌入 PNG 图片（“导出前端卡”）
  - 使用图片绑定模块将 zip 以自定义 PNG 块写入 png 文件尾部
  - 已取消嵌入大小限制（MAX_FILE_SIZE 无上限）
- 从嵌入图片自动反嵌入并导入项目（“从图片导入”）
  - 自动提取 zip、校验 `modularflow_config.py`、复制到 `frontend_projects/` 下并重新发现项目
- API 文档自动生成（/docs）

关键后端函数（可从 API 网关自动暴露为 HTTP 接口）：
- [project_manager.embed_zip_into_image()](api/modules/project_manager/impl.py:1201)
- [project_manager.extract_zip_from_image()](api/modules/project_manager/impl.py:1268)
- [project_manager.import_project_from_image()](api/modules/project_manager/impl.py:1322)
- [project_manager.import_project()](api/modules/project_manager/impl.py:884)

图片绑定实现要点：
- 嵌入： [api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
- 提取： [api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
- 嵌入检测： [api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
- 取消大小限制变量（已设为无限）：[api/modules/Smarttraven/image_binding/variables.py](api/modules/Smarttraven/image_binding/variables.py)

---

## 目录结构（关键路径）

- 后端启动脚本： [backend_projects/ProjectManager/start_server.py](backend_projects/ProjectManager/start_server.py)
- 后端模块：
  - API 网关（核心）：[core/api_gateway.py](core/api_gateway.py)
  - Web 服务器：[api/modules/web_server/web_server.py](api/modules/web_server/web_server.py)
  - 项目管理器：[api/modules/project_manager/impl.py](api/modules/project_manager/impl.py)
- 前端管理面板（静态 HTML）：
  - 页面：[frontend_projects/ProjectManager/index.html](frontend_projects/ProjectManager/index.html)
  - 逻辑：[frontend_projects/ProjectManager/js/main.js](frontend_projects/ProjectManager/js/main.js)
  - API 封装：[frontend_projects/ProjectManager/js/api.js](frontend_projects/ProjectManager/js/api.js)
- 示例 Next.js 项目：[frontend_projects/manosaba_ai/](frontend_projects/manosaba_ai)
- 图片绑定模块：
  - 实现：[api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
  - 变量（包含 PNG 块名与大小限制设置）：[api/modules/Smarttraven/image_binding/variables.py](api/modules/Smarttraven/image_binding/variables.py)
- 导出文件目录（图片提取默认输出）：exports/

---

## 环境要求

- Python：>= 3.8（建议 3.10+）
- Node.js：建议 >= 18.18.0（用于管理 Next.js/Vue/React 等前端项目）
- npm：建议 >= 9
- 建议安装 pnpm（更快且磁盘复用）

Python 依赖见 [requirements.txt](requirements.txt)。主要包含：
- fastapi、uvicorn、python-multipart（API 网关与上传支持）
- Pillow（图像处理）
- psutil（进程管理）

---

## 安装步骤

以下示例以 Windows PowerShell 为例。其他平台请据实际环境调整命令。

1) 克隆仓库
```bash
git clone https://github.com/Lianues/ModularFlow-Framework
cd ModularFlow
```

2) 创建并激活 Python 虚拟环境，安装依赖（可以跳过，直接安装Python依赖）
```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Windows）
.\.venv\Scripts\activate
# 激活（Linux/macOS）
# source .venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

3) 安装 Node.js 与 pnpm（强烈建议）
- 安装 Node.js（从 https://nodejs.org/ 获取 LTS 或 Current 版本，建议 >= 18.18）
- 使用 npm 全局安装 pnpm（推荐）
```bash
npm i -g pnpm
```
说明：
- pnpm 在多项目/多版本场景可显著减少磁盘占用并加速安装，前端依赖建议统一使用 pnpm。
- 仍可使用 npm/yarn，但本项目推荐 pnpm。

4) （可选）为示例前端项目安装依赖（以 Next.js 示例为例）
```bash
cd frontend_projects\manosaba_ai
pnpm install
# 或者使用 npm（不推荐）：
# npm install
```
注意：管理面板会在首次启动前端项目时尝试自动执行安装命令，但手动安装更可控。

---

## 启动与访问

推荐使用统一启动脚本（自动启动 API 网关和管理面板前端）：
```bash
# 确保在仓库根目录且已激活 Python 虚拟环境
python backend_projects/ProjectManager/start_server.py
```

启动成功后，将：
- 启动 API 网关（默认 http://localhost:8050）
- 启动管理面板前端（默认 http://localhost:8055）
- 自动打开浏览器访问管理面板

API 文档（Swagger UI）地址：
- http://localhost:8050/docs

---

## 使用管理面板

在浏览器访问管理面板（默认 http://localhost:8055），可进行：
- 刷新状态
- 启动/停止/重启项目
- 安装依赖（对某个项目执行其 `install_command`）
- 修改端口配置（前端端口/后端端口/WebSocket 端口）
- 导入项目（上传 zip）
- 删除项目（含备份）
- “导出前端卡”（zip 嵌入到 PNG）
- “从图片导入”（从 PNG 自动反嵌入 zip 并导入）

项目自动发现规则：
- 管理器会扫描 `frontend_projects/` 下的子目录，将其视为待管理的前端项目
- 每个前端项目根目录需提供 `modularflow_config.py`（用于提供项目信息/运行命令/依赖检查等）
  - 管理器会根据该配置决定安装命令、开发命令以及端口分配等

---

## 前端项目导入/导出

1) 导出前端卡（zip 嵌入 PNG）
   - 打开管理面板，点击“导出前端卡”
   - 选择前端项目压缩包（.zip）与一张 PNG 图片（.png）
   - 提交后生成“嵌入后的 PNG”，浏览器自动下载
   - 背后调用：[project_manager.embed_zip_into_image()](api/modules/project_manager/impl.py:1201)
   - 注意：已取消大小上限（[MAX_FILE_SIZE](api/modules/Smarttraven/image_binding/variables.py:18) 为无限），但请注意文件体积

2) 从图片导入项目（自动反嵌入）
   - 打开管理面板，点击“从图片导入”，选择嵌入了 zip 的 PNG
   - 将自动提取 zip 并解压
   - 解压后必须在前端项目根目录发现 `modularflow_config.py`，否则报错并清理解压的临时内容
   - 成功导入后自动复制到 `frontend_projects/` 并重新发现项目
   - 背后调用：[project_manager.import_project_from_image()](api/modules/project_manager/impl.py:1322)

3) 直接导入 zip（不通过图片）
   - 在管理面板“导入项目”处上传 zip
   - 要求同上：压缩包解压后的前端项目根目录必须包含 `modularflow_config.py`
   - 背后调用：[project_manager.import_project()](api/modules/project_manager/impl.py:884)

4) 手动提取图片内文件（仅查看/提取）
   - 背后实现： [api/modules/Smarttraven/image_binding/impl.py](api/modules/Smarttraven/image_binding/impl.py)
   - API 函数： [project_manager.extract_zip_from_image()](api/modules/project_manager/impl.py:1268)

打包 zip 提示：
- 请在前端项目的根目录（包含 `modularflow_config.py` 的目录）执行打包
- 避免将系统隐藏文件与多余的临时目录一起打包（如 `.git`、`node_modules` 可视情况排除或保留）

---

## 示例：管理 Next.js 项目

示例项目位于 [frontend_projects/manosaba_ai/](frontend_projects/manosaba_ai)。常见命令：
```bash
# 进入项目目录
cd frontend_projects\manosaba_ai

# 使用 pnpm 安装依赖（推荐）
pnpm install

# 开发模式
pnpm dev
# 或由管理面板统一启动（面板会调用项目配置中的 dev_command）
```

说明：
- 示例项目脚本位于：
  - 开发启动脚本：[frontend_projects/manosaba_ai/scripts/start-dev.js](frontend_projects/manosaba_ai/scripts/start-dev.js)
  - 生产启动脚本：[frontend_projects/manosaba_ai/scripts/start-prod.js](frontend_projects/manosaba_ai/scripts/start-prod.js)

---

## 常见问题（FAQ）

- 端口被占用
  - 管理器会为每个项目分配端口，冲突时会尝试偏移
  - 若仍冲突，可在面板中“修改端口”或关闭占用端口的进程后重试
- 上传/导入失败
  - 检查 zip 是否在根目录包含 `modularflow_config.py`
  - 查看 API 文档页面或后端控制台日志
- 图片导出后的体积过大
  - 当前未限制嵌入大小（[MAX_FILE_SIZE](image_binding_module/variables.py:18) 为无限）
  - 如需控制体积，请自行压缩项目内容或裁剪资源
- Windows 下 Node 命令不可用
  - 确保 Node.js 与 npm 已正确安装，并将其目录加入 PATH
  - 推荐使用 pnpm：`npm i -g pnpm`，再在项目内执行 `pnpm install`

---

## 安全与注意事项

- PNG 嵌入仅将 zip 数据以自定义块附加至 PNG 末尾，不做加密/签名
- 不要打开不可信来源的嵌入图片或导入未知 zip 内容
- 若将嵌入图片对外发布，请告知其中包含打包数据，以免意外泄露

---

## 开源与许可

- 本仓库中的默认示例配置与说明遵循 MIT 风格（如未另行声明）
- 具体项目的许可请参考各项目自身说明文件

---

## 附录：如何使用 npm 安装 pnpm（再次强调）

强烈建议在全局安装 pnpm，用于所有前端项目的依赖管理与运行脚本执行，加速安装并降低磁盘占用：
```bash
npm i -g pnpm
```

随后，在任意前端项目目录下：
```bash
pnpm install
pnpm dev
```

如确有需要，也可继续使用：
```bash
npm install
npm run dev
---

## API 规范（新）

本框架已全面改为“API 优先”的注册与消费方式，统一规范如下：

- 装饰器签名（推荐顺序）：
  - `@register_api(name, description, path, input_schema, output_schema)`
  - path 使用“斜杠路径”，不再使用点式名称，且不包含传输层前缀（不带 /api）。
  - 命名空间由文件路径自动解析：
    - 位于 api/modules/* 下 → 命名空间为 modules → 对外路由前缀为 /api/modules
    - 位于 api/workflow/* 下 → 命名空间为 workflow → 对外路由前缀为 /api/workflow
  - input_schema / output_schema 为 JSON Schema（draft-07/2020-12），作为唯一接口契约来源，严禁再使用 inputs/outputs 列表式定义。

- 对外 HTTP 路由：
  - 最终对外路径统一为 /api/{namespace}/{path}
  - 例如在 [python.web_server.py](api/modules/web_server/web_server.py) 中注册 path="web_server/start_project"，对外路由为：
    - POST /api/modules/web_server/start_project
    - GET  /api/modules/web_server/start_project（便捷调用，无请求体）

- SDK 调用（核心模式）：
  - 统一通过 SDK（HTTP）调用，禁止直接 import API 模块，避免耦合。
  - 斜杠路径调用示例：
    - Python（SDK）：
      - `resp = call_api("project_manager/start_project", {"project_name": "ProjectManager"}, method="POST", namespace="modules")` 见 [python.call_api()](core/api_client.py:227)
    - 若未指定 namespace，SDK 将自动按 modules → workflow 顺序尝试。

- WebSocket function_call 规范：
  - 消息结构示例：
    ```json
    {
      "type": "function_call",
      "function": "project_manager/start_project",
      "params": { "project_name": "ProjectManager" }
    }
    ```
  - function 必须为“斜杠路径”；如果包含点号“.”或反斜杠“\”，网关将返回错误（FUNCTION_PATH_FORMAT）。
  - 行为见 [python.APIGateway._handle_websocket_message()](core/api_gateway.py:676)

- OpenAPI 文档：
  - 网关在 [python.APIGateway._register_endpoints_to_fastapi()](core/api_gateway.py:449) 阶段基于注册表自动生成 OpenAPI，仅展示 api/* 层能力，严格使用 JSON Schema 描述请求与响应结构。
  - 文档路径：/docs（默认 http://localhost:8050/docs）

- 列出所有已注册 API：
  - 通过模块端点：`GET /api/modules/api_gateway/list_apis`
  - 返回字段：name（推荐作为展示名）、description、path、namespace、input_schema、output_schema
  - 实现位置：[python.api_gateway_list_apis](api/modules/api_gateway/api_gateway.py:97)

### 示例：模块级 API（image_binding）

在 [python.image_binding.py](api/modules/Smarttraven/image_binding/image_binding.py:1) 内注册模块对外 API，示例（节选）：

```python
@register_api(
    name="嵌入文件到图片",
    description="将文件嵌入到PNG图片中",
    path="smarttraven/image_binding/embed_files_to_image",
    input_schema={
        "type": "object",
        "properties": {
            "image_path": {"type": "string"},
            "file_paths": {"type": "array", "items": {"type": "string"}},
            "output_path": {"type": "string"}
        },
        "required": ["image_path", "file_paths"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "output_path": {"type": "string"},
            "relative_path": {"type": "string"}
        },
        "required": ["success"]
    }
)
def embed_files_to_image(image_path: str, file_paths: List[str], output_path: Optional[str] = None) -> Dict[str, Any]:
    ...
```

对外路由为：
- POST /api/modules/smarttraven/image_binding/embed_files_to_image

### 示例：工作流级 API（转发模块 API）

在 [python.image_binding.py](api/workflow/image_binding/image_binding.py:1) 中注册工作流 API 并通过 SDK 转发调用模块 API，示例（节选）：

```python
@register_api(
    name="工作流:获取嵌入文件信息",
    description="获取PNG图片中嵌入的文件信息",
    path="image_binding/get_embedded_files_info",
    input_schema={
        "type": "object",
        "properties": {"image_path": {"type": "string"}},
        "required": ["image_path"]
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "message": {"type": "string"},
            "files_info": {"type": "array", "items": {"type": "object", "additionalProperties": True}}
        },
        "required": ["success"]
    }
)
def api_get_embedded_files_info(image_path: str) -> Dict[str, Any]:
    payload = {"image_path": image_path}
    return call_api("smarttraven/image_binding/get_embedded_files_info", payload, method="GET", namespace="modules")
```

对外路由为：
- GET /api/workflow/image_binding/get_embedded_files_info

---

## 迁移指南（Breaking Changes）

- 已移除旧装饰器格式
  - 旧：`@register_api(name="a.b.c", inputs=[...], outputs=[...])`
  - 新：`@register_api(name, description, path, input_schema, output_schema)`
  - 说明：必须提供 JSON Schema；inputs/outputs 列表不再支持。

- 统一使用斜杠路径
  - SDK：`call_api("project_manager/start_project", {...})` 而非 `"project_manager.start_project"`
  - WebSocket：function 字段必须为斜杠路径。

- 自动命名空间
  - 装饰器不再接受/需要 namespace；路由层根据文件所在目录自动选择 modules 或 workflow。

- 文档与契约统一
  - JSON Schema 为接口契约的唯一来源；OpenAPI 基于 Schema 自动生成。

---

## 关键路径与参考实现（更新）

- 注册中心与装饰器（新规范）：[python.api_registry.register_api()](core/api_registry.py:167)
- 网关：自动发现与路由、OpenAPI、WS 规范
  - [python.APIGateway.discover_and_register_functions()](core/api_gateway.py:511)
  - [python.APIGateway._register_endpoints_to_fastapi()](core/api_gateway.py:449)
  - [python.APIGateway._handle_websocket_message()](core/api_gateway.py:676)
- SDK 客户端（斜杠路径约束）：[python.ApiClient._paths_for()](core/api_client.py:86)、[python.call_api()](core/api_client.py:227)

---

## 自检清单

为避免遗漏，请按下列清单检查：

- 适配器层（api/modules/* 与 api/workflow/*）
  - 所有 @register_api 已改为新签名（path + JSON Schema），路径为斜杠风格。
- SDK 调用
  - repo 内所有 call_api() 入参均为斜杠路径；不再出现点式字符串。
- WebSocket
  - function_call 的 function 字段为斜杠路径；网关对点式明确报错。
- 文档与路由
  - /docs 展示的路径为 /api/{namespace}/{path}，Schema 符合预期。

---

## API 列表接口与示例（获取全部注册 API 定义）

- 端点：GET /api/modules/api_gateway/list_apis
- 返回字段：
  - name（展示名，建议用于工作流编辑器的节点标题）
  - description（描述）
  - path（相对业务路径，斜杠风格）
  - namespace（modules 或 workflow）
  - input_schema（JSON Schema 请求结构）
  - output_schema（JSON Schema 响应结构）
  - total（总数）
- 实现位置： [python.api_gateway_list_apis](api/modules/api_gateway/api_gateway.py:120)

示例（curl）：
```bash
curl -s http://localhost:8050/api/modules/api_gateway/list_apis | python -m json.tool
```

示例（Python SDK）：
```python
from core.api_client import call_api

# API 网关应已启动（参考 backend_projects/ProjectManager/start_server.py 或自行启动 APIGateway）
result = call_api("api_gateway/list_apis", method="GET", namespace="modules")
print("total:", result.get("total"))
for i, api in enumerate(result.get("apis", [])[:5], start=1):
    print(f"{i}. [{api['namespace']}] {api['name']} -> {api['path']}")
```

装饰器签名（推荐顺序）：
- `@register_api(name, description, path, input_schema, output_schema)`
- 说明：
  - path 使用斜杠风格（不含 /api），命名空间由文件所在路径自动解析（api/modules → modules，api/workflow → workflow）。
  - input_schema / output_schema 均为 JSON Schema（draft-07/2020-12），是接口契约的唯一来源。
  - name 必填（用于工作流编辑器显示等）；如未填写，注册中心会使用函数名作为内部标识，但建议显式提供。
