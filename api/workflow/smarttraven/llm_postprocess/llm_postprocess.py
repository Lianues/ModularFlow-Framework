#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartTavern LLM Post-Process Workflow Registration (llm_postprocess.py)

职责（封装/注册层，仅声明 API，不包含实现逻辑）:
- 通过 @core.register_api 暴露工作流 API（斜杠路径 + JSON Schema）
- 实际实现委托给同目录的 impl.py

功能概述：
- 调用通用 LLM API（modules/llm_api/chat，支持 stream=true/false）
- 流式场景：在 SSE 完整结束后聚合文本，再进入后处理
- 将 LLM 的最终回答追加为一条 assistant 消息
- 固定以 user_view 调用单视图后处理工作流 smarttavern/prompt_postprocess/apply
- 宏阶段可接收上游传入的 variables（已扩展支持）

输入：
- llm: LLM API 配置（含 messages）
- variables: 可选，传入宏初始变量
- rules: 可选，正则规则（数组或 {rules:[...]}）

输出：
- {"message":[...], "variables": {"initial":{}, "final":{}}}
"""
from typing import Any, Dict, List, Optional

import core  # type: ignore

from .impl import apply as _apply


# Schema 片段复用
_message_item_schema: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "role": {"type": "string", "enum": ["system", "user", "assistant", "thinking"]},
        "content": {"type": "string"},
        "source": {"type": "object", "additionalProperties": True}
    },
    "required": ["role", "content"],
    "additionalProperties": True
}

_llm_config_schema: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "provider": {"type": "string", "enum": ["openai", "anthropic", "gemini", "openai_compatible", "custom"]},
        "api_key": {"type": "string"},
        "base_url": {"type": "string"},
        "messages": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                    "content": {"type": "string"}
                },
                "required": ["role", "content"],
                "additionalProperties": True
            }
        },
        "stream": {"type": "boolean", "default": False},
        "model": {"type": "string"},
        "max_tokens": {"type": "integer", "default": 2048},
        "temperature": {"type": "number", "default": 0.7},
        "top_p": {"type": "number"},
        "presence_penalty": {"type": "number"},
        "frequency_penalty": {"type": "number"},
        "custom_params": {"type": "object", "additionalProperties": True},
        "safety_settings": {"type": "object", "additionalProperties": True},
        "timeout": {"type": "integer"},
        "connect_timeout": {"type": "integer"},
        "enable_logging": {"type": "boolean"},
        "models": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["provider", "api_key", "base_url", "messages"],
    "additionalProperties": True
}


@core.register_api(
    path="smarttavern/llm_postprocess/apply",
    name="LLM 调用 + 单视图后处理（user_view）",
    description=(
        "先调用 llm_api/chat（支持 stream），在流式结束后聚合文本，"
        "将 assistant 最终文本追加到原 messages，"
        "再以 user_view 调用 prompt_postprocess：before_macro → macro → after_macro。"
        "宏阶段支持传入 variables 作为初始变量。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "llm": _llm_config_schema,
            "variables": {"type": "object", "additionalProperties": True},
            "rules": {"type": ["array", "object"]},
        },
        "required": ["llm"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "message": {
                "type": "array",
                "items": _message_item_schema
            },
            "variables": {
                "type": "object",
                "properties": {
                    "initial": {"type": "object", "additionalProperties": True},
                    "final": {"type": "object", "additionalProperties": True}
                },
                "required": ["initial", "final"],
                "additionalProperties": False
            }
        },
        "required": ["message", "variables"],
        "additionalProperties": False
    },
)
async def apply(
    llm: Dict[str, Any],
    variables: Optional[Dict[str, Any]] = None,
    rules: Any = None,
) -> Dict[str, Any]:
    """
    适配器：转发到实现层（impl.py），遵循 “API 优先 / 解耦” 原则。
    """
    return await _apply(llm=llm, variables=variables, rules=rules)


if __name__ == "__main__":
    import json
    print(json.dumps({
        "message": "This file registers the LLM + Post-Process workflow API. Please run the API gateway or call the API instead."
    }, ensure_ascii=False))