"""
API 封装层：SmartTraven.chat_branches（分支重试对话）
- 遵循 DEVELOPMENT_NOTES 新规范：斜杠 path + JSON Schema
- 通过 @core.register_api 暴露公共 API，内部实现位于 impl.py
"""
from typing import Any, Dict, List, Optional
import core
from .impl import (
    create_conversation as _create_conversation,
    get_path as _get_path,
    append_message as _append_message,
    truncate_after as _truncate_after,
    switch_branch_and_start_new_session as _switch_branch,
    branch_indicator as _branch_indicator,
    list_conversations as _list_conversations,
    list_sessions as _list_sessions,
    openai_messages as _openai_messages,
    branch_table as _branch_table,
    export as _export_chat,
    import_chat as _import_chat,
)

# ============== Core Branching APIs ==============

@core.register_api(
    path="smarttraven/chat_branches/create_conversation",
    name="创建对话（含active会话）",
    description="创建一个新对话，含root节点与active会话",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {"type": ["string", "null"]},
            "title": {"type": ["string", "null"]},
        },
    },
    output_schema={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "session_id": {"type": "string"},
            "path": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
        },
        "required": ["conversation_id", "session_id", "path"],
    },
)
def create_conversation(user_id: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
    return _create_conversation(user_id=user_id, title=title)


@core.register_api(
    path="smarttraven/chat_branches/get_path",
    name="获取当前路径",
    description="获取指定会话的路径视图",
    input_schema={
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
        "required": ["session_id"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def get_path(session_id: str) -> Dict[str, Any]:
    return _get_path(session_id=session_id)


@core.register_api(
    path="smarttraven/chat_branches/append",
    name="追加楼层",
    description="在active会话尾部追加一层消息",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "role": {"type": "string", "enum": ["user", "assistant", "system"]},
            "content": {"type": "string"},
        },
        "required": ["session_id", "role", "content"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def append_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    return _append_message(session_id=session_id, role=role, content=content)


@core.register_api(
    path="smarttraven/chat_branches/truncate",
    name="修剪路径",
    description="将active会话修剪到 keep_depth 层（保留前缀，删除后缀）",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "keep_depth": {"type": "integer", "minimum": 1},
        },
        "required": ["session_id", "keep_depth"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def truncate_after(session_id: str, keep_depth: int) -> Dict[str, Any]:
    return _truncate_after(session_id=session_id, keep_depth=keep_depth)


@core.register_api(
    path="smarttraven/chat_branches/switch",
    name="切换分支并新建会话",
    description="在指定层左右切换分支，归档旧会话并创建新会话",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "at_depth": {"type": "integer", "minimum": 2},
            "direction": {"type": "string", "enum": ["left", "right"]},
        },
        "required": ["session_id", "at_depth", "direction"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def switch_branch_and_start_new_session(session_id: str, at_depth: int, direction: str) -> Dict[str, Any]:
    return _switch_branch(session_id=session_id, at_depth=at_depth, direction=direction)


@core.register_api(
    path="smarttraven/chat_branches/branch_indicator",
    name="分支指示 j/n",
    description="获取指定会话在某层的分支 j/n 指示",
    input_schema={
        "type": "object",
        "properties": {
            "session_id": {"type": "string"},
            "depth": {"type": "integer", "minimum": 2},
        },
        "required": ["session_id", "depth"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "j": {"type": ["integer", "null"]},
            "n": {"type": ["integer", "null"]},
        },
        "required": ["j", "n"],
    },
)
def branch_indicator(session_id: str, depth: int) -> Dict[str, Optional[int]]:
    return _branch_indicator(session_id=session_id, depth=depth)


# ============== Listing ==============

@core.register_api(
    path="smarttraven/chat_branches/list_conversations",
    name="列出对话",
    description="列出当前内存中的所有对话与活跃会话",
    input_schema={"type": "object", "properties": {}},
    output_schema={"type": "object", "additionalProperties": True},
)
def list_conversations() -> Dict[str, Any]:
    return _list_conversations()


@core.register_api(
    path="smarttraven/chat_branches/list_sessions",
    name="列出会话",
    description="列出某个对话下的所有会话",
    input_schema={
        "type": "object",
        "properties": {"conversation_id": {"type": "string"}},
        "required": ["conversation_id"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def list_sessions(conversation_id: str) -> Dict[str, Any]:
    return _list_sessions(conversation_id=conversation_id)




# ============== Derived Views ==============

@core.register_api(
    path="smarttraven/chat_branches/openai_messages",
    name="OpenAI 消息导出",
    description="导出当前分支为 OpenAI Chat messages 数组",
    input_schema={
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
        "required": ["session_id"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "session_id": {"type": "string"},
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["role", "content"],
                },
            },
        },
        "required": ["conversation_id", "session_id", "messages"],
    },
)
def openai_messages(session_id: str) -> Dict[str, Any]:
    return _openai_messages(session_id=session_id)


@core.register_api(
    path="smarttraven/chat_branches/branch_table",
    name="分支情况表",
    description="返回分支情况表，包括最新楼层 j/n 与各层分支信息",
    input_schema={
        "type": "object",
        "properties": {"session_id": {"type": "string"}},
        "required": ["session_id"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def branch_table(session_id: str) -> Dict[str, Any]:
    return _branch_table(session_id=session_id)

# ============== Stable File IO aliases (no version suffix) ==============
@core.register_api(
    path="smarttraven/chat_branches/export",
    name="导出对话文件",
    description="导出对话为 chat-branches 标准文件结构",
    input_schema={
        "type": "object",
        "properties": {"conversation_id": {"type": "string"}},
        "required": ["conversation_id"],
    },
    output_schema={"type": "object", "additionalProperties": True},
)
def export(conversation_id: str) -> Dict[str, Any]:
    # 内部实现沿用内部导出函数
    return _export_chat(conversation_id=conversation_id)


@core.register_api(
    path="smarttraven/chat_branches/import",
    name="导入对话文件",
    description="从 chat-branches 标准文件导入为内存对话，返回 active 会话",
    input_schema={
        "type": "object",
        "properties": {"doc": {"type": "object", "additionalProperties": True}},
        "required": ["doc"],
    },
    output_schema={
        "type": "object",
        "properties": {
            "conversation_id": {"type": "string"},
            "active_session_id": {"type": "string"},
        },
        "required": ["conversation_id", "active_session_id"],
    },
)
def import_chat(doc: Dict[str, Any]) -> Dict[str, str]:
    # 内部实现沿用内部导入函数
    return _import_chat(doc=doc)
