from __future__ import annotations

"""
SmartTraven.regex_replace 实现层

功能概述
- 根据规则文件（数组 JSON）和 placement（before_macro/after_macro）对内容执行正则替换
- 支持两种输入形态：messages（带 role/content/source）或 text（纯文本）
- 对 messages：
  - 先基于“深度（depth）”限定生效范围（仅 messages 生效；text 默认对整段生效）
  - 再按 targets 过滤（role 或 source.type 匹配）
  - 再按 views（user_view/assistant_view）分别应用替换
  - 保留原 messages 结构，仅替换 content；输出 original/user_view/assistant_view 三套视图
- 对 text：
  - 忽略 depth 与 targets，默认整段生效
  - 按 views 产出 user_view/assistant_view 两套文本，同时透传 original

深度（depth）计算规则（仅 messages）
- 先过滤掉 source.type=='preset' 且 source.position=='relative' 的消息（仅用于计算锚点，不影响最终输出）
- 将剩余消息中，role ∈ {'user','assistant'} 的消息索引作为“锚点”
- 定义 depth(i) = 共有多少个锚点索引 >= i（含等号）
  - i > 最后一个锚点 → depth=0
  - 最后一个锚点 ≤ i ≤ 最后一个锚点 → depth=1（即最后一个锚点本身属于 depth=1）
  - 介于倒数第2与最后一个锚点之间（不含倒数第2锚点）→ depth=1
  - 倒数第2锚点本身 → depth=2
  - 以此类推；若没有锚点，则所有消息 depth=0
- 规则字段：
  - min_depth 未提供时默认 0
  - max_depth 未提供时默认“无上限”
"""

from typing import Any, Dict, List, Optional, Tuple
import re
import copy
import bisect


ALLOWED_VIEWS = {"user_view", "assistant_view"}
ROLE_SET = {"user", "assistant", "system"}


def _normalize_rules(rules: Any) -> List[Dict[str, Any]]:
    """
    接受数组或 {rules:[...]} 结构，返回规则数组
    """
    if isinstance(rules, list):
        return [r for r in rules if isinstance(r, dict)]
    if isinstance(rules, dict):
        arr = rules.get("rules")
        if isinstance(arr, list):
            return [r for r in arr if isinstance(r, dict)]
    return []


def _transform_replacement(s: str) -> str:
    """
    将 $1/$2 形式替换为 Python re.sub 支持的 \\g<1> 形式
    """
    if not isinstance(s, str):
        return "" if s is None else str(s)
    return re.sub(r"\$(\d+)", r"\\g<\1>", s)


def _apply_regex_to_text(text: str, find_regex: str, replace_regex: str) -> str:
    """
    对单段文本应用一次 find/replace；不抛异常，失败时返回原文
    """
    try:
        pattern = re.compile(find_regex)
        repl = _transform_replacement(replace_regex)
        return pattern.sub(repl, text)
    except Exception:
        return text


def _is_relative_preset_source(src: Any) -> bool:
    """
    判断来源是否为 relative 预设（仅用于深度锚点过滤）
    - 兼容新枚举：preset.relative
    """
    if not isinstance(src, dict):
        return False
    t = str(src.get("type", "")).lower()
    p = str(src.get("position", "")).lower()
    return t == "preset.relative" or (t.startswith("preset") and p == "relative")


def _compute_depths(messages: List[Dict[str, Any]]) -> List[int]:
    """
    计算每条消息的 depth 值（参见顶部注释）
    """
    n = len(messages)
    if n == 0:
        return []

    # 仅用于锚点计算的过滤（不改变最终输出）
    keep_indices: List[int] = []
    for i, m in enumerate(messages):
        src = m.get("source", {})
        if not _is_relative_preset_source(src):
            keep_indices.append(i)

    # 提取 user/assistant 锚点
    anchors: List[int] = []
    for i in keep_indices:
        role = str(messages[i].get("role", "")).lower()
        if role in ("user", "assistant"):
            anchors.append(i)

    anchors.sort()
    depths: List[int] = [0] * n
    if not anchors:
        # 无锚点 → 所有 depth=0
        return depths

    # depth(i) = 共有多少个锚点索引 >= i
    # 等价：len(anchors) - bisect_left(anchors, i)
    for i in range(n):
        k = bisect.bisect_left(anchors, i)
        depths[i] = len(anchors) - k
    return depths


def _depth_in_range(d: int, min_d: Optional[int], max_d: Optional[int]) -> bool:
    if min_d is None:
        min_d = 0
    if max_d is None:
        return d >= min_d
    return (d >= min_d) and (d <= max_d)


def _matches_targets(msg: Dict[str, Any], targets: Optional[List[str]]) -> bool:
    """
    targets 匹配语义（单字段，仅基于 source.type，不再支持角色匹配）：
    - 精确来源：完整 type 值（如 'preset.in-chat', 'world_book.before_char'）
    - 前缀大类：'preset' | 'world_book' | 'history' | 'char' | 'persona'
      - 命中规则：stype == prefix 或 stype 以 'prefix.' 开头
    - targets 为空或非法 → 视为“全部匹配”
    - 若同时选择前缀大类与其子集，视为命中大类（实现为统一 True）
    """
    if not isinstance(targets, list) or not targets:
        return True

    tset = {str(t).lower() for t in targets if t is not None}
    src = msg.get("source", {}) or {}
    stype = str(src.get("type", "")).lower()

    # 1) 精确来源命中
    if stype in tset:
        return True

    # 2) 前缀大类命中
    PREFIXES = {"preset", "world_book", "history", "char", "persona"}
    for t in tset:
        if t in PREFIXES and (stype == t or stype.startswith(t + ".")):
            return True

    return False


def _filter_rules_by_placement(rules: List[Dict[str, Any]], placement: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in rules:
        try:
            if r.get("enabled") is not True:
                continue
            if str(r.get("placement", "")).lower() != str(placement).lower():
                continue
            if not r.get("find_regex"):
                continue
            # 视图过滤：若 views 非法或为空，则忽略该规则
            views = r.get("views") or []
            if not isinstance(views, list) or not views:
                continue
            if not any(v in ALLOWED_VIEWS for v in views):
                continue
            out.append(r)
        except Exception:
            continue
    return out


def _apply_rules_to_messages(
    messages: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    placement: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    返回 (user_view_messages, assistant_view_messages)
    - 均为对原 messages 的浅拷贝，仅修改 content
    """
    # 基础副本（两套视图）
    user_view_msgs = [dict(m) for m in (messages or [])]
    assistant_view_msgs = [dict(m) for m in (messages or [])]

    # 预计算 depth
    depths = _compute_depths(messages)

    # 过滤规则（placement & enabled & views）
    selected_rules = _filter_rules_by_placement(rules, placement)

    for rule in selected_rules:
        find_regex = str(rule.get("find_regex", ""))
        replace_regex = str(rule.get("replace_regex", ""))
        min_d = rule.get("min_depth", 0)
        try:
            min_d = int(min_d) if min_d is not None else 0
        except Exception:
            min_d = 0
        max_d_raw = rule.get("max_depth", None)
        try:
            max_d = int(max_d_raw) if max_d_raw is not None else None
        except Exception:
            max_d = None

        targets = rule.get("targets", [])
        views = [v for v in (rule.get("views") or []) if v in ALLOWED_VIEWS]

        # 预编译正则一次
        try:
            pattern = re.compile(find_regex)
            repl = _transform_replacement(replace_regex)
        except Exception:
            # 正则非法则忽略此规则
            continue

        for view_name in views:
            view_msgs = user_view_msgs if view_name == "user_view" else assistant_view_msgs
            for idx, m in enumerate(view_msgs):
                try:
                    d = depths[idx] if idx < len(depths) else 0
                    if not _depth_in_range(d, min_d, max_d):
                        continue
                    # 使用原消息（未被修改过的结构）来判定 targets
                    orig_m = messages[idx]
                    if not _matches_targets(orig_m, targets):
                        continue
                    old = m.get("content", "")
                    if not isinstance(old, str):
                        old = "" if old is None else str(old)
                    new_text = pattern.sub(repl, old)
                    if new_text != old:
                        m["content"] = new_text
                except Exception:
                    # 单条出错不影响整体
                    continue

    return user_view_msgs, assistant_view_msgs


def _apply_rules_to_text(
    text: str,
    rules: List[Dict[str, Any]],
    placement: str,
) -> Tuple[str, str]:
    """
    对纯文本按 views 应用规则，返回 (user_view_text, assistant_view_text)
    - 对 text 不考虑 depth/targets
    """
    txt_user = "" if text is None else str(text)
    txt_assist = "" if text is None else str(text)

    selected_rules = _filter_rules_by_placement(rules, placement)

    for rule in selected_rules:
        find_regex = str(rule.get("find_regex", ""))
        replace_regex = str(rule.get("replace_regex", ""))
        views = [v for v in (rule.get("views") or []) if v in ALLOWED_VIEWS]
        try:
            pattern = re.compile(find_regex)
            repl = _transform_replacement(replace_regex)
        except Exception:
            continue
        if "user_view" in views:
            try:
                txt_user = pattern.sub(repl, txt_user)
            except Exception:
                pass
        if "assistant_view" in views:
            try:
                txt_assist = pattern.sub(repl, txt_assist)
            except Exception:
                pass

    return txt_user, txt_assist


def apply_regex(
    rules: Any,
    placement: str,
    messages: Optional[List[Dict[str, Any]]] = None,
    text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    顶层入口
    - placement 必填：'before_macro' | 'after_macro'
    - messages 与 text 二选一；同时提供时优先处理 messages
    - 返回 original + user_view + assistant_view 三套视图
      - messages 输入：各视图包含 {messages:[...]}（原结构保留，仅 content 可能变更）
      - text 输入：各视图包含 {text:"..."}
    """
    placement_norm = str(placement or "").lower()
    if placement_norm not in ("before_macro", "after_macro"):
        raise ValueError("placement 必须为 'before_macro' 或 'after_macro'")

    rule_list = _normalize_rules(rules)

    # 优先处理 messages
    if isinstance(messages, list):
        # 透传原始
        original = [dict(m) for m in messages]
        user_view_msgs, assistant_view_msgs = _apply_rules_to_messages(original, rule_list, placement_norm)
        return {
            "original": {"messages": original},
            "user_view": {"messages": user_view_msgs},
            "assistant_view": {"messages": assistant_view_msgs},
            "placement": placement_norm,
        }

    # 处理 text
    if isinstance(text, str):
        original_text = text
        u, a = _apply_rules_to_text(original_text, rule_list, placement_norm)
        return {
            "original": {"text": original_text},
            "user_view": {"text": u},
            "assistant_view": {"text": a},
            "placement": placement_norm,
        }

    # 二者皆未提供
    raise ValueError("必须提供 messages（数组）或 text（字符串）中的一个")