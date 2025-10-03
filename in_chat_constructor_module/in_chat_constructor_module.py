# in_chat_constructor_module.py
# 模块核心逻辑：从多个来源组装和排序对话内部的上下文。

from typing import Any, Dict, List, Literal, TypedDict, Optional
from collections import defaultdict

from core.function_registry import register_function
from shared.SmartTavern import globals as g
from . import variables as v

# --- 类型定义 ---

class HistoryMessage(TypedDict):
    """一条来自聊天历史的消息。"""
    role: Literal["user", "assistant", "system"]
    content: str

class InChatPreset(TypedDict):
    """代表一个预设提示词条目，用于混入聊天记录。"""
    name: Optional[str] # 用于来源识别
    content: str
    role: Literal["user", "assistant", "system"]
    depth: Optional[int]
    order: Optional[int]
    enabled: bool

class WorldBookEntry(TypedDict):
    """代表一个可以注入到上下文中的世界书条目。"""
    id: int
    name: Optional[str] # 用于来源识别
    content: str
    mode: Literal["always", "conditional"]
    position: str # 映射到角色
    depth: Optional[int]
    order: Optional[int]
    enabled: bool

# --- 核心函数 ---

@register_function(name="in_chat.construct", outputs=["context"])
def construct(
    history: List[HistoryMessage],
    triggered_wb_ids: List[int],
) -> Dict[str, Any]:
    """
    通过注入对话内预设和世界书条目来构造聊天历史。
    此版本不会合并消息，并为每个条目添加来源标识符。
    它从 shared.globals 读取预设和世界书。
    """
    # 1. 从全局变量中收集并过滤所有非历史记录的来源
    other_sources = _collect_other_sources(set(triggered_wb_ids))
    
    enabled_sources = [
        s for s in other_sources if s["data"].get("enabled", True)
    ]

    # 2. 根据规则对这些来源进行排序
    sorted_sources = _sort_by_order_rules(enabled_sources)

    # 3. 基于 depth 将排序后的来源注入到历史记录中
    constructed_list = []
    for i, msg in enumerate(history):
        role = msg["role"]
        source_type = 'user' if role == 'user' else 'assistant' if role == 'assistant' else 'system'
        constructed_list.append({
            "role": role,
            "content": msg["content"],
            "source_type": source_type,
            "source_id": f"history_{i}"
        })

    depth_groups = defaultdict(list)
    for source in sorted_sources:
        depth = source.get("depth", v.DEFAULT_DEPTH) or v.DEFAULT_DEPTH
        depth_groups[depth].append(source)
        
    for depth in sorted(depth_groups.keys(), reverse=True):
        insertion_index = len(constructed_list) - depth
        if insertion_index < 0:
            insertion_index = 0
        
        for source in reversed(depth_groups[depth]):
            source_type_val = source["type"]
            source_data = source["data"]
            source_id = f"preset_{source_data.get('name', 'untitled')}" if source_type_val == "preset" else f"wb_{source_data.get('id', -1)}"
            
            # 直接在这里确定最终的 source_type
            final_source_type = 'world_book' if source_type_val == 'world' else source_type_val

            message = {
                "role": source["role"],
                "content": source_data["content"],
                "source_type": final_source_type,
                "source_id": source_id
            }
            constructed_list.insert(insertion_index, message)

    return {"context": constructed_list}


# --- 辅助函数 ---

def _collect_other_sources(triggered_ids: set[int]) -> List[Dict[str, Any]]:
    """从全局变量中收集并准备除聊天历史外的所有来源。"""
    sources = []
    
    # 1. 从全局变量中收集 'in-chat' 预设
    preset_prompts = []
    if hasattr(g, 'preset') and g.preset and 'prompts' in g.preset:
        preset_prompts = g.preset['prompts']
    
    for i, p in enumerate(preset_prompts):
        if p.get("position") != "in-chat":
            continue
        sources.append({
            "data": p,
            "type": "preset",
            "depth": p.get("depth", v.DEFAULT_DEPTH),
            "order": p.get("order", v.DEFAULT_ORDER),
            "role": p.get("role", "user"),
            "internal_order": i
        })

    # 2. 从全局变量中收集相关的世界书条目
    world_book_entries = []
    if hasattr(g, 'world_book_files') and isinstance(g.world_book_files, list):
        # 处理可能的嵌套数组结构 [[{...}]]
        for wb_item in g.world_book_files:
            if isinstance(wb_item, list):
                world_book_entries.extend(wb_item)
            elif isinstance(wb_item, dict):
                world_book_entries.append(wb_item)
    
    for i, wb in enumerate(world_book_entries):
        if not isinstance(wb, dict):
            continue
            
        if wb.get("position") in ["before_char", "after_char"]:
            continue
            
        if wb.get("mode") == 'always' or (wb.get("mode") == 'conditional' and wb.get("id") in triggered_ids):
            sources.append({
                "data": wb,
                "type": "world",
                "depth": wb.get("depth", v.DEFAULT_DEPTH),
                "order": wb.get("order", v.DEFAULT_ORDER),
                "role": _map_wb_pos_to_role(wb.get("position", "system")),
                "internal_order": len(preset_prompts) + i
            })
            
    return sources

def _sort_by_order_rules(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据 order、role 和内部顺序对条目进行排序。"""
    def sort_key(entry):
        order = entry.get("order", v.DEFAULT_ORDER) or v.DEFAULT_ORDER
        role = entry.get("role", "system")
        internal_order = entry.get("internal_order", 0)
        
        return (order, _get_role_priority(role), internal_order)
    
    return sorted(entries, key=sort_key)

def _get_role_priority(role: str) -> int:
    """获取角色的排序优先级。"""
    role_priority = {"assistant": 0, "user": 1, "system": 2}
    return role_priority.get(str(role), 2)

def _map_wb_pos_to_role(position: str) -> str:
    """将世界书的 position 映射到消息角色。"""
    return "assistant" if position == "assistant" else "user" if position == "user" else "system"
