#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：framing_prompt 来源类型规范化（source.type）
覆盖枚举：
- history.user / history.assistant / history.thinking
- preset.relative
- world_book.before_char / world_book.after_char
- char.description / persona.description
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
    gateway.start_server(background=True)
    time.sleep(0.25)
    return gateway


def main():
    _ensure_gateway()

    # 构造“已处理或原始”历史（thinking 为显式角色）
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好，我是助手"},
        {"role": "thinking", "content": "（助手思考，不显示）"},
    ]

    # relative 预设与占位符（使用新的占位符名：charBefore/charAfter）
    presets_relative = [
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "charBefore",   # before_char 世界书
            "content": "(ignored)",
            "order": 1
        },
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "chatHistory",  # 插入历史
            "content": "(ignored)",
            "order": 2
        },
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "someGuidelines",  # 纯 relative 文本
            "content": "这是 relative 纯文本",
            "order": 3
        },
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "charAfter",    # after_char 世界书
            "content": "(ignored)",
            "order": 4
        },
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "charDescription",  # 角色描述
            "content": "(ignored)",
            "order": 5
        },
        {
            "position": "relative",
            "enabled": True,
            "role": "system",
            "identifier": "personaDescription",  # 画像描述
            "content": "(ignored)",
            "order": 6
        },
    ]

    # 世界书：before_char 与 after_char
    world_books = [
        {
            "id": "wb_before_1",
            "enabled": True,
            "position": "before_char",
            "mode": "always",
            "content": "世界书：在角色描述前",
            "order": 10
        },
        {
            "id": "wb_after_1",
            "enabled": True,
            "position": "after_char",
            "mode": "always",
            "content": "世界书：在角色描述后",
            "order": 20
        }
    ]

    character = {"name": "心与露", "description": "角色设定：温柔体贴。"}
    persona = {"name": "用户甲", "description": "画像：程序员。"}

    payload = {
        "history": history,
        "world_books": world_books,
        "presets_relative": presets_relative,
        "character": character,
        "persona": persona,
    }

    res = core.call_api("smarttraven/framing_prompt/assemble", payload, method="POST", namespace="modules")
    assert isinstance(res, dict), "返回应为字典"
    msgs = res.get("messages", [])
    assert isinstance(msgs, list) and len(msgs) >= 1, "messages 不应为空"

    types = [m.get("source", {}).get("type") for m in msgs if isinstance(m, dict)]
    tset = set(t for t in types if isinstance(t, str))

    # 断言类型存在
    assert "history.user" in tset, "缺少 history.user"
    assert "history.assistant" in tset, "缺少 history.assistant"
    assert "history.thinking" in tset, "缺少 history.thinking"
    assert "preset.relative" in tset, "缺少 preset.relative"
    assert "world_book.before_char" in tset, "缺少 world_book.before_char"
    assert "world_book.after_char" in tset, "缺少 world_book.after_char"
    assert "char.description" in tset, "缺少 char.description"
    assert "persona.description" in tset, "缺少 persona.description"

    print("✓ framing_prompt source.type 规范化测试通过")
    # 打印摘要
    sample = [
        {"role": m.get("role"), "type": m.get("source", {}).get("type"), "content": m.get("content")}
        for m in msgs
    ]
    print(json.dumps(sample, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()