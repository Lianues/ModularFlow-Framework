#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：in_chat_constructor 来源类型规范化（source.type）
覆盖枚举：
- history.user / history.assistant / history.thinking
- preset.in-chat
- world_book.in-chat
"""

import os
import sys
import json
import time

# 将仓库根目录加入 sys.path 以便 import core 门面
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import core  # noqa: E402


def _ensure_gateway():
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    sm.load_project_modules()
    try:
        gateway.start_server(background=True)
    except Exception as e:
        txt = str(e)
        if ("10048" in txt) or ("address" in txt.lower()) or ("bind" in txt.lower()):
            pass
        else:
            raise
    time.sleep(0.25)
    return gateway


def main():
    _ensure_gateway()

    # 构造历史（包含 thinking 角色）
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，我是助手"},
        {"role": "thinking", "content": "（助手思考，不显示）"},
    ]

    # in-chat 预设（纯文本）
    presets_in_chat = [
        {
            "position": "in-chat",
            "enabled": True,
            "role": "system",
            "content": "这是 in-chat 预设文本",
            "identifier": "inchat_text_1",
            "order": 10,
            "depth": 0,
        }
    ]

    # in-chat 世界书（position 非 before_char/after_char）
    world_books = [
        {
            "id": "wb_inchat_1",
            "enabled": True,
            "position": "assistant",  # 将被映射为 assistant role
            "mode": "always",
            "content": "这是 in-chat 世界书段落",
            "order": 20,
            "depth": 0,
        }
    ]

    payload = {
        "history": history,
        "presets_in_chat": presets_in_chat,
        "world_books": world_books,
    }

    res = core.call_api("smarttraven/in_chat_constructor/construct", payload, method="POST", namespace="modules")
    assert isinstance(res, dict), "返回应为字典"
    msgs = res.get("messages", [])
    assert isinstance(msgs, list) and len(msgs) >= 4, "应包含历史 3 条 + 预设/世界书注入"

    types = [m.get("source", {}).get("type") for m in msgs if isinstance(m, dict)]
    types_set = set(t for t in types if isinstance(t, str))

    # 断言类型存在
    assert "history.user" in types_set, "缺少 history.user"
    assert "history.assistant" in types_set, "缺少 history.assistant"
    assert "history.thinking" in types_set, "缺少 history.thinking"
    assert "preset.in-chat" in types_set, "缺少 preset.in-chat"
    assert "world_book.in-chat" in types_set, "缺少 world_book.in-chat"

    print("✓ in_chat_constructor source.type 规范化测试通过")
    # 打印一份摘要
    sample = [
        {"role": m.get("role"), "type": m.get("source", {}).get("type"), "content": m.get("content")}
        for m in msgs
    ]
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()