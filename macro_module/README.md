# 宏处理模块 (`macro_module`) 文档

本模块提供了强大的宏处理功能，采用**模块化架构**设计，能够解析和执行文本及消息序列中嵌入的宏命令和Python代码。

## 🏗️ 模块化架构

宏模块采用了三个独立组件的模块化设计：

### 1. 主处理器 (`macro_module.py`)
- **功能**: 统一宏处理器的核心实现
- **职责**: 
  - 协调传统宏和Python宏的执行
  - 管理宏执行上下文和作用域
  - 提供统一的宏处理接口
  - 处理消息序列的顺序执行
- **关键类**: `UnifiedMacroProcessor`, `MacroExecutionContext`

### 2. 缓存管理器 (`macro_cache_manager.py`) 
- **功能**: 智能缓存系统，支持状态感知的增量处理
- **职责**:
  - 消息内容和变量状态的哈希计算
  - 缓存的持久化存储和加载
  - 缓存命中检测和失效管理
  - 支持跨会话的缓存持久性
- **关键类**: `MacroCacheManager`
- **缓存文件**: `shared/SmartTavern/cache/macro_cache.json`

### 3. 传统宏转换器 (`legacy_macro_converter.py`)
- **功能**: 将传统SmartTavern宏转换为Python代码
- **职责**:
  - 支持所有传统宏格式（`{{getvar::name}}` 和 `{{getvar:name}}`）
  - 系统变量宏（user, char, time等）
  - 功能性宏（random, roll, pick等）
  - 数学和字符串操作宏
  - 变量操作宏的作用域感知转换
- **关键类**: `LegacyMacroConverter`

## 🎯 核心功能

模块提供了两个核心函数，已通过 `@register_function` 注册到工作流系统中。

### 1. `process_text_macros`

处理单个字符串中的所有宏。

-   **函数名**: `process_text_macros`
-   **描述**: 接收一个包含宏的字符串，并返回处理和计算后的结果字符串。

#### 输入 (`inputs`)

| 参数名         | 类型         | 描述                                                                                                                              |
| :------------- | :----------- | :-------------------------------------------------------------------------------------------------------------------------------- |
| `text`         | `str`        | **必需**。包含一个或多个宏的文本字符串。例如: `"你好, {{python:1+1}}"`。                                                              |
| `scope_type`   | `str`        | (可选, 默认: `'temp'`)。指定宏执行时的作用域，影响变量的读写位置。可以是 `'preset'`, `'world'`, `'conversation'`, `'char'` 等。 |
| `context_data` | `dict`       | (可选)。一个字典，用于动态更新宏处理器的上下文，例如传入 `character_data` 或 `chat_history`。                                      |

#### 输出 (`outputs`)

| 字段名           | 类型  | 描述                               |
| :--------------- | :---- | :--------------------------------- |
| `processed_text` | `str` | 经过宏处理和计算后生成的最终文本。 |

---

### 2. `process_message_sequence_macros`

按顺序处理一个消息列表，支持智能缓存和增量计算。

-   **函数名**: `process_message_sequence_macros`
-   **描述**: 接收一个消息对象列表，按顺序处理其中的宏、代码块和启用条件，返回一个处理好的消息列表。

#### 输入 (`inputs`)

| 参数名         | 类型              | 描述                                                                                                                                                                                                                                                             |
| :------------- | :---------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `messages`     | `list[dict]`      | **必需**。一个消息对象列表。每个消息字典可以包含 `content` (str), `code_block` (str, 可选), `enabled` (bool/str, 可选), 和 `_source_types` (list, 可选) 等键。 |
| `context_data` | `dict`            | (可选)。与上面相同，用于更新宏处理器的上下文。                                                                                                                                                                                                                         |

#### 输出 (`outputs`)

| 字段名               | 类型         | 描述                                                                 |
| :------------------- | :----------- | :------------------------------------------------------------------- |
| `processed_messages` | `list[dict]` | 一个处理后的消息对象列表。`enabled` 字段评估为 `False` 的消息将被移除。 |

## ⚡ 高级特性

### 1. 状态感知缓存
- **智能哈希**: 基于消息内容和变量状态计算缓存键
- **增量处理**: 只重新计算发生变化的部分
- **跨会话持久性**: 缓存结果保存到文件，支持重启后复用
- **状态快照**: 每个缓存条目包含完整的变量状态快照

### 2. 作用域感知变量管理
- **前缀变量访问**: 支持 `world_var`, `preset_var`, `char_var` 等跨作用域访问
- **动态作用域切换**: 根据消息的 `_source_types` 自动确定作用域
- **变量隔离**: 不同作用域的变量完全隔离，避免意外覆盖

### 3. 统一宏处理
- **Python宏**: `{{python:expression}}` 格式，支持复杂的Python表达式
- **传统宏**: 兼容SmartTavern的所有传统宏格式
- **双分隔符支持**: 同时支持 `{{macro:param}}` 和 `{{macro::param}}` 格式
- **自动转换**: 传统宏在运行时自动转换为Python代码执行

### 4. 消息处理流程
严格按照以下顺序处理每个消息：
1. **`enabled` 评估**: 使用当前变量状态评估启用条件
2. **`code_block` 执行**: 执行Python代码块，修改变量状态
3. **`content` 渲染**: 处理内容中的宏，读取最新变量状态

## 📊 使用示例

```python
# 假设已通过 registry.call() 或类似方式调用

# 示例 1: 处理简单文本
result = registry.call(
    "process_text_macros",
    text="当前时间: {{time}}，计算结果: {{python:10 + 5}}"
)
# result['processed_text'] 将是 "当前时间: 14:30:25，计算结果: 15"

# 示例 2: 传统宏兼容性
result = registry.call(
    "process_text_macros", 
    text="角色名: {{char}}，变量值: {{getvar::my_variable}}"
)
# 自动转换并执行传统宏

# 示例 3: 处理消息序列（带缓存）
messages = [
    {
        "code_block": "setvar('is_ready', True)",
        "_source_types": ["preset"]
    },
    {
        "enabled": "{{python:getvar('is_ready')}}",
        "content": "系统已就绪: {{python:getvar('is_ready')}}",
        "_source_types": ["world"]
    }
]
result = registry.call(
    "process_message_sequence_macros",
    messages=messages
)
# 第二次调用相同的消息时将使用缓存，显著提升性能
```

## 🔧 配置选项

### 变量控制 (`modules/SmartTavern/macro_module/variables.py`)
- `ENABLE_MACRO_PROCESSING`: 全局开关，控制是否启用宏处理
- `macros_processed_count`: 统计处理的宏数量

### 缓存配置
- **缓存文件路径**: `shared/SmartTavern/cache/macro_cache.json`
- **自动清理**: 系统会自动清理无效的缓存条目
- **哈希排除**: 时间相关变量（time, date等）不参与状态哈希计算

## 🔍 调试和监控

### 日志输出
- 缓存命中/未命中信息
- 宏执行成功/失败状态
- 变量状态变化追踪
- 性能统计信息

### 错误处理
- 优雅降级：出现错误时返回原始内容
- 详细错误信息：包含完整的堆栈跟踪
- 隔离错误：单个宏的错误不影响其他宏的执行

## 🚀 性能优化

### 缓存策略
- **O(1) 缓存查找**: 基于哈希的快速缓存检索
- **最小化重计算**: 只有内容或状态发生变化时才重新计算
- **内存效率**: 智能的状态快照管理

### 执行优化
- **单遍处理**: 按顺序逐个处理，确保依赖关系正确
- **沙盒复用**: Python沙盒实例在整个会话中复用
- **惰性加载**: 只在需要时才初始化转换器和缓存管理器

## 📚 扩展开发

### 添加新的传统宏
在 `legacy_macro_converter.py` 的 `convert_macro_to_python` 方法中添加新的转换规则：

```python
elif macro_name == 'my_new_macro':
    return f"result = my_custom_function({json.dumps(params)})"
```

### 自定义缓存策略
继承 `MacroCacheManager` 类并覆盖相关方法：

```python
class CustomCacheManager(MacroCacheManager):
    def get_state_hash(self, state):
        # 自定义状态哈希逻辑
        pass
```

### 扩展执行上下文
修改 `MacroExecutionContext` 数据类以添加新的上下文信息：

```python
@dataclass
class MacroExecutionContext:
    # 现有字段...
    custom_data: Dict[str, Any] = None