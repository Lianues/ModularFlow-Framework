# SmartTraven / In-Chat Constructor（对话内构造）

本模块在 SmartTraven 命名空间下提供“对话内构造”能力：在既有聊天历史基础上，按 depth/order 规则注入 in-chat 预设与命中的世界书条目，并为每条消息打上来源字段 source（不合并相邻同角色）。

- 实现层：[`impl.py`](api/modules/SmartTraven/in_chat_constructor/impl.py)
- 封装层（API 注册）：[`in_chat_constructor.py`](api/modules/SmartTraven/in_chat_constructor/in_chat_constructor.py)
- 测试脚本：[`test_in_chat_constructor.py`](api/modules/SmartTraven/in_chat_constructor/test_in_chat_constructor.py)
- 参考数据：
  - 预设：[`Default.json`](backend_projects/SmartTraven/data/presets/Default.json)
  - 世界书：[`参考用main_world.json`](backend_projects/SmartTraven/data/world_books/参考用main_world.json)


一、职责与行为
- 从 API 入参接收以下三类数据：history（OpenAI messages）、in-chat 预设、世界书条目，以及 conditional 命中的 id 列表
- 根据如下规则将预设/世界书注入到历史列表中（无合并），并在每条消息上添加 source 来源信息


二、公共 API
路由（斜杠路径）：
- modules/smarttraven/in_chat_constructor/construct

请求（POST，JSON）：
- history: OpenAI Chat messages 数组
  - [{"role":"system|user|assistant","content":"..."}]
- presets_in_chat: in-chat 预设数组（参考 Default.json 的 prompts 条目结构），仅处理 position=="in-chat" 且 enabled 的条目
- world_books: 世界书条目数组（参考 参考用main_world.json；支持嵌套数组 [[{...}], {...}]）
- triggered_worldbook_ids: int 数组，用于筛选 mode=="conditional" 的世界书 id

响应（JSON）：
- messages: OpenAI messages 扩展数组，元素结构：
  - {"role":"...","content":"...","source":{...}}


三、来源字段（source）说明
为每条消息添加 source 字段，以便 UI 显示与业务追溯：

- 历史消息（来自 history 数组）
  - source = {"type":"history","id":"history_{i}","index":i}
- in-chat 预设（过滤：position=="in-chat" 且 enabled，content 非空）
  - 排序键：order 升序 → 角色优先级 assistant > user > system → internal_order（稳定）
  - 插入键：按 depth 分组；insertion_index = len(list) - depth，若负则置 0；组内逆序插入保持相对顺序
  - 角色：来自条目 role（非法值回退为 user）
  - source = {"type":"preset","id":"preset_{identifier|name|index}","name","identifier","depth","order","role}
- 世界书（过滤：排除 position ∈ {"before_char","after_char"}；enabled；content 非空；mode=="always" 或 mode=="conditional" 且 id 命中）
  - 角色映射：position → role（assistant|user|system）
  - 排序与插入规则同上
  - source = {"type":"world_book","id":"wb_{id|index}","name","wb_id","mode","position","depth","order","role}

注意：
- 不合并相邻同角色消息，保持未合并序列
- include_trace=true 时，响应 trace 提供插入概要（非重复含所有字段）以避免过大


四、示例调用（注意：dict 的打印工具如 pprint 默认会排序键，可能导致显示顺序与插入顺序不同。若需保序请使用 json.dumps(sort_keys=False) 或 pprint(..., sort_dicts=False)。）

Python（通过 core.call_api）
```python
import json, core

gateway = core.get_api_gateway()
sm = core.get_service_manager()
sm.load_project_modules()
gateway.start_server(background=True)

# 准备数据
with open("backend_projects/SmartTraven/data/presets/Default.json", "r", encoding="utf-8") as f:
    preset_doc = json.load(f)
presets = [p for p in (preset_doc.get("prompts") or []) if str(p.get("position")) == "in-chat"]

with open("backend_projects/SmartTraven/data/world_books/参考用main_world.json", "r", encoding="utf-8") as f:
    world_books_doc = json.load(f)

payload = {
    "history": [
        {"role": "system", "content": "系统开场"},
        {"role": "user", "content": "你好"}
    ],
    "presets_in_chat": presets,
    "world_books": world_books_doc,
    "triggered_worldbook_ids": [2]
}

result = core.call_api("smarttraven/in_chat_constructor/construct", payload, method="POST", namespace="modules")
print(result["messages"][0])  # {"role":"...", "content":"...", "source": {...}}
```

curl（假设网关端口 8050）
```bash
curl -s -X POST "http://127.0.0.1:8050/api/modules/smarttraven/in_chat_constructor/construct" \
  -H "Content-Type: application/json" \
  -d "{\"history\":[{\"role\":\"system\",\"content\":\"系统开场\"},{\"role\":\"user\",\"content\":\"你好\"}],\"presets_in_chat\":[{\"position\":\"in-chat\",\"enabled\":true,\"role\":\"system\",\"depth\":0,\"order\":98,\"name\":\"示例\",\"content\":\"注入示例\"}],\"world_books\":[[{\"id\":2,\"name\":\"艾拉的背景\",\"mode\":\"conditional\",\"position\":\"user\",\"depth\":0,\"order\":101,\"enabled\":true,\"content\":\"艾拉是机械工程师\"}]],\"triggered_worldbook_ids\":[2]}"
```


五、测试
内置测试脚本会自动启动网关、加载模块，并执行全量接口调用与断言：
- [`test_in_chat_constructor.py`](api/modules/SmartTraven/in_chat_constructor/test_in_chat_constructor.py)

运行（在仓库根目录执行）：
```bash
python api/modules/SmartTraven/in_chat_constructor/test_in_chat_constructor.py
```

该脚本将：
- 调用 construct 接口
- 断言 messages 内每条含 source


六、迁移检查与注意事项
- 已迁移：模块重命名为 in_chat_constructor，存放于 api/modules/SmartTraven；实现层与封装层拆分完成
- 不再依赖 shared.globals；所有数据由 API 入参提供
- 不保留旧函数注册名（in_chat.construct），仅暴露新斜杠路径 API
- 默认参数（DEFAULT_DEPTH=0, DEFAULT_ORDER=100）已内联到实现层，未保留 variables.py
- 待清理（如需要）：旧目录 in_chat_constructor_module/（不再使用），可后续删除以避免混淆

如需进一步扩展（例如：相邻同角色合并开关、额外校验接口、支持 name 字段承载角标），可在实现层添加可选参数并更新封装层的 JSON Schema。