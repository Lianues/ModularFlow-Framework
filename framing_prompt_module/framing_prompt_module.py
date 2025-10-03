# framing_prompt_module.py
# 模块核心逻辑：从 relative 预设和世界书组装前缀提示词。

from typing import Any, Dict, List, Literal, TypedDict, Optional

from core.function_registry import register_function
from shared.SmartTavern import globals as g
from . import variables as v

# --- 类型定义 ---

class ConstructedMessage(TypedDict):
    """构造上下文中消息部分的统一格式。"""
    role: Literal["user", "assistant", "system"]
    content: str
    source_type: str
    source_id: str

# --- 核心函数 ---

@register_function(name="framing.assemble", outputs=["prefix_prompt"])
def assemble(
    triggered_wb_ids: List[int],
) -> Dict[str, Any]:
    """
    组装提示词的前缀部分，包括 relative 预设、
    角色/用户描述以及特定的世界书条目。
    """
    all_sources = _collect_prefix_sources()
    
    sorted_sources = _sort_by_order_rules(all_sources)
    
    prefix_prompt = _build_prefix_prompt(sorted_sources, set(triggered_wb_ids))
    
    return {"prefix_prompt": prefix_prompt}

# --- 辅助函数 ---

def _collect_prefix_sources() -> List[Dict[str, Any]]:
    """从全局变量中收集所有 'relative' 预设。"""
    sources = []
    # 修复：从 g.preset.prompts 读取预设配置，而不是 g.presets
    preset_prompts = []
    if hasattr(g, 'preset') and g.preset and 'prompts' in g.preset:
        preset_prompts = g.preset['prompts']
    
    for i, p in enumerate(preset_prompts):
        if p.get("position") == "relative":
            sources.append({
                "data": p,
                "type": "preset",
                "order": p.get("order", v.DEFAULT_ORDER),
                "role": p.get("role", v.DEFAULT_ROLE),
                "internal_order": i
            })
    return sources

def _sort_by_order_rules(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """根据 order、role 和内部顺序对条目进行排序。"""
    def sort_key(entry):
        order = entry.get("order", v.DEFAULT_ORDER)
        role = entry.get("role", v.DEFAULT_ROLE)
        internal_order = entry.get("internal_order", 0)
        
        # 排序规则: order (升序), role (assistant > user > system), internal_order (升序)
        return (order, _get_role_priority(role), internal_order)
    
    return sorted(entries, key=sort_key)

def _build_prefix_prompt(sorted_sources: List[Dict[str, Any]], triggered_ids: set[int]) -> List[ConstructedMessage]:
    """构建最终的消息列表，处理占位符。"""
    final_prompt = []
    for source in sorted_sources:
        item = source["data"]
        
        # 动态 enabled 判断 (如果未来需要)
        if not item.get("enabled", True):
            continue

        identifier = item.get("identifier", "")
        
        # --- 处理占位符 ---
        if identifier == "worldInfoBefore":
            final_prompt.extend(_get_world_info_messages("before_char", triggered_ids))
        elif identifier == "worldInfoAfter":
            final_prompt.extend(_get_world_info_messages("after_char", triggered_ids))
        elif identifier == "charDescription":
            # 修复：从 g.character 读取角色描述
            character_content = ""
            if hasattr(g, 'character') and g.character:
                character_content = g.character.get("description", "")
            elif hasattr(g, 'character_data') and g.character_data:
                character_content = g.character_data.get("description", "")
            
            if character_content.strip():
                final_prompt.append({
                    "role": source["role"],
                    "content": character_content,
                    "source_type": "character",
                    "source_id": "char_description"
                })
        elif identifier == "personaDescription":
            # 修复：从 g.persona 读取用户角色描述
            persona_content = ""
            if hasattr(g, 'persona') and g.persona:
                persona_content = g.persona.get("description", "")
            elif hasattr(g, 'persona_data') and g.persona_data:
                persona_content = g.persona_data.get("description", "")
                
            if persona_content.strip():
                final_prompt.append({
                    "role": source["role"],
                    "content": persona_content,
                    "source_type": "persona",
                    "source_id": "persona_description"
                })
        elif identifier == "chatHistory":
            # chatHistory 占位符在此模块中被忽略，由 in_chat_constructor_module 处理
            continue
        else:
            # --- 处理普通 relative 预设 ---
            content = item.get("content", "")
            if content.strip():
                final_prompt.append({
                    "role": source["role"],
                    "content": content,
                    "source_type": "preset",
                    "source_id": f"preset_{item.get('name', 'untitled')}"
                })
                
    return final_prompt

def _get_world_info_messages(position: str, triggered_ids: set[int]) -> List[ConstructedMessage]:
    """
    获取特定位置的、经过排序和过滤的世界书条目，
    并将每个条目作为单独的 ConstructedMessage 返回。
    """
    wb_sources = []
    
    # 修复：从所有可能的源获取世界书条目（需要处理嵌套数组结构）
    world_book_entries = []
    
    # 从独立世界书文件（需要处理嵌套数组结构）
    if hasattr(g, 'world_book_files') and g.world_book_files:
        for wb_item in g.world_book_files:
            if isinstance(wb_item, list):
                # 处理嵌套数组结构 [[{...}, {...}]]
                for nested_item in wb_item:
                    if isinstance(nested_item, dict):
                        world_book_entries.append(nested_item)
            elif isinstance(wb_item, dict):
                # 直接的字典条目
                world_book_entries.append(wb_item)
    elif hasattr(g, 'world_book_entries') and g.world_book_entries:
        for wb_item in g.world_book_entries:
            if isinstance(wb_item, list):
                # 处理嵌套数组结构
                for nested_item in wb_item:
                    if isinstance(nested_item, dict):
                        world_book_entries.append(nested_item)
            elif isinstance(wb_item, dict):
                # 直接的字典条目
                world_book_entries.append(wb_item)
    
    # 从角色卡中的世界书条目
    if hasattr(g, 'character') and g.character and 'world_book' in g.character:
        character_wb = g.character['world_book']
        if isinstance(character_wb, dict) and 'entries' in character_wb:
            character_entries = character_wb['entries']
            if isinstance(character_entries, list):
                for entry in character_entries:
                    if isinstance(entry, dict):
                        world_book_entries.append(entry)
    
    for i, wb in enumerate(world_book_entries):
        # 工作流已经处理了 enabled 和触发逻辑，这里只负责匹配
        if wb.get("id") in triggered_ids and wb.get("position") == position:
            wb_sources.append({
                "data": wb,
                "type": "world",
                "order": wb.get("order", v.DEFAULT_ORDER),
                "role": _map_wb_pos_to_role(wb.get("position", "system")),
                "internal_order": i
            })
    
    sorted_wbs = _sort_by_order_rules(wb_sources)
    
    messages = []
    for source in sorted_wbs:
        wb = source["data"]
        content = wb.get("content", "")
        if content.strip():
            messages.append({
                "role": source["role"],
                "content": content,
                "source_type": "world_book",
                "source_id": f"wb_{wb.get('id', -1)}"
            })
            
    return messages

def _get_role_priority(role: str) -> int:
    """获取角色的排序优先级。"""
    role_priority = {"assistant": 0, "user": 1, "system": 2}
    return role_priority.get(str(role), 2)

def _map_wb_pos_to_role(position: str) -> str:
    """将世界书的 position 映射到消息角色。"""
    # before_char 和 after_char 通常是系统级指令
    return "system"