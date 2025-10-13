# -*- coding: utf-8 -*-
"""
API 封装层：SmartTavern.chat_branches（无状态版）

只提供基于“单个对话分支树文件（最小结构）”的派生视图能力：
- openai_messages(doc): 从最小分支树文件导出 OpenAI Chat messages
- branch_table(doc): 从最小分支树文件计算分支情况表（含最新层 j/n）

最小分支树文件结构（仅四个字段）：
{
  "roots": ["node_id1", "node_id2", ...],  // 所有根节点ID数组
  "nodes": {
    "node_id": { "pid": "parent_id|null", "role": "system|user|assistant", "content": "..." }
  },
  "children": { "parent_id": ["child_id1","child_id2",...] },   // 可选
  "active_path": ["current_root","...","leafId"]                // 第一个元素是当前使用的根节点
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
    get_latest_message_from_doc as _get_latest_message_from_doc,
    update_message_content as _update_message_content,
    truncate_after_node as _truncate_after_node,
    append_new_message as _append_new_message,
    create_conversation_impl as _create_conversation_impl,
    settings_impl as _settings_impl,
    variables_impl as _variables_impl,
)


@core.register_api(
    path="smarttavern/chat_branches/openai_messages",
    name="OpenAI 消息导出（无状态）",
    description="从最小分支树文件导出 OpenAI Chat messages 数组。支持传入 doc（JSON 对象）或 file（文件路径）二选一",
    input_schema={
        "type": "object",
        "properties": {
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "additionalProperties": False,
        "oneOf": [
            {"required": ["doc"]},
            {"required": ["file"]}
        ]
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
def openai_messages(doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _openai_messages_from_doc(doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/branch_table",
    name="分支情况表（无状态）",
    description="从最小分支树文件计算分支情况表（含最新层 j/n）。支持传入 doc（JSON 对象）或 file（文件路径）二选一",
    input_schema={
        "type": "object",
        "properties": {
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "additionalProperties": False,
        "oneOf": [
            {"required": ["doc"]},
            {"required": ["file"]}
        ]
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
def branch_table(doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _branch_table_from_doc(doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/get_latest_message",
    name="获取最后一条消息（无状态）",
    description="根据 active_path 提取最后一条消息。支持传入 doc（JSON 对象）或 file（文件路径）二选一",
    input_schema={
        "type": "object",
        "properties": {
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "additionalProperties": False,
        "oneOf": [
            {"required": ["doc"]},
            {"required": ["file"]}
        ]
    },
    output_schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string"},
            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
            "content": {"type": "string"},
            "depth": {"type": "integer"}
        },
        "required": ["node_id", "role", "content", "depth"],
        "additionalProperties": False,
    },
)
def get_latest_message(doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _get_latest_message_from_doc(doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/update_message",
    name="修改消息内容",
    description="修改指定节点的 content，返回更新后的完整 doc（含 updated_at）",
    input_schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string"},
            "content": {"type": "string"},
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "required": ["node_id", "content"],
        "additionalProperties": False,
        "oneOf": [
            {"required": ["node_id", "content", "doc"]},
            {"required": ["node_id", "content", "file"]}
        ]
    },
    output_schema={
        "type": "object",
        "additionalProperties": True
    },
)
def update_message(node_id: str, content: str, doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _update_message_content(node_id=node_id, content=content, doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/truncate_after",
    name="修剪消息树",
    description="删除指定节点及其所有子孙；更新 nodes/children/active_path（截断到父节点）/updated_at",
    input_schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string"},
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "required": ["node_id"],
        "additionalProperties": False,
        "oneOf": [
            {"required": ["node_id", "doc"]},
            {"required": ["node_id", "file"]}
        ]
    },
    output_schema={
        "type": "object",
        "additionalProperties": True
    },
)
def truncate_after(node_id: str, doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _truncate_after_node(node_id=node_id, doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/append_message",
    name="追加新消息",
    description="创建新节点，更新父节点 children 与 active_path，返回完整 doc（含 updated_at）",
    input_schema={
        "type": "object",
        "properties": {
            "node_id": {"type": "string"},
            "pid": {"type": "string"},
            "role": {"type": "string", "enum": ["system", "user", "assistant"]},
            "content": {"type": "string"},
            "doc": {"type": "object", "additionalProperties": True},
            "file": {"type": "string"}
        },
        "required": ["node_id", "pid", "role", "content"],
        "additionalProperties": False,
        "oneOf": [
            {"required": ["node_id", "pid", "role", "content", "doc"]},
            {"required": ["node_id", "pid", "role", "content", "file"]}
        ]
    },
    output_schema={
        "type": "object",
        "additionalProperties": True
    },
)
def append_message(node_id: str, pid: str, role: str, content: str, doc: Dict[str, Any] = None, file: str = None) -> Dict[str, Any]:
    return _append_new_message(node_id=node_id, pid=pid, role=role, content=content, doc=doc, file=file)


@core.register_api(
    path="smarttavern/chat_branches/create_conversation",
    name="创建初始对话文件（从角色卡 messages[0] 派生）",
    description=(
        "根据 NewGame 选择项创建一套对话三件套：{slug}.json / {slug}.settings.json / {slug}.variables.json。"
        "从角色卡文件读取 messages[0] 作为根消息（暂不启用多分支）。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "type": {"type": "string", "enum": ["threaded"]},
            "character_file": {"type": "string"},
            "preset_file": {"type": "string"},
            "persona_file": {"type": "string"},
            "regex_file": {"type": ["string", "null"]},
            "worldbook_file": {"type": ["string", "null"]},
        },
        "required": ["name", "description", "character_file", "preset_file", "persona_file"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "settings_file": {"type": "string"},
            "variables_file": {"type": "string"},
            "name": {"type": "string"},
            "root_node_id": {"type": "string"},
            "nodes_count": {"type": "integer"},
            "updated_at": {"type": "string"},
            "slug": {"type": "string"},
        },
        "required": ["file", "settings_file", "variables_file", "name", "root_node_id", "nodes_count", "updated_at", "slug"],
        "additionalProperties": True,
    },
)
def create_conversation(
    name: str,
    description: str,
    character_file: str,
    preset_file: str,
    persona_file: str,
    regex_file: str = None,
    worldbook_file: str = None,
    type: str = "threaded",
) -> Dict[str, Any]:
    return _create_conversation_impl(
        name=name,
        description=description,
        character_file=character_file,
        preset_file=preset_file,
        persona_file=persona_file,
        regex_file=regex_file,
        worldbook_file=worldbook_file,
        chat_type=type or "threaded",
    )


@core.register_api(
    path="smarttavern/chat_branches/settings",
    name="对话设置综合管理（settings.json）",
    description=(
        "读取或更新 conversations/{name}.settings.json。"
        "action=get: 读取当前设置；action=update: 更新指定字段。"
        "允许字段：preset(string)、character(string)、persona(string)、regex_rules(array)、world_books(array)。"
        "使用 file 或 slug 二选一定位。"
    ),
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["get", "update"]},
            "patch": {
                "type": "object",
                "properties": {
                    "preset": {"type": "string"},
                    "character": {"type": "string"},
                    "persona": {"type": "string"},
                    "regex_rules": {"type": "array", "items": {"type": "string"}},
                    "world_books": {"type": "array", "items": {"type": "string"}}
                },
                "additionalProperties": False
            },
            "file": {"type": "string"},
            "slug": {"type": "string"}
        },
        "required": ["action"],
        "additionalProperties": False,
        "oneOf": [
            {"required": ["action", "file"]},
            {"required": ["action", "slug"]}
        ]
    },
    output_schema={
        "type": "object",
        "properties": {
            "settings_file": {"type": "string"},
            "settings": {"type": "object", "additionalProperties": True},
            "slug": {"type": "string"},
        },
        "required": ["settings_file", "settings", "slug"],
        "additionalProperties": False,
    },
)
def settings(action: str, file: str = None, slug: str = None, patch: Dict[str, Any] = None) -> Dict[str, Any]:
    return _settings_impl(action=action, file=file, slug=slug, patch=patch)


@core.register_api(
    path="smarttavern/chat_branches/variables",
    name="对话变量管理（variables.json）",
    description="管理 conversations/{name}.variables.json：action=get|set|merge|reset。set/merge 需 data 对象。使用 file 或 slug 二选一定位。",
    input_schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["get", "set", "merge", "reset"]},
            "data": {"type": "object"},
            "file": {"type": "string"},
            "slug": {"type": "string"}
        },
        "required": ["action"],
        "additionalProperties": False,
        "oneOf": [
            {"required": ["action", "file"]},
            {"required": ["action", "slug"]}
        ]
    },
    output_schema={
        "type": "object",
        "properties": {
            "variables_file": {"type": "string"},
            "variables": {"type": "object", "additionalProperties": True},
            "slug": {"type": "string"},
        },
        "required": ["variables_file", "variables", "slug"],
        "additionalProperties": False,
    },
)
def variables(action: str, file: str = None, slug: str = None, data: Dict[str, Any] = None) -> Dict[str, Any]:
    return _variables_impl(action=action, file=file, slug=slug, data=data)




