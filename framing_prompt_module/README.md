# 🖼️ Framing Prompt Module

## 🎯 核心职责

`framing_prompt_module` (框架提示词模块) 的**唯一职责**是构建在主对话历史**之前**的“前缀上下文”或“框架提示词”。

它负责处理所有与对话历史不直接混合、但对AI行为至关重要的指令型文本，例如系统提示、角色描述、以及通过占位符注入的世界信息。

### 设计原则

-   **职责分离**: 此模块**不**处理 `in--chat` 类型的预设或聊天历史记录。它的工作范围严格限定在对话开始之前的内容。
-   **全局状态驱动**: 模块从 `shared.globals` 读取所有需要的数据，包括预设、世界书、角色和用户描述。
-   **占位符驱动**: 模块的核心功能之一是解析特殊的 `relative` 预设（占位符），并将其替换为相应的内容。
-   **信息追溯**: 输出的每条消息都包含详细的来源信息 (`source` 和 `source_id`)，确保了上下文的完全透明和可调试性。
-   **无损输出**: 对于通过占位符注入的多个世界书条目，模块**不会**将它们合并。每个条目都会被构造成一个独立的消息，以保留最精细的来源信息。

## 📦 API 接口

本模块向工作流系统注册了以下函数：

### `framing.assemble(triggered_wb_ids)`

根据规则构造前缀上下文。

-   **输入**:
    -   `triggered_wb_ids` (List[int]): 已被触发的 `conditional` 世界书条目的ID列表。
-   **数据源**:
    -   函数会从 `shared.globals.presets` 读取 `relative` 预设。
    -   函数会从 `shared.globals.world_book_entries` 读取 `before_char` 和 `after_char` 的世界书条目。
    -   函数会从 `shared.globals.character_data` 和 `shared.globals.persona_data` 读取描述信息。
-   **输出**:
    -   `prefix_prompt` (List[ConstructedMessage]): 一个经过排序和处理的、最终的前缀上下文列表。

## 💾 数据结构

### 输入数据结构 (来自 `shared.globals`)

#### `Preset` (`position: "relative"`)

```python
{
    "name": "preset_name",
    "identifier": "system_prompt" | "charDescription" | "worldInfoBefore" | ...,
    "content": "预设内容 (对于占位符通常为空)",
    "role": "user" | "assistant" | "system",
    "order": int,
    "position": "relative",
    "enabled": bool
}
```

#### `WorldBookEntry` (`position: "before_char" | "after_char"`)

```python
{
    "id": int,
    "name": "wb_name",
    "content": "世界书条目内容",
    "mode": "always" | "conditional",
    "position": "before_char" | "after_char",
    "order": int,
    "enabled": bool
}
```

#### `CharacterData` & `PersonaData`

```python
{
    "description": "角色或用户的描述文本"
}
```

### 输出数据结构

#### `ConstructedMessage`

```python
{
    "role": "user" | "assistant" | "system",
    "content": "消息内容",
    "source": "preset" | "world" | "character" | "persona",
    "source_id": "preset_{name}" | "wb_{id}" | "char_description" | "persona_description"
}
```

## ⚙️ 组装与排序逻辑

1.  **收集**: 模块首先从 `g.presets` 中收集所有 `position` 为 `relative` 的预设。
2.  **排序**: 对收集到的 `relative` 预设，按照 `order` (升序) 和 `role` (assistant > user > system) 进行排序。
3.  **构建与解析**: 模块遍历排序后的预设列表：
    -   **普通预设**: 直接将其内容转换为 `ConstructedMessage`。
    -   **占位符预设**:
        -   `charDescription` / `personaDescription`: 从 `g.character_data` / `g.persona_data` 获取描述并创建消息。
        -   `worldInfoBefore` / `worldInfoAfter`: 触发内部逻辑，该逻辑会：
            1.  收集所有对应 `position` (`before_char` / `after_char`) 的世界书。
            2.  对这些世界书进行过滤（基于 `enabled` 和 `triggered_ids`）和排序（基于 `order` 和 `role`）。
            3.  **为每一个符合条件的世界书条目创建一个独立的 `ConstructedMessage`**。
        -   `chatHistory`: 此占位符被忽略，因为它由 `in_chat_constructor_module` 负责处理。
4.  **输出**: 生成的最终列表是一个有序的、带有来源信息的消息序列，可直接用在对话历史之前。

## 🚀 使用示例 (在工作流中)

```python
# (在一个工作流文件中)

from shared import globals as g
registry = get_registry()

# 1. (由其他模块) 填充全局变量
g.presets = [...] 
g.world_book_entries = [...]
g.character_data = {"description": "..."}
g.persona_data = {"description": "..."}

# 2. (通过其他模块判断哪些 world book ids 被触发)
triggered_ids = [5, 12]

# 3. 调用本模块构造前缀上下文
result = registry.call(
    "framing.assemble",
    triggered_wb_ids=triggered_ids
)
prefix_prompt = result.get("prefix_prompt")

# 4. 调用 in_chat_constructor_module 构造对话历史
# ...

# 5. 组合最终提示词
final_prompt = prefix_prompt + chat_history_prompt