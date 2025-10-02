# 💬 In-Chat Constructor Module

## 🎯 核心职责

`in_chat_constructor_module` (对话内构造模块) 的**唯一职责**是处理对话部分的上下文构建。

它负责接收原始的聊天历史记录，并将 `in--chat` 类型的预设和符合条件的世界书条目，根据一套精确的排序规则（基于 `depth` 和 `order`）**注入**到该历史记录中，形成一个有序的对话列表。

### 设计原则

-   **职责单一**: 此模块**不**处理系统提示、角色描述等 `relative` 类型的框架性提示词。它只关心对话流的构建。
-   **全局状态驱动**: 模块从 `shared.globals` 读取预设和世界书数据，使其与系统的中央状态保持一致。
-   **信息追溯**: 输出的每条消息都包含来源信息，便于调试和后续处理。
-   **无损输出**: 模块**不合并**相邻的同角色消息，保留了最原始的注入结构。

## 📦 API 接口

本模块向工作流系统注册了以下函数：

### `in_chat.construct(history, triggered_wb_ids)`

根据规则构造最终的对话上下文。

-   **输入**:
    -   `history` (List[HistoryMessage]): 原始的聊天历史记录。
    -   `triggered_wb_ids` (List[int]): 已被触发的 `conditional` 世界书条目的ID列表。
-   **数据源**:
    -   函数会从 `shared.globals.presets` 读取 `in-chat` 预设。
    -   函数会从 `shared.globals.world_book_entries` 读取除 `before_char`/`after_char` 之外的世界书条目。
-   **输出**:
    -   `context` (List[ConstructedMessage]): 一个经过排序和注入的、最终的对话上下文列表。

## 💾 数据结构

### 输入数据结构

#### `HistoryMessage` (from input)

```python
{
    "role": "user" | "assistant" | "system",
    "content": "消息内容"
}
```

#### `Preset` (`position: "in-chat"`, from `shared.globals`)

```python
{
    "name": "preset_name",
    "content": "预设内容",
    "role": "user" | "assistant" | "system",
    "depth": int,
    "order": int,
    "position": "in-chat",
    "enabled": bool
}
```

#### `WorldBookEntry` (from `shared.globals`)

```python
{
    "id": int,
    "name": "wb_name",
    "content": "世界书条目内容",
    "mode": "always" | "conditional",
    "position": "user" | "assistant" | "system", # Not before/after_char
    "depth": int,
    "order": int,
    "enabled": bool
}
```

### 输出数据结构

#### `ConstructedMessage`

```python
{
    "role": "user" | "assistant" | "system",
    "content": "消息内容",
    "source_type": "user" | "assistant" | "system" | "preset" | "world_book" | "character" | "persona",
    "source_id": "history_{index}" | "preset_{name}" | "wb_{id}"
}
```

## ⚙️ 排序与注入逻辑

1.  **收集**: 模块首先从 `shared.globals` 收集所有启用的 `in-chat` 预设，以及 `always` 或已触发的 `conditional` 世界书条目（排除了 `before_char` 和 `after_char` 类型）。
2.  **排序**: 对收集到的条目，按照 `order` (升序) 和 `role` (assistant > user > system) 进行排序。
3.  **注入**: 模块根据每个条目的 `depth` 值，将其注入到原始聊天历史的精确位置。
    -   `depth` 代表距离聊天历史**末尾**的距离。
    -   `depth: 0` 表示注入到列表的**最后**。
    -   `depth: 1` 表示注入到**倒数第二个**位置。
    -   以此类推。
4.  **输出**: 生成的最终列表是一个**未合并**的消息序列，每条消息都带有其来源信息。

## 🚀 使用示例 (在工作流中)

```python
# (在一个工作流文件中)

from shared import globals as g
registry = get_registry()

# 1. (由其他模块) 填充全局变量
g.presets = [...] 
g.world_book_entries = [...]

# 2. 从各个来源获取数据
raw_history = registry.call("history.get_history").get("history")
# ... (通过其他模块判断哪些 world book ids 被触发)
triggered_ids = [2, 5]

# 3. 调用本模块进行构造
result = registry.call(
    "in_chat.construct",
    history=raw_history,
    triggered_wb_ids=triggered_ids
)

# 4. 获取最终的对话上下文
final_chat_context = result.get("context")

# final_chat_context 现在是一个带有来源信息的、未合并的消息列表
# [
#   {'role': 'user', 'content': '...', 'source': 'world', 'source_id': 'wb_2'},
#   {'role': 'user', 'content': '...', 'source': 'history', 'source_id': 'history_0'},
#   ...
# ]