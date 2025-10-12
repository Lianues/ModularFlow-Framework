#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：对话配置（conversations）清单 + 导入 chat_branches + 快速校验

运行方式（仓库根目录）:
  python api/modules/SmartTavern/data_catalog/test_conversations_cli.py
"""
import sys
import time
import json
from pathlib import Path

# 仓库根目录
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core  # noqa: E402


def _ensure_gateway():
    sm = core.get_service_manager()
    sm.load_project_modules()  # 自动发现并导入 api/modules 下的模块（含 data_catalog 与 chat_branches）
    gw = core.get_api_gateway()
    gw.start_server(background=True)
    time.sleep(0.4)  # 等待网关与注册完成
    return gw


def _print_section(title, obj):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[print_error] {e}")
        print(str(obj))


def _find_demo_file(items):
    """
    在 list_conversations items 中寻找 branch_demo.json，否则回退第一项
    """
    for it in items:
        f = str(it.get("file"))
        if f.endswith("/branch_demo.json") or f.endswith("\\branch_demo.json"):
            return f, it
    if items:
        it = items[0]
        return str(it.get("file")), it
    return None, None


def main():
    _ensure_gateway()

    # 1) 列出 conversations
    res = core.call_api(
        "smarttavern/data_catalog/list_conversations",
        {},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict), "list_conversations 应返回 dict"
    print(f"✓ list_conversations OK (total={res.get('total')})")
    _print_section("list_conversations response", res)

    items = res.get("items", [])
    file_path, info = _find_demo_file(items)
    assert file_path, "未找到任何 conversations 文件"
    print(f"使用文件: {file_path}")
    if info:
        print(f"name={info.get('name')!r}, description={info.get('description')!r}")

    # 2) 读取文件（最小分支树 doc）并直接调用无状态 API
    abs_path = ROOT / file_path
    with abs_path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    # 3) OpenAI messages（确认路径可用）
    msgs = core.call_api(
        "smarttavern/chat_branches/openai_messages",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(msgs, dict) and isinstance(msgs.get("messages"), list), "openai_messages 返回异常"
    print(f"✓ openai_messages OK, count={len(msgs['messages'])}")
    _print_section("openai_messages sample (first 3)", {"messages": msgs["messages"][:3]})

    # 4) 分支情况表（j/n）
    table = core.call_api(
        "smarttavern/chat_branches/branch_table",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(table, dict) and "latest" in table, "branch_table 返回异常"
    print(f"✓ branch_table OK, latest={table['latest']}")
    _print_section("branch_table (trimmed)", {"latest": table["latest"], "levels": table.get("levels", [])[:5]})

    print("\nAll conversation tests passed.")


if __name__ == "__main__":
    main()