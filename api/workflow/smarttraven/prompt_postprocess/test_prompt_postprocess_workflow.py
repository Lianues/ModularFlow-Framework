#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：smarttraven/prompt_postprocess/apply 工作流
- 覆盖两种宏开关：macro_enabled = False / True
- 验证单视图正则（before_macro / after_macro）与宏处理串联是否按预期执行
"""
import os
import sys
import time
import json

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
        # 若端口已被占用（已有实例在跑），忽略重复启动错误并复用现有实例
        gateway.start_server(background=True)
    except Exception as e:
        txt = str(e)
        if ("10048" in txt) or ("address" in txt.lower()) or ("bind" in txt.lower()):
            pass
        else:
            raise
    time.sleep(0.3)  # 稍等网关就绪
    return gateway


def test_postprocess_macro_disabled():
    """
    流水线：before_macro → after_macro（跳过宏）
    - before_macro：移除 XML 标签（两视图）
    - after_macro：状态栏占位符替换（仅 user_view）
    """
    _ensure_gateway()

    messages = [
        # 0: relative preset（仅用于演示 targets "preset" 前缀），角色用 system
        {"role": "system", "content": "<p>Preset XML</p>", "source": {"type": "preset.relative", "position": "relative"}},
        # 1: user 含 XML 标签
        {"role": "user", "content": "你好 <tag>content</tag> world", "source": {"type": "history.user", "id": "h1", "index": 1}},
        # 2: assistant 含状态栏占位符
        {"role": "assistant", "content": "<StatusPlaceHolderImpl/> I'm assistant", "source": {"type": "history.assistant", "id": "h2", "index": 2}},
        # 3: world_book.in-chat（验证 targets 'world_book' 前缀）
        {"role": "system", "content": "<wb>replace_me</wb>", "source": {"type": "world_book.in-chat", "id": "wb_1"}},
    ]

    rules = [
        {
            "id": "remove_xml_tags_rule",
            "name": "Remove XML Tags",
            "enabled": True,
            "find_regex": "<([a-zA-Z0-9]+)>(.|\\n)*?</\\1>",
            "replace_regex": "移除xml",
            "targets": ["preset", "world_book", "history"],  # 基于 source.type 前缀
            "placement": "before_macro",
            "views": ["user_view", "assistant_view"],
        },
        {
            "id": "status_bar_demo",
            "name": "状态栏",
            "enabled": True,
            "find_regex": "<StatusPlaceHolderImpl/>",
            "replace_regex": "这里是状态栏",
            "targets": ["history"],
            "placement": "after_macro",
            "views": ["user_view"],  # 仅 user_view
            "min_depth": 0,
            "max_depth": 5,
        },
    ]

    payload = {
        "messages": messages,
        "rules": rules,
        "macro_enabled": False,
    }
    res = core.call_api("smarttraven/prompt_postprocess/apply", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict), "返回应为字典"
    assert "user_view" in res and "assistant_view" in res
    uv = res["user_view"]
    av = res["assistant_view"]
    assert isinstance(uv, list) and isinstance(av, list)
    assert len(uv) == len(messages) and len(av) == len(messages)

    # before_macro：两视图都应移除 XML
    assert uv[0]["content"] == "移除xml"
    assert av[0]["content"] == "移除xml"
    assert uv[1]["content"] == "你好 移除xml world"
    assert av[1]["content"] == "你好 移除xml world"
    # world_book.* 前缀
    assert uv[-1]["content"] == "移除xml"
    assert av[-1]["content"] == "移除xml"

    # after_macro：仅 user_view 替换状态栏
    assert uv[2]["content"].startswith("这里是状态栏"), "user_view 应替换占位符"
    assert "<StatusPlaceHolderImpl/>" in av[2]["content"], "assistant_view 不应替换占位符"

    print("✓ postprocess macro_disabled 测试通过")


def test_postprocess_macro_enabled_simple():
    """
    流水线：before_macro → macro → after_macro
    - 验证宏生效：使用 setvar/getvar 的最小例子（不会影响正则断言）
    - 正则规则为空（重点验证宏）
    """
    _ensure_gateway()

    messages = [
        # 宏设置 x=OK，然后读取
        {"role": "system", "content": "<<setvar:x::OK>>value={{getvar:x}}", "source": {"type": "preset.relative", "position": "relative"}},
        {"role": "user", "content": "Hello", "source": {"type": "history.user", "id": "h1", "index": 1}},
    ]

    rules = []  # 不做正则替换，聚焦宏处理

    payload = {
        "messages": messages,
        "rules": rules,
        "macro_enabled": True,
    }
    res = core.call_api("smarttraven/prompt_postprocess/apply", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict)
    assert "user_view" in res and "assistant_view" in res
    uv = res["user_view"]
    av = res["assistant_view"]
    assert isinstance(uv, list) and isinstance(av, list)
    # 宏应在两视图均生效（各自独立变量上下文）
    assert uv[0]["content"] == "value=OK"
    assert av[0]["content"] == "value=OK"

    print("✓ postprocess macro_enabled 测试通过")


def main():
    test_postprocess_macro_disabled()
    test_postprocess_macro_enabled_simple()
    print("OK: prompt_postprocess workflow tests passed")


if __name__ == "__main__":
    main()