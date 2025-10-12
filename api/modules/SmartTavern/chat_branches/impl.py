# -*- coding: utf-8 -*-
"""
SmartTavern.chat_branches 实现层（无状态版）

职责（只处理“单个对话文件”的派生视图计算，不管理会话/对话状态）：
- openai_messages_from_doc(doc): 由最小分支树文件导出 OpenAI Chat messages
- branch_table_from_doc(doc): 由最小分支树文件计算分支情况表（包含每层 j/n 与 latest）

最小分支树文件格式（仅四个字段）：
{
  "root": "node_id",
  "nodes": {
    "node_id": { "pid": "parent_id|null", "role": "system|user|assistant", "content": "..." },
    ...
  },
  "children": { "parent_id": ["child_id1","child_id2",...] },   // 可选；若缺省将由 nodes[*].pid 推导
  "active_path": ["root", "...", "leafId"]                      // 可选；若缺省或不连通将被规范化
}
"""
from __future__ import annotations
from typing import Any, Dict, List


def _buckets_from_doc(doc: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    由 children 与 nodes[*].pid 构建 parent->children 桶。
    - 优先采用 doc.children 的显式顺序
    - 补全 nodes[*].pid 所隐含但未在 children 给出的边
    """
    nodes_doc = (doc.get("nodes") or {})
    children_doc = (doc.get("children") or {})
    buckets: Dict[str, List[str]] = {}

    # 显式 children
    for pid, arr in (children_doc or {}).items():
        if isinstance(arr, list):
            buckets[pid] = [cid for cid in arr if cid in nodes_doc]

    # 根据 pid 隐式补全
    for nid, nd in (nodes_doc or {}).items():
        pid = (nd or {}).get("pid")
        if pid is not None:
            buckets.setdefault(pid, [])
            if nid not in buckets[pid]:
                buckets[pid].append(nid)
    return buckets


def _normalize_path_from_doc(doc: Dict[str, Any]) -> List[str]:
    """
    规范化 active_path，确保从 root 连通。
    规则：
      - 若 active_path 缺省，则为 [root]
      - 若 active_path[0] != root，则在前置 root
      - 自左向右逐步验证连通，遇到不连通则截断
    """
    root = doc.get("root")
    nodes_doc = (doc.get("nodes") or {})
    if root is None or root not in nodes_doc:
        raise ValueError("invalid doc: missing/invalid root")

    buckets = _buckets_from_doc(doc)
    active_path = list(doc.get("active_path") or [])
    if not isinstance(active_path, list) or not active_path:
        active_path = [root]
    if active_path[0] != root:
        active_path = [root] + active_path

    norm: List[str] = [root]
    for i in range(1, len(active_path)):
        prev = norm[-1]
        nxt = active_path[i]
        if nxt in set(buckets.get(prev, [])):
            norm.append(nxt)
        else:
            break
    return norm


def openai_messages_from_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    从最小分支树文件导出 OpenAI Chat messages。
    返回：
      {
        "messages": [{ "role": "system|user|assistant", "content": "..." }, ...],
        "path": ["node_id", ...]
      }
    """
    nodes_doc = (doc.get("nodes") or {})
    path = _normalize_path_from_doc(doc)
    messages: List[Dict[str, str]] = []
    for nid in path:
        nd = (nodes_doc.get(nid) or {})
        role = nd.get("role") or "system"
        if role in ("system", "user", "assistant"):
            messages.append({"role": role, "content": (nd.get("content") or "")})
    return {"messages": messages, "path": path}


def branch_table_from_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    由最小分支树文件计算分支情况表。
    返回：
      {
        "latest": { "depth": number, "j": number|null, "n": number|null, "node_id": "..." },
        "levels": [
          { "depth": number, "node_id": "...", "j": number|null, "n": number|null },
          ...
        ]
      }
    说明：
      - j/n 来自父节点 children 顺序位置（1-based）；若不可判定则为 null
    """
    path = _normalize_path_from_doc(doc)
    buckets = _buckets_from_doc(doc)
    L = len(path)
    latest = {"depth": L, "j": None, "n": None, "node_id": path[-1] if L >= 1 else None}
    levels: List[Dict[str, Any]] = []
    for depth in range(2, L + 1):
        parent_id = path[depth - 2]
        child_id = path[depth - 1]
        children = buckets.get(parent_id, [])
        n = len(children)
        j = (children.index(child_id) + 1) if child_id in children else None
        row = {"depth": depth, "node_id": child_id, "j": j, "n": n}
        levels.append(row)
        if depth == L:
            latest.update({"j": j, "n": n})
    return {"latest": latest, "levels": levels}