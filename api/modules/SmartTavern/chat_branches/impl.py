# -*- coding: utf-8 -*-
"""
SmartTavern.chat_branches 实现层（无状态版）

职责（只处理"单个对话文件"的派生视图计算，不管理会话/对话状态）：
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
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json


# ---------- 文件读取工具 ----------

def _repo_root() -> Path:
    """返回仓库根目录（基于当前文件层级向上回溯）"""
    return Path(__file__).resolve().parents[4]


def _safe_read_json(p: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """安全读取 JSON 文件，返回 (doc, error)"""
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _is_within(child: Path, parent: Path) -> bool:
    """检查 child 是否在 parent 目录范围内"""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _load_doc_from_file_or_obj(
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    二选一加载对话文件（深拷贝以避免副作用）：
    - 若 doc 非空，深拷贝后返回
    - 若 file 非空，从 conversations 目录读取 JSON
    - 若都为空或读取失败，抛出 ValueError
    """
    import copy
    
    if doc is not None:
        if not isinstance(doc, dict):
            raise ValueError("doc must be a dictionary")
        return copy.deepcopy(doc)
    
    if file is not None and isinstance(file, str) and file.strip():
        root = _repo_root()
        conversations_dir = root / "backend_projects" / "SmartTavern" / "data" / "conversations"
        target = (root / Path(file)).resolve()
        
        if not _is_within(target, conversations_dir):
            raise ValueError(f"File must be within conversations directory: {file}")
        
        loaded_doc, err = _safe_read_json(target)
        if err:
            raise ValueError(f"Failed to read file {file}: {err}")
        
        if not isinstance(loaded_doc, dict):
            raise ValueError(f"File content must be a JSON object: {file}")
        
        return loaded_doc
    
    raise ValueError("Either 'doc' or 'file' must be provided")


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


def openai_messages_from_doc(
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    从最小分支树文件导出 OpenAI Chat messages。
    
    参数（二选一）：
    - doc: 最小分支树 JSON 对象
    - file: 对话文件路径（相对仓库根，如 "backend_projects/SmartTavern/data/conversations/branch_demo.json"）
    
    返回：
      {
        "messages": [{ "role": "system|user|assistant", "content": "..." }, ...],
        "path": ["node_id", ...]
      }
    """
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    nodes_doc = (loaded_doc.get("nodes") or {})
    path = _normalize_path_from_doc(loaded_doc)
    messages: List[Dict[str, str]] = []
    for nid in path:
        nd = (nodes_doc.get(nid) or {})
        role = nd.get("role") or "system"
        if role in ("system", "user", "assistant"):
            messages.append({"role": role, "content": (nd.get("content") or "")})
    return {"messages": messages, "path": path}


def branch_table_from_doc(
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    由最小分支树文件计算分支情况表。
    
    参数（二选一）：
    - doc: 最小分支树 JSON 对象
    - file: 对话文件路径（相对仓库根，如 "backend_projects/SmartTavern/data/conversations/branch_demo.json"）
    
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
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    path = _normalize_path_from_doc(loaded_doc)
    buckets = _buckets_from_doc(loaded_doc)
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


def get_latest_message_from_doc(
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    根据 active_path 提取最后一条消息。
    
    参数（二选一）：
    - doc: 最小分支树 JSON 对象
    - file: 对话文件路径（相对仓库根，如 "backend_projects/SmartTavern/data/conversations/branch_demo.json"）
    
    返回：
      {
        "node_id": "...",
        "role": "system|user|assistant",
        "content": "...",
        "depth": number
      }
    
    若 active_path 为空或无效，返回 root 节点。
    """
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    nodes_doc = (loaded_doc.get("nodes") or {})
    path = _normalize_path_from_doc(loaded_doc)
    
    if not path:
        raise ValueError("No valid path found in document")
    
    latest_node_id = path[-1]
    latest_node = (nodes_doc.get(latest_node_id) or {})
    
    return {
        "node_id": latest_node_id,
        "role": latest_node.get("role") or "system",
        "content": latest_node.get("content") or "",
        "depth": len(path)
    }


def _update_timestamp(doc: Dict[str, Any]) -> str:
    """更新并返回 ISO 8601 时间戳（UTC+8）"""
    from datetime import datetime, timezone, timedelta
    tz_cn = timezone(timedelta(hours=8))
    ts = datetime.now(tz_cn).isoformat(timespec='seconds')
    doc["updated_at"] = ts
    return ts


def update_message_content(
    node_id: str,
    content: str,
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    修改某个节点的 content。
    
    参数：
    - node_id: 要修改的节点 ID
    - content: 新的内容
    - doc/file: 二选一输入
    
    返回：
      更新后的完整 doc（含 updated_at）
    """
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    nodes = loaded_doc.get("nodes") or {}
    
    if node_id not in nodes:
        raise ValueError(f"Node not found: {node_id}")
    
    nodes[node_id]["content"] = content
    _update_timestamp(loaded_doc)
    
    return loaded_doc


def truncate_after_node(
    node_id: str,
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    修剪：保留指定节点及之前，删除其所有子树。
    
    参数：
    - node_id: 保留到此节点（不包括其子节点）
    - doc/file: 二选一输入
    
    返回：
      更新后的完整 doc（nodes 删除子树，children 清理，active_path 截断，updated_at 更新）
    
    说明：
    - 级联删除：递归删除 node_id 的所有子孙节点
    - active_path 截断：若 node_id 在 active_path 中，截断到该节点；否则不变
    - children 清理：移除 node_id 的 children 条目
    """
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    nodes = loaded_doc.get("nodes") or {}
    children_map = loaded_doc.get("children") or {}
    active_path = list(loaded_doc.get("active_path") or [])
    
    if node_id not in nodes:
        raise ValueError(f"Node not found: {node_id}")
    
    # 递归收集所有子孙节点（使用栈避免深度递归）
    to_delete = set()
    stack = list(children_map.get(node_id, []))
    
    while stack:
        current = stack.pop()
        if current in to_delete:
            continue
        to_delete.add(current)
        # 将当前节点的子节点加入栈
        for child in (children_map.get(current) or []):
            if child not in to_delete:
                stack.append(child)
    
    # 删除节点
    for nid in to_delete:
        nodes.pop(nid, None)
    
    # 清理 children_map：删除被删节点的条目 + 清理引用
    for nid in to_delete:
        children_map.pop(nid, None)
    
    for pid in list(children_map.keys()):
        children_map[pid] = [cid for cid in children_map[pid] if cid not in to_delete]
        if not children_map[pid]:
            children_map.pop(pid, None)
    
    # 清理 node_id 的 children
    children_map.pop(node_id, None)
    
    # 截断 active_path
    if node_id in active_path:
        idx = active_path.index(node_id)
        active_path = active_path[:idx + 1]
    
    loaded_doc["nodes"] = nodes
    loaded_doc["children"] = children_map
    loaded_doc["active_path"] = active_path
    _update_timestamp(loaded_doc)
    
    return loaded_doc


def append_new_message(
    node_id: str,
    pid: str,
    role: str,
    content: str,
    doc: Optional[Dict[str, Any]] = None,
    file: Optional[str] = None
) -> Dict[str, Any]:
    """
    追加新消息：创建新节点并更新父节点 children 与 active_path。
    
    参数：
    - node_id: 新节点 ID（必须唯一）
    - pid: 父节点 ID（必须存在）
    - role: system|user|assistant
    - content: 消息内容
    - doc/file: 二选一输入
    
    返回：
      更新后的完整 doc（nodes 新增，children 更新父节点，active_path 追加，updated_at 更新）
    """
    loaded_doc = _load_doc_from_file_or_obj(doc, file)
    nodes = loaded_doc.get("nodes") or {}
    children_map = loaded_doc.get("children") or {}
    active_path = list(loaded_doc.get("active_path") or [])
    
    if node_id in nodes:
        raise ValueError(f"Node ID already exists: {node_id}")
    
    if pid not in nodes:
        raise ValueError(f"Parent node not found: {pid}")
    
    if role not in ("system", "user", "assistant"):
        raise ValueError(f"Invalid role: {role}")
    
    # 创建新节点
    nodes[node_id] = {
        "pid": pid,
        "role": role,
        "content": content
    }
    
    # 更新父节点 children
    if pid not in children_map:
        children_map[pid] = []
    if node_id not in children_map[pid]:
        children_map[pid].append(node_id)
    
    # 追加到 active_path（如果 pid 是 active_path 的最后一个节点）
    if active_path and active_path[-1] == pid:
        active_path.append(node_id)
    
    loaded_doc["nodes"] = nodes
    loaded_doc["children"] = children_map
    loaded_doc["active_path"] = active_path
    _update_timestamp(loaded_doc)
    
    return loaded_doc