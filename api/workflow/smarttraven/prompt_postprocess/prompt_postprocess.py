#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartTraven Prompt Post-Process Workflow Registration (prompt_postprocess.py)

职责（封装/注册层，仅声明 API，不包含实现逻辑）:
- 通过 @core.register_api 暴露工作流 API（斜杠路径 + JSON Schema）
- 实际实现委托给同目录的 impl.py

接口说明:
- 输入:
  - messages: OpenAI Chat 消息数组（[{role, content, source?}]），建议含 source
  - rules: 正则规则（数组或 {rules:[...]}）
  - macro_enabled: 是否启用宏处理（True: before_macro → macro → after_macro; False: before_macro → after_macro）
- 输出:
  - {"user_view":[...], "assistant_view":[...]}，两者均为 OpenAI Chat 消息数组（仅 content 可能被修改）
"""
from typing import Any, Dict, List

import core  # type: ignore

from .impl import apply as _apply


@core.register_api(
    path="smarttraven/prompt_postprocess/apply",
    name="提示词后处理（正则单视图 + 可选宏）",
    description=(
        "基于一份原始 messages，分别对 user_view/assistant_view 执行 "
        "before_macro →（可选）macro → after_macro 的后处理流水线；"
        "宏仅替换 content，保留 source 等其它字段。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant", "thinking"]},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
            },
            "rules": {"type": ["array", "object"]},
            "macro_enabled": {"type": "boolean"}
        },
        "required": ["messages", "rules", "macro_enabled"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "user_view": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant", "thinking"]},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
            },
            "assistant_view": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant", "thinking"]},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
            }
        },
        "required": ["user_view", "assistant_view"],
        "additionalProperties": False
    },
)
async def apply(
    messages: List[Dict[str, Any]],
    rules: Any,
    macro_enabled: bool,
) -> Dict[str, Any]:
    """
    适配器：转发到实现层（impl.py），遵循 “API 优先 / 解耦” 原则。
    """
    return await _apply(messages=messages, rules=rules, macro_enabled=macro_enabled)


if __name__ == "__main__":
    # 本文件为工作流 API 的注册封装层，非独立可执行脚本。
    # 请通过 API 网关运行或使用测试脚本进行验证。
    import json
    print(json.dumps({
        "message": "This file registers the Post-Process workflow API. Please run the API gateway or call the API instead."
    }, ensure_ascii=False))