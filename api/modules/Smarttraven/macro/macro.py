#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 封装层：SmartTraven.macro
- 注册“顺序宏处理（仅修改 content）”API
"""
from typing import Any, Dict, List, Optional
import core
from .impl import process_messages as _process_messages, process_text_value as _process_text_value


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

@core.register_api(
    path="smarttraven/macro/process_text",
    name="纯文本顺序宏处理（支持 {{..}} 与 <<..>>）",
    description="按顺序处理单个纯文本中的宏，仅返回处理后的 text 与变量表（initial/final）",
    input_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "variables": {"type": "object", "additionalProperties": True},
        },
        "required": ["text"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string"},
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
        "required": ["text", "variables"],
        "additionalProperties": False
    },
)
def process_text(
    text: str,
    variables: Optional[Dict[str, Any]] = None,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _process_text_value(text=text, variables=variables or {}, policy=policy or {})