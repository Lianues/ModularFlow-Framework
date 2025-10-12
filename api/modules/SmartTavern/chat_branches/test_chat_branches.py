#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
无状态版 chat_branches 快速验证脚本

仅测试两个无状态接口（基于“单个最小分支树文件”）：
- smarttavern/chat_branches/openai_messages
- smarttavern/chat_branches/branch_table

运行（仓库根目录）:
  python api/modules/SmartTavern/chat_branches/test_chat_branches.py
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
    sm.load_project_modules()  # 触发 @register_api 注册
    gw = core.get_api_gateway()
    gw.start_server(background=True)
    time.sleep(0.4)
    return gw


def pp(title: str, obj):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    except Exception:
        print(obj)


def main():
    _ensure_gateway()

    # 读取最小分支树文件（示例）
    rel = "backend_projects/SmartTavern/data/conversations/branch_demo.json"
    path = ROOT / rel
    if not path.exists():
        raise FileNotFoundError(f"对话示例文件不存在: {rel}")
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    # 无状态消息导出
    msgs = core.call_api(
        "smarttavern/chat_branches/openai_messages",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(msgs, dict) and isinstance(msgs.get("messages"), list)
    print(f"✓ openai_messages OK, count={len(msgs['messages'])}")
    pp("openai_messages (first 3)", {"messages": msgs["messages"][:3]})

    # 无状态分支情况表
    table = core.call_api(
        "smarttavern/chat_branches/branch_table",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(table, dict) and "latest" in table
    print(f"✓ branch_table OK, latest={table['latest']}")
    pp("branch_table (trimmed)", {"latest": table["latest"], "levels": table.get("levels", [])[:5]})

    print("\n[done] 无状态 chat_branches 接口验证通过。")


if __name__ == "__main__":
    main()