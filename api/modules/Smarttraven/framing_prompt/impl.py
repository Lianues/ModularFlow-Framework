from __future__ import annotations

"""
SmartTraven.framing_prompt 实现层

职责
- 根据 relative 预设占位符在“对话历史之前”构建前缀提示词（prefix）
- 支持两类 history 输入：
  1) 原始 OpenAI messages（不含 source）→ 规范化补齐 source
  2) 已处理过的 in-chat 风格 messages（含 source）→ 原样透传并校验结构
- 支持从 presets_doc.prompts 或直接传入 presets_relative 数组两种来源
- 从 world_books（支持嵌套数组结构）中抽取 before_char/after_char 的条目
- 支持 persona/character 描述占位符
- 输出键顺序统一：role → content → source（source 字段内部尽量保持来源条目字段顺序）

注意
- 不处理 chatHistory（保持与 in_chat_constructor 的职责边界）
- 世界书在本模块仅处理 position ∈ {before_char, after_char} 的条目
"""

from typing import Any, Dict, List, Optional, Union

# 常量
DEFAULT_ORDER: int = 100
ALLOWED_ROLES = {"user", "assistant", "system"}


def _is_enabled(val: Any) -> bool:
    """None 视为启用，仅显式 False 视为禁用。"""
    return False if val is False else True


def _role_priority(role: str) -> int:
    """assistant(0) < user(1) < system(2)"""
    return {"assistant": 0, "user": 1, "system": 2}.get(str(role), 2)


def _map_wb_pos_to_role(position: str) -> str:
    """
    世界书 position → 对话角色的映射
    - before_char / after_char → system（旧模块语义）
    - 否则当作显式角色（user|assistant|system）或回退 system
    """
    pos = str(position or "").lower()
    if pos in ("before_char", "after_char"):
        return "system"
    if pos in ALLOWED_ROLES:
        return pos
    return "system"


def _flatten_world_books(items: Any) -> List[Dict[str, Any]]:
    """扁平化世界书数组，兼容 [[{...}], {...}] 与单对象容错。"""
    out: List[Dict[str, Any]] = []
    if not items:
        return out
    if isinstance(items, dict):
        out.append(items)  # 容错：单个对象
        return out
    if isinstance(items, list):
        for it in items:
            if isinstance(it, dict):
                out.append(it)
            elif isinstance(it, list):
                for sub in it:
                    if isinstance(sub, dict):
                        out.append(sub)
    return out


def _sort_sources(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 order 升序 → 角色优先级（assistant < user < system）→ internal_order 稳定排序。"""
    return sorted(
        entries,
        key=lambda e: (
            int(e.get("order", DEFAULT_ORDER) or DEFAULT_ORDER),
            _role_priority(e.get("role", "system")),
            int(e.get("internal_order", 0) or 0),
        ),
    )


def _build_source_for_history(index: int) -> Dict[str, Any]:
    """历史消息的来源字段，字段顺序：type → id → index。"""
    return {
        "type": "history",
        "id": f"history_{index}",
        "index": index,
    }


def _build_source_for_preset(p: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    """
    预设来源字段：
    - 先放置 type 与 id
    - 再按原条目字段顺序复制（Python 3.7+ dict 保序）
    """
    src: Dict[str, Any] = {
        "type": "preset",
        "id": source_id,
    }
    for k in p.keys():
        src[k] = p.get(k)
    return src


def _build_source_for_wb(wb: Dict[str, Any], source_id: str, derived_role: str) -> Dict[str, Any]:
    """
    世界书来源字段：
    - 先放置 type 与 id
    - 按原条目字段顺序复制；遇到原始 'id' 改名为 'wb_id' 避免冲突
    - 若来源缺少 role，则在末尾追加 role 以不打乱原字段顺序
    """
    src: Dict[str, Any] = {
        "type": "world_book",
        "id": source_id,
    }
    for k in wb.keys():
        if k == "id":
            src["wb_id"] = wb.get(k)
        else:
            src[k] = wb.get(k)
    if "role" not in src:
        src["role"] = derived_role
    return src


def _build_source_for_character(character: Dict[str, Any]) -> Dict[str, Any]:
    """
    角色来源字段：
    - 先放置 type 与 id
    - 再按原文档键顺序复制（常见字段：name, description, ...）
    """
    src: Dict[str, Any] = {
        "type": "character",
        "id": "char_description",
    }
    for k in character.keys():
        src[k] = character.get(k)
    return src


def _build_source_for_persona(persona: Dict[str, Any]) -> Dict[str, Any]:
    """用户画像来源字段，同上。"""
    src: Dict[str, Any] = {
        "type": "persona",
        "id": "persona_description",
    }
    for k in persona.keys():
        src[k] = persona.get(k)
    return src


def _collect_relative_presets(
    presets_relative: Optional[List[Dict[str, Any]]],
    presets_doc: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    收集 relative 预设条目。
    - 优先使用 presets_relative；否则尝试从 presets_doc.prompts 过滤 position=="relative"
    - 返回带排序辅助字段的条目列表
    """
    candidates: List[Dict[str, Any]] = []
    rel: List[Dict[str, Any]] = []

    if isinstance(presets_relative, list):
        rel = [p for p in presets_relative if isinstance(p, dict)]
    elif isinstance(presets_doc, dict):
        prompts = presets_doc.get("prompts") or []
        if isinstance(prompts, list):
            rel = [p for p in prompts if isinstance(p, dict) and str(p.get("position")) == "relative"]

    for i, p in enumerate(rel):
        if not _is_enabled(p.get("enabled", True)):
            # 对占位符类（如 worldInfoBefore/After）通常未显式 enabled，此处 None 视为 True；显式 False 则跳过
            continue
        role = str(p.get("role", "system")).lower()
        role = role if role in ALLOWED_ROLES else "system"
        candidates.append({
            "data": p,
            "type": "preset",
            "order": int(p.get("order", DEFAULT_ORDER) or DEFAULT_ORDER),
            "role": role,
            "internal_order": i,
        })
    return _sort_sources(candidates)


def _world_info_messages(
    position: str,
    world_books: Any,
    triggered_ids: set[int],
) -> List[Dict[str, Any]]:
    """
    构建 before_char / after_char 的世界书消息列表。
    - 过滤：position 精确匹配、enabled、content 非空、mode 允许（always 或 conditional & 命中）
    - 排序：order 升序 → 角色优先级 → internal_order
    - 每条消息不合并，逐条输出
    """
    flat = _flatten_world_books(world_books)
    wb_sources: List[Dict[str, Any]] = []

    for i, wb in enumerate(flat):
        if not isinstance(wb, dict):
            continue
        pos = str(wb.get("position", ""))
        if pos != position:
            continue
        if not _is_enabled(wb.get("enabled", True)):
            continue
        content = wb.get("content")
        if not isinstance(content, str) or content.strip() == "":
            continue
        mode = str(wb.get("mode", "always"))
        if mode == "conditional":
            wid = wb.get("id")
            if wid is None or int(wid) not in triggered_ids:
                continue
        role = _map_wb_pos_to_role(pos)
        wb_sources.append({
            "data": wb,
            "type": "world",
            "order": int(wb.get("order", DEFAULT_ORDER) or DEFAULT_ORDER),
            "role": role,
            "internal_order": i,
        })

    sorted_wb = _sort_sources(wb_sources)
    out: List[Dict[str, Any]] = []
    for e in sorted_wb:
        data = e["data"]
        content = data.get("content", "")
        src = _build_source_for_wb(
            data,
            source_id=f"wb_{data.get('id') if data.get('id') is not None else e.get('internal_order', 0)}",
            derived_role=e["role"],
        )
        out.append({
            "role": e["role"],
            "content": content,
            "source": src,
        })
    return out


def assemble(
    history: List[Dict[str, Any]],
    triggered_worldbook_ids: List[int],
    world_books: Union[List[Any], Dict[str, Any], None] = None,
    presets_relative: Optional[List[Dict[str, Any]]] = None,
    presets_doc: Optional[Dict[str, Any]] = None,
    character: Optional[Dict[str, Any]] = None,
    persona: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    构建前缀提示词，并返回规范化后的历史消息。

    入参
    - history: OpenAI messages 数组（若条目无 source，将补齐）
    - triggered_worldbook_ids: 命中的 conditional 世界书 id 列表
    - world_books: 世界书条目数组（支持嵌套）
    - presets_relative: 已过滤好的 relative 预设（可选）
    - presets_doc: Default.json 文档（可选；当未提供 presets_relative 时从其中过滤）
    - character: 角色卡（可选；用于 charDescription）
    - persona: 用户画像（可选；用于 personaDescription）

    返回
    - {
        "messages": prefix_messages,           # 前缀提示词（每条：role → content → source）
        "normalized_history": normalized_list  # 补齐 source 的历史消息（每条：role → content → source）
      }
    """
    # 0) 归一化入参
    trig_set = set(int(x) for x in (triggered_worldbook_ids or []))
    history = history or []
    world_books = world_books or []
    sorted_rel = _collect_relative_presets(presets_relative, presets_doc)

    # 1) 规范化 history（每条补齐 source，字段顺序 role → content → source）
    normalized_history: List[Dict[str, Any]] = []
    for i, msg in enumerate(history):
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "")).lower()
        content = msg.get("content", "")
        if role not in ALLOWED_ROLES:
            # 容错：非法角色回退为 user，以避免中断流程
            role = "user"
        if not isinstance(content, str):
            content = "" if content is None else str(content)
        src = msg.get("source")
        if not isinstance(src, dict):
            src = _build_source_for_history(i)
        normalized_history.append({
            "role": role,
            "content": content,
            "source": src,
        })

    # 2) 基于 relative 预设构建 prefix
    prefix: List[Dict[str, Any]] = []
    for e in sorted_rel:
        p = e["data"]
        identifier = str(p.get("identifier", "") or "")
        role = e["role"]

        # chatHistory：忽略（由 in_chat_constructor 处理真正的历史）
        if identifier == "chatHistory":
            continue

        # world info before/after
        if identifier == "worldInfoBefore":
            prefix.extend(_world_info_messages("before_char", world_books, trig_set))
            continue
        if identifier == "worldInfoAfter":
            prefix.extend(_world_info_messages("after_char", world_books, trig_set))
            continue

        # char / persona
        if identifier == "charDescription":
            desc = ""
            if isinstance(character, dict):
                desc = character.get("description") or ""
            if isinstance(desc, str) and desc.strip():
                prefix.append({
                    "role": role,
                    "content": desc,
                    "source": _build_source_for_character(character or {}),
                })
            continue

        if identifier == "personaDescription":
            pdesc = ""
            if isinstance(persona, dict):
                pdesc = persona.get("description") or ""
            if isinstance(pdesc, str) and pdesc.strip():
                prefix.append({
                    "role": role,
                    "content": pdesc,
                    "source": _build_source_for_persona(persona or {}),
                })
            continue

        # 其他 relative 预设（普通文本）
        content = p.get("content", "")
        if isinstance(content, str) and content.strip():
            pid = p.get("identifier") or p.get("name") or str(e.get("internal_order", 0))
            src = _build_source_for_preset(p, source_id=f"preset_{pid}")
            prefix.append({
                "role": role,
                "content": content,
                "source": src,
            })

    return {
        "messages": prefix,
        "normalized_history": normalized_history,
    }