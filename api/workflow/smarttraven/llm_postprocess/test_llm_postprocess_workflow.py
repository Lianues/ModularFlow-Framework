#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test: smarttavern/llm_postprocess/apply with mocked LLM and downstream
- 不启动API网关；通过 monkeypatch core.call_api 来伪造：
  • modules/llm_api/chat → 返回非流式JSON或流式SSE文本
  • workflow/smarttavern/prompt_postprocess/apply → 直接在测试里做最小模拟（变量替换 + 简单去标签），检验：
      - view 固定为 user_view
      - variables 透传
      - LLM assistant 消息已被追加
运行:
  python -u api/workflow/smarttavern/llm_postprocess/test_llm_postprocess_workflow.py
"""
import asyncio
import json
import re
import copy
from typing import Any, Dict, Optional
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import core  # noqa: E402
from api.workflow.smarttavern.llm_postprocess.impl import apply as llm_apply


def _strip_xml(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "")


def _mock_prompt_postprocess_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    # 断言视图
    assert payload.get("view") == "user_view", f"expect user_view, got {payload.get('view')}"
    messages = copy.deepcopy(payload.get("messages") or [])
    variables = dict(payload.get("variables") or {})

    # before_macro: 简单去标签（模拟规则效果；不深究 placement/targets/view）
    for m in messages:
        m["content"] = _strip_xml(m.get("content", ""))

    # macro: 执行最简单的 {{getvar:name}} 替换；忽略其他宏
    def _macro_getvar_replace(s: str) -> str:
        def _repl(mo):
            name = mo.group(1).strip()
            return "" if variables.get(name) is None else str(variables.get(name, ""))
        return re.sub(r"\{\{\s*getvar:([a-zA-Z0-9_\-\.]+)\s*\}\}", _repl, s)
    for m in messages:
        m["content"] = _macro_getvar_replace(m.get("content", ""))

    # after_macro: 再做一次去标签（示意）
    for m in messages:
        m["content"] = _strip_xml(m.get("content", ""))

    return {
        "message": messages,
        "variables": {
            "initial": variables,
            "final": variables
        }
    }


def _build_sse(*events: Dict[str, Any]) -> str:
    # 构造 text/event-stream 文本
    parts = []
    for e in events:
        parts.append("data: " + json.dumps(e, ensure_ascii=False))
    return "\n\n".join(parts) + "\n\n"


def _make_fake_call_api(streaming: bool, variables_expected: Optional[Dict[str, Any]]):
    """
    返回一个 fake core.call_api，用于 monkeypatch。
    """

    def _fake(name: str,
              payload: Optional[Dict[str, Any]] = None,
              method: str = "POST",
              headers=None,
              files=None,
              namespace: Optional[str] = None) -> Any:
        if name == "llm_api/chat":
            # 非流式：返回 JSON
            if not (payload or {}).get("stream"):
                # content 含变量占位与HTML标签，便于后续处理验证
                return {
                    "success": True,
                    "content": "AI答复：关于 {{getvar:topic}} <b>小节</b>",
                    "usage": {"prompt_tokens": 12, "completion_tokens": 7, "total_tokens": 19},
                    "finish_reason": "stop",
                    "provider": (payload or {}).get("provider", "openai"),
                }
            # 流式：返回完整 SSE 文本（两段chunk + finish + end）
            sse = _build_sse(
                {"type": "chunk", "content": "AI答复：关"},
                {"type": "chunk", "content": "于 {{getvar:topic}} <i>流式</i>"},
                {"type": "finish", "finish_reason": "stop"},
                {"type": "end"}
            )
            return sse

        if name == "smarttavern/prompt_postprocess/apply":
            # 断言 variables 已透传
            if variables_expected is not None:
                v = (payload or {}).get("variables") or {}
                assert all(v.get(k) == variables_expected.get(k) for k in variables_expected.keys()), \
                    f"variables not propagated: expected {variables_expected}, got {v}"
            return _mock_prompt_postprocess_apply(payload or {})

        # 其他API默认返回404风格
        return {"error_code": "HTTP_ERROR", "status": 404, "message": f"Not mocked: {name}"}

    return _fake


async def _case_non_streaming() -> Dict[str, Any]:
    # 输入
    llm = {
        "provider": "openai",
        "api_key": "sk-test",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "stream": False,
        "messages": [
            {"role": "system", "content": "系统：<p>引导</p>"},
            {"role": "user", "content": "请介绍 {{getvar:topic}} 并移除<b>标签</b>"},
        ]
    }
    variables = {"topic": "夜晚的海风与路灯"}
    rules = {
        "rules": [
            {"id": "rm_xml", "enabled": True, "placement": "before_macro", "views": ["user_view","assistant_view"],
             "targets": ["history","preset","world_book"], "find_regex": "<[^>]+>", "replace_regex": ""}
        ]
    }

    # monkeypatch
    old = core.call_api
    core.call_api = _make_fake_call_api(streaming=False, variables_expected=variables)
    try:
        res = await llm_apply(llm=llm, variables=variables, rules=rules)
    finally:
        core.call_api = old
    return res


async def _case_streaming() -> Dict[str, Any]:
    llm = {
        "provider": "openai",
        "api_key": "sk-test",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "stream": True,
        "messages": [
            {"role": "user", "content": "流式测试：{{getvar:topic}} <u>U</u>"}
        ]
    }
    variables = {"topic": "海边的清晨"}
    rules = {"rules": []}  # 简化：不提供正则

    old = core.call_api
    core.call_api = _make_fake_call_api(streaming=True, variables_expected=variables)
    try:
        res = await llm_apply(llm=llm, variables=variables, rules=rules)
    finally:
        core.call_api = old
    return res


def _print(title: str, obj: Any) -> None:
    print("=" * 80)
    print(title)
    print("-" * 80)
    print(json.dumps(obj, indent=2, ensure_ascii=False))


async def main():
    res1 = await _case_non_streaming()
    _print("非流式用例（期望：变量替换 + 去标签）", res1)
    # 基本断言
    assert isinstance(res1, dict) and isinstance(res1.get("message"), list), "invalid output (non-stream)"
    assert any(m.get("role") == "assistant" for m in res1["message"]), "assistant message missing"
    # 确认变量替换生效
    out_text = " ".join(m.get("content","") for m in res1["message"])
    assert "夜晚的海风与路灯" in out_text, "variable expansion failed (non-stream)"
    assert "<" not in out_text and ">" not in out_text, "xml tag not stripped (non-stream)"

    res2 = await _case_streaming()
    _print("流式用例（期望：SSE 聚合 + 变量替换）", res2)
    assert isinstance(res2, dict) and isinstance(res2.get("message"), list), "invalid output (stream)"
    out_text2 = " ".join(m.get("content","") for m in res2["message"])
    assert "海边的清晨" in out_text2, "variable expansion failed (stream)"

    print("OK: llm_postprocess mocked tests passed")


if __name__ == "__main__":
    asyncio.run(main())