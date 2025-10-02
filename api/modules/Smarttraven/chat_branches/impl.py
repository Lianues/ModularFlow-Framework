from __future__ import annotations

# In-memory branching conversation engine (module-level, no HTTP server)
# Provides create/append/truncate/switch + file import/export + derived views (OpenAI messages, branch table)

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import threading
import time
import secrets


# ============== Data Models ==============
@dataclass
class Node:
    id: str
    conversation_id: str
    parent_id: Optional[str]
    depth: int
    role: str
    content: Optional[str]
    sibling_ord: int  # 1..n among siblings (undefined for root)
    created_at: float


@dataclass
class Conversation:
    id: str
    user_id: Optional[str]
    title: Optional[str]
    root_node_id: str
    created_at: float


@dataclass
class Session:
    id: str
    conversation_id: str
    status: str  # "active" | "archived"
    rev: int
    path: List[str] = field(default_factory=list)  # list of node ids ordered by depth
    created_at: float = field(default_factory=lambda: time.time())
    closed_at: Optional[float] = None


# ============== In-memory Store ==============
STORE_LOCK = threading.RLock()
CONVERSATIONS: Dict[str, Conversation] = {}
NODES: Dict[str, Node] = {}
PARENT_CHILDREN: Dict[str, List[str]] = {}  # parent_id -> [child_ids ordered by sibling_ord]
SESSIONS: Dict[str, Session] = {}
_ID_LOCK = threading.Lock()
_ID_COUNTER = 0


def new_id(prefix: str = "") -> str:
    """Generate a compact unique id (roughly sortable)."""
    global _ID_COUNTER
    with _ID_LOCK:
        _ID_COUNTER += 1
        c = _ID_COUNTER
    return f"{prefix}{int(time.time()*1000):x}{secrets.token_hex(3)}{c}"


# ============== Helpers ==============
def _children_of(parent_id: str) -> List[str]:
    return PARENT_CHILDREN.get(parent_id, [])


def _append_child(parent: Node, child: Node) -> None:
    lst = PARENT_CHILDREN.setdefault(parent.id, [])
    lst.append(child.id)


def _ensure_active_session(session_id: str) -> Session:
    sess = SESSIONS.get(session_id)
    if not sess:
        raise ValueError("session not found")
    if sess.status != "active":
        raise ValueError("session is not active")
    return sess


def _node(node_id: str) -> Node:
    n = NODES.get(node_id)
    if not n:
        raise ValueError(f"node {node_id} not found")
    return n


def _branch_indicator(parent_id: Optional[str], child_id: str) -> Tuple[Optional[int], Optional[int]]:
    if parent_id is None:
        return None, None
    children = _children_of(parent_id)
    n = len(children)
    if n == 0:
        return None, None
    child = _node(child_id)
    j = child.sibling_ord
    return j, n


def _materialize_path(session: Session) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, nid in enumerate(session.path):
        node = _node(nid)
        parent_id = None if idx == 0 else session.path[idx - 1]
        j, n = _branch_indicator(parent_id, nid)
        out.append({
            "id": node.id,
            "depth": node.depth,
            "role": node.role,
            "content": node.content,
            "branch_j": j,
            "branch_n": n
        })
    return out


# ============== Core Operations ==============
def create_conversation(user_id: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Any]:
    with STORE_LOCK:
        conv_id = new_id("c_")
        root_id = new_id("n_")
        now = time.time()
        root = Node(
            id=root_id, conversation_id=conv_id, parent_id=None,
            depth=1, role="system", content="root", sibling_ord=1, created_at=now
        )
        NODES[root_id] = root
        conv = Conversation(
            id=conv_id, user_id=user_id, title=title or f"Conv {conv_id[-6:]}",
            root_node_id=root_id, created_at=now
        )
        CONVERSATIONS[conv_id] = conv
        sess_id = new_id("s_")
        sess = Session(id=sess_id, conversation_id=conv_id, status="active", rev=0, path=[root_id])
        SESSIONS[sess_id] = sess
        return {
            "conversation_id": conv_id,
            "session_id": sess_id,
            "path": _materialize_path(sess)
        }


def get_path(session_id: str) -> Dict[str, Any]:
    with STORE_LOCK:
        sess = SESSIONS.get(session_id)
        if not sess:
            raise ValueError("session not found")
        return {"session_id": sess.id, "status": sess.status, "path": _materialize_path(sess)}


def append_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    if role not in ("user", "assistant", "system"):
        raise ValueError("invalid role")
    with STORE_LOCK:
        sess = _ensure_active_session(session_id)
        last_id = sess.path[-1]
        parent = _node(last_id)
        children = _children_of(parent.id)
        sibling_ord = len(children) + 1
        node_id = new_id("n_")
        node = Node(
            id=node_id, conversation_id=sess.conversation_id, parent_id=parent.id,
            depth=parent.depth + 1, role=role, content=content, sibling_ord=sibling_ord, created_at=time.time()
        )
        NODES[node_id] = node
        _append_child(parent, node)
        sess.path.append(node_id)
        sess.rev += 1
        return {"session_id": sess.id, "status": sess.status, "path": _materialize_path(sess)}


def truncate_after(session_id: str, keep_depth: int) -> Dict[str, Any]:
    with STORE_LOCK:
        sess = _ensure_active_session(session_id)
        if keep_depth > len(sess.path):
            raise ValueError(f"keep_depth {keep_depth} exceeds path length {len(sess.path)}")
        if keep_depth < 1:
            raise ValueError("keep_depth must be >= 1")
        sess.path = sess.path[: keep_depth]
        sess.rev += 1
        return {"session_id": sess.id, "status": sess.status, "path": _materialize_path(sess)}


def switch_branch_and_start_new_session(session_id: str, at_depth: int, direction: str) -> Dict[str, Any]:
    if direction not in ("left", "right"):
        raise ValueError("direction must be 'left' or 'right'")
    with STORE_LOCK:
        old = _ensure_active_session(session_id)
        if at_depth - 1 > len(old.path):
            raise ValueError(f"at_depth {at_depth} exceeds path length {len(old.path)}")
        if at_depth < 2:
            raise ValueError("at_depth must be >= 2")

        parent_index = at_depth - 2  # 0-based
        parent_id = old.path[parent_index]
        parent = _node(parent_id)
        children = _children_of(parent_id)
        current_child_id = old.path[at_depth - 1] if len(old.path) >= at_depth else None

        # decide target sibling_ord
        if not children:
            target_ord = 1
        elif current_child_id is None:
            target_ord = 1 if direction == "left" else (len(children) + 1)
        else:
            current_node = _node(current_child_id)
            idx = current_node.sibling_ord - 1
            if direction == "left":
                target_ord = current_node.sibling_ord - 1 if idx > 0 else 1
            else:
                target_ord = current_node.sibling_ord + 1 if idx < len(children) - 1 else (len(children) + 1)

        # resolve/create target child
        if target_ord <= len(children):
            target_child_id = children[target_ord - 1]
        else:
            node_id = new_id("n_")
            node = Node(
                id=node_id, conversation_id=old.conversation_id, parent_id=parent.id,
                depth=parent.depth + 1, role="assistant", content=None,
                sibling_ord=len(children) + 1, created_at=time.time()
            )
            NODES[node_id] = node
            _append_child(parent, node)
            target_child_id = node_id

        # archive old session; create new active session
        old.status = "archived"
        old.closed_at = time.time()
        new_sid = new_id("s_")
        new_path = list(old.path[: at_depth - 1])
        new_path.append(target_child_id)
        new_sess = Session(id=new_sid, conversation_id=old.conversation_id, status="active", rev=0, path=new_path)
        SESSIONS[new_sid] = new_sess
        return {"old_session_id": old.id, "new_session_id": new_sid, "path": _materialize_path(new_sess)}


def branch_indicator(session_id: str, depth: int) -> Dict[str, Optional[int]]:
    with STORE_LOCK:
        sess = SESSIONS.get(session_id)
        if not sess:
            raise ValueError("session not found")
        if depth < 2 or depth > len(sess.path):
            return {"j": None, "n": None}
        parent_id = sess.path[depth - 2]
        child_id = sess.path[depth - 1]
        j, n = _branch_indicator(parent_id, child_id)
        return {"j": j, "n": n}


# ============== Listing ==============
def list_conversations() -> Dict[str, Any]:
    with STORE_LOCK:
        items = []
        # gather sessions grouped by conversation
        conv_sessions: Dict[str, List[Tuple[str, Session]]] = {}
        for sid, s in SESSIONS.items():
            conv_sessions.setdefault(s.conversation_id, []).append((sid, s))
        for cid, conv in CONVERSATIONS.items():
            sess = conv_sessions.get(cid, [])
            active = next((sid for sid, s in sess if s.status == "active"), None)
            items.append({
                "id": conv.id,
                "title": conv.title,
                "user_id": conv.user_id,
                "root_node_id": conv.root_node_id,
                "created_at": conv.created_at,
                "sessions_count": len(sess),
                "active_session_id": active
            })
        return {"items": items}


def list_sessions(conversation_id: str) -> Dict[str, Any]:
    with STORE_LOCK:
        if conversation_id not in CONVERSATIONS:
            raise ValueError("conversation not found")
        items = []
        for sid, s in SESSIONS.items():
            if s.conversation_id == conversation_id:
                items.append({
                    "id": s.id,
                    "status": s.status,
                    "rev": s.rev,
                    "path_length": len(s.path),
                    "created_at": s.created_at,
                    "closed_at": s.closed_at
                })
        items.sort(key=lambda x: x["created_at"])
        return {"items": items}


# ============== File IO (import/export) ==============
def export_v2(conversation_id: str) -> Dict[str, Any]:
    with STORE_LOCK:
        conv = CONVERSATIONS.get(conversation_id)
        if not conv:
            raise ValueError("conversation not found")

        nodes_doc: Dict[str, Dict] = {}
        for nid, n in NODES.items():
            if n.conversation_id == conversation_id:
                nodes_doc[nid] = {
                    "pid": n.parent_id,
                    "role": n.role,
                    "content": n.content
                }

        children_doc: Dict[str, List[str]] = {}
        for pid, lst in PARENT_CHILDREN.items():
            if pid in nodes_doc:
                children_doc[pid] = [cid for cid in lst if cid in nodes_doc]

        # pick active or latest session for active_path
        active_sid = next((sid for sid, s in SESSIONS.items()
                           if s.conversation_id == conversation_id and s.status == "active"), None)
        if active_sid:
            active_path = list(SESSIONS[active_sid].path)
        else:
            candidates = [s for s in SESSIONS.values() if s.conversation_id == conversation_id]
            candidates.sort(key=lambda s: s.created_at, reverse=True)
            active_path = list(candidates[0].path) if candidates else [conv.root_node_id]

        return {
            "schema": {"name": "chat-branches", "version": 2},
            "meta": {"id": conv.id, "title": conv.title},
            "root": conv.root_node_id,
            "nodes": nodes_doc,
            "children": children_doc,
            "active_path": active_path
        }


def import_v2(doc: Dict[str, Any]) -> Dict[str, str]:
    if not isinstance(doc, dict):
        raise ValueError("invalid payload")

    schema = (doc.get("schema") or {})
    if schema.get("name") != "chat-branches" or int(schema.get("version", 0)) != 2:
        raise ValueError("unsupported schema (expect chat-branches)")

    meta = doc.get("meta") or {}
    root = doc.get("root")
    nodes_doc = doc.get("nodes") or {}
    children_doc = doc.get("children") or {}
    active_path = doc.get("active_path") or []
    if not root or root not in nodes_doc:
        raise ValueError("invalid file: missing/invalid root")
    conv_id = meta.get("id") or new_id("c_")
    title = meta.get("title")
    now = time.time()

    with STORE_LOCK:
        # replace existing conversation with same id (clear)
        if conv_id in CONVERSATIONS:
            # remove sessions
            to_del_sessions = [sid for sid, s in SESSIONS.items() if s.conversation_id == conv_id]
            for sid in to_del_sessions:
                SESSIONS.pop(sid, None)
            # collect nodes
            to_del_nodes = [nid for nid, n in NODES.items() if n.conversation_id == conv_id]
            # remove parent children buckets for these nodes
            for nid in to_del_nodes:
                PARENT_CHILDREN.pop(nid, None)
            # remove nodes
            for nid in to_del_nodes:
                NODES.pop(nid, None)
            # remove conversation
            CONVERSATIONS.pop(conv_id, None)

        # create conversation
        CONVERSATIONS[conv_id] = Conversation(
            id=conv_id, user_id=None, title=title, root_node_id=root, created_at=now
        )

        # build children buckets; ensure implicit links exist
        buckets: Dict[str, List[str]] = {}
        for pid, arr in (children_doc or {}).items():
            if isinstance(arr, list):
                buckets[pid] = [cid for cid in arr if cid in nodes_doc]
        for nid, nd in nodes_doc.items():
            pid = (nd or {}).get("pid")
            if pid is not None:
                buckets.setdefault(pid, [])
                if nid not in buckets[pid]:
                    buckets[pid].append(nid)

        # depth memoization
        depth_cache: Dict[str, int] = {root: 1}

        def depth_of(nid: str, seen: Optional[set] = None) -> int:
            if nid in depth_cache:
                return depth_cache[nid]
            if seen is None:
                seen = set()
            if nid in seen:
                return 1  # cycle guard
            seen.add(nid)
            pid = (nodes_doc.get(nid) or {}).get("pid")
            if pid is None or pid not in nodes_doc:
                depth = 1
            else:
                depth = depth_of(pid, seen) + 1
            depth_cache[nid] = depth
            return depth

        # sync buckets
        for pid, arr in buckets.items():
            PARENT_CHILDREN[pid] = list(arr)

        # sibling ordinal map
        sibling_ord: Dict[str, int] = {}
        for pid, arr in buckets.items():
            for idx, cid in enumerate(arr, start=1):
                sibling_ord[cid] = idx

        # create nodes
        for nid, nd in nodes_doc.items():
            NODES[nid] = Node(
                id=nid,
                conversation_id=conv_id,
                parent_id=(nd or {}).get("pid"),
                depth=depth_of(nid),
                role=(nd or {}).get("role") or "system",
                content=(nd or {}).get("content"),
                sibling_ord=sibling_ord.get(nid, 1),
                created_at=now
            )

        # normalize active path
        if not isinstance(active_path, list) or not active_path:
            active_path = [root]
        if active_path[0] != root:
            active_path = [root] + active_path
        norm_path = [root]
        for i in range(1, len(active_path)):
            prev = norm_path[-1]
            nxt = active_path[i]
            if nxt in set(PARENT_CHILDREN.get(prev, [])):
                norm_path.append(nxt)
            else:
                break

        sess_id = new_id("s_")
        SESSIONS[sess_id] = Session(
            id=sess_id, conversation_id=conv_id, status="active", rev=0, path=norm_path
        )
        return {"conversation_id": conv_id, "active_session_id": sess_id}
    
# Stable aliases without version suffix

def export(conversation_id: str) -> Dict[str, Any]:
    return export_v2(conversation_id)


def import_chat(doc: Dict[str, Any]) -> Dict[str, str]:
    return import_v2(doc)

# ============== Derived Views ==============
def openai_messages(session_id: str) -> Dict[str, Any]:
    """Return current branch as OpenAI Chat messages [{role, content}, ...]."""
    with STORE_LOCK:
        sess = SESSIONS.get(session_id)
        if not sess:
            raise ValueError("session not found")
        messages: List[Dict[str, str]] = []
        for nid in sess.path:
            n = _node(nid)
            if n.role not in ("system", "user", "assistant"):
                continue
            messages.append({"role": n.role, "content": n.content or ""})
        return {"conversation_id": sess.conversation_id, "session_id": sess.id, "messages": messages}


def branch_table(session_id: str) -> Dict[str, Any]:
    """
    Return a branch situation table for external UI.
    Includes:
      - latest: latest depth j/n and node_id
      - levels: list for each depth >= 2 with j/n
    """
    with STORE_LOCK:
        sess = SESSIONS.get(session_id)
        if not sess:
            raise ValueError("session not found")
        levels: List[Dict] = []
        L = len(sess.path)
        latest = {"depth": L, "j": None, "n": None, "node_id": sess.path[-1] if L >= 1 else None}
        for depth in range(2, L + 1):
            parent_id = sess.path[depth - 2]
            child_id = sess.path[depth - 1]
            j, n = _branch_indicator(parent_id, child_id)
            row = {"depth": depth, "node_id": child_id, "j": j, "n": n}
            levels.append(row)
            if depth == L:
                latest.update({"j": j, "n": n})
        return {"session_id": sess.id, "latest": latest, "levels": levels}