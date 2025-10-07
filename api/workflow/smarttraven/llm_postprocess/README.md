# SmartTavern.llm_postprocess 工作流说明

位置：api/workflow/smarttavern/llm_postprocess/

本工作流完成“调用通用 LLM → 聚合模型回答 → 单视图后处理（正则 + 宏）”的一条龙流程，适用于需要在服务端统一消费流式/非流式 LLM 响应、并在最终阶段再做一次性正则与宏处理的场景。

相关代码
- 注册封装层： [filename](api/workflow/smarttavern/llm_postprocess/llm_postprocess.py)
- 实现层（核心逻辑）： [filename](api/workflow/smarttavern/llm_postprocess/impl.py)
- 依赖模块/工作流
  - 通用 LLM 调用模块： [filename](api/modules/llm_api/llm_api.py)
  - 单视图后处理工作流： [filename](api/workflow/smarttavern/prompt_postprocess/prompt_postprocess.py)

API 列表
- smarttavern/llm_postprocess/apply（LLM 调用 + 单视图后处理）

功能概述
- 调用通用 LLM API（modules/llm_api/chat），支持 stream=true/false。
  - 当 stream=true：按照 SSE（text/event-stream）协议逐帧接收，在流完全结束后聚合完整文本。
  - 当 stream=false：一次性 JSON 返回完整文本。
- 将 LLM 最终回答组装为一条 assistant 消息（附带 source.type="history.assistant"），追加到原始 messages 尾部，便于后续正则按 targets 命中。
- 固定以 user_view 调用单视图后处理工作流 smarttavern/prompt_postprocess/apply，流水线为：
  - 宏前正则（before_macro）
  - 宏处理（始终执行，仅替换 content）；支持传入 variables 作为宏初始变量
  - 宏后正则（after_macro）
- 最终返回 message（数组）与 variables（宏变量表 initial/final）。

输入/输出契约（概览）
- 输入（JSON）
  - llm: object（必填）LLM 调用配置，结构对齐 [filename](api/modules/llm_api/llm_api.py) 的 llm_api/chat 输入
    - provider: "openai" | "anthropic" | "gemini" | "openai_compatible" | "custom"
    - api_key: string
    - base_url: string
    - messages: array of {role, content}（OpenAI 风格）
    - stream?: boolean（默认 false；true 时按 SSE 推送）
    - model?, max_tokens?, temperature?, top_p?, presence_penalty?, frequency_penalty?
    - custom_params?, safety_settings?, timeout?, connect_timeout?, enable_logging?, models?
  - variables: object（可选）初始变量表，作为宏模块的初始状态注入
  - rules: array | object（可选）正则规则，数组或 {rules:[...]} 容器（与 regex_replace 模块兼容）
- 输出（JSON）
  - message: array of {role, content, source?}（仅 content 可能被修改；source 信息保留/透传）
  - variables: {initial: object, final: object}

工作流处理步骤
1) LLM 调用
   - POST /api/modules/llm_api/chat
   - stream=false：直接读取 JSON.content
   - stream=true：读取 SSE 文本，解析 data: {"type":"chunk","content":"..."} 进行拼接，捕获 usage/finish/end
2) 组装消息
   - 将最终 assistant 文本构造成一条消息（带 source.type="history.assistant"），追加到 llm.messages 尾部，形成 messages_for_postprocess
3) 单视图后处理（user_view）
   - POST /api/workflow/smarttavern/prompt_postprocess/apply
   - 入参：{messages: messages_for_postprocess, rules, view:"user_view", variables}
4) 返回
   - 直接返回 prompt_postprocess 的输出结构 {"message":[...], "variables":{initial, final}}

请求示例（非流式）
```bash
curl -X POST "http://localhost:8050/api/workflow/smarttavern/llm_postprocess/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "llm": {
      "provider": "openai",
      "api_key": "sk-***",
      "base_url": "https://api.openai.com/v1",
      "messages": [
        {"role":"system","content":"你是个有帮助的助手"},
        {"role":"user","content":"请使用变量：{{getvar:topic}}"}
      ],
      "model": "gpt-4o-mini",
      "stream": false,
      "temperature": 0.3
    },
    "variables": { "topic": "夜晚的海风与路灯" },
    "rules": {
      "rules": [
        {
          "id":"remove_xml",
          "enabled": true,
          "placement":"before_macro",
          "views":["user_view","assistant_view"],
          "targets":["history","preset","world_book"],
          "find_regex":"<[^>]+>",
          "replace_regex":""
        }
      ]
    }
  }'
```

响应示例（非流式）
```json
{
  "message": [
    {"role":"system","content":"你是个有帮助的助手"},
    {"role":"user","content":"请使用变量：夜晚的海风与路灯"},
    {"role":"assistant","content":"……（LLM 回答，经宏/正则处理后）……","source":{"type":"history.assistant","id":"llm_output","from":"smarttavern.llm_postprocess"}}
  ],
  "variables": {
    "initial": {"topic":"夜晚的海风与路灯"},
    "final": {"topic":"夜晚的海风与路灯"}
  }
}
```

使用说明与注意事项
- 流式聚合策略：本工作流不在 token 级别做后处理；而是在 SSE 完整结束后一次性处理，保证宏与正则逻辑的确定性。
- variables 注入：可在模板中使用 {{getvar:name}} 或 <<getvar:name>>，也可通过 setvar 修改变量；输出 variables.final 为宏执行后的最终表。
- rules 可传空数组以绕过正则阶段，但本工作流仍会执行宏阶段。
- messages/source：上游 messages（system/user/assistant）建议保留 source 信息，便于正则 targets 命中（如 history.user / preset.relative / world_book.in-chat 等）。
- 视图固定为 user_view：若需对 assistant_view 执行后处理，建议直接调用 prompt_postprocess 接口并指定 view。

与其他模块关系
- llm_api/chat：统一 LLM 能力，支持多厂商与 SSE；路径 /api/modules/llm_api/chat
- prompt_postprocess/apply：单视图正则+宏流水线；路径 /api/workflow/smarttavern/prompt_postprocess/apply
- regex_replace/macro：分别提供正则与宏能力；本工作流通过 prompt_postprocess 进行编排调用

边界与错误处理
- LLM 请求失败或响应不可解析：assistant 文本将为空字符串（""），仍会走后处理；请通过上游监控 error 字段（直接调用 llm_api/chat 时可见）。
- SSE 事件解析：仅解析 {"type":"chunk"|"usage"|"finish"|"end"|"error"} 事件；未知事件忽略。
- 宏或正则阶段异常：各阶段失败会回退到进入该阶段前的消息（保持鲁棒性），并返回空 variables 或原样规则。

版本与变更
- 初版：新增工作流注册/实现/文档，流/非流统一后处理，支持 variables 注入宏，固定 user_view 执行后处理。