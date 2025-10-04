"""
SmartTraven Prompt-Macro Workflow Registration (prompt_macro.py)

职责（封装/注册层，仅声明 API，不包含实现逻辑）:
- 注册工作流 smarttraven/prompt_macro/run
- 输入：变量初值 + 原始对话构件（presets/world_books/history/character/persona）
- 输出：宏处理后的 messages 与变量初末态（仅替换 content，保留 source 等字段）
- 严格模式固定启用（未定义变量输出错误占位词），本工作流不再接受 policy 入参
"""
from typing import Any, Dict, List, Optional

import core  # type: ignore

from .impl import run as _run


@core.register_api(
    path="smarttraven/prompt_macro/run",
    name="提示词装配并执行宏（prompt_macro）",
    description="先装配 framing+in-chat，随后对装配后的 messages 执行宏处理；仅替换 content，保留 source 等字段。严格模式固定启用。",
    input_schema={
        "type": "object",
        "properties": {
            "variables": {"type": "object", "additionalProperties": True},
            "presets": {"type": "object", "additionalProperties": True},
            "world_books": {"type": ["array", "object"]},
            "history": {
                "type": ["array", "object"],
                "additionalProperties": True
            },
            "character": {"type": "object", "additionalProperties": True},
            "persona": {"type": "object", "additionalProperties": True}
        },
        "required": ["variables", "presets", "world_books", "history"],
        "additionalProperties": True
    },
    output_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["system", "user", "assistant"]},
                        "content": {"type": "string"},
                        "source": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["role", "content"]
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
async def run(
    variables: Dict[str, Any],
    presets: Dict[str, Any],
    world_books: Any,
    history: Any,
    character: Optional[Dict[str, Any]] = None,
    persona: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    适配器：转发到实现层（impl.py），遵循 “API 优先 / 解耦” 原则。
    """
    return await _run(
        variables=variables or {},
        presets=presets,
        world_books=world_books,
        history=history,
        character=character,
        persona=persona,
    )


if __name__ == "__main__":
    import json
    print(json.dumps({
        "message": "This file registers the workflow API. Please run the API gateway or call the API instead."
    }, ensure_ascii=False))