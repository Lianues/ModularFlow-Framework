#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
传统酒馆宏转换器 (Legacy SmartTavern Macro Converter)

负责将传统SmartTavern宏转换为Python代码并执行。
支持所有传统宏类型，包括：
- 系统变量宏 (user, char, description等)
- 时间相关宏 (time, date, weekday等)
- 消息相关宏 (input, lastMessage等)
- 功能性宏 (random, roll, pick等)
- 变量操作宏 (getvar, setvar等)
- 数学运算宏 (add, sub, mul等)
- 字符串操作宏 (upper, lower等)
- 日期时间格式化宏
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Optional


class LegacyMacroConverter:
    """传统宏转换器"""
    
    def __init__(self):
        self._init_macro_converters()
    
    def _init_macro_converters(self):
        """初始化传统宏转换规则"""
        self.macro_converters = {
            # 系统变量 - 直接访问
            'user': "result = user",
            'char': "result = char", 
            'description': "result = description",
            'personality': "result = personality",
            'scenario': "result = scenario",
            'persona': "result = persona",
            
            # 时间变量
            'time': "result = time",
            'date': "result = date",
            'weekday': "result = weekday",
            'isotime': "result = isotime",
            'isodate': "result = isodate",
            
            # 消息变量
            'input': "result = input",
            'lastMessage': "result = lastMessage",
            'lastUserMessage': "result = lastUserMessage", 
            'lastCharMessage': "result = lastCharMessage",
            'messageCount': "result = messageCount",
            'userMessageCount': "result = userMessageCount",
            'conversationLength': "result = conversationLength",
            
            # 特殊宏
            'newline': "result = '\\n'",
            'trim': "result = ''",  # trim宏的特殊处理在外层
            'noop': "result = ''",
            'enable': "result = True",
        }
    
    def convert_macro_to_python(self, macro_name: str, params: str) -> str:
        """将传统宏转换为Python代码"""
        
        # 1. 简单系统变量
        if macro_name in self.macro_converters:
            return self.macro_converters[macro_name]
        
        # 2. 注释宏
        if macro_name.startswith('//'):
            return "result = ''"
        
        # 3. 功能性宏
        if macro_name == 'roll':
            return f"result = legacy_roll({json.dumps(params)})"
        
        elif macro_name == 'random':
            if '::' in params:
                # {{random::a::b::c}} 格式
                choices = [json.dumps(choice.strip()) for choice in params.split('::') if choice.strip()]
            else:
                # {{random:a,b,c}} 格式
                choices = [json.dumps(choice.strip()) for choice in params.split(',') if choice.strip()]
            choices_code = ', '.join(choices)
            return f"result = legacy_random({choices_code})"
        
        elif macro_name == 'pick':
            if '::' in params:
                choices = [json.dumps(choice.strip()) for choice in params.split('::') if choice.strip()]
            else:
                choices = [json.dumps(choice.strip()) for choice in params.split(',') if choice.strip()]
            choices_code = ', '.join(choices)
            return f"result = legacy_pick({choices_code})"
        
        # 4. 数学运算宏
        elif macro_name in ['add', 'sub', 'mul', 'div', 'max', 'min']:
            if '::' in params:
                param_list = params.split('::')
            elif ':' in params:
                param_list = params.split(':')
            else:
                param_list = [params]
            
            if len(param_list) >= 2:
                a, b = param_list[0].strip(), param_list[1].strip()
                return f"result = legacy_math_op({json.dumps(macro_name)}, {a}, {b})"
            else:
                return f"result = legacy_math_op({json.dumps(macro_name)}, {params})"
        
        # 5. 字符串操作宏
        elif macro_name in ['upper', 'lower', 'length', 'reverse']:
            return f"result = legacy_string_op({json.dumps(macro_name)}, {json.dumps(params)})"
        
        # 6. 时间差计算
        elif macro_name == 'timeDiff':
            if '::' in params:
                time_parts = params.split('::')
                if len(time_parts) >= 2:
                    time1, time2 = time_parts[0], time_parts[1]
                    # 注意：这里使用 strptime 解析时间字符串，可能需要特定格式
                    return f"""
try:
    from datetime import datetime
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S']
    time1_dt = None
    time2_dt = None
    
    # 尝试多种格式解析时间
    for fmt in formats:
        try:
            time1_dt = datetime.strptime('{time1}', fmt)
            break
        except ValueError:
            continue
    
    for fmt in formats:
        try:
            time2_dt = datetime.strptime('{time2}', fmt)
            break
        except ValueError:
            continue
    
    if time1_dt and time2_dt:
        diff = time2_dt - time1_dt
        result = f'{{diff.days}}天{{diff.seconds//3600}}小时{{(diff.seconds%3600)//60}}分钟'
    else:
        result = '时间格式无效'
except Exception as e:
    result = f'时间差计算错误: {{e}}'
"""
            return "result = '时间格式无效'"
            
        # 7. 变量操作宏（统一作用域感知）
        elif macro_name == 'getvar':
            return f"result = getvar({json.dumps(params)})"
        
        elif macro_name == 'setvar':
            if '::' in params:
                parts = params.split('::', 1)
                if len(parts) >= 2:
                    var_name, value = parts[0].strip(), parts[1].strip()
                    return f"result = setvar({json.dumps(var_name)}, {json.dumps(value)})"
            return "result = ''"
        
        elif macro_name == 'addvar':
            if '::' in params:
                parts = params.split('::', 1)
                if len(parts) >= 2:
                    var_name, increment = parts[0].strip(), parts[1].strip()
                    return f"result = addvar({json.dumps(var_name)}, {json.dumps(increment)})"
            return "result = ''"
        
        elif macro_name == 'incvar':
            return f"result = incvar({json.dumps(params)})"
        
        elif macro_name == 'decvar':
            return f"result = decvar({json.dumps(params)})"
        
        # 8. 全局变量操作宏
        elif macro_name == 'getglobalvar':
            return f"result = getglobalvar({json.dumps(params)})"
        
        elif macro_name == 'setglobalvar':
            if '::' in params:
                parts = params.split('::', 1)
                if len(parts) >= 2:
                    var_name, value = parts[0].strip(), parts[1].strip()
                    return f"result = setglobalvar({json.dumps(var_name)}, {json.dumps(value)})"
            return "result = ''"
            
        elif macro_name == 'addglobalvar':
            if '::' in params:
                parts = params.split('::', 1)
                if len(parts) >= 2:
                    var_name, value = parts[0].strip(), parts[1].strip()
                    return f"""
try:
    current = getglobalvar({json.dumps(var_name)}, '0')
    safe_value = {json.dumps(value)}
    if str(current).isdigit() and str(safe_value).isdigit():
        result = str(int(current) + int(safe_value))
        setglobalvar({json.dumps(var_name)}, result)
    else:
        try:
            result = str(float(current) + float(safe_value))
            setglobalvar({json.dumps(var_name)}, result)
        except (ValueError, TypeError):
            result = str(current) + str(safe_value)  # 非数字则拼接字符串
            setglobalvar({json.dumps(var_name)}, result)
except Exception as e:
    result = f'错误: {{e}}'
"""
            return "result = '参数不足'"
            
        elif macro_name == 'incglobalvar':
            return f"""
try:
    safe_params = {json.dumps(params)}
    current = getglobalvar(safe_params, '0')
    if str(current).isdigit():
        result = str(int(current) + 1)
    else:
        try:
            result = str(float(current) + 1)
        except ValueError:
            result = '1'  # 无法转换为数字则重置为1
    setglobalvar(safe_params, result)
except Exception as e:
    result = f'错误: {{e}}'
"""

        elif macro_name == 'decglobalvar':
            return f"""
try:
    safe_params = {json.dumps(params)}
    current = getglobalvar(safe_params, '0')
    if str(current).isdigit():
        result = str(int(current) - 1)
    else:
        try:
            result = str(float(current) - 1)
        except ValueError:
            result = '-1'  # 无法转换为数字则重置为-1
    setglobalvar(safe_params, result)
except Exception as e:
    result = f'错误: {{e}}'
"""
        
        # 9. 日期时间格式化
        elif macro_name == 'datetimeformat':
            # 这里可以添加日期格式化逻辑
            return f"result = datetime.now().strftime({json.dumps(params)})"
        
        # 10. 时区相关
        elif macro_name.startswith('time_UTC'):
            # 提取UTC偏移值
            try:
                offset_str = macro_name[8:]  # 提取"time_UTC"后面的部分
                if offset_str:
                    offset = int(offset_str)  # 转换为整数
                    # 计算指定时区的时间
                    utc_time = datetime.now()
                    target_time = utc_time + timedelta(hours=offset)
                    return f"result = '{target_time.strftime('%H:%M:%S')}'"
                else:
                    return "result = datetime.now().strftime('%H:%M:%S')"
            except ValueError:
                # 偏移值无效，返回当前时间
                return "result = datetime.now().strftime('%H:%M:%S')"
        
        # 未知宏
        else:
            return ""  # 返回空字符串表示无法转换
    
    def execute_traditional_macro(self, macro_content: str, scope_type: str, sandbox) -> str:
        """执行传统宏（转换为Python代码）"""
        
        # 解析传统宏名称和参数
        # 支持多种分隔符格式：`:`, `::`
        if '::' in macro_content:
            # {{getvar::variable_name}} 格式
            parts = macro_content.split('::', 1)
            macro_name = parts[0].strip().lower()
            params = parts[1].strip()
        elif ':' in macro_content:
            # {{getvar:variable_name}} 格式
            parts = macro_content.split(':', 1)
            macro_name = parts[0].strip().lower()
            params = parts[1].strip()
        else:
            # {{getvar}} 或 {{char}} 格式
            macro_name = macro_content.strip().lower()
            params = ""
        
        # 转换为Python代码
        python_code = self.convert_macro_to_python(macro_name, params)
        
        if python_code:
            # 执行转换后的Python代码
            result = sandbox.execute_code(python_code, scope_type=scope_type)
            if result.success:
                return str(result.result) if result.result is not None else ""
            else:
                print(f"⚠️ 传统宏执行失败: {result.error}")
                return ""
        else:
            # 无法转换的宏，保持原样
            return f"{{{{{macro_content}}}}}"
    
    def is_traditional_macro(self, macro_content: str) -> bool:
        """检查是否为传统宏（非Python宏）"""
        # Python宏以 'python:' 开头
        if macro_content.strip().startswith('python:'):
            return False
        
        # 其他都是传统宏
        return True


# 创建全局实例
_legacy_converter_instance = None

def get_legacy_converter() -> LegacyMacroConverter:
    """获取传统宏转换器单例"""
    global _legacy_converter_instance
    if _legacy_converter_instance is None:
        _legacy_converter_instance = LegacyMacroConverter()
    return _legacy_converter_instance