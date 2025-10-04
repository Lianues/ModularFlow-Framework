#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：SmartTraven.regex_replace 模块
- 覆盖两种输入：
  1) messages（带 role/content/source）
  2) text（纯文本）
- 覆盖两种 placement：
  - before_macro：匹配 remove_xml_tags_rule
  - after_macro：匹配“状态栏”占位符替换规则
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
    time.sleep(0.3)  # 稍等网关就绪
    return gateway


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_messages_before_after(rules):
    # 构造一个 messages 块：
    # index=0: relative preset（仅用于深度锚点过滤，不纳入锚点）
    # index=1: user，含 XML 标签；期望在 before_macro 时被替换（两个视图都生效）
    # index=2: assistant，含 <StatusPlaceHolderImpl/>；期望在 after_macro 且 user_view 被替换
    # index=3: system（尾部），用于验证 depth=0 范围
    messages = [
        {
            "role": "system",
            "content": "<b>System relative</b>",
            "source": {"type": "preset.relative", "position": "relative", "id": "preset_rel"},
        },
        {
            "role": "user",
            "content": "你好 <tag>content</tag> world",
            "source": {"type": "history.user", "id": "history_1", "index": 1},
        },
        {
            "role": "assistant",
            "content": "<StatusPlaceHolderImpl/> I'm assistant",
            "source": {"type": "history.assistant", "id": "history_2", "index": 2},
        },
        {
            "role": "system",
            "content": "tail system",
            "source": {"type": "history.user", "id": "history_3", "index": 3},
        },
        {
            "role": "system",
            "content": "<wb>replace_me</wb>",
            "source": {"type": "world_book.in-chat", "id": "wb_1"}
        },
    ]

    # 1) before_macro：应命中 remove_xml_tags_rule（两个视图）
    payload_before = {
        "rules": rules,
        "placement": "before_macro",
        "messages": messages,
    }
    # 单视图：user_view
    payload_before = {
        "rules": rules,
        "placement": "before_macro",
        "view": "user_view",
        "messages": messages,
    }
    res_before = core.call_api("smarttraven/regex_replace/apply_messages", payload_before, method="POST", namespace="modules")
    assert isinstance(res_before, dict), "before_macro 返回应为字典"
    assert "message" in res_before and isinstance(res_before["message"], list)
    assert len(res_before["message"]) == len(messages)

    # 校验 before_macro 的替换效果：XML -> '移除xml'（仅单视图）
    uv_msgs = res_before["message"]

    # index 1 的 user 消息应被替换
    assert uv_msgs[1]["content"] == "你好 移除xml world"

    # index 0 的 relative preset 如果 targets 包含 preset 也会被替换
    assert uv_msgs[0]["content"] == "移除xml"

    # world_book.* 前缀（这里是 world_book.in-chat）
    last = len(messages) - 1
    assert uv_msgs[last]["content"] == "移除xml", "world_book.* 应被 before_macro 规则替换（user_view）"

    # 2) after_macro：应命中“状态栏”规则（仅 user_view）
    payload_after = {
        "rules": rules,
        "placement": "after_macro",
        "view": "user_view",
        "messages": messages,
    }
    res_after = core.call_api("smarttraven/regex_replace/apply_messages", payload_after, method="POST", namespace="modules")
    assert isinstance(res_after, dict), "after_macro 返回应为字典"
    assert "message" in res_after and isinstance(res_after["message"], list)
    uv_msgs2 = res_after["message"]

    # index 2 的 assistant 消息应仅在 user_view 被替换（views 仅 user_view）
    assert uv_msgs2[2]["content"].startswith("这里是状态栏"), "user_view 应替换占位符"

    print("✓ messages before/after 替换测试通过")


def test_text_before(rules):
    # 纯文本：before_macro 作用于整个文本
    payload = {
        "rules": rules,
        "placement": "before_macro",
        "view": "assistant_view",
        "text": "<x>abc</x> 123",
    }
    res = core.call_api("smarttraven/regex_replace/apply_text", payload, method="POST", namespace="modules")
    assert isinstance(res, dict) and "text" in res
    # 根据 remove_xml_tags_rule，应把 <x>abc</x> 替换为 "移除xml"
    assert res["text"].startswith("移除xml"), "assistant_view 文本应替换 XML"

    print("✓ text before 替换测试通过")


def main():
    _ensure_gateway()

    # 使用内联规则，按新 targets 规范（仅基于 source.type 或前缀）
    rules = [
        {
            "id": "remove_xml_tags_rule",
            "name": "Remove XML Tags",
            "enabled": True,
            "find_regex": "<([a-zA-Z0-9]+)>(.|\\n)*?</\\1>",
            "replace_regex": "移除xml",
            "targets": ["preset", "world_book", "history"],  # 不再使用角色
            "placement": "before_macro",
            "views": ["user_view", "assistant_view"],
            "description": "移除 XML 标签（适用于 preset.*, world_book.*, history.*）"
        },
        {
            "id": "status_bar_demo",
            "name": "状态栏",
            "enabled": True,
            "find_regex": "<StatusPlaceHolderImpl/>",
            "replace_regex": "这里是状态栏",
            "targets": ["history"],  # 仅历史消息命中（assistant/user/thinking 均可）
            "placement": "after_macro",
            "views": ["user_view"],
            "min_depth": 0,
            "max_depth": 5,
            "description": "仅在 user_view 应用"
        }
    ]

    test_messages_before_after(rules)
    test_text_before(rules)

    # 打印示例输出（可选）
    # 仅演示一次 before_macro+messages 的结果
    demo_payload = {
        "rules": rules,
        "placement": "before_macro",
        "view": "user_view",
        "messages": [
            {
                "role": "user",
                "content": "你好 <tag>content</tag> world",
                "source": {"type": "history.user", "id": "history_demo", "index": 0},
            }
        ],
    }
    demo_res = core.call_api("smarttraven/regex_replace/apply_messages", demo_payload, method="POST", namespace="modules")
    print(json.dumps(demo_res, ensure_ascii=False, indent=2, sort_keys=False))

    print("OK: regex_replace tests passed")


if __name__ == "__main__":
    main()