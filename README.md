# ModularFlow 统一项目管理面板（ProjectManager）与图片嵌入导入/导出

本仓库提供一个基于 ModularFlow-Framework 的统一项目管理面板，包含：
- 后端 API 网关（FastAPI）与 Web 服务器管理
- 前端“项目管理面板”站点（静态 HTML）
- 前端项目的导入/删除/端口管理/依赖安装/启动与停止
- 将前端项目压缩包（zip）嵌入 PNG 图片导出，以及从图片中反嵌入并导入项目

核心代码参考：
- 后端入口脚本：[backend_projects/ProjectManager/start_server.py](backend_projects/ProjectManager/start_server.py)
- API 网关模块：[modules/api_gateway_module/api_gateway_module.py](modules/api_gateway_module/api_gateway_module.py)
- Web 服务器模块：[modules/web_server_module/web_server_module.py](modules/web_server_module/web_server_module.py)
- 项目管理器主模块：[modules/ProjectManager/project_manager_module/project_manager_module.py](modules/ProjectManager/project_manager_module/project_manager_module.py)
- 图片绑定模块：[image_binding_module/image_binding_module.py](image_binding_module/image_binding_module.py)
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
- [project_manager.embed_zip_into_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1134)
- [project_manager.extract_zip_from_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1202)
- [project_manager.import_project_from_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1257)
- [project_manager.import_project()](modules/ProjectManager/project_manager_module/project_manager_module.py:805)

图片绑定实现要点：
- 嵌入： [ImageBindingModule.embed_files_to_image()](image_binding_module/image_binding_module.py:170)
- 提取： [ImageBindingModule.extract_files_from_image()](image_binding_module/image_binding_module.py:256)
- 嵌入检测： [ImageBindingModule.is_image_with_embedded_files()](image_binding_module/image_binding_module.py:386)
- 取消大小限制变量（已设为无限）：[MAX_FILE_SIZE](image_binding_module/variables.py:18)

---

## 目录结构（关键路径）

- 后端启动脚本： [backend_projects/ProjectManager/start_server.py](backend_projects/ProjectManager/start_server.py)
- 后端模块：
  - API 网关：[modules/api_gateway_module/api_gateway_module.py](modules/api_gateway_module/api_gateway_module.py)
  - Web 服务器：[modules/web_server_module/web_server_module.py](modules/web_server_module/web_server_module.py)
  - 项目管理器：[modules/ProjectManager/project_manager_module/project_manager_module.py](modules/ProjectManager/project_manager_module/project_manager_module.py)
- 前端管理面板（静态 HTML）：
  - 页面：[frontend_projects/ProjectManager/index.html](frontend_projects/ProjectManager/index.html)
  - 逻辑：[frontend_projects/ProjectManager/js/main.js](frontend_projects/ProjectManager/js/main.js)
  - API 封装：[frontend_projects/ProjectManager/js/api.js](frontend_projects/ProjectManager/js/api.js)
- 示例 Next.js 项目：[frontend_projects/manosaba_ai/](frontend_projects/manosaba_ai)
- 图片绑定模块：
  - 实现：[image_binding_module/image_binding_module.py](image_binding_module/image_binding_module.py)
  - 变量（包含 PNG 块名与大小限制设置）：[image_binding_module/variables.py](image_binding_module/variables.py)
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
   - 背后调用：[project_manager.embed_zip_into_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1134)
   - 注意：已取消大小上限（[MAX_FILE_SIZE](image_binding_module/variables.py:18) 为无限），但请注意文件体积

2) 从图片导入项目（自动反嵌入）
   - 打开管理面板，点击“从图片导入”，选择嵌入了 zip 的 PNG
   - 将自动提取 zip 并解压
   - 解压后必须在前端项目根目录发现 `modularflow_config.py`，否则报错并清理解压的临时内容
   - 成功导入后自动复制到 `frontend_projects/` 并重新发现项目
   - 背后调用：[project_manager.import_project_from_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1257)

3) 直接导入 zip（不通过图片）
   - 在管理面板“导入项目”处上传 zip
   - 要求同上：压缩包解压后的前端项目根目录必须包含 `modularflow_config.py`
   - 背后调用：[project_manager.import_project()](modules/ProjectManager/project_manager_module/project_manager_module.py:805)

4) 手动提取图片内文件（仅查看/提取）
   - 背后实现： [ImageBindingModule.extract_files_from_image()](image_binding_module/image_binding_module.py:256)
   - API 函数： [project_manager.extract_zip_from_image()](modules/ProjectManager/project_manager_module/project_manager_module.py:1202)

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