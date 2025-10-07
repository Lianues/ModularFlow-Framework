# SmartTavern.macro 模块说明

位置：api/modules/SmartTavern/macro/

本模块提供“顺序宏处理”能力，支持在消息数组或单个纯文本中按从左到右、内层优先的策略解析并执行宏。宏仅替换 content（或纯文本）内容，不改变其他字段，并维护单一变量表（variables.initial → variables.final）。

相关代码
- 注册封装层：api/modules/SmartTavern/macro/macro.py
- 实现层：api/modules/SmartTavern/macro/impl.py
- 沙盒依赖：api/modules/SmartTavern/python_sandbox/python_sandbox.py
- 变量约定：api/modules/SmartTavern/macro/SYSTEM_VARIABLES.md

API 列表
- smarttavern/macro/process（处理消息数组）
- smarttavern/macro/process_text（处理纯文本）

统一策略
- 严格模式默认启用（未定义变量 getvar 输出 [UndefinedVar:{name}]）。客户端请求不接受 policy 字段。

宏语法
- 定界符：{{ ... }} 与 << ... >>（等价，可嵌套）
- 宏种类：
  - python:EXPR
  - setvar:NAME:VALUE 或 setvar:NAME::VALUE（返回空串）
  - getvar:NAME
  - 传统宏（legacy，转译为 Python 后在沙盒执行）：newline, noop, enable, trim, random, pick, roll, add, sub, mul, div, max, min, upper, lower, length, reverse, time, date, weekday, isotime, isodate, datetimeformat, time_utc, input, lastmessage, lastusermessage, lastcharmessage, messagecount, usermessagecount, conversationlength, user, char, description, personality, scenario, persona, getglobalvar, setglobalvar, addglobalvar, incglobalvar, decglobalvar, addvar, incvar, decvar, timediff

执行机制（简述）
- 单条文本处理流程：
  1) 扫描寻找“最内层可识别宏”片段。
  2) 分类：
     - python → 调用沙盒 API 求值，结果转字符串。
     - setvar → 更新变量表，替换为空串。
     - getvar → 读取变量；未定义输出占位词。
     - legacy → 转译为 Python，再走沙盒。
  3) 用结果替换原片段，继续下一轮，直到无可替换项或达到保护上限。
- 嵌套解析：内层优先，避免跨层误替换。
- 历史相关宏：统一按“系统变量”读取，上游应在 variables 中注入，例如 chat_last_message、user_name、character_name 等，详见 SYSTEM_VARIABLES.md。

API：messages 数组处理（smarttavern/macro/process）
- 输入
  - messages: [{role, content, ...}]（仅修改 content，保留其他字段）
  - variables?: 对话上下文变量初值
- 输出
  - messages: 替换后的数组
  - variables: {initial, final}
- 调用示例（Python SDK）
  - 示例代码：
    - core.call_api("smarttavern/macro/process", {"messages": [...], "variables": {...}}, method="POST", namespace="modules")

API：纯文本处理（smarttavern/macro/process_text）
- 输入
  - text: string
  - variables?: 对话上下文变量初值
- 输出
  - text: 替换后的字符串
  - variables: {initial, final}
- 调用示例（Python SDK）
  - 示例代码：
    - core.call_api("smarttavern/macro/process_text", {"text": "a={{setvar:x:1}} b={{getvar:x}} c={{getvar:y}} d=<<python:3+4>>", "variables": {"pre": "v"}}, method="POST", namespace="modules")
  - 示例返回：
    - {"text": "a= b=1 c=[UndefinedVar:y] d=7", "variables": {"initial": {"pre": "v"}, "final": {"pre": "v", "x": "1"}}}

变量与策略
- 单一作用域（dict），输入 variables 作为 initial，执行后输出 final。
- 严格模式：undefined_get="error"，error_token="[UndefinedVar:{name}]"。

错误与边界
- 未识别宏：不替换（产出空串）。
- 沙盒失败：结果视为""；变量表仍以沙盒返回为准（final 合并）。
- 保护上限：单文本最多 10000 次替换迭代，防止死循环。

相关实现要点（源码索引）
- 注册 API：macro.py
- 主处理：impl.py 中的 _process_text、process_messages、_legacy_to_python、_find_next_recognized_span

示例（messages）
- 输入 messages：
  - [{"role":"user","content":"{{setvar:x:1}}"}, {"role":"assistant","content":"x={{getvar:x}}"}]
- 输出 messages：
  - [{"role":"user","content":""}, {"role":"assistant","content":"x=1"}]

许可与安全
- 所有 python/legacy 宏均在受限沙盒内执行，禁止导入/任意 IO/反射等危险操作。

参考
- api/modules/SmartTavern/macro/macro.py
- api/modules/SmartTavern/macro/impl.py
- api/modules/SmartTavern/macro/SYSTEM_VARIABLES.md
- api/modules/SmartTavern/macro/test_macro.py