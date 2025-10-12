# -*- coding: utf-8 -*-
"""
API 封装层：SmartTavern.chat_branches（无状态版）

只提供基于“单个对话分支树文件（最小结构）”的派生视图能力：
- openai_messages(doc): 从最小分支树文件导出 OpenAI Chat messages
- branch_table(doc): 从最小分支树文件计算分支情况表（含最新层 j/n）

最小分支树文件结构（仅四个字段）：
{
  "root": "node_id",
  "nodes": {
    "node_id": { "pid": "parent_id|null", "role": "system|user|assistant", "content": "..." }
  },
  "children": { "parent_id": ["child_id1","child_id2",...] },   // 可选
  "active_path": ["root","...","leafId"]                        // 可选
}

注意：
- 本模块不再管理任何对话/会话状态（无 create/append/truncate/switch/export/import/list_* 等接口）
- 外部可直接存储与读取 JSON 文件；此处仅负责计算视图
"""
from typing import Any, Dict
import core
from .impl import (
    openai_messages_from_doc as _openai_messages_from_doc,
    branch_table_from_doc as _branch_table_from_doc,
)


@core.register_api(
    path="smarttavern/chat_branches/openai_messages",
    name="OpenAI 消息导出（无状态）",
    description="从最小分支树文件 doc 导出 OpenAI Chat messages 数组",
    input_schema={
        "type": "object",
        "properties": {
            "doc": {"type": "object", "additionalProperties": True}
        },
        "required": ["doc"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"role": {"type": "string"}, "content": {"type": "string"}},
                    "required": ["role", "content"],
                },
            },
            "path": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["messages"],
        "additionalProperties": True,
    },
)
def openai_messages(doc: Dict[str, Any]) -> Dict[str, Any]:
    return _openai_messages_from_doc(doc=doc)


@core.register_api(
    path="smarttavern/chat_branches/branch_table",
    name="分支情况表（无状态）",
    description="从最小分支树文件 doc 计算分支情况表（含最新层 j/n）",
    input_schema={
        "type": "object",
        "properties": {
            "doc": {"type": "object", "additionalProperties": True}
        },
        "required": ["doc"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "latest": {"type": "object", "additionalProperties": True},
            "levels": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        },
        "required": ["latest", "levels"],
        "additionalProperties": True,
    },
)
def branch_table(doc: Dict[str, Any]) -> Dict[str, Any]:
    return _branch_table_from_doc(doc=doc)
