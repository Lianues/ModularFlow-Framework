# SmartTraven.prompt_postprocess 工作流说明

位置：api/workflow/smarttraven/prompt_postprocess/

本工作流用于对一份“规范化的 messages（带或不带 source）”进行两视图的后处理流水线，生成 user_view 与 assistant_view 两份可直接用于渲染或送模的消息数组。流水线包含：
- before_macro 的正则替换（按视图）
- 可选的宏处理（仅替换 content，保留 source 等字段）
- after_macro 的正则替换（按视图）

相关代码
- 注册封装层：[python.prompt_postprocess.prompt_postprocess.py](api/workflow/smarttraven/prompt_postprocess/prompt_postprocess.py:1)
  - API 注册与 Schema：[python.function(apply)](api/workflow/smarttraven/prompt_postprocess/prompt_postprocess.py:89)
- 实现层（核心逻辑）：[python.prompt_postprocess.impl.py](api/workflow/smarttraven/prompt_postprocess/impl.py:1)
  - 工作流主入口：[python.function(apply)](api/workflow/smarttraven/prompt_postprocess/impl.py:139)
  - 单视图正则适配器（messages）：[python.function(_regex_apply_messages)](api/workflow/smarttraven/prompt_postprocess/impl.py:61)
  - 宏处理适配器（messages）：[python.function(_macro_process_messages)](api/workflow/smarttraven/prompt_postprocess/impl.py:110)
- 依赖模块
  - 正则模块（单视图 API）：[python.regex_replace.regex_replace.py](api/modules/SmartTraven/regex_replace/regex_replace.py:22)
  - 宏模块：smarttraven/macro/process，参考模块文档：[filename](api/modules/SmartTraven/macro/README.md)
- 测试用例（如存在）：[filename](api/workflow/smarttraven/prompt_postprocess/test_prompt_postprocess_workflow.py)

API 列表
- smarttraven/prompt_postprocess/apply（两视图后处理流水线）
  - 注册位置：[python.function(apply)](api/workflow/smarttraven/prompt_postprocess/prompt_postprocess.py:89)

功能与规则
- 输入是一份 canonical messages（建议来自 framing_prompt 或 in_chat_constructor 的输出），输出分别为 user_view 与 assistant_view。
- 正则替换
  - 使用 modules/smarttraven/regex_replace/apply_messages 单视图 API，分别对两个视图执行
  - placement 必须为 "before_macro" 或 "after_macro"
  - 规则按 view 过滤，按 targets（基于 source.type）命中消息，仅替换 content
- 宏处理（可选）
  - 使用 modules/smarttraven/macro/process
  - 仅替换 content，保留 message 的 role 与 source
  - 两视图各自独立执行；默认 variables 为空对象，可按需扩展
- 统一打印
  - 实现层在完成时会打印一次完整 JSON，包含 input_messages、user_view、assistant_view，便于调试观测（生产可按需关闭）

输入/输出契约
- 输入（JSON Schema 概览，详见注册层定义：[python.function(apply)](api/workflow/smarttraven/prompt_postprocess/prompt_postprocess.py:25)）
  - messages: array（[{role, content, source?}]）
    - role ∈ {"system","user","assistant","thinking"}
    - content: string
    - source: object（建议包含 source.type 以便正则 targets 命中）
  - rules: array | object（数组或 {rules:[...]} 容器；格式参考 [filename](backend_projects/SmartTraven/data/presets/Default.json) 的 regex_rules）
  - macro_enabled: boolean（是否启用宏处理）
- 输出（JSON）
  - user_view: array（处理后的消息数组，仅 content 可能被改变）
  - assistant_view: array（处理后的消息数组，仅 content 可能被改变）

处理流程（两视图各自执行）
1) before_macro: 调用 regex_replace/apply_messages 执行本视图的 before_macro 规则
2) macro（可选）: 若 macro_enabled=true，调用 macro/process 替换 content（保留 source）
3) after_macro: 再次调用 regex_replace/apply_messages 执行本视图的 after_macro 规则

调用示例（Python SDK）
```python
import core

messages = [
  {"role":"system","content":"<b>System</b>", "source":{"type":"preset.relative","position":"relative","id":"p0"}},
  {"role":"user","content":"你好 <x>标签</x>", "source":{"type":"history.user","id":"history_0","index":0}},
  {"role":"assistant","content":"<StatusPlaceHolderImpl/> 回复", "source":{"type":"history.assistant","id":"history_1","index":1}},
]

rules = {
  "rules": [
    {
      "id":"remove_xml_tags",
      "enabled": True,
      "find_regex": "<([a-zA-Z0-9]+)>(.|\\n)*?</\\1>",
      "replace_regex": "移除xml",
      "targets": ["preset","history","world_book"],
      "placement": "before_macro",
      "views": ["user_view","assistant_view"]
    },
    {
      "id":"status_bar_demo",
      "enabled": True,
      "find_regex": "<StatusPlaceHolderImpl/>",
      "replace_regex": "这里是状态栏",
      "targets": ["history"],
      "placement": "after_macro",
      "views": ["user_view"]
    }
  ]
}

res = core.call_api(
  "smarttraven/prompt_postprocess/apply",
  {"messages": messages, "rules": rules, "macro_enabled": True},
  method="POST",
  namespace="workflow"  # 若以 modules 命名空间注册工作流统一入口，可按实际调整
)
# 返回：{"user_view":[...], "assistant_view":[...]}
```

注意事项与边界
- 规则视图过滤：view 不匹配的规则不会应用到该视图
- placement 错配或非法：正则调用将直接回退输出原 messages
- 规则 find_regex 编译失败：忽略该条规则，不抛异常
- 宏处理失败：回退原 messages（仅该阶段回退）
- messages 的 content 非字符串会被转为字符串（None → ""）
- depth 窗口与 targets 匹配逻辑由 regex_replace 模块负责，详见其 README 与实现
- 打印一次完整 JSON：位于实现层 [python.function(apply)](api/workflow/smarttraven/prompt_postprocess/impl.py:139) 的尾部，包含 input_messages 与两个视图结果

与其他模块关系
- framing_prompt：负责“对话前缀（relative + before/after 世界书）”的装配与来源规范化，参考：[filename](api/modules/SmartTraven/framing_prompt/README.md)
- in_chat_constructor：负责“对话内注入（in-chat 预设/世界书）”，参考：[filename](api/modules/SmartTraven/in_chat_constructor/README.md)
- regex_replace：本工作流调用其单视图 API 完成按视图的正则替换，参考：[filename](api/modules/SmartTraven/regex_replace/README.md)
- macro：宏系统作为可选中间阶段，参考：[filename](api/modules/SmartTraven/macro/README.md)

实现索引（源码锚点）
- 工作流入口：[python.function(apply)](api/workflow/smarttraven/prompt_postprocess/impl.py:139)
- 正则适配器（单视图）：[python.function(_regex_apply_messages)](api/workflow/smarttraven/prompt_postprocess/impl.py:61)
- 宏适配器：[python.function(_macro_process_messages)](api/workflow/smarttraven/prompt_postprocess/impl.py:110)
- 注册： [python.function(apply)](api/workflow/smarttraven/prompt_postprocess/prompt_postprocess.py:89)

运行与测试
- 建议先通过 framing_prompt/in_chat_constructor 产出带 source 的 messages，再调用本工作流验证
- 如存在测试脚本可直接运行（来自本目录）：[filename](api/workflow/smarttraven/prompt_postprocess/test_prompt_postprocess_workflow.py)