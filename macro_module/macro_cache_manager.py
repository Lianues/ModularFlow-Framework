#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
宏缓存管理器 (Macro Cache Manager)

负责宏处理结果的持久化加载和保存，以及缓存相关的哈希计算。
"""

import os
import json
import hashlib
from typing import Dict, Any, List

# 缓存文件路径
MACRO_CACHE_FILE = "shared/SmartTavern/cache/macro_cache.json"


class MacroCacheManager:
    """宏缓存管理器类，负责缓存的加载、保存和哈希计算"""
    
    def __init__(self):
        pass
    
    def load_cache(self) -> Dict[str, Any]:
        """从文件加载宏缓存"""
        try:
            if os.path.exists(MACRO_CACHE_FILE):
                with open(MACRO_CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    return cache_data
            else:
                return {"entries": []}
        except Exception as e:
            print(f"⚠️ 加载宏缓存失败: {e}")
            return {"entries": []}

    def save_cache(self, cache_data: Dict[str, Any]):
        """将宏缓存保存到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(MACRO_CACHE_FILE), exist_ok=True)
            
            with open(MACRO_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"⚠️ 保存宏缓存失败: {e}")
    
    def get_message_hash(self, message: Dict[str, Any]) -> str:
        """计算消息内容的稳定哈希值"""
        # 对整个消息字典进行哈希，以确保任何变化都能被捕捉到
        # sort_keys=True 确保了键的顺序不会影响最终的哈希值
        message_string = json.dumps(message, sort_keys=True)
        return hashlib.sha256(message_string.encode('utf-8')).hexdigest()

    def get_state_hash(self, state: Dict[str, Dict[str, Any]]) -> str:
        """计算当前沙盒状态的稳定哈希值，排除时间相关的不稳定变量"""
        # 排除时间相关的不稳定变量
        time_related_vars = {'time', 'date', 'weekday', 'isotime', 'isodate'}
        
        filtered_state = {}
        for scope_name, scope_vars in state.items():
            if isinstance(scope_vars, dict):
                # 创建副本，排除时间相关变量
                filtered_vars = {k: v for k, v in scope_vars.items() if k not in time_related_vars}
                filtered_state[scope_name] = filtered_vars
            else:
                filtered_state[scope_name] = scope_vars
        
        state_string = json.dumps(filtered_state, sort_keys=True)
        return hashlib.sha256(state_string.encode('utf-8')).hexdigest()
    
    def process_messages_with_cache(self, messages: List[Dict[str, Any]], processor_callback) -> List[Dict[str, Any]]:
        """
        使用缓存机制处理消息列表
        
        Args:
            messages: 待处理的消息列表
            processor_callback: 处理器回调函数，用于实际处理消息
            
        Returns:
            处理后的消息列表
        """
        if not messages:
            return []

        # 从文件加载缓存
        file_cache = self.load_cache()
        cached_entries = file_cache.get("entries", [])
        
        new_cache_entries = []
        processed_messages = []

        cache_pointer = 0
        for i, msg in enumerate(messages):
            msg_hash = self.get_message_hash(msg)
            
            # 获取当前状态哈希（通过回调获取）
            start_state_hash = processor_callback('get_state_hash')

            # 尝试在缓存中找到匹配项
            cache_hit = None
            if cache_pointer < len(cached_entries):
                entry = cached_entries[cache_pointer]
                cached_msg_hash = entry.get("raw_message_hash", "")
                cached_state_hash = entry.get("start_state_hash", "")
                
                if cached_msg_hash == msg_hash and cached_state_hash == start_state_hash:
                    cache_hit = entry

            if cache_hit:
                # --- 缓存命中 ---
                processed_msg = cache_hit["processed_message"]
                end_state = cache_hit.get("end_state_snapshot")

                if processed_msg is not None:
                    processed_messages.append(processed_msg)
                
                if end_state:
                    processor_callback('set_state', end_state)
                
                new_cache_entries.append(cache_hit)
                cache_pointer += 1
            else:
                # --- 缓存未命中 ---
                try:
                    processed_msg = processor_callback('process_message', msg)
                    
                    if processed_msg is not None:
                        processed_messages.append(processed_msg)
                        
                        # 创建新的缓存条目
                        new_cache_entry = {
                            "raw_message_hash": msg_hash,
                            "start_state_hash": start_state_hash,
                            "processed_message": processed_msg,
                            "end_state_snapshot": processor_callback('get_state')
                        }
                        new_cache_entries.append(new_cache_entry)

                except Exception as e:
                    print(f"⚠️ 处理消息时出错: {e}")
                    import traceback
                    print(f"⚠️ 完整错误堆栈: {traceback.format_exc()}")
                    processed_messages.append(msg.copy())
                
                cache_pointer += 1

        # 更新文件缓存
        new_cache_data = {"entries": new_cache_entries}
        self.save_cache(new_cache_data)
        
        return processed_messages


# 向后兼容的全局函数
def load_macro_cache() -> Dict[str, Any]:
    """从文件加载宏缓存（向后兼容）"""
    manager = MacroCacheManager()
    return manager.load_cache()


def save_macro_cache(cache_data: Dict[str, Any]):
    """将宏缓存保存到文件（向后兼容）"""
    manager = MacroCacheManager()
    manager.save_cache(cache_data)


# 创建全局实例
_cache_manager_instance = None

def get_cache_manager() -> MacroCacheManager:
    """获取缓存管理器单例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = MacroCacheManager()
    return _cache_manager_instance