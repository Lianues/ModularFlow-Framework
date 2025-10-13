#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 get_conversation_detail 和 append_message API
"""
import sys
import time
import json
from pathlib import Path

# 仓库根目录
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core

def _ensure_gateway():
    sm = core.get_service_manager()
    sm.load_project_modules()
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
    
    # 测试文件路径
    test_file = "backend_projects/SmartTavern/data/conversations/branch_demo.json"
    
    print("\n" + "="*60)
    print("测试 1: 获取对话详情")
    print("="*60)
    
    # 调用 get_conversation_detail
    result = core.call_api(
        "smarttavern/data_catalog/get_conversation_detail",
        {"file": test_file},
        method="POST",
        namespace="modules",
    )
    
    assert isinstance(result, dict), "返回结果必须是字典"
    assert "content" in result, "返回结果必须包含 content"
    assert "file" in result, "返回结果必须包含 file"
    
    doc = result["content"]
    assert isinstance(doc, dict), "content 必须是字典"
    assert "nodes" in doc, "content 必须包含 nodes"
    assert "active_path" in doc, "content 必须包含 active_path"
    
    print(f"[OK] 获取对话详情成功")
    print(f"  - 文件: {result['file']}")
    print(f"  - 名称: {result.get('name', 'N/A')}")
    print(f"  - 节点数: {len(doc.get('nodes', {}))}")
    print(f"  - active_path: {doc.get('active_path', [])}")
    
    pp("对话文档结构", {
        "roots": doc.get("roots"),
        "nodes_count": len(doc.get("nodes", {})),
        "active_path": doc.get("active_path"),
        "children": doc.get("children", {})
    })
    
    print("\n" + "="*60)
    print("测试 2: 追加新消息")
    print("="*60)
    
    # 获取当前 active_path 的最后一个节点作为父节点
    active_path = doc.get("active_path", [])
    if not active_path:
        print("[ERROR] active_path 为空")
        return
    
    parent_id = active_path[-1]
    new_node_id = f"n_user_test_{int(time.time())}"
    
    print(f"  - 父节点ID: {parent_id}")
    print(f"  - 新节点ID: {new_node_id}")
    
    # 调用 append_message
    append_result = core.call_api(
        "smarttavern/chat_branches/append_message",
        {
            "file": test_file,
            "node_id": new_node_id,
            "pid": parent_id,
            "role": "user",
            "content": "这是一条测试消息，由自动化测试脚本添加"
        },
        method="POST",
        namespace="modules",
    )
    
    assert isinstance(append_result, dict), "返回结果必须是字典"
    assert "nodes" in append_result, "返回结果必须包含 nodes"
    assert new_node_id in append_result["nodes"], "新节点必须在 nodes 中"
    assert "active_path" in append_result, "返回结果必须包含 active_path"
    assert append_result["active_path"][-1] == new_node_id, "新节点必须在 active_path 末尾"
    
    print(f"[OK] 追加消息成功")
    print(f"  - 新节点已添加: {new_node_id}")
    print(f"  - 新的 active_path: {append_result['active_path']}")
    print(f"  - 更新时间: {append_result.get('updated_at', 'N/A')}")
    
    # 验证新消息内容
    new_node = append_result["nodes"][new_node_id]
    print(f"  - 新消息内容:")
    print(f"    - pid: {new_node.get('pid')}")
    print(f"    - role: {new_node.get('role')}")
    print(f"    - content: {new_node.get('content')[:50]}...")
    
    print("\n" + "="*60)
    print("测试 3: 验证文件已更新")
    print("="*60)
    
    # 重新读取文件验证
    verify_result = core.call_api(
        "smarttavern/data_catalog/get_conversation_detail",
        {"file": test_file},
        method="POST",
        namespace="modules",
    )
    
    verify_doc = verify_result["content"]
    assert new_node_id in verify_doc["nodes"], "新节点必须在文件中"
    assert verify_doc["active_path"][-1] == new_node_id, "active_path 必须包含新节点"
    
    print(f"[OK] 文件验证成功，新消息已持久化")
    
    print("\n" + "="*60)
    print("✅ 所有测试通过！")
    print("="*60)

if __name__ == "__main__":
    main()