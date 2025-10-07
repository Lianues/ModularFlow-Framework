#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartTavern LLM Post-Process Workflow Implementation (impl.py)

目标：
- 调用通用 LLM API（modules/llm_api/chat），支持 stream=true/false
- 将最终 AI 回答聚合为一条 assistant 消息，追加到原始 messages 尾部
- 固定以 user_view 调用 prompt_postprocess（workflow）做“宏前正则 → 宏 → 宏后正则”
- 支持从工作流输入中注入 variables 作为宏初始变量（已在 prompt_postprocess 中支持透传）

输出：
- {"message":[...], "variables": {"initial":{}, "final":{}}}
"""
from typing import Any, Dict, List, Optional, Tuple
import asyncio
import copy
import json

import core  # type: ignore


def _deepcopy_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        return copy.deepcopy(messages or [])
    except Exception:
        return [dict(m) for m in (messages or [])]


def _normalize_llm_messages(messages: Any) -> List[Dict[str, str]]:
    """
    规范 llm.messages 至 [{role, content}]，忽略未知字段。
    - 只保留 role, content 两个字段；role 不在 {system,user,assistant} 的将被过滤/纠正为 user
    """
    if not isinstance(messages, list):
        return []
    out: List[Dict[str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role", "")).lower()
        content = "" if m.get("content") is None else str(m.get("content"))
        if role not in ("system", "user", "assistant"):
            # 非法/未知角色，保守视为 user
            role = "user"
        out.append({"role": role, "content": content})
    return out


def _build_assistant_message(text: str) -> Dict[str, Any]:
    """
    构造一条带 source 的 assistant 消息，便于后续正则 targets 命中。
    """
    return {
        "role": "assistant",
        "content": "" if text is None else str(text),
        "source": {
            "type": "history.assistant",
            "id": "llm_output",
            "from": "smarttavern.llm_postprocess",
        },
    }


def _parse_sse_aggregate(sse_text: str) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """
    将 text/event-stream（SSE）文本聚合为完整 content。
    - 逐帧解析 data: {...} 行
    - 聚合 {"type":"chunk","content":"..."} 的 content
    - 捕获 {"type":"usage","usage":{...}} 和 {"type":"finish","finish_reason":"..."}
    """
    full = []
    usage = None
    finish = None
    if not isinstance(sse_text, str) or not sse_text:
        return "", usage, finish

    # 以 \n\n 分帧（每帧形如：data: {...}\n\n）；容错处理 CRLF
    parts = sse_text.replace("\r\n", "\n").split("\n\n")
    for part in parts:
        p = part.strip()
        if not p or not p.startswith("data: "):
            continue
        body = p[6:].strip()
        if not body:
            continue
        try:
            evt = json.loads(body)
        except Exception:
            continue
        t = str(evt.get("type", ""))
        if t == "chunk" and isinstance(evt.get("content"), str):
            full.append(evt["content"])
        elif t == "usage" and isinstance(evt.get("usage"), dict):
            usage = evt["usage"]
        elif t == "finish":
            finish = evt.get("finish_reason")
        elif t == "error":
            # 出错则不中断聚合，但可考虑清空结果（此处保守保留已有文本）
            pass
        elif t == "end":
            # 结束帧，无需处理
            pass

    return "".join(full), usage, finish


async def _call_llm_and_collect(llm: Dict[str, Any]) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:
    """
    调用 modules/llm_api/chat 并收集最终文本。
    - stream=false：直接取 JSON 的 content
    - stream=true：会收到完整 SSE 文本（core.ApiClient 以文本返回），解析聚合得到最终 content
    返回：(content, usage, finish_reason)
    """
    # 仅透传允许字段，避免多余数据引发上游拒绝
    payload = dict(llm or {})
    res = await asyncio.to_thread(
        core.call_api,
        "llm_api/chat",
        payload,
        "POST",
        None,
        None,
        "modules",
    )

    # 非流式：JSON 对象
    if isinstance(payload.get("stream"), bool) and not payload.get("stream"):
        if isinstance(res, dict):
            content = "" if res.get("content") is None else str(res.get("content"))
            usage = res.get("usage") if isinstance(res.get("usage"), dict) else None
            finish = res.get("finish_reason")
            return content, usage, finish
        # 兜底
        return "", None, None

    # 流式：ApiClient 返回完整的 SSE 文本（非 JSON）
    if isinstance(res, str):
        return _parse_sse_aggregate(res)

    # 兜底
    return "", None, None


async def _postprocess_single_view(messages: List[Dict[str, Any]],
                                   rules: Any,
                                   variables: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    调用 workflow/smarttavern/prompt_postprocess/apply（单视图=user_view）
    - 传入 variables（宏初始变量，已由 prompt_postprocess 透传给宏模块）
    """
    payload = {
        "messages": messages,
        "rules": (rules if rules is not None else []),
        "view": "user_view",
        "variables": dict(variables or {}),
    }
    res = await asyncio.to_thread(
        core.call_api,
        "smarttavern/prompt_postprocess/apply",
        payload,
        "POST",
        None,
        None,
        "workflow",
    )
    # 结果标准化
    out_msg = []
    out_vars: Dict[str, Any] = {"initial": {}, "final": {}}
    if isinstance(res, dict):
        if isinstance(res.get("message"), list):
            out_msg = res["message"]
        if isinstance(res.get("variables"), dict):
            out_vars = res["variables"]
    return {"message": out_msg, "variables": out_vars}


async def apply(
    llm: Dict[str, Any],
    variables: Optional[Dict[str, Any]] = None,
    rules: Any = None,
) -> Dict[str, Any]:
    """
    工作流主入口：
    1) 调用 LLM（支持流/非流），聚合出最终 AI 文本
    2) 将 assistant 文本追加到原始 messages 尾部
    3) 固定 user_view 调用 prompt_postprocess（传入 variables）
    4) 返回 {"message":[...], "variables": {...}}
    """
    # 1) 规范/拷贝输入 messages
    llm = dict(llm or {})
    base_messages = _normalize_llm_messages(llm.get("messages", []))
    # 映射到带 source 的工作流消息（可直接将 role/content 作为基础；source 非必须）
    workflow_msgs = [{"role": m["role"], "content": m["content"]} for m in base_messages]

    # 2) 调用 LLM 并聚合文本
    content, _usage, _finish = await _call_llm_and_collect(llm)

    # 3) 追加 assistant 消息
    workflow_msgs.append(_build_assistant_message(content))

    # 4) 单视图后处理（user_view）
    result = await _postprocess_single_view(workflow_msgs, rules, variables)

    return result