# -*- coding: utf-8 -*-
"""
SmartTavern AI 对话补全工作流 - API 封装层

提供统一的AI对话补全能力：
- 读取对话文件获取messages
- 使用LLM配置调用AI
- 保存响应到对话文件
"""
from typing import Any, Dict
import core

from .impl import (
    chat_completion_non_streaming as _chat_completion_non_streaming,
    chat_completion_streaming as _chat_completion_streaming,
)


@core.register_api(
    path="smarttraven/chat_completion/complete",
    name="AI对话补全（非流式）",
    description="读取对话文件，调用AI生成响应，保存到对话文件。适用于一次性获取完整响应的场景",
    input_schema={
        "type": "object",
        "properties": {
            "conversation_file": {"type": "string"},
            "llm_config_file": {"type": "string"},
        },
        "required": ["conversation_file", "llm_config_file"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "node_id": {"type": "string"},
            "content": {"type": "string"},
            "usage": {"type": "object", "additionalProperties": True},
            "response_time": {"type": "number"},
            "model_used": {"type": "string"},
            "doc": {"type": "object", "additionalProperties": True},
            "error": {"type": "string"},
        },
        "required": ["success"],
        "additionalProperties": True,
    },
)
def complete(
    conversation_file: str,
    llm_config_file: str,
) -> Dict[str, Any]:
    return _chat_completion_non_streaming(
        conversation_file=conversation_file,
        llm_config_file=llm_config_file,
    )


@core.register_api(
    path="smarttraven/chat_completion/complete_stream",
    name="AI对话补全（流式）",
    description="读取对话文件，调用AI流式生成响应，逐块返回并最终保存到对话文件。返回SSE事件流",
    input_schema={
        "type": "object",
        "properties": {
            "conversation_file": {"type": "string"},
            "llm_config_file": {"type": "string"},
        },
        "required": ["conversation_file", "llm_config_file"],
        "additionalProperties": False,
    },
    output_schema={
        "type": "object",
        "description": "SSE流，事件类型：chunk/finish/usage/saved/error/end",
        "additionalProperties": True,
    },
)
def complete_stream(
    conversation_file: str,
    llm_config_file: str,
) -> Any:
    """
    流式补全：返回SSE
    事件格式：
    - data: {"type": "chunk", "content": "..."}
    - data: {"type": "finish", "finish_reason": "..."}
    - data: {"type": "usage", "usage": {...}}
    - data: {"type": "saved", "node_id": "...", "doc": {...}}
    - data: {"type": "error", "message": "..."}
    - data: {"type": "end"}
    """
    try:
        from fastapi.responses import StreamingResponse
    except Exception as e:
        return {
            "success": False,
            "error": f"SSE不可用（依赖fastapi未就绪）: {str(e)}"
        }
    
    import json
    
    def _sse_line(obj: Dict[str, Any]) -> str:
        return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
    
    def _make_sse_generator():
        try:
            for event in _chat_completion_streaming(
                conversation_file=conversation_file,
                llm_config_file=llm_config_file,
            ):
                yield _sse_line(event)
        except Exception as e:
            yield _sse_line({"type": "error", "message": str(e)})
            yield _sse_line({"type": "end"})
    
    return StreamingResponse(
        _make_sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )