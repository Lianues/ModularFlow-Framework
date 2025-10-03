"""
SmartTraven Prompt Workflow Implementation (impl.py)

说明:
- 仅包含实现逻辑，不做 API 注册
- 输入为 JSON 对象/数组，参考 backend_projects/SmartTraven/data 的结构，但不读取文件
"""
from typing import Any, Dict, List, Optional
import asyncio
import core


def _extract_prompts(doc: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从 presets 文档中提取 prompts 数组（容错）。"""
    if not isinstance(doc, dict):
        return []
    arr = doc.get("prompts")
    return arr if isinstance(arr, list) else []


def _split_presets(doc: Optional[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """拆分 relative 与 in-chat 预设。"""
    rel, inch = [], []
    for p in _extract_prompts(doc):
        if not isinstance(p, dict):
            continue
        pos = str(p.get("position", "")).lower()
        if pos == "relative":
            rel.append(p)
        elif pos == "in-chat":
            inch.append(p)
    return {"relative": rel, "in_chat": inch}


async def assemble_full(
    presets: Dict[str, Any],
    world_books: Any,
    history: List[Dict[str, Any]],
    triggered_worldbook_ids: List[int],
    character: Optional[Dict[str, Any]] = None,
    persona: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    执行流程
    1) 组合世界书：world_books_doc + character_doc.world_book.entries（若存在）
    2) 调用 modules/smarttraven/framing_prompt/assemble（HTTP via core.call_api → 线程池）
    3) 提取 in-chat 预设并调用 modules/smarttraven/in_chat_constructor/construct（HTTP via core.call_api → 线程池）
    4) 拼接与返回
    """
    # 1) 世界书透传（不做扁平与合并；上游负责准备完整 world_books）
    combined_wb: Any = world_books if world_books is not None else []

    # 2) framing（前缀 + 规范化历史）
    framing_payload = {
        "history": history or [],
        "triggered_worldbook_ids": triggered_worldbook_ids or [],
        "world_books": combined_wb,
        "presets_doc": presets or {},
        "character": character or {},
        "persona": persona or {},
    }
    framing_res = await asyncio.to_thread(
        core.call_api,
        "smarttraven/framing_prompt/assemble",
        framing_payload,
        "POST",
        "modules",
    )
    prefix_messages = framing_res.get("messages", []) or []
    normalized_history = framing_res.get("normalized_history", []) or []

    # 3) in-chat（在历史中按 depth/order 注入 in-chat 预设与世界书）
    presets_split = _split_presets(presets or {})
    presets_in_chat = presets_split["in_chat"]

    in_chat_payload = {
        "history": normalized_history,
        "presets_in_chat": presets_in_chat,
        "world_books": combined_wb,
        "triggered_worldbook_ids": triggered_worldbook_ids or [],
    }
    inchat_res = await asyncio.to_thread(
        core.call_api,
        "smarttraven/in_chat_constructor/construct",
        in_chat_payload,
        "POST",
        "modules",
    )
    in_chat_messages = inchat_res.get("messages", []) or []

    # 4) 拼接
    final_messages = list(prefix_messages) + list(in_chat_messages)
    return {"messages": final_messages}