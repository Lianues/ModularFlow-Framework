# SmartTraven.chat_branches 模块说明（分支重试对话）

位置：api/modules/SmartTraven/chat_branches/

本模块提供“分支重试对话（chat-branches）”能力：以不可变消息树 + 可变会话路径方式管理对话，支持创建对话、追加消息、修剪路径、左右切换分支（归档旧会话并新建新会话）、导入/导出标准聊天文件（chat-branches v2），并可导出当前分支为 OpenAI messages 与分支情况表（j/n）。

相关代码
- 注册封装层（API 定义/Schema）：[filename](api/modules/SmartTraven/chat_branches/chat_branches.py:1)
  - 创建对话：[python.function(create_conversation)](api/modules/SmartTraven/chat_branches/chat_branches.py:46)
  - 获取路径：[python.function(get_path)](api/modules/SmartTraven/chat_branches/chat_branches.py:61)
  - 追加消息：[python.function(append_message)](api/modules/SmartTraven/chat_branches/chat_branches.py:80)
  - 修剪路径：[python.function(truncate_after)](api/modules/SmartTraven/chat_branches/chat_branches.py:98)
  - 切换分支并新会话：[python.function(switch_branch_and_start_new_session)](api/modules/SmartTraven/chat_branches/chat_branches.py:117)
  - 分支 j/n 指示：[python.function(branch_indicator)](api/modules/SmartTraven/chat_branches/chat_branches.py:142)
  - 列出对话/会话：[python.function(list_conversations)](api/modules/SmartTraven/chat_branches/chat_branches.py:155), [python.function(list_sessions)](api/modules/SmartTraven/chat_branches/chat_branches.py:170)
  - 派生视图：OpenAI 消息：[python.function(openai_messages)](api/modules/SmartTraven/chat_branches/chat_branches.py:207)，分支情况表：[python.function(branch_table)](api/modules/SmartTraven/chat_branches/chat_branches.py:222)
  - 导出/导入别名（稳定路径）：[python.function(export)](api/modules/SmartTraven/chat_branches/chat_branches.py:237), [python.function(import_chat)](api/modules/SmartTraven/chat_branches/chat_branches.py:260)
- 实现层（内存引擎）：[filename](api/modules/SmartTraven/chat_branches/impl.py:1)
  - 创建对话：[python.function(create_conversation)](api/modules/SmartTraven/chat_branches/impl.py:121)
  - 追加消息：[python.function(append_message)](api/modules/SmartTraven/chat_branches/impl.py:154)
  - 修剪路径：[python.function(truncate_after)](api/modules/SmartTraven/chat_branches/impl.py:175)
  - 切换分支并新会话：[python.function(switch_branch_and_start_new_session)](api/modules/SmartTraven/chat_branches/impl.py:187)
  - 分支 j/n 指示：[python.function(branch_indicator)](api/modules/SmartTraven/chat_branches/impl.py:241)
  - 列出对话/会话：[python.function(list_conversations)](api/modules/SmartTraven/chat_branches/impl.py:255), [python.function(list_sessions)](api/modules/SmartTraven/chat_branches/impl.py:277)
  - 导出/导入（v2）：[python.function(export_v2)](api/modules/SmartTraven/chat_branches/impl.py:297), [python.function(import_v2)](api/modules/SmartTraven/chat_branches/impl.py:337)；稳定别名：[python.function(export)](api/modules/SmartTraven/chat_branches/impl.py:455), [python.function(import_chat)](api/modules/SmartTraven/chat_branches/impl.py:459)
  - 派生视图：OpenAI 消息：[python.function(openai_messages)](api/modules/SmartTraven/chat_branches/impl.py:463)，分支情况表：[python.function(branch_table)](api/modules/SmartTraven/chat_branches/impl.py:478)
- 测试脚本：[filename](api/modules/SmartTraven/chat_branches/test_chat_branches.py:1)
- 示例数据（chat-branches 文件）：[filename](backend_projects/SmartTraven/data/conversations/branch_demo.json:1)

模块职责与数据模型
- 不可变消息树（Node）：
  - 字段：id, conversation_id, parent_id, depth, role, content, sibling_ord（同父下的子序，用于 j/n）, created_at
- 会话（Session）：
  - 字段：id, conversation_id, status(active/archived), path（当前所选分支的节点 id 列表）, created_at, closed_at
- 会话路径可变：仅 active 会话允许修改；切分支时归档旧会话、新建新会话，path 在 at_depth 处左右切换或新建子节点

API 列表（modules 命名空间）
- smarttraven/chat_branches/create_conversation
  - 输入：{ user_id?: string|null, title?: string|null }
  - 输出：{ conversation_id: string, session_id: string, path: object[] }
- smarttraven/chat_branches/get_path
  - 输入：{ session_id: string }
  - 输出：{ session_id, status, path: [{ id, depth, role, content, branch_j, branch_n }] }
- smarttraven/chat_branches/append
  - 输入：{ session_id: string, role: "user"|"assistant"|"system", content: string }
  - 输出：{ session_id, status, path: [...] }
- smarttraven/chat_branches/truncate
  - 输入：{ session_id: string, keep_depth: integer (>=1) }
  - 输出：{ session_id, status, path: [...] }
- smarttraven/chat_branches/switch
  - 输入：{ session_id: string, at_depth: integer (>=2), direction: "left"|"right" }
  - 输出：{ old_session_id, new_session_id, path: [...] }
- smarttraven/chat_branches/branch_indicator
  - 输入：{ session_id: string, depth: integer (>=2) }
  - 输出：{ j: integer|null, n: integer|null }
- smarttraven/chat_branches/list_conversations
  - 输入：{}（空对象）
  - 输出：{ items: [{ id, title, user_id, root_node_id, created_at, sessions_count, active_session_id }] }
- smarttraven/chat_branches/list_sessions
  - 输入：{ conversation_id: string }
  - 输出：{ items: [{ id, status, rev, path_length, created_at, closed_at }] }
- smarttraven/chat_branches/openai_messages
  - 输入：{ session_id: string }
  - 输出：{ conversation_id, session_id, messages: [{ role, content }] }
- smarttraven/chat_branches/branch_table
  - 输入：{ session_id: string }
  - 输出：{ session_id, latest: { depth, j, n, node_id }, levels: [{ depth, node_id, j, n }, ...] }
- smarttraven/chat_branches/export（稳定别名）
  - 输入：{ conversation_id: string }
  - 输出：chat-branches v2 标准文件对象：{ schema:{name:"chat-branches",version:2}, meta:{id,title}, root, nodes:{id:{pid,role,content}}, children:{pid:[cid...]}, active_path:[...] }
- smarttraven/chat_branches/import（稳定别名）
  - 输入：{ doc: chat-branches v2 标准文件 }
  - 输出：{ conversation_id: string, active_session_id: string }

使用示例（Python SDK）
- 初始化与导入
  - 参考测试脚本：[filename](api/modules/SmartTraven/chat_branches/test_chat_branches.py:39)
  - 典型流程：
    1) 启动网关与模块加载
    2) 读取 branch_demo.json 并调用 import
    3) 获取 active_session_id，随后进行路径/派生视图/分支操作
- 追加/修剪/切分支
  - 追加：core.call_api("smarttraven/chat_branches/append", {"session_id": sid, "role":"user","content":"..."},"POST","modules")
  - 修剪：core.call_api("smarttraven/chat_branches/truncate", {"session_id": sid, "keep_depth": 2},"POST","modules")
  - 切分支：core.call_api("smarttraven/chat_branches/switch", {"session_id": sid, "at_depth": 2, "direction": "right"},"POST","modules")

行为细节与边界
- 仅 active 会话允许 append/truncate/switch（见 [python.function(_ensure_active_session)](api/modules/SmartTraven/chat_branches/impl.py:75)）
- 分支指示 j/n 由父节点的 children 顺序与 sibling_ord 决定（见 [python.function(_branch_indicator)](api/modules/SmartTraven/chat_branches/impl.py:91)）
- 切分支策略：
  - at_depth≥2；left/right 会在当前子序左右寻找目标；必要时新建子节点（role="assistant"，content=None）（见 [python.function(switch_branch_and_start_new_session)](api/modules/SmartTraven/chat_branches/impl.py:187)）
- 导入行为：
  - 若传入的 conversation_id 已存在，将清空旧会话/节点并以文件内容重建（见 [python.function(import_v2)](api/modules/SmartTraven/chat_branches/impl.py:337)）
  - active_path 会被规范化：确保从 root 连通，否则回退/截断
- 导出行为：
  - 仅导出 pid/role/content 和有序 children，active_path 选取当前 active 或最近创建的会话路径（见 [python.function(export_v2)](api/modules/SmartTraven/chat_branches/impl.py:297)）

测试
- 内置测试脚本会自动启动网关、加载模块并调用全量接口：
  - [filename](api/modules/SmartTraven/chat_branches/test_chat_branches.py:1)
- 运行（仓库根目录）：
  ```bash
  python api/modules/SmartTraven/chat_branches/test_chat_branches.py
  ```

参考
- API 封装层： [filename](api/modules/SmartTraven/chat_branches/chat_branches.py:1)
- 实现层： [filename](api/modules/SmartTraven/chat_branches/impl.py:1)
- 示例对话文件： [filename](backend_projects/SmartTraven/data/conversations/branch_demo.json:1)