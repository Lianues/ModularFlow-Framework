# -*- coding: utf-8 -*-
"""
SmartTavern.data_catalog 实现层

职责
- 扫描 backend_projects/SmartTavern/data 下各类资源文件夹
- 首期：实现“预设（presets）目录”的清单读取（name/description 字段提取）
- 扩展：实现 world_books / characters / persona / regex_rules 的清单读取

说明
- 本文件仅提供纯实现函数；API 注册在同目录 data_catalog.py 中完成
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json


# ---------- 路径与工具 ----------

def _repo_root() -> Path:
    """
    返回仓库根目录（基于当前文件层级向上回溯）
    当前文件位于: repo_root/api/modules/SmartTavern/data_catalog/impl.py
    parents[4] => repo_root
    """
    return Path(__file__).resolve().parents[4]


def _safe_read_json(p: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _ensure_str(x: Any) -> Optional[str]:
    if x is None:
        return None
    try:
        return str(x)
    except Exception:
        return None


def _path_rel_to_root(p: Path, root: Path) -> str:
    """
    统一返回 POSIX 风格路径（使用 '/' 分隔），避免在 Windows 下出现 '\\' 与断言不匹配。
    """
    try:
        return p.relative_to(root).as_posix()
    except Exception:
        # 兼容老版本 Python 无 Path.is_relative_to 或跨盘情况
        try:
            return p.resolve().as_posix()
        except Exception:
            # 最后一层保证：替换反斜杠
            return str(p).replace("\\", "/")


# ---------- 实现：列出 presets ----------

def list_presets_impl(base_dir: Optional[str] = None,
                      fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    扫描 presets 目录，返回文件相对路径与所需字段（name/description）

    Args:
      base_dir: 可选，覆盖默认目录（绝对路径或相对仓库根）
      fields:   允许传入 ["name","description"] 的子集；默认两者都返回

    Returns:
      {
        "folder": "backend_projects/SmartTavern/data/presets",
        "total": N,
        "items": [
          {"file":"backend_projects/.../Default.json","name":"..","description":".."}, ...
        ],
        "errors": [{"file":"...","error":"..."}?]
      }
    """
    root = _repo_root()
    default_folder = root / "backend_projects" / "SmartTavern" / "data" / "presets"

    if base_dir:
        b = Path(base_dir)
        folder = (root / b).resolve() if not b.is_absolute() else b.resolve()
    else:
        folder = default_folder

    want_name = True
    want_desc = True
    if isinstance(fields, list) and fields:
        fs = [str(x).strip().lower() for x in fields if isinstance(x, str)]
        want_name = "name" in fs
        want_desc = "description" in fs

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not folder.exists() or not folder.is_dir():
        return {
            "folder": _path_rel_to_root(folder, root),
            "total": 0,
            "items": [],
            "errors": [{"file": None, "error": f"Folder not found: {folder}"}]
        }

    for p in sorted(folder.glob("*.json")):
        doc, err = _safe_read_json(p)
        if err:
            errors.append({"file": _path_rel_to_root(p, root), "error": err})
            continue

        name = _ensure_str((doc or {}).get("name")) if want_name else None
        desc = _ensure_str((doc or {}).get("description")) if want_desc else None

        item: Dict[str, Any] = {"file": _path_rel_to_root(p, root)}
        if want_name:
            item["name"] = name
        if want_desc:
            item["description"] = desc
        items.append(item)

    out: Dict[str, Any] = {
        "folder": _path_rel_to_root(folder, root),
        "total": len(items),
        "items": items
    }
    if errors:
        out["errors"] = errors
    return out


# ---------- 实现：列出 world_books ----------

def list_world_books_impl(base_dir: Optional[str] = None,
                          fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    扫描 world_books 目录，返回文件相对路径与所需字段（name/description）
    """
    root = _repo_root()
    default_folder = root / "backend_projects" / "SmartTavern" / "data" / "world_books"

    if base_dir:
        b = Path(base_dir)
        folder = (root / b).resolve() if not b.is_absolute() else b.resolve()
    else:
        folder = default_folder

    want_name = True
    want_desc = True
    if isinstance(fields, list) and fields:
        fs = [str(x).strip().lower() for x in fields if isinstance(x, str)]
        want_name = "name" in fs
        want_desc = "description" in fs

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not folder.exists() or not folder.is_dir():
        return {
            "folder": _path_rel_to_root(folder, root),
            "total": 0,
            "items": [],
            "errors": [{"file": None, "error": f"Folder not found: {folder}"}]
        }

    for p in sorted(folder.glob("*.json")):
        doc, err = _safe_read_json(p)
        if err:
            errors.append({"file": _path_rel_to_root(p, root), "error": err})
            continue

        name = _ensure_str((doc or {}).get("name")) if want_name else None
        desc = _ensure_str((doc or {}).get("description")) if want_desc else None

        item: Dict[str, Any] = {"file": _path_rel_to_root(p, root)}
        if want_name:
            item["name"] = name
        if want_desc:
            item["description"] = desc
        items.append(item)

    out: Dict[str, Any] = {
        "folder": _path_rel_to_root(folder, root),
        "total": len(items),
        "items": items
    }
    if errors:
        out["errors"] = errors
    return out


# ---------- 实现：列出 characters ----------

def list_characters_impl(base_dir: Optional[str] = None,
                         fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    扫描 characters 目录，返回文件相对路径与所需字段（name/description）
    """
    root = _repo_root()
    default_folder = root / "backend_projects" / "SmartTavern" / "data" / "characters"

    if base_dir:
        b = Path(base_dir)
        folder = (root / b).resolve() if not b.is_absolute() else b.resolve()
    else:
        folder = default_folder

    want_name = True
    want_desc = True
    if isinstance(fields, list) and fields:
        fs = [str(x).strip().lower() for x in fields if isinstance(x, str)]
        want_name = "name" in fs
        want_desc = "description" in fs

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not folder.exists() or not folder.is_dir():
        return {
            "folder": _path_rel_to_root(folder, root),
            "total": 0,
            "items": [],
            "errors": [{"file": None, "error": f"Folder not found: {folder}"}]
        }

    for p in sorted(folder.glob("*.json")):
        doc, err = _safe_read_json(p)
        if err:
            errors.append({"file": _path_rel_to_root(p, root), "error": err})
            continue

        name = _ensure_str((doc or {}).get("name")) if want_name else None
        desc = _ensure_str((doc or {}).get("description")) if want_desc else None

        item: Dict[str, Any] = {"file": _path_rel_to_root(p, root)}
        if want_name:
            item["name"] = name
        if want_desc:
            item["description"] = desc
        items.append(item)

    out: Dict[str, Any] = {
        "folder": _path_rel_to_root(folder, root),
        "total": len(items),
        "items": items
    }
    if errors:
        out["errors"] = errors
    return out


# ---------- 实现：列出 persona ----------

def list_personas_impl(base_dir: Optional[str] = None,
                       fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    扫描 persona 目录，返回文件相对路径与所需字段（name/description）
    """
    root = _repo_root()
    default_folder = root / "backend_projects" / "SmartTavern" / "data" / "persona"

    if base_dir:
        b = Path(base_dir)
        folder = (root / b).resolve() if not b.is_absolute() else b.resolve()
    else:
        folder = default_folder

    want_name = True
    want_desc = True
    if isinstance(fields, list) and fields:
        fs = [str(x).strip().lower() for x in fields if isinstance(x, str)]
        want_name = "name" in fs
        want_desc = "description" in fs

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not folder.exists() or not folder.is_dir():
        return {
            "folder": _path_rel_to_root(folder, root),
            "total": 0,
            "items": [],
            "errors": [{"file": None, "error": f"Folder not found: {folder}"}]
        }

    for p in sorted(folder.glob("*.json")):
        doc, err = _safe_read_json(p)
        if err:
            errors.append({"file": _path_rel_to_root(p, root), "error": err})
            continue

        name = _ensure_str((doc or {}).get("name")) if want_name else None
        desc = _ensure_str((doc or {}).get("description")) if want_desc else None

        item: Dict[str, Any] = {"file": _path_rel_to_root(p, root)}
        if want_name:
            item["name"] = name
        if want_desc:
            item["description"] = desc
        items.append(item)

    out: Dict[str, Any] = {
        "folder": _path_rel_to_root(folder, root),
        "total": len(items),
        "items": items
    }
    if errors:
        out["errors"] = errors
    return out


# ---------- 实现：列出 regex_rules ----------

def list_regex_rules_impl(base_dir: Optional[str] = None,
                          fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    扫描 regex_rules 目录，返回文件相对路径与所需字段（name/description）
    """
    root = _repo_root()
    default_folder = root / "backend_projects" / "SmartTavern" / "data" / "regex_rules"

    if base_dir:
        b = Path(base_dir)
        folder = (root / b).resolve() if not b.is_absolute() else b.resolve()
    else:
        folder = default_folder

    want_name = True
    want_desc = True
    if isinstance(fields, list) and fields:
        fs = [str(x).strip().lower() for x in fields if isinstance(x, str)]
        want_name = "name" in fs
        want_desc = "description" in fs

    items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not folder.exists() or not folder.is_dir():
        return {
            "folder": _path_rel_to_root(folder, root),
            "total": 0,
            "items": [],
            "errors": [{"file": None, "error": f"Folder not found: {folder}"}]
        }

    for p in sorted(folder.glob("*.json")):
        doc, err = _safe_read_json(p)
        if err:
            errors.append({"file": _path_rel_to_root(p, root), "error": err})
            continue

        name = _ensure_str((doc or {}).get("name")) if want_name else None
        desc = _ensure_str((doc or {}).get("description")) if want_desc else None

        item: Dict[str, Any] = {"file": _path_rel_to_root(p, root)}
        if want_name:
            item["name"] = name
        if want_desc:
            item["description"] = desc
        items.append(item)

    out: Dict[str, Any] = {
        "folder": _path_rel_to_root(folder, root),
        "total": len(items),
        "items": items
    }
    if errors:
        out["errors"] = errors
    return out


# ---------- 实现：读取单个 preset 详情 ----------

def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def get_preset_detail_impl(file: str) -> Dict[str, Any]:
    """
    读取 backend_projects/SmartTavern/data/presets 下指定 JSON 文件，返回基础字段与完整内容。

    入参:
      - file: POSIX 风格相对路径（来自 list_presets 的 items[*].file），例如：
              "backend_projects/SmartTavern/data/presets/Default.json"

    返回:
      {
        "file": "...",
        "name": "...|null",
        "description": "...|null",
        "content": {...}
      }
    """
    root = _repo_root()
    presets_dir = root / "backend_projects" / "SmartTavern" / "data" / "presets"

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, presets_dir):
        return {"error": "OUT_OF_SCOPE", "message": "仅允许读取 presets 目录下的文件"}

    doc, err = _safe_read_json(target)
    if err:
        return {"error": "READ_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    name = _ensure_str((doc or {}).get("name"))
    desc = _ensure_str((doc or {}).get("description"))

    return {
        "file": _path_rel_to_root(target, root),
        "name": name,
        "description": desc,
        "content": doc,
    }

# ---------- 实现：读取单个 world_book 详情 ----------

def get_world_book_detail_impl(file: str) -> Dict[str, Any]:
    """
    读取 backend_projects/SmartTavern/data/world_books 下指定 JSON 文件，返回完整内容与基础字段。
    """
    root = _repo_root()
    world_dir = root / "backend_projects" / "SmartTavern" / "data" / "world_books"

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, world_dir):
        return {"error": "OUT_OF_SCOPE", "message": "仅允许读取 world_books 目录下的文件"}

    doc, err = _safe_read_json(target)
    if err:
        return {"error": "READ_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    name = _ensure_str((doc or {}).get("name"))
    desc = _ensure_str((doc or {}).get("description"))

    return {
        "file": _path_rel_to_root(target, root),
        "name": name,
        "description": desc,
        "content": doc,
    }


# ---------- 实现：读取单个 character 详情 ----------

def get_character_detail_impl(file: str) -> Dict[str, Any]:
    """
    读取 backend_projects/SmartTavern/data/characters 下指定 JSON 文件，返回完整内容与基础字段。
    """
    root = _repo_root()
    char_dir = root / "backend_projects" / "SmartTavern" / "data" / "characters"

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, char_dir):
        return {"error": "OUT_OF_SCOPE", "message": "仅允许读取 characters 目录下的文件"}

    doc, err = _safe_read_json(target)
    if err:
        return {"error": "READ_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    name = _ensure_str((doc or {}).get("name"))
    desc = _ensure_str((doc or {}).get("description"))

    return {
        "file": _path_rel_to_root(target, root),
        "name": name,
        "description": desc,
        "content": doc,
    }


# ---------- 实现：读取单个 persona 详情 ----------

def get_persona_detail_impl(file: str) -> Dict[str, Any]:
    """
    读取 backend_projects/SmartTavern/data/persona 下指定 JSON 文件，返回完整内容与基础字段。
    """
    root = _repo_root()
    persona_dir = root / "backend_projects" / "SmartTavern" / "data" / "persona"

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, persona_dir):
        return {"error": "OUT_OF_SCOPE", "message": "仅允许读取 persona 目录下的文件"}

    doc, err = _safe_read_json(target)
    if err:
        return {"error": "READ_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    name = _ensure_str((doc or {}).get("name"))
    desc = _ensure_str((doc or {}).get("description"))

    return {
        "file": _path_rel_to_root(target, root),
        "name": name,
        "description": desc,
        "content": doc,
    }


# ---------- 实现：读取单个 regex_rules 详情 ----------

def get_regex_rule_detail_impl(file: str) -> Dict[str, Any]:
    """
    读取 backend_projects/SmartTavern/data/regex_rules 下指定 JSON 文件，返回完整内容与基础字段。
    """
    root = _repo_root()
    regex_dir = root / "backend_projects" / "SmartTavern" / "data" / "regex_rules"

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, regex_dir):
        return {"error": "OUT_OF_SCOPE", "message": "仅允许读取 regex_rules 目录下的文件"}

    doc, err = _safe_read_json(target)
    if err:
        return {"error": "READ_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    name = _ensure_str((doc or {}).get("name"))
    desc = _ensure_str((doc or {}).get("description"))

    return {
        "file": _path_rel_to_root(target, root),
        "name": name,
        "description": desc,
        "content": doc,
    }


# ---------- 写入与更新（保存）通用工具 ----------

def _write_json_atomic(target: Path, data: Any) -> Optional[str]:
    """
    将 JSON 原子化写入目标路径（UTF-8, ensure_ascii=False, indent=2）。
    返回 None 表示成功；返回错误字符串表示失败。
    """
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        tmp.replace(target)
        return None
    except Exception as e:
        return f"{type(e).__name__}: {e}"


def _update_json_in_dir(file: str, allowed_dir: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    在指定 allowed_dir 范围内创建/更新一个 JSON 文件。
    约定：
    - payload.content 为完整 JSON（object 或 array）
    - 若 payload.name / payload.description 传入，则写入 content['name'/'description']（覆盖）
    - 若文件不存在则创建；存在则完全覆盖为 content
    - 返回与 *detail_impl 同构的结构：{ file, name, description, content } 或 { error, message }
    """
    root = _repo_root()

    if not isinstance(file, str) or not file:
        return {"error": "INVALID_INPUT", "message": "file 必须为非空字符串"}
    if not isinstance(payload, dict):
        return {"error": "INVALID_INPUT", "message": "payload 必须为对象"}

    content = payload.get("content")
    name = payload.get("name", None)
    desc = payload.get("description", None)

    # 允许 content 为对象或数组
    if not (isinstance(content, dict) or isinstance(content, list)):
        return {"error": "INVALID_INPUT", "message": "content 必须为 object 或 array"}

    target = (root / Path(file)).resolve()
    if not _is_within(target, allowed_dir):
        return {"error": "OUT_OF_SCOPE", "message": f"仅允许写入 {allowed_dir.as_posix()} 目录下的文件"}

    # 将 name/description（若提供）回写到 content 顶层（仅当 content 是对象时）
    if isinstance(content, dict):
        if name is not None:
            content["name"] = name
        if desc is not None:
            content["description"] = desc

    err = _write_json_atomic(target, content)
    if err:
        return {"error": "WRITE_FAILED", "message": err, "file": _path_rel_to_root(target, root)}

    # 规范化返回
    if isinstance(content, dict):
        out_name = _ensure_str(content.get("name"))
        out_desc = _ensure_str(content.get("description"))
    else:
        out_name = None
        out_desc = None

    return {
        "file": _path_rel_to_root(target, root),
        "name": out_name,
        "description": out_desc,
        "content": content,
    }


# ---------- 实现：按类型保存（创建/更新） ----------

def update_preset_file_impl(file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = _repo_root()
    presets_dir = root / "backend_projects" / "SmartTavern" / "data" / "presets"
    return _update_json_in_dir(file, presets_dir, payload)


def update_world_book_file_impl(file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = _repo_root()
    world_dir = root / "backend_projects" / "SmartTavern" / "data" / "world_books"
    return _update_json_in_dir(file, world_dir, payload)


def update_character_file_impl(file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = _repo_root()
    char_dir = root / "backend_projects" / "SmartTavern" / "data" / "characters"
    return _update_json_in_dir(file, char_dir, payload)


def update_persona_file_impl(file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = _repo_root()
    persona_dir = root / "backend_projects" / "SmartTavern" / "data" / "persona"
    return _update_json_in_dir(file, persona_dir, payload)


def update_regex_rule_file_impl(file: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    root = _repo_root()
    regex_dir = root / "backend_projects" / "SmartTavern" / "data" / "regex_rules"
    return _update_json_in_dir(file, regex_dir, payload)