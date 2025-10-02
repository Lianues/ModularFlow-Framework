# SmartTraven / Chat Branches 模块（分支重试对话）

本模块在 SmartTraven 命名空间下提供“分支重试对话”能力：不可变消息树 + 可变会话路径。支持：创建对话、追加楼层、修剪、切分支（并新建会话与归档旧会话）、导入/导出标准聊天文件（chat-branches）、导出当前分支为 OpenAI Chat messages、输出分支情况表。

- 实现引擎（内存）：[`impl.py`](api/modules/SmartTraven/chat_branches/impl.py)
- API 封装与注册：[`chat_branches.py`](api/modules/SmartTraven/chat_branches/chat_branches.py)
- 示例对话文件：[`branch_demo.json`](backend_projects/SmartTraven/data/conversations/branch_demo.json)
- 测试脚本：[`test_chat_branches.py`](api/modules/SmartTraven/chat_branches/test_chat_branches.py)

参考开发规范：[`DEVELOPMENT_NOTES.md`](DEVELOPMENT_NOTES.md)


一、数据模型（简述）
- 节点树不可变：每条消息是一个节点（role, content, parent_id, depth, sibling_ord）；同一父节点的子序用于“分支 j/n”。
- 会话路径可变：一条会话是一条路径视图（root → ... → leaf）。仅 active 会话允许修改；切分支会新建新的 active 会话并归档旧会话。

chat-branches 标准文件
- 仅保留 pid/role/content、children（有序）和 active_path
- 文件示例：[`branch_demo.json`](backend_projects/SmartTraven/data/conversations/branch_demo.json)
- 用途：外部系统存放/管理多个聊天文件 → 通过“导入接口”加载本模块 → 导出视图或再次导出 chat-branches 文件


二、API 一览（路径基于新规范，命名空间 modules）
说明：所有 API 均注册于 [`chat_branches.py`](api/modules/SmartTraven/chat_branches/chat_branches.py) 并通过 core 门面暴露。以下为“斜杠 path”（不含 /api 前缀）。

核心分支操作
- POST modules/smarttraven/chat_branches/create_conversation
  - 入参：{ user_id?, title? }
  - 出参：{ conversation_id, session_id, path: [] }
- GET/POST modules/smarttraven/chat_branches/get_path
  - 入参：{ session_id }
  - 出参：{ session_id, status, path: [] }
- POST modules/smarttraven/chat_branches/append
  - 入参：{ session_id, role: user|assistant|system, content }
  - 出参：{ session_id, status, path: [] }
- POST modules/smarttraven/chat_branches/truncate
  - 入参：{ session_id, keep_depth >= 1 }
  - 出参：{ session_id, status, path: [] }
- POST modules/smarttraven/chat_branches/switch
  - 入参：{ session_id, at_depth >= 2, direction: left|right }
  - 出参：{ old_session_id, new_session_id, path: [] }
- GET/POST modules/smarttraven/chat_branches/branch_indicator
  - 入参：{ session_id, depth >= 2 }
  - 出参：{ j, n }（若无效则为空）

导入/导出与视图
- GET/POST modules/smarttraven/chat_branches/export
  - 入参：{ conversation_id }
  - 出参：chat-branches 标准文件
- POST modules/smarttraven/chat_branches/import
  - 入参：{ doc: chat-branches 标准文件 }
  - 出参：{ conversation_id, active_session_id }
- GET/POST modules/smarttraven/chat_branches/openai_messages
  - 入参：{ session_id }
  - 出参：{ conversation_id, session_id, messages: [{ role, content }] }
- GET/POST modules/smarttraven/chat_branches/branch_table
  - 入参：{ session_id }
  - 出参：{ latest: { depth, j, n, node_id }, levels: [{ depth, j, n, node_id }, ...] }

列表
- GET/POST modules/smarttraven/chat_branches/list_conversations
- GET/POST modules/smarttraven/chat_branches/list_sessions
  - 入参：{ conversation_id }


三、快速开始
1) 启动 API 网关并加载模块（在本仓库根目录执行）
- 方式 A：测试脚本会自动启动（见下）
- 方式 B：手动启动（Python 内部）
  - 在脚本中写入：
    - gateway = core.get_api_gateway(); core.get_service_manager().load_project_modules(); gateway.start_server(background=True)

2) 导入示例对话（chat-branches）
- curl 示例（假设网关端口 8050）：
  - curl -s -X POST http://127.0.0.1:8050/api/modules/smarttraven/chat_branches/import -H "Content-Type: application/json" --data-binary @backend_projects/SmartTraven/data/conversations/branch_demo.json

3) 导出当前分支为 OpenAI messages
- curl -s "http://127.0.0.1:8050/api/modules/smarttraven/chat_branches/openai_messages?session_id=SESSION_ID"

4) 获取分支情况表（含最新楼层 j/n）
- curl -s "http://127.0.0.1:8050/api/modules/smarttraven/chat_branches/branch_table?session_id=SESSION_ID"


四、通过 SDK（core.call_api）调用示例
Python
```python
import core, json

# 启动网关并加载模块
gateway = core.get_api_gateway()
sm = core.get_service_manager()
sm.load_project_modules()
gateway.start_server(background=True)

# 导入 chat-branches 文件
with open("backend_projects/SmartTraven/data/conversations/branch_demo.json", "r", encoding="utf-8") as f:
    doc = json.load(f)
imp = core.call_api("smarttraven/chat_branches/import", {"doc": doc}, method="POST", namespace="modules")
print("import:", imp)

sess = imp["active_session_id"]
print("openai:", core.call_api("smarttraven/chat_branches/openai_messages", {"session_id": sess}, method="GET", namespace="modules"))
print("table:", core.call_api("smarttraven/chat_branches/branch_table", {"session_id": sess}, method="GET", namespace="modules"))

# 核心操作
print("append:", core.call_api("smarttraven/chat_branches/append", {"session_id": sess, "role": "user", "content": "再解释下切分支"}, method="POST", namespace="modules"))
print("truncate:", core.call_api("smarttraven/chat_branches/truncate", {"session_id": sess, "keep_depth": 2}, method="POST", namespace="modules"))
sw = core.call_api("smarttraven/chat_branches/switch", {"session_id": sess, "at_depth": 2, "direction": "right"}, method="POST", namespace="modules")
print("switch:", sw)
print("indicator:", core.call_api("smarttraven/chat_branches/branch_indicator", {"session_id": sw["new_session_id"], "depth": 2}, method="GET", namespace="modules"))
```

五、实现参考
- 内存引擎：[`impl.py`](api/modules/SmartTraven/chat_branches/impl.py)
- API 注册：[`chat_branches.py`](api/modules/SmartTraven/chat_branches/chat_branches.py)
- 注册规范与路由自动发现：[`core/api_registry.py`](core/api_registry.py), [`core/api_gateway.py`](core/api_gateway.py), [`core/services.py`](core/services.py)

六、注意事项
- 本模块为内存实现，进程重启后需要重新导入 chat-branches 文件
- 仅 active 会话允许追加/修剪/切分支；切分支会归档旧会话并生成新会话
- j/n 由父节点 children 顺序计算；文件不冗余该信息
- 建议以 8050 作为默认 API 网关端口；如端口冲突可自定义（参见全局/项目配置）

七、测试脚本
- 见：[`test_chat_branches.py`](api/modules/SmartTraven/chat_branches/test_chat_branches.py)
- 作用：自动启动网关、加载模块、导入示例、执行全量接口调用并打印结果