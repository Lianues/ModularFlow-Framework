#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：smarttraven/prompt_postprocess/apply 工作流（单视图）
- 验证单视图流水线：before_macro → macro → after_macro
- 覆盖 user_view 与 assistant_view 两个视图
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

# 仅首次启动 API 网关，避免重复注册端点
_STARTED = False

def _ensure_gateway():
    global _STARTED
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    if not _STARTED:
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
        _STARTED = True
    return gateway

def _sample_messages():
    return [
        {"role": "system", "content": "<p>Preset XML</p>", "source": {"type": "preset.relative", "position": "relative"}},
        {"role": "user", "content": "你好 <tag>content</tag> world", "source": {"type": "history.user", "id": "h1", "index": 1}},
        {"role": "assistant", "content": "<StatusPlaceHolderImpl/> I'm assistant", "source": {"type": "history.assistant", "id": "h2", "index": 2}},
        {"role": "system", "content": "<wb>replace_me</wb>", "source": {"type": "world_book.in-chat", "id": "wb_1"}},
    ]

def _sample_rules():
    return [
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

def test_postprocess_user_view_pipeline():
    """
    user_view：before_macro → macro → after_macro
    """
    _ensure_gateway()

    messages = _sample_messages()
    rules = _sample_rules()

    payload = {
        "messages": messages,
        "rules": rules,
        "view": "user_view",
    }
    res = core.call_api("smarttraven/prompt_postprocess/apply", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict), "返回应为字典"
    assert "message" in res and "variables" in res
    out = res["message"]
    assert isinstance(out, list)
    assert len(out) == len(messages)

    # before_macro：两视图都应移除 XML
    assert out[0]["content"] == "移除xml"
    assert out[1]["content"] == "你好 移除xml world"
    # world_book.* 前缀
    assert out[-1]["content"] == "移除xml"

    # after_macro：仅 user_view 替换状态栏
    assert out[2]["content"].startswith("这里是状态栏"), "user_view 应替换占位符"

def test_postprocess_assistant_view_pipeline():
    """
    assistant_view：before_macro → macro → after_macro
    - after_macro 阶段的状态栏规则仅针对 user_view，因此 assistant_view 不应替换
    """
    _ensure_gateway()

    messages = _sample_messages()
    rules = _sample_rules()

    payload = {
        "messages": messages,
        "rules": rules,
        "view": "assistant_view",
    }
    res = core.call_api("smarttraven/prompt_postprocess/apply", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict)
    assert "message" in res and "variables" in res
    out = res["message"]
    assert isinstance(out, list)
    assert len(out) == len(messages)

    # before_macro：移除 XML
    assert out[0]["content"] == "移除xml"
    assert out[1]["content"] == "你好 移除xml world"
    assert out[-1]["content"] == "移除xml"

    # after_macro：assistant_view 不应替换状态栏
    assert "<StatusPlaceHolderImpl/>" in out[2]["content"], "assistant_view 不应替换占位符"

def test_postprocess_macro_integration_simple():
    """
    宏集成最小验证：无正则，仅验证 variables.final 与内容替换
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
        "view": "user_view",
    }
    res = core.call_api("smarttraven/prompt_postprocess/apply", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict)
    assert "message" in res and "variables" in res
    out = res["message"]
    vars_obj = res["variables"]
    assert out[0]["content"] == "value=OK"
    assert isinstance(vars_obj, dict) and "final" in vars_obj
    assert vars_obj["final"].get("x") == "OK"

def main():
    test_postprocess_user_view_pipeline()
    test_postprocess_assistant_view_pipeline()
    test_postprocess_macro_integration_simple()
    print("OK: prompt_postprocess (single-view) workflow tests passed")


if __name__ == "__main__":
    main()