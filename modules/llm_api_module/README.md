# 通用LLM API模块

本模块提供统一的LLM API调用接口，支持多个API提供商，包括OpenAI、Anthropic、Google Gemini等。

## 特性

- 🔌 **多提供商支持**: 支持OpenAI、Anthropic、Gemini和自定义提供商
- 🚀 **统一接口**: 提供一致的API调用体验，无论使用哪个提供商
- 📡 **流式响应**: 支持实时流式文本生成
- 🔄 **自动格式转换**: 自动处理不同提供商的请求/响应格式
- 🛡️ **错误处理**: 完善的错误处理和重试机制
- 📊 **使用统计**: 内置令牌使用统计和监控
- 🔧 **灵活配置**: 可自定义超时、日志等配置

## 快速开始

### 基本使用

```python
from modules.llm_api_module import LLMAPIManager, APIConfiguration

# 创建API配置
config = APIConfiguration(
    provider="openai",
    api_key="your-api-key",
    base_url="https://api.openai.com/v1",
    models=["gpt-4", "gpt-3.5-turbo"],
    enabled=True
)

# 创建API管理器
manager = LLMAPIManager(config)

# 准备消息
messages = [
    {"role": "system", "content": "你是一个AI助手"},
    {"role": "user", "content": "你好"}
]

# 调用API
response = manager.call_api(
    messages=messages,
    model="gpt-4",
    max_tokens=2048,
    temperature=0.7
)

if response.success:
    print(response.content)
else:
    print(f"错误: {response.error}")
```

### 流式响应

```python
# 使用流式响应
response_stream = manager.call_api(
    messages=messages,
    model="gpt-4",
    stream=True
)

for chunk in response_stream:
    if chunk.content:
        print(chunk.content, end="", flush=True)
    if chunk.finish_reason:
        print(f"\n完成原因: {chunk.finish_reason}")
        if chunk.usage:
            print(f"使用统计: {chunk.usage}")
```

## 支持的提供商

### OpenAI
```python
config = APIConfiguration(
    provider="openai",
    api_key="sk-...",
    base_url="https://api.openai.com/v1",
    models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
)
```

### Anthropic Claude
```python
config = APIConfiguration(
    provider="anthropic",
    api_key="sk-ant-...",
    base_url="https://api.anthropic.com/v1",
    models=["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
)
```

### Google Gemini
```python
config = APIConfiguration(
    provider="gemini",
    api_key="AIza...",
    base_url="https://generativelanguage.googleapis.com/v1beta",
    models=["gemini-1.5-pro", "gemini-1.5-flash"]
)
```

### 自定义提供商
```python
config = APIConfiguration(
    provider="custom",
    api_key="your-key",
    base_url="https://your-api.com/v1",
    models=["your-model-1", "your-model-2"]
)
```

## API配置选项

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `provider` | str | 是 | 提供商名称 (openai/anthropic/gemini/custom) |
| `api_key` | str | 是 | API密钥 |
| `base_url` | str | 是 | API基础URL |
| `models` | List[str] | 是 | 可用模型列表 |
| `enabled` | bool | 否 | 是否启用 (默认: True) |
| `timeout` | int | 否 | 请求超时时间 (默认: 60秒) |
| `connect_timeout` | int | 否 | 连接超时时间 (默认: 10秒) |
| `enable_logging` | bool | 否 | 是否启用详细日志 (默认: False) |

## 响应格式

### 非流式响应
```python
@dataclass
class APIResponse:
    success: bool                    # 请求是否成功
    content: str                     # 生成的内容
    error: Optional[str]             # 错误信息
    usage: Optional[Dict[str, Any]]  # 使用统计
    response_time: float             # 响应时间
    model_used: Optional[str]        # 使用的模型
    finish_reason: Optional[str]     # 完成原因
    raw_response: Optional[Dict]     # 原始响应数据
    provider: Optional[str]          # 提供商名称
```

### 流式响应
```python
@dataclass
class StreamChunk:
    content: str                     # 内容片段
    finish_reason: Optional[str]     # 完成原因
    usage: Optional[Dict[str, Any]]  # 使用统计（最后一个chunk）
```

## 高级功能

### 自定义参数
```python
response = manager.call_api(
    messages=messages,
    model="gpt-4",
    temperature=0.8,
    top_p=0.9,
    max_tokens=4096,
    presence_penalty=0.1,
    frequency_penalty=0.1,
    stop_sequences=["[STOP]"]
)
```

### Gemini特性
```python
response = manager.call_api(
    messages=messages,
    model="gemini-1.5-pro",
    disable_thinking=True  # 禁用思考模式
)
```

### Anthropic特性
```python
response = manager.call_api(
    messages=messages,
    model="claude-3-opus-20240229",
    enable_thinking=True,          # 启用扩展思考
    thinking_budget=16000,         # 思考token预算
    stop_sequences=["Human:", "AI:"]
)
```

## 错误处理

```python
try:
    response = manager.call_api(messages)
    if not response.success:
        if "rate limit" in response.error.lower():
            print("请求频率过高，请稍后重试")
        elif "invalid api key" in response.error.lower():
            print("API密钥无效")
        else:
            print(f"API调用失败: {response.error}")
except Exception as e:
    print(f"意外错误: {e}")
```

## 最佳实践

1. **密钥管理**: 使用环境变量存储API密钥，不要硬编码
2. **错误重试**: 对临时网络错误实施指数退避重试
3. **流式响应**: 对于长文本生成使用流式响应提升用户体验
4. **使用统计**: 监控token使用量来控制成本
5. **超时设置**: 根据应用需求合理设置超时时间
6. **日志记录**: 在开发环境启用详细日志便于调试

## 许可证

本模块采用MIT许可证。