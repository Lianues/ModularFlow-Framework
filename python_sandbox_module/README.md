# Python沙盒模块 (`python_sandbox_module`) 文档

本模块提供了一个安全的、受限制的Python代码执行环境。

## 核心功能

模块提供了一个核心函数，已通过 `@register_function` 注册到工作流系统中。

### 1. `execute_python_code`

此函数用于在沙盒环境中安全地执行Python代码字符串。

-   **函数名**: `execute_python_code`
-   **描述**: 接收一段Python代码字符串，在受限的环境中执行它，并返回执行结果。

#### 输入 (`inputs`)

| 参数名           | 类型         | 描述                                                                                                                                                             |
| :--------------- | :----------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `code`           | `str`        | **必需**。要执行的Python代码字符串。代码可以是一个表达式（例如 `"1 + 2"`）或一个语句（例如 `"my_var = 10"`）。                                                     |
| `scope_type`     | `str`        | (可选, 默认: `'temp'`)。指定代码执行时的默认作用域，影响无前缀变量的读写位置。                                                                                   |
| `context_vars`   | `dict`       | (可选)。一个字典，包含额外的变量，这些变量将被注入到代码执行的上下文中。                                                                                           |

#### 输出 (`outputs`)

| 字段名    | 类型    | 描述                                         |
| :-------- | :------ | :------------------------------------------- |
| `success` | `bool`  | 代码是否成功执行。                           |
| `result`  | `Any`   | 如果代码是表达式，则为表达式的计算结果。     |
| `error`   | `str`   | 如果执行失败，则为错误信息。                 |

## 与全局变量交互

沙盒模块通过 `shared.globals.global_state` 与全局作用域进行交互。

-   **读取**: 在沙盒代码中，可以通过访问 `global_vars` 字典来读取全局变量。
-   **写入**: 在沙盒代码中，对 `global_vars` 字典的任何修改都会在执行后同步回 `shared.globals.global_state`。

## 使用示例

```python
# 假设已通过 registry.call() 或类似方式调用
from shared import globals as g

# 示例 1: 执行简单表达式
result = registry.call(
    "execute_python_code",
    code="'Hello, ' + 'World!'"
)
# result['success'] 将是 True
# result['result'] 将是 "Hello, World!"

# 示例 2: 与全局变量交互
g.global_state['counter'] = 5

result = registry.call(
    "execute_python_code",
    code="global_vars['counter'] += 1"
)

# g.global_state['counter'] 现在将是 6