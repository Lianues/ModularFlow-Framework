#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一宏处理器 (Unified Macro Processor)

解决宏处理与变量作用域的核心问题：
- 统一处理传统宏和Python宏
- 真正的作用域感知处理
- 按上下文顺序单遍执行
- 支持前缀变量访问

设计原则：
1. 所有宏都通过Python沙盒执行，确保作用域一致性
2. 传统宏在运行时自动转换为Python代码
3. 支持前缀变量访问（world_var → world作用域）
4. 单遍处理，按injection_order执行
"""

import re
import json
import random
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass

# 模块化依赖
from modules.SmartTavern.python_sandbox_module.python_sandbox_module import PythonSandbox, get_sandbox_instance
from .macro_cache_manager import get_cache_manager
from .legacy_macro_converter import get_legacy_converter

from core.function_registry import register_function
from core.services import get_current_globals
from . import variables as v


@dataclass
class MacroExecutionContext:
    """宏执行上下文"""
    current_scope: str = 'temp'  # 当前执行作用域
    character_data: Dict[str, Any] = None
    persona_data: Dict[str, Any] = None
    chat_history: List[Any] = None
    user_input: str = ""
    current_time: datetime = None
    
    def __post_init__(self):
        if self.character_data is None:
            self.character_data = {}
        if self.persona_data is None:
            self.persona_data = {}
        if self.chat_history is None:
            self.chat_history = []
        if self.current_time is None:
            self.current_time = datetime.now()


class UnifiedMacroProcessor:
    """
    统一宏处理器
    
    核心特性：
    1. 统一处理：所有宏都通过Python沙盒执行
    2. 作用域感知：自动检测和应用正确的作用域
    3. 前缀变量：支持 world_var, preset_var 等跨作用域访问
    4. 单遍处理：按顺序逐个处理，确保依赖关系正确
    """
    
    def __init__(self, context: MacroExecutionContext = None):
        self.context = context or MacroExecutionContext()
        self.sandbox = get_sandbox_instance()
        self.legacy_converter = get_legacy_converter()
        self.cache_manager = get_cache_manager()
        self._init_sandbox()
    
    def _init_sandbox(self):
        """初始化Python沙盒"""
        if not self.sandbox:
            print("⚠️ Python沙盒不可用，宏功能受限")
            return
            
        try:
            self._inject_unified_functions()
            self._inject_context_variables()
        except Exception as e:
            print(f"⚠️ 沙盒初始化失败: {e}")
            self.sandbox = None
    
    
    def _inject_unified_functions(self):
        """注入统一的宏函数到沙盒"""
        if not self.sandbox:
            return
            
        # 注入传统宏兼容函数（简化版本，避免import问题）
        compatibility_code = '''
# 作用域感知的变量操作函数
def unified_getvar(name, default=""):
    """统一的作用域感知变量获取"""
    # 检查前缀，确定目标作用域
    if name.startswith('world_'):
        var_name = name[6:]  # 移除 'world_' 前缀
        return world_vars.get(var_name, default)
    elif name.startswith('preset_'):
        var_name = name[7:]  # 移除 'preset_' 前缀
        return preset_vars.get(var_name, default)
    elif name.startswith('char_') or name.startswith('character_'):
        prefix_len = 5 if name.startswith('char_') else 10
        var_name = name[prefix_len:]
        return char_vars.get(var_name, default)
    elif name.startswith('conv_') or name.startswith('conversation_'):
        prefix_len = 5 if name.startswith('conv_') else 13
        var_name = name[prefix_len:]
        return conversation_vars.get(var_name, default)
    elif name.startswith('global_'):
        var_name = name[7:]  # 移除 'global_' 前缀
        return global_vars.get(var_name, default)
    else:
        # 无前缀，使用当前作用域
        current_scope = globals().get('_current_scope', 'temp')
        if current_scope == 'world':
            return world_vars.get(name, default)
        elif current_scope == 'preset':
            return preset_vars.get(name, default)
        elif current_scope == 'char':
            return char_vars.get(name, default)
        elif current_scope == 'conversation':
            return conversation_vars.get(name, default)
        else:
            return temp_vars.get(name, default)

def unified_setvar(name, value):
    """统一的作用域感知变量设置"""
    # 检查前缀，确定目标作用域
    if name.startswith('world_'):
        var_name = name[6:]
        world_vars[var_name] = value
    elif name.startswith('preset_'):
        var_name = name[7:]
        preset_vars[var_name] = value
    elif name.startswith('char_') or name.startswith('character_'):
        prefix_len = 5 if name.startswith('char_') else 10
        var_name = name[prefix_len:]
        char_vars[var_name] = value
    elif name.startswith('conv_') or name.startswith('conversation_'):
        prefix_len = 5 if name.startswith('conv_') else 13
        var_name = name[prefix_len:]
        conversation_vars[var_name] = value
    elif name.startswith('global_'):
        var_name = name[7:]
        global_vars[var_name] = value
    else:
        # 无前缀，使用当前作用域
        current_scope = globals().get('_current_scope', 'temp')
        if current_scope == 'world':
            world_vars[name] = value
        elif current_scope == 'preset':
            preset_vars[name] = value
        elif current_scope == 'char':
            char_vars[name] = value
        elif current_scope == 'conversation':
            conversation_vars[name] = value
        else:
            temp_vars[name] = value
    return ""

# 将函数注册到全局命名空间
getvar = unified_getvar
setvar = unified_setvar

# 向后兼容的全局变量操作
getglobalvar = lambda name, default="": global_vars.get(name, default)
setglobalvar = lambda name, value: global_vars.update({name: value}) or ""
'''
        
        result = self.sandbox.execute_code(compatibility_code, scope_type='global')
        if not result.success:
            print(f"⚠️ 统一函数注入失败: {result.error}")
    
    def _inject_context_variables(self):
        """注入上下文变量到沙盒"""
        if not self.sandbox:
            return
        
        # 构建上下文变量
        context_vars = {
            # 角色信息
            'char': self.context.character_data.get('name', ''),
            'description': self.context.character_data.get('description', ''),
            'personality': self.context.character_data.get('personality', ''),
            'scenario': self.context.character_data.get('scenario', ''),
            'user': self.context.persona_data.get('name', 'User'),
            'persona': self._get_persona_description(),
            
            # 时间相关
            'time': self.context.current_time.strftime('%H:%M:%S'),
            'date': self.context.current_time.strftime('%Y-%m-%d'),
            'weekday': self._get_weekday_chinese(),
            'isotime': self.context.current_time.strftime('%H:%M:%S'),
            'isodate': self.context.current_time.strftime('%Y-%m-%d'),
            
            # 聊天信息
            'input': self.context.user_input,
            'lastMessage': self._get_last_message(),
            'lastUserMessage': self._get_last_user_message(),
            'lastCharMessage': self._get_last_char_message(),
            'messageCount': str(len(self.context.chat_history)),
            'userMessageCount': str(self._count_user_messages()),
            'conversationLength': str(self._get_conversation_length()),
            
            # 保留变量
            'enable': True,
        }
        
        # 注入到临时作用域
        for name, value in context_vars.items():
            # 对字符串进行JSON编码，以安全地处理换行符和引号
            if isinstance(value, str):
                # 使用json.dumps来创建安全的、带引号的字符串表示
                # 然后在沙盒中，这个字符串会被Python解释器正确解析
                safe_value = json.dumps(value)
                self.sandbox.scope_manager.temp_vars[name] = value
            else:
                self.sandbox.scope_manager.temp_vars[name] = value
    
    def _get_persona_description(self) -> str:
        """获取玩家角色描述"""
        if not self.context.persona_data:
            return ""
        
        parts = []
        if "description" in self.context.persona_data:
            parts.append(self.context.persona_data["description"])
        if "personality" in self.context.persona_data:
            parts.append(f"性格: {self.context.persona_data['personality']}")
        
        return " ".join(parts)
    
    def _get_weekday_chinese(self) -> str:
        """获取中文星期"""
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[self.context.current_time.weekday()]
    
    def _get_last_message(self) -> str:
        """获取最后一条消息"""
        if not self.context.chat_history:
            return ""
        last_msg = self.context.chat_history[-1]
        if hasattr(last_msg, 'content'):
            return last_msg.content
        elif isinstance(last_msg, dict):
            return last_msg.get('content', '')
        return str(last_msg)
    
    def _get_last_user_message(self) -> str:
        """获取最后一条用户消息"""
        for msg in reversed(self.context.chat_history):
            if hasattr(msg, 'role'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                if role == 'user':
                    return msg.content
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                return msg.get('content', '')
        return ""
    
    def _get_last_char_message(self) -> str:
        """获取最后一条角色消息"""
        for msg in reversed(self.context.chat_history):
            if hasattr(msg, 'role'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                if role == 'assistant':
                    return msg.content
            elif isinstance(msg, dict) and msg.get('role') == 'assistant':
                return msg.get('content', '')
        return ""
    
    def _count_user_messages(self) -> int:
        """统计用户消息数量"""
        count = 0
        for msg in self.context.chat_history:
            if hasattr(msg, 'role'):
                role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
                if role == 'user':
                    count += 1
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                count += 1
        return count
    
    def _get_conversation_length(self) -> int:
        """计算对话总长度"""
        length = 0
        for msg in self.context.chat_history:
            if hasattr(msg, 'content'):
                length += len(msg.content)
            elif isinstance(msg, dict):
                length += len(msg.get('content', ''))
            else:
                length += len(str(msg))
        return length
    
    def process_content(self, content: str, scope_type: str = 'temp') -> str:
        """
        统一处理内容中的所有宏
        
        Args:
            content: 待处理的内容
            scope_type: 当前作用域类型
            
        Returns:
            处理后的内容
        """
        if not content or "{{" not in content:
            return content
        
        if not self.sandbox:
            return content  # 沙盒不可用时返回原内容
        
        # 设置当前作用域
        self.sandbox.execute_code(f"globals()['_current_scope'] = '{scope_type}'", scope_type='global')
        
        try:
            result = self._process_all_macros(content, scope_type)
            return result
        except Exception as e:
            print(f"⚠️ 宏处理失败: {e}")
            import traceback
            print(f"⚠️ 完整错误堆栈: {traceback.format_exc()}")
            return content
    
    def _process_all_macros(self, content: str, scope_type: str) -> str:
        """处理所有宏：统一转换和执行"""
        result_content = content
        
        # 查找所有宏
        macro_pattern = r'\{\{([^{}]*)\}\}'
        macros_found = re.findall(macro_pattern, result_content)
        
        if not macros_found:
            return result_content
        
        # 逐个处理宏
        for i, macro_content in enumerate(macros_found):
            full_macro = f"{{{{{macro_content}}}}}"
            
            try:
                # 转换并执行宏
                replacement = self._execute_single_macro(macro_content.strip(), scope_type)
                
                # 替换宏为结果（只替换第一个匹配，避免重复替换）
                result_content = result_content.replace(full_macro, str(replacement), 1)
                
            except Exception as e:
                print(f"⚠️ 宏 '{full_macro}' 处理失败: {e}")
                import traceback
                print(f"⚠️ 完整错误堆栈: {traceback.format_exc()}")
                # 失败时保持原样
                pass
        
        final_result = self._clean_macro_artifacts(result_content)
        return final_result
    
    def _execute_single_macro(self, macro_content: str, scope_type: str) -> str:
        """执行单个宏"""
        if not macro_content:
            return ""
        
        # 1. 处理Python宏
        if macro_content.startswith('python:'):
            python_code = macro_content[7:]  # 移除 'python:' 前缀
            
            if not self.sandbox:
                return ""
                
            result = self.sandbox.execute_code(python_code, scope_type=scope_type)
            
            final_result = str(result.result) if result.success and result.result is not None else ""
            return final_result
        
        # 2. 处理传统宏
        traditional_result = self.legacy_converter.execute_traditional_macro(macro_content, scope_type, self.sandbox)
        return traditional_result
    
    
    def _clean_macro_artifacts(self, content: str) -> str:
        """清理宏处理后的空白和格式问题"""
        if not content:
            return ""
        
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = not line.strip()
            if is_empty and prev_empty:
                continue  # 跳过连续的空行
            cleaned_lines.append(line)
            prev_empty = is_empty
        
        # 移除开头和结尾的空行
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def update_context(self, **kwargs):
        """更新执行上下文"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        
        # 重新注入上下文变量
        self._inject_context_variables()
    
    def get_all_variables(self) -> Dict[str, Dict[str, Any]]:
        """获取所有作用域的变量状态"""
        if not self.sandbox:
            return {}
        
        return {
            "preset": dict(self.sandbox.scope_manager.preset_vars),
            "char": dict(self.sandbox.scope_manager.char_vars),
            "world": dict(self.sandbox.scope_manager.world_vars),
            "conversation": dict(self.sandbox.scope_manager.conversation_vars),
            "global": dict(self.sandbox.scope_manager.global_vars),
            "temp": dict(self.sandbox.scope_manager.temp_vars),
        }

    def set_all_variables(self, state: Dict[str, Dict[str, Any]]):
        """设置所有作用域的变量状态"""
        if not self.sandbox:
            return
        
        self.sandbox.scope_manager.preset_vars = state.get("preset", {})
        self.sandbox.scope_manager.char_vars = state.get("char", {})
        self.sandbox.scope_manager.world_vars = state.get("world", {})
        self.sandbox.scope_manager.conversation_vars = state.get("conversation", {})
        self.sandbox.scope_manager.global_vars = state.get("global", {})
        self.sandbox.scope_manager.temp_vars = state.get("temp", {})
    
    def execute_code_block(self, code: str, scope_type: str = 'temp') -> Dict[str, Any]:
        """执行代码块"""
        if not self.sandbox:
            return {"success": False, "error": "沙盒不可用"}
        
        # 设置当前作用域
        self.sandbox.execute_code(f"globals()['_current_scope'] = '{scope_type}'", scope_type='global')
        
        result = self.sandbox.execute_code(code, scope_type=scope_type)
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error
        }
    

    def process_messages_sequentially(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按上下文顺序增量处理消息列表中的宏，并使用更智能的状态感知缓存。
        """
        if not messages:
            return []

        # 重置沙盒状态以开始新的处理流程
        self.sandbox.scope_manager.reset_all_scopes()
        self._init_sandbox()

        # 使用缓存管理器处理消息
        def processor_callback(action, *args):
            if action == 'get_state_hash':
                return self.cache_manager.get_state_hash(self.get_all_variables())
            elif action == 'set_state':
                self.set_all_variables(args[0])
            elif action == 'get_state':
                return self.get_all_variables()
            elif action == 'process_message':
                msg = args[0]
                scope_type = self._determine_message_scope(msg)
                return self._process_single_message(msg, scope_type)
            
        processed_messages = self.cache_manager.process_messages_with_cache(messages, processor_callback)
        
        # 同时更新内存缓存（保持向后兼容）
        g = get_current_globals()
        file_cache = self.cache_manager.load_cache()
        g.macro_cache = file_cache
        
        print(f"🔍 [宏模块调试] 处理完成，共生成 {len(processed_messages)} 条处理后的消息")
        return processed_messages
    
    def _determine_message_scope(self, message: Dict[str, Any]) -> str:
        """
        根据消息的来源类型确定作用域
        
        Args:
            message: 消息对象，可能包含 _source_types 字段
            
        Returns:
            作用域类型字符串
        """
        source_types = message.get('_source_types', [])
        
        # 按优先级确定作用域
        if 'preset' in source_types:
            return 'preset'
        elif 'world' in source_types:
            return 'world'
        elif 'conversation' in source_types:
            return 'conversation'
        elif 'character' in source_types:
            return 'char'
        else:
            return 'temp'  # 默认作用域
    
    def _process_single_message(self, message: Dict[str, Any], scope_type: str) -> Dict[str, Any]:
        """
        处理单个消息的宏和代码块
        
        严格按照文档规定的执行顺序：
        - Step 1: enabled评估 - 使用当前最新的变量状态评估
        - Step 2: code_block执行 - 如果enabled为true，执行代码块
        - Step 3: content处理 - 处理传统宏、Python宏等
        - Step 4: 变量状态更新 - 共享沙盒自动实现，后续词条可见最新状态
        """
        processed_msg = message.copy()
        
        # Step 1: enabled评估 - 使用当前最新的变量状态评估
        enabled = message.get('enabled', True)
        
        if enabled != True and enabled != False:
            # enabled 是宏表达式，需要计算
            try:
                enabled_result = self._evaluate_enabled_expression(enabled, scope_type)
                if not enabled_result:
                    # enabled 为 false，跳过这个消息
                    return None
            except Exception as e:
                print(f"⚠️ enabled 字段计算失败: {e}")
                # 计算失败时默认启用
                pass
        elif enabled == False:
            # 明确禁用的消息
            return None
        
        # Step 2: code_block执行 - 如果enabled为true，执行代码块
        if 'code_block' in message and message['code_block']:
            try:
                code_result = self.execute_code_block(message['code_block'], scope_type)
                if not code_result['success']:
                    print(f"⚠️ 代码块执行失败: {code_result['error']}")
            except Exception as e:
                print(f"⚠️ 代码块执行异常: {e}")
        
        # Step 3: content处理 - 处理传统宏、Python宏等
        if 'content' in processed_msg:
            processed_msg['content'] = self.process_content(processed_msg['content'], scope_type)
        
        # Step 4: 变量状态更新 - 在共享沙盒中自动完成
        # 所有的变量修改都已经实时反映到沙盒状态中，后续词条可以立即看到最新状态
        
        return processed_msg
    
    def _evaluate_enabled_expression(self, enabled_expr: Union[str, bool], scope_type: str) -> bool:
        """
        计算 enabled 表达式的值
        
        支持的格式：
        - 布尔值: True/False
        - 宏表达式: "{{getvar('ready')}}"
        - Python表达式: "{{python:getvar('ready') == 'true'}}"
        - 简化Python: "getvar('ready') == 'true'"
        """
        if isinstance(enabled_expr, bool):
            return enabled_expr
        
        if not isinstance(enabled_expr, str):
            return True  # 默认启用
        
        # 如果包含宏，先处理宏
        if '{{' in enabled_expr:
            processed_expr = self.process_content(enabled_expr, scope_type)
        else:
            processed_expr = enabled_expr
        
        # 尝试作为Python表达式计算
        try:
            # 如果不是明显的Python代码，包装成表达式
            if not any(keyword in processed_expr for keyword in ['and', 'or', 'not', '==', '!=', '>', '<', 'getvar', 'True', 'False']):
                # 简单的变量名或值，尝试直接获取
                python_code = f"result = bool(getvar('{processed_expr}'))"
            else:
                # 复杂表达式，直接计算
                python_code = f"result = bool({processed_expr})"
            
            exec_result = self.sandbox.execute_code(python_code, scope_type=scope_type)
            if exec_result.success:
                return bool(exec_result.result)
            else:
                print(f"⚠️ enabled 表达式计算失败: {exec_result.error}")
                return True  # 默认启用
                
        except Exception as e:
            print(f"⚠️ enabled 表达式处理异常: {e}")
            return True  # 默认启用


# --- 模块集成 ---

# 创建一个单例的宏处理器实例
_macro_processor_instance = None

def get_macro_processor() -> UnifiedMacroProcessor:
    """获取宏处理器单例"""
    global _macro_processor_instance
    if _macro_processor_instance is None:
        # 这里的上下文可以从全局变量或配置中初始化
        context = MacroExecutionContext()
        _macro_processor_instance = UnifiedMacroProcessor(context)
    return _macro_processor_instance

@register_function(name="process_text_macros", outputs=["processed_text"])
def process_text_macros(text: str, scope_type: str = 'temp', context_data: Dict[str, Any] = None):
    """
    处理单个文本字符串中的所有宏。
    """
    if not v.ENABLE_MACRO_PROCESSING:
        return {"processed_text": text}

    processor = get_macro_processor()
    
    # 更新上下文
    if context_data:
        processor.update_context(**context_data)

    v.macros_processed_count += text.count("{{")
    processed_text = processor.process_content(text, scope_type)
    return {"processed_text": processed_text}

@register_function(name="process_message_sequence_macros", outputs=["processed_messages"])
def process_message_sequence_macros(messages: List[Dict[str, Any]], context_data: Dict[str, Any] = None):
    """
    按顺序处理消息列表中的所有宏和代码块。
    """
    if not v.ENABLE_MACRO_PROCESSING:
        return {"processed_messages": messages}

    processor = get_macro_processor()

    # 更新上下文
    if context_data:
        processor.update_context(**context_data)
    
    processed_messages = processor.process_messages_sequentially(messages)
    
    # 过滤掉被disabled的消息
    final_messages = [msg for msg in processed_messages if msg is not None]
    
    return {"processed_messages": final_messages}