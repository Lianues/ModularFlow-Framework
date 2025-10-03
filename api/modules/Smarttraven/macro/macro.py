#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 封装层：SmartTraven.macro
- 注册“顺序宏处理（仅修改 content）”API
"""
from typing import Any, Dict, List, Optional
import core
from .impl import process_messages as _process_messages


@core.register_api(
    path="smarttraven/macro/process",
    name="顺序宏处理（支持 {{..}} 与 <<..>>）",
    description="按顺序处理消息数组中的宏（setvar/getvar/python），仅替换 content，保留 source 等其他字段不变，并返回变量表（initial/final）",
    input_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
            },
            "variables": {"type": "object", "additionalProperties": True},
            "policy": {
                "type": "object",
                "properties": {
                    "undefined_get": {"type": "string", "enum": ["error", "empty"]},
                    "error_token": {"type": "string"}
                },
                "additionalProperties": True
            }
        },
        "required": ["messages"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
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
        "required": ["messages", "variables"],
        "additionalProperties": False
    },
)
def process(
    messages: List[Dict[str, Any]],
    variables: Optional[Dict[str, Any]] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _process_messages(messages=messages, variables=variables or {}, policy=policy or {})