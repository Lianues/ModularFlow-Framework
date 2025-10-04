#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartTraven Prompt Post-Process Workflow Implementation (impl.py)

职责：
- 基于一份 canonical 原始 messages，分别为 user_view / assistant_view 执行：
  before_macro → （可选）macro → after_macro
- 正则调用统一使用 modules/smarttraven/regex_replace 两个单视图 API（apply_messages）
- 宏调用统一使用 modules/smarttraven/macro/process（仅替换 content，保留 source）
- 输出两个视图各自的消息数组（不再包裹 {"messages":[] }）

输入（由注册层校验）：
- messages: List[ChatMessage]
- rules: List[Rule] 或 {rules:[...]}
- macro_enabled: bool

输出：
- {"user_view":[...], "assistant_view":[...]}

注意：
- 变量上下文：各视图独立（此处采用空变量初值 {}，若未来需要注入变量可扩展入参）
"""

from typing import Any, Dict, List, Optional
import asyncio
import copy
import core  # type: ignore
import json

def _dbg(label: str, data: Any = None) -> None:
    # 调试关闭：不输出任何日志
    return None

def _first_content(msgs: List[Dict[str, Any]]) -> str:
    try:
        if msgs and isinstance(msgs[0], dict):
            return str(msgs[0].get("content", ""))
    except Exception:
        pass
    return ""


def _deepcopy_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        # 消息为浅结构（role/content/source），浅拷贝足够；此处使用 deepcopy 以更保守
        return copy.deepcopy(messages or [])
    except Exception:
        return [dict(m) for m in (messages or [])]


def _safe_get_messages(res: Any, fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    try:
        if isinstance(res, dict) and isinstance(res.get("message"), list):
            return res["message"]
    except Exception:
        pass
    return fallback


async def _regex_apply_messages(
    messages: List[Dict[str, Any]],
    rules: Any,
    placement: str,
    view: str,
) -> List[Dict[str, Any]]:
    """
    单视图正则处理（messages）
    - 调用 modules/smarttraven/regex_replace/apply_messages
    - 返回处理后的 messages；失败时返回原 messages
    """
    _dbg(f"regex.call.{view}.{placement}.in_first", _first_content(messages))
    payload = {
        "rules": rules,
        "placement": placement,
        "view": view,
        "messages": messages,
    }
    try:
        res = await asyncio.to_thread(
            core.call_api,
            "smarttraven/regex_replace/apply_messages",
            payload,
            "POST",
            None,   # headers
            None,   # files
            "modules",  # namespace (must be the 6th positional arg)
        )
        try:
            _dbg(f"regex.res.{view}.{placement}.type", type(res).__name__)
            if isinstance(res, dict):
                _dbg(f"regex.res.{view}.{placement}.keys", list(res.keys()))
                first = ""
                try:
                    if isinstance(res.get("message"), list) and res["message"]:
                        first = str(res["message"][0].get("content", ""))
                except Exception:
                    first = ""
                _dbg(f"regex.res.{view}.{placement}.out_first_preview", first)
        except Exception:
            pass
        out = _safe_get_messages(res, messages)
        _dbg(f"regex.call.{view}.{placement}.out_first", _first_content(out))
        return out
    except Exception as e:
        _dbg(f"regex.call.{view}.{placement}.exception", repr(e))
        return messages


async def _macro_process_messages(
    messages: List[Dict[str, Any]],
    variables: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    调用 modules/smarttraven/macro/process
    - 返回处理后的 messages；失败时返回原 messages
    """
    payload = {
        "messages": messages,
        "variables": dict(variables or {}),
    }
    try:
        res = await asyncio.to_thread(
            core.call_api,
            "smarttraven/macro/process",
            payload,
            "POST",
            None,   # headers
            None,   # files
            "modules",  # namespace
        )
        if isinstance(res, dict) and isinstance(res.get("messages"), list):
            return res["messages"]
    except Exception:
        pass
    return messages


async def apply(
    messages: List[Dict[str, Any]],
    rules: Any,
    macro_enabled: bool,
) -> Dict[str, Any]:
    """
    工作流主入口（实现层）
    - 顺序：before_macro → (macro?) → after_macro
    - 分别对 user_view 与 assistant_view 跑一遍
    """
    try:
        _dbg("input.messages.count", len(messages or []))
    except Exception:
        pass
    try:
        _dbg("rules.type", type(rules).__name__)
        if isinstance(rules, list):
            _dbg("rules.len", len(rules))
        elif isinstance(rules, dict):
            arr = rules.get("rules") if isinstance(rules, dict) else None
            _dbg("rules.rules.len", len(arr or []))
    except Exception:
        pass

    base = _deepcopy_messages(messages)
    _dbg("base.first", _first_content(base))

    # user_view 流水线
    user_msgs = _deepcopy_messages(base)
    _dbg("user.start.first", _first_content(user_msgs))
    user_msgs = await _regex_apply_messages(user_msgs, rules, "before_macro", "user_view")
    _dbg("user.after_before_macro.first", _first_content(user_msgs))
    if macro_enabled:
        user_msgs = await _macro_process_messages(user_msgs, variables={})
        _dbg("user.after_macro.first", _first_content(user_msgs))
    user_msgs = await _regex_apply_messages(user_msgs, rules, "after_macro", "user_view")
    _dbg("user.after_after_macro.first", _first_content(user_msgs))

    # assistant_view 流水线
    assist_msgs = _deepcopy_messages(base)
    _dbg("assistant.start.first", _first_content(assist_msgs))
    assist_msgs = await _regex_apply_messages(assist_msgs, rules, "before_macro", "assistant_view")
    _dbg("assistant.after_before_macro.first", _first_content(assist_msgs))
    if macro_enabled:
        assist_msgs = await _macro_process_messages(assist_msgs, variables={})
        _dbg("assistant.after_macro.first", _first_content(assist_msgs))
    assist_msgs = await _regex_apply_messages(assist_msgs, rules, "after_macro", "assistant_view")
    _dbg("assistant.after_after_macro.first", _first_content(assist_msgs))

    # 输出完整 JSON（输入原始提示词 + 两个视图的提示词）
    try:
        print(json.dumps({
            "input_messages": messages,
            "user_view": user_msgs,
            "assistant_view": assist_msgs
        }, ensure_ascii=False, indent=2))
    except Exception:
        pass

    return {
        "user_view": user_msgs,
        "assistant_view": assist_msgs,
    }