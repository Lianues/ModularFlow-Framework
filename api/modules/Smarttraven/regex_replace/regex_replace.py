#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 封装层：SmartTraven.regex_replace
- 根据正则规则（参考 backend_projects/SmartTraven/data/regex_rules/*.json）对 messages 或 text 执行替换
- 支持 placement: before_macro / after_macro
- 输出三套视图：original / user_view / assistant_view
"""
from typing import Any, Dict, List, Optional
import core
from .impl import apply_regex as _apply_regex


@core.register_api(
    path="smarttraven/regex_replace/apply",
    name="正则替换（支持 messages 与 text）",
    description="根据规则文件对提示词进行正则替换，支持 placement before/after，按 views 产出 user_view/assistant_view，并透传 original。",
    input_schema={
        "type": "object",
        "properties": {
            "rules": {
                "type": ["array", "object"],
                "description": "正则规则数组或 {rules:[...]} 结构，参考 backend_projects/SmartTraven/data/regex_rules/*.json"
            },
            "placement": {
                "type": "string",
                "enum": ["before_macro", "after_macro"]
            },
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"],
                    "additionalProperties": True
                }
            },
            "text": {"type": "string"}
        },
        "required": ["rules", "placement"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "original": {"type": "object", "additionalProperties": True},
            "user_view": {"type": "object", "additionalProperties": True},
            "assistant_view": {"type": "object", "additionalProperties": True},
            "placement": {"type": "string"}
        },
        "required": ["original", "user_view", "assistant_view", "placement"],
        "additionalProperties": False
    },
)
def apply(
    rules: Any,
    placement: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    return _apply_regex(
        rules=rules,
        placement=placement,
        messages=messages,
        text=text,
    )