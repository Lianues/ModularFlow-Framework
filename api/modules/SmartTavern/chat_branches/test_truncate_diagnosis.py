#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 truncate_after 当前行为
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core  # noqa: E402

def main():
    # 读取测试数据
    rel = "backend_projects/SmartTavern/data/conversations/branch_demo.json"
    path = ROOT / rel
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    
    print("=== 原始数据 ===")
    print(f"nodes: {list(doc['nodes'].keys())}")
    print(f"active_path: {doc['active_path']}")
    print(f"children of n_ass1: {doc.get('children', {}).get('n_ass1', [])}")
    
    # 测试：truncate_after n_ass1
    print("\n=== 调用 truncate_after(node_id='n_ass1') ===")
    
    # 使用实现层直接测试
    from api.modules.SmartTavern.chat_branches.impl import truncate_after_node
    result = truncate_after_node(node_id="n_ass1", doc=doc)
    
    print("\n=== 结果分析 ===")
    print(f"n_ass1 是否存在: {'n_ass1' in result['nodes']}")
    print(f"n_user2 是否存在: {'n_user2' in result['nodes']}")
    print(f"n_ass3 是否存在: {'n_ass3' in result['nodes']}")
    print(f"结果 nodes: {list(result['nodes'].keys())}")
    print(f"结果 active_path: {result['active_path']}")
    print(f"结果 children: {result.get('children', {})}")
    
    print("\n=== 用户预期 ===")
    print("应该删除: n_ass1 及其所有子孙 (n_user2, n_ass3, n_user_test_*)")
    print("应该保留: n_root, n_user1")
    print("active_path 应该截断到: n_user1 (n_ass1 的父节点)")
    
    print("\n=== 当前实现行为 ===")
    if 'n_ass1' in result['nodes']:
        print("❌ 保留了 n_ass1 节点本身")
    else:
        print("✓ 删除了 n_ass1 节点本身")
    
    if 'n_user2' not in result['nodes']:
        print("✓ 删除了 n_user2 子节点")
    else:
        print("❌ 未删除 n_user2 子节点")

if __name__ == "__main__":
    main()