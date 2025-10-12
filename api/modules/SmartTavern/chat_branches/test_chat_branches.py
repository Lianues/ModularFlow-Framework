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

    # 测试1：传入 doc 对象
    msgs = core.call_api(
        "smarttavern/chat_branches/openai_messages",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(msgs, dict) and isinstance(msgs.get("messages"), list)
    print(f"[OK] openai_messages(doc) OK, count={len(msgs['messages'])}")
    pp("openai_messages (first 3)", {"messages": msgs["messages"][:3]})

    # 测试2：传入 file 路径
    msgs_file = core.call_api(
        "smarttavern/chat_branches/openai_messages",
        {"file": rel},
        method="POST",
        namespace="modules",
    )
    assert isinstance(msgs_file, dict) and isinstance(msgs_file.get("messages"), list)
    assert len(msgs_file["messages"]) == len(msgs["messages"])
    print(f"[OK] openai_messages(file) OK, count={len(msgs_file['messages'])}")

    # 测试3：分支情况表（传入 doc）
    table = core.call_api(
        "smarttavern/chat_branches/branch_table",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(table, dict) and "latest" in table
    print(f"[OK] branch_table(doc) OK, latest={table['latest']}")
    pp("branch_table (trimmed)", {"latest": table["latest"], "levels": table.get("levels", [])[:5]})

    # 测试4：分支情况表（传入 file）
    table_file = core.call_api(
        "smarttavern/chat_branches/branch_table",
        {"file": rel},
        method="POST",
        namespace="modules",
    )
    assert isinstance(table_file, dict) and "latest" in table_file
    assert table_file["latest"] == table["latest"]
    print(f"[OK] branch_table(file) OK, latest={table_file['latest']}")

    # 测试5：获取最后一条消息（传入 doc）
    latest_msg = core.call_api(
        "smarttavern/chat_branches/get_latest_message",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(latest_msg, dict)
    assert "node_id" in latest_msg and "role" in latest_msg and "content" in latest_msg
    print(f"[OK] get_latest_message(doc) OK, node_id={latest_msg['node_id']}, role={latest_msg['role']}")
    pp("latest_message", latest_msg)

    # 测试6：获取最后一条消息（传入 file）
    latest_msg_file = core.call_api(
        "smarttavern/chat_branches/get_latest_message",
        {"file": rel},
        method="POST",
        namespace="modules",
    )
    assert isinstance(latest_msg_file, dict)
    assert latest_msg_file == latest_msg
    print(f"[OK] get_latest_message(file) OK, node_id={latest_msg_file['node_id']}")

    # 测试7：修改消息内容
    updated_doc = core.call_api(
        "smarttavern/chat_branches/update_message",
        {"doc": doc, "node_id": "n_ass1", "content": "修改后的内容"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(updated_doc, dict)
    assert updated_doc["nodes"]["n_ass1"]["content"] == "修改后的内容"
    assert "updated_at" in updated_doc
    print(f"[OK] update_message OK, updated_at={updated_doc.get('updated_at')}")

    # 测试8：修剪消息树（删除 n_user2 及其子孙）
    truncated_doc = core.call_api(
        "smarttavern/chat_branches/truncate_after",
        {"doc": doc, "node_id": "n_ass1"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(truncated_doc, dict)
    assert "n_user2" not in truncated_doc["nodes"]  # n_user2 应被删除
    assert "n_ass3" not in truncated_doc["nodes"]   # n_ass3 应被删除
    assert "n_ass1" in truncated_doc["nodes"]       # n_ass1 应保留
    assert truncated_doc["active_path"][-1] == "n_ass1"  # active_path 应截断到 n_ass1
    print(f"[OK] truncate_after OK, active_path={truncated_doc['active_path']}")

    # 测试9：追加新消息
    appended_doc = core.call_api(
        "smarttavern/chat_branches/append_message",
        {
            "doc": doc,
            "node_id": "n_new_user",
            "pid": "n_ass3",
            "role": "user",
            "content": "这是新追加的用户消息"
        },
        method="POST",
        namespace="modules",
    )
    assert isinstance(appended_doc, dict)
    assert "n_new_user" in appended_doc["nodes"]
    assert appended_doc["nodes"]["n_new_user"]["content"] == "这是新追加的用户消息"
    assert "n_new_user" in appended_doc["children"]["n_ass3"]
    assert appended_doc["active_path"][-1] == "n_new_user"  # 新消息应追加到 active_path
    assert "updated_at" in appended_doc
    print(f"[OK] append_message OK, new_node in path={appended_doc['active_path'][-1]}")

    print("\n[done] 无状态 chat_branches 接口验证通过（doc + file + get_latest + update/truncate/append）。")


if __name__ == "__main__":
    main()