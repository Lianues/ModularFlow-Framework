#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartTraven.macro 实现层

功能
- 顺序处理消息列表（从第一条到最后一条），仅修改 content，保留 source 等其他字段不变
- 支持宏定界符：{{ ... }} 与 << ... >>（两者等价）
- 支持嵌套宏（内层优先），采用单遍扫描 + 栈匹配，避免误识别
- 支持的宏：
  - python:EXPR    使用本项目 SmartTraven.python_sandbox 安全求值，返回字符串
  - setvar:NAME:VALUE 或 setvar:NAME::VALUE  创建/更新变量；替换为空字符串
  - getvar:NAME     读取变量；未定义时根据 policy 输出错误占位词（默认 [UndefinedVar:{name}]）

- 所有变量处于“单一作用域”（一个 dict）
- 输入可携带 variables（初值）；输出 variables 包含 initial/final 两份快照
- policy（可选）：{"undefined_get":"error|empty","error_token":"[UndefinedVar:{name}]"}
"""
from typing import Any, Dict, List, Optional, Tuple
import core
import random
from datetime import datetime, timedelta

DEFAULT_POLICY = {
    "undefined_get": "error",             # "error" | "empty"
    "error_token": "[UndefinedVar:{name}]",
}


# 支持的传统宏名（小写）
SUPPORTED_LEGACY_MACROS = {
    "newline","noop","enable","trim",
    "random","pick","roll",
    "add","sub","mul","div","max","min",
    "upper","lower","length","reverse",
    "time","date","weekday","isotime","isodate","datetimeformat",
    "time_utc",
    "input","lastmessage","lastusermessage","lastcharmessage",
    "messagecount","usermessagecount","conversationlength",
    "user","char","description","personality","scenario","persona",
    "getglobalvar","setglobalvar","addglobalvar","incglobalvar","decglobalvar",
    "addvar","incvar","decvar",
    "timediff"
}

def _error_token(name: str, policy: Dict[str, Any]) -> str:
    tpl = str(policy.get("error_token", "[UndefinedVar:{name}]"))
    return tpl.replace("{name}", str(name))

def _split_params(params: str) -> List[str]:
    if params is None:
        return []
    s = str(params)
    if "::" in s:
        parts = [p for p in s.split("::") if p is not None]
    else:
        parts = [p for p in s.split(",") if p is not None]
    return [p.strip() for p in parts]

def _to_number(s: Any) -> float:
    try:
        if isinstance(s, (int, float)):
            return float(s)
        s2 = str(s).strip()
        if s2.lower().startswith("[undefinedvar"):
            return 0.0
        if "." in s2:
            return float(s2)
        return float(int(s2))
    except Exception:
        return 0.0

def _ctx_last_by_role(all_msgs: List[Dict[str, Any]], idx: int, role: str) -> str:
    j = min(max(idx - 1, -1), len(all_msgs)-1)
    for k in range(j, -1, -1):
        m = all_msgs[k]
        if str(m.get("role","")).lower() == role:
            return str(m.get("content","") or "")
    return ""

def _ctx_last_message(all_msgs: List[Dict[str, Any]], idx: int) -> str:
    if idx <= 0 or idx > len(all_msgs):
        return ""
    return str(all_msgs[idx-1].get("content","") or "")

def _ctx_count_by_role(all_msgs: List[Dict[str, Any]], role: str) -> int:
    return sum(1 for m in all_msgs if str(m.get("role","")).lower() == role)

def _ctx_conversation_length(all_msgs: List[Dict[str, Any]]) -> int:
    total = 0
    for m in all_msgs:
        c = m.get("content","")
        total += len(c or "")
    return total

def _roll_expr(expr: str) -> str:
    try:
        s = (expr or "").strip().lower()
        if "d" not in s:
            return "1"
        left, right = s.split("d", 1)
        num = int(left.strip()) if left.strip() else 1
        sides = int(right.strip())
        num = max(1, min(num, 50))
        sides = max(2, min(sides, 1000))
        return str(sum(random.randint(1, sides) for _ in range(num)))
    except Exception:
        return "1"

def _execute_legacy_macro(name: str, params: str, state: Dict[str, Any], policy: Dict[str, Any], all_msgs: List[Dict[str, Any]], idx: int) -> str:
    n = (name or "").strip().lower()

    # 注释宏（//...）直接为空
    if n.startswith("//"):
        return ""

    # 动态时区时间 time_UTC{offset}
    if n.startswith("time_utc"):
        try:
            off = n[len("time_utc"):]
            offset = int(off) if off else 0
        except Exception:
            offset = 0
        return (datetime.now() + timedelta(hours=offset)).strftime("%H:%M:%S")

    # 系统变量（从单一变量表读取，未定义返回空串）
    if n in ("user","char","description","personality","scenario","persona"):
        return str(state.get(n, "") if state.get(n, "") is not None else "")

    # 基础与无副作用宏
    if n == "newline":
        return "\n"
    if n in ("noop","trim"):
        return ""
    if n == "enable":
        return "True"

    # 选择类
    if n in ("random","pick"):
        choices = _split_params(params)
        return str(random.choice(choices)) if choices else ""

    # 掷骰
    if n == "roll":
        return _roll_expr(params or "1d6")

    # 数学
    if n in ("add","sub","mul","div","max","min"):
        parts = _split_params(params)
        a = _to_number(parts[0]) if len(parts) >= 1 else 0.0
        b = _to_number(parts[1]) if len(parts) >= 2 else 0.0
        if n == "add":
            return str(a + b)
        if n == "sub":
            return str(a - b)
        if n == "mul":
            return str(a * b)
        if n == "div":
            try:
                return str(a / b if b != 0 else 0.0)
            except Exception:
                return "0"
        if n == "max":
            return str(max(a, b))
        if n == "min":
            return str(min(a, b))

    # 变量操作（按单作用域实现）
    if n in ("addvar","addglobalvar"):
        parts = _split_params(params)
        var_name = parts[0] if parts else ""
        inc = parts[1] if len(parts) > 1 else "0"
        cur = state.get(var_name, "0")
        a = _to_number(cur)
        b = _to_number(inc)
        # 若均为数字则相加，否则字符串拼接
        if (str(cur).replace('.','',1).lstrip('-').isdigit() and str(inc).replace('.','',1).lstrip('-').isdigit()):
            state[var_name] = str(a + b)
        else:
            state[var_name] = str(cur) + str(inc)
        return ""

    if n in ("incvar","incglobalvar"):
        var_name = (params or "").strip()
        cur = _to_number(state.get(var_name, "0"))
        state[var_name] = str(cur + 1)
        return ""

    if n in ("decvar","decglobalvar"):
        var_name = (params or "").strip()
        cur = _to_number(state.get(var_name, "0"))
        state[var_name] = str(cur - 1)
        return ""

    if n in ("getglobalvar",):
        var_name = (params or "").strip()
        return str(state.get(var_name, "") if state.get(var_name, "") is not None else "")

    if n in ("setglobalvar",):
        # setglobalvar:name::value 或 name:value
        body = params or ""
        if "::" in body:
            var_name, value = body.split("::", 1)
        elif ":" in body:
            var_name, value = body.split(":", 1)
        else:
            var_name, value = body, ""
        state[var_name.strip()] = value
        return ""

    # 字符串
    if n in ("upper","lower","length","reverse"):
        s = params or ""
        if n == "upper":
            return s.upper()
        if n == "lower":
            return s.lower()
        if n == "length":
            return str(len(s))
        if n == "reverse":
            return s[::-1]

    # 日期时间格式化
    if n == "datetimeformat":
        fmt = params or "%Y-%m-%d %H:%M:%S"
        try:
            return datetime.now().strftime(fmt)
        except Exception:
            return ""

    # 时间
    if n in ("time","isotime"):
        return datetime.now().strftime("%H:%M:%S")
    if n in ("date","isodate"):
        return datetime.now().strftime("%Y-%m-%d")
    if n == "weekday":
        return ["星期一","星期二","星期三","星期四","星期五","星期六","星期日"][datetime.now().weekday()]

    # 时间差
    if n == "timediff":
        raw = params or ""
        if "::" in raw:
            t1, t2 = raw.split("::", 1)
        elif ":" in raw:
            t1, t2 = raw.split(":", 1)
        else:
            t1, t2 = "", ""
        t1 = t1.strip()
        t2 = t2.strip()
        fmts = ['%Y-%m-%d %H:%M:%S','%Y-%m-%d','%H:%M:%S']
        def _parse(s: str):
            for f in fmts:
                try:
                    return datetime.strptime(s, f)
                except Exception:
                    continue
            return None
        dt1 = _parse(t1)
        dt2 = _parse(t2)
        if dt1 and dt2:
            diff = dt2 - dt1
            days = diff.days
            secs = diff.seconds
            hours = secs // 3600
            minutes = (secs % 3600) // 60
            return f"{days}天{hours}小时{minutes}分钟"
        return ""

    # 对话相关（使用输入消息上下文）
    if n == "input":
        return ""  # 暂无专门 input 源
    if n == "lastmessage":
        return _ctx_last_message(all_msgs, idx)
    if n == "lastusermessage":
        return _ctx_last_by_role(all_msgs, idx, "user")
    if n == "lastcharmessage":
        return _ctx_last_by_role(all_msgs, idx, "assistant")
    if n == "messagecount":
        return str(len(all_msgs))
    if n == "usermessagecount":
        return str(_ctx_count_by_role(all_msgs, "user"))
    if n == "conversationlength":
        return str(_ctx_conversation_length(all_msgs))

    # 未识别的传统宏
    return ""


def _recognize_macro(raw: str) -> Tuple[str, Any] | Tuple[None, None]:
    """
    判断并解析宏内容
    返回: (kind, payload)
      - ("python", expr: str)
      - ("setvar", (name: str, value: str))
      - ("getvar", name: str)
      - ("legacy", (name: str, params: str))
      - (None, None) 未识别
    """
    if not isinstance(raw, str):
        return (None, None)
    s = raw.strip()
    low = s.lower()

    # 注释宏：//... -> 空
    if s.strip().startswith("//"):
        return ("legacy", ("//", ""))

    # python:EXPR
    if low.startswith("python:"):
        return ("python", s[7:].strip())

    # setvar
    if low.startswith("setvar"):
        body = s[6:].lstrip()  # 去掉关键字
        if body.startswith("::"):
            body = body[2:]
        elif body.startswith(":"):
            body = body[1:]
        if "::" in body:
            name, value = body.split("::", 1)
        elif ":" in body:
            name, value = body.split(":", 1)
        else:
            # 仅 setvar:name （值为空）
            name, value = body, ""
        return ("setvar", (name.strip(), value))

    # getvar
    if low.startswith("getvar"):
        body = s[6:].lstrip()
        if body.startswith("::"):
            body = body[2:]
        elif body.startswith(":"):
            body = body[1:]
        name = body.strip()
        return ("getvar", name)

    # legacy（受支持名称或 time_utc* 动态）
    name = low
    params = ""
    if "::" in s:
        parts = s.split("::", 1)
        name = parts[0].strip().lower()
        params = parts[1]
    elif ":" in s:
        parts = s.split(":", 1)
        name = parts[0].strip().lower()
        params = parts[1]
    else:
        name = s.strip().lower()
        params = ""

    if name in SUPPORTED_LEGACY_MACROS or name.startswith("time_utc"):
        return ("legacy", (name, params))

    return (None, None)


def _find_next_recognized_span(text: str) -> Tuple[int, int, str] | None:
    """
    查找从左到右的下一个“被识别”的最内层宏片段，返回 (start, end, inner)
    - start: 宏起始索引（含定界符）
    - end:   宏结束索引（不含定界符后的字符），即切片 text[start:end] 是整个宏
    - inner: 定界符内部文本
    若未找到，返回 None
    """
    n = len(text)
    stack_curly: List[int] = []
    stack_angle: List[int] = []
    i = 0
    while i < n - 1:
        two = text[i:i+2]
        if two == "{{":
            stack_curly.append(i)
            i += 2
            continue
        if two == "<<":
            stack_angle.append(i)
            i += 2
            continue
        if two == "}}":
            if stack_curly:
                start = stack_curly.pop()
                inner = text[start+2:i]
                kind, _ = _recognize_macro(inner)
                if kind is not None:
                    return (start, i+2, inner)
            i += 2
            continue
        if two == ">>":
            if stack_angle:
                start = stack_angle.pop()
                inner = text[start+2:i]
                kind, _ = _recognize_macro(inner)
                if kind is not None:
                    return (start, i+2, inner)
            i += 2
            continue
        i += 1
    return None


def _eval_python(expr: str, state: Dict[str, Any], policy: Dict[str, Any]) -> str:
    """
    使用 SmartTraven.python_sandbox 模块求值表达式
    - 仅通过 HTTP API 调用，避免函数直调耦合
    - 将 state 作为 variables 传入，返回时合并 final 到 state
    """
    payload = {
        "code": expr,
        "variables": state,
        "policy": policy,
    }
    res = core.call_api("smarttraven/python_sandbox/eval", payload, method="POST", namespace="modules")
    try:
        if isinstance(res, dict):
            # 同步变量（final）
            vars_dict = ((res.get("variables") or {}).get("final") or {})
            if isinstance(vars_dict, dict):
                state.clear()
                state.update(vars_dict)
            if res.get("success"):
                return str(res.get("result", ""))
            # 失败返回空串（保守处理）
            return ""
    except Exception:
        return ""
    return ""


def _py_literal(v: Any) -> str:
    """将 Python 值安全转为 Python 源码字面量（字符串带引号）"""
    return repr("" if v is None else str(v))

def _legacy_to_python(name: str, params: str) -> str:
    """
    将“传统宏”转换为在沙盒内执行的 Python 代码（表达式/语句），并统一交由 python_sandbox 执行。
    - 不再依赖对话历史；所有“历史/输入”类宏映射为 getvar('...') 的系统变量读取
    - 变量操作宏通过已注入的 legacy_* 与 getvar/setvar 完成
    """
    n = (name or "").strip().lower()
    p = "" if params is None else str(params)

    # 注释宏
    if n.startswith("//"):
        return "''"

    # 简单控制类
    if n == "newline":
        return "'\\n'"
    if n in ("noop", "trim"):
        return "''"
    if n == "enable":
        return "'True'"

    # 随机选择类
    if n in ("random", "pick"):
        items = _split_params(p)
        if not items:
            return "''"
        arr = "[" + ", ".join(_py_literal(x) for x in items) + "]"
        return f"random.choice({arr})"

    # 掷骰
    if n == "roll":
        expr = p if p.strip() else "1d6"
        return f"legacy_roll({_py_literal(expr)})"

    # 数学
    if n in ("add","sub","mul","div","max","min"):
        parts = _split_params(p)
        a = parts[0] if len(parts) >= 1 else "0"
        b = parts[1] if len(parts) >= 2 else "0"
        A = f"legacy_num({_py_literal(a)},0)"
        B = f"legacy_num({_py_literal(b)},0)"
        if n == "add":
            return f"({A} + {B})"
        if n == "sub":
            return f"({A} - {B})"
        if n == "mul":
            return f"({A} * {B})"
        if n == "div":
            return f"({A} / {B} if {B} != 0 else 0.0)"
        if n == "max":
            return f"max({A}, {B})"
        if n == "min":
            return f"min({A}, {B})"

    # 字符串
    if n in ("upper","lower","length","reverse"):
        s = p
        if n == "upper":
            return f"legacy_upper({_py_literal(s)})"
        if n == "lower":
            return f"legacy_lower({_py_literal(s)})"
        if n == "length":
            return f"len({_py_literal(s)})"
        if n == "reverse":
            return f"({_py_literal(s)})[::-1]"

    # 日期时间
    if n == "datetimeformat":
        fmt = p if p.strip() else "%Y-%m-%d %H:%M:%S"
        return f"legacy_time({_py_literal(fmt)})"
    if n in ("time", "isotime"):
        return "legacy_time('%H:%M:%S')"
    if n in ("date", "isodate"):
        return "legacy_time('%Y-%m-%d')"
    if n == "weekday":
        return "legacy_weekday_cn()"
    if n.startswith("time_utc"):
        rest = n[len("time_utc"):]
        try:
            offset = int(rest) if rest else 0
        except Exception:
            offset = 0
        return f"legacy_time_utc({offset}, '%H:%M:%S')"

    # 变量操作
    if n in ("getglobalvar",):
        var_name = p.strip()
        return f"getvar({_py_literal(var_name)})"
    if n in ("setglobalvar",):
        body = p
        if "::" in body:
            var_name, value = body.split("::", 1)
        elif ":" in body:
            var_name, value = body.split(":", 1)
        else:
            var_name, value = body, ""
        return f"setvar({_py_literal(var_name.strip())}, {_py_literal(value)})"

    if n in ("addvar","addglobalvar"):
        parts = _split_params(p)
        var_name = parts[0] if parts else ""
        inc = parts[1] if len(parts) > 1 else "0"
        return f"legacy_addvar({_py_literal(var_name)}, {_py_literal(inc)})"

    if n in ("incvar","incglobalvar"):
        var_name = p.strip()
        return f"legacy_inc({_py_literal(var_name)})"

    if n in ("decvar","decglobalvar"):
        var_name = p.strip()
        return f"legacy_dec({_py_literal(var_name)})"

    # 历史/输入宏 → 系统变量读取（不记录历史，交由上游注入 variables）
    hist_map = {
        "input": "user_input_text",
        "lastmessage": "chat_last_message",
        "lastusermessage": "chat_last_user_message",
        "lastcharmessage": "chat_last_assistant_message",
        "messagecount": "chat_message_count",
        "usermessagecount": "chat_user_message_count",
        "conversationlength": "chat_conversation_length",
    }
    if n in hist_map:
        return f"getvar({_py_literal(hist_map[n])})"

    # 系统变量类（更具体的命名）
    sys_map = {
        "user": "user_name",
        "char": "character_name",
        "description": "character_description",
        "personality": "character_personality",
        "scenario": "scenario_description",
        "persona": "persona_description",
    }
    if n in sys_map:
        return f"getvar({_py_literal(sys_map[n])})"

    # 兜底
    return "''"

def _process_text(content: str, state: Dict[str, Any], policy: Dict[str, Any], all_msgs: List[Dict[str, Any]], idx: int) -> str:
    """
    处理单条文本中的宏（支持嵌套）
    - 迭代寻找下一个“已识别”的最内层宏，替换为结果，直至无可替换项
    """
    if not isinstance(content, str) or ("{{" not in content and "<<" not in content):
        return "" if content is None else str(content)

    text = content
    # 防止极端情况下的死循环
    guard = 0
    while guard < 10000:
        guard += 1
        span = _find_next_recognized_span(text)
        if not span:
            break
        start, end, inner = span
        kind, payload = _recognize_macro(inner)
        repl = ""
        if kind == "python":
            repl = _eval_python(str(payload), state, policy)
        elif kind == "setvar":
            name, value = payload
            state[str(name)] = value
            repl = ""  # setvar 本身不产出文本
        elif kind == "getvar":
            name = str(payload)
            if name in state:
                repl = "" if state[name] is None else str(state[name])
            else:
                if str(policy.get("undefined_get", "error")).lower() == "error":
                    repl = _error_token(name, policy)
                else:
                    repl = ""
        elif kind == "legacy":
            name, params = payload
            code = _legacy_to_python(name, params)
            repl = _eval_python(code, state, policy)
        else:
            repl = ""

        text = f"{text[:start]}{repl}{text[end:]}"
    return text


def process_messages(messages: List[Dict[str, Any]],
                     variables: Optional[Dict[str, Any]] = None,
                     policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理消息列表中的宏。
    - 仅修改 content；保留其他字段（尤其 source）不变
    - 返回处理后的 messages 以及变量表 {initial, final}
    """
    msgs = messages or []
    init_state: Dict[str, Any] = dict(variables or {})
    state: Dict[str, Any] = dict(init_state)
    pol: Dict[str, Any] = dict(DEFAULT_POLICY)
    if isinstance(policy, dict):
        pol.update(policy)

    out: List[Dict[str, Any]] = []
    for idx, m in enumerate(msgs):
        try:
            if not isinstance(m, dict):
                continue
            new_m = dict(m)  # 浅拷贝，保留原字段
            new_m["content"] = _process_text(m.get("content", ""), state, pol, msgs, idx)
            out.append(new_m)
        except Exception:
            # 出错时保留原消息
            out.append(m)

    return {
        "messages": out,
        "variables": {
            "initial": init_state,
            "final": state,
        }
    }

def process_text_value(text: str,
                       variables: Optional[Dict[str, Any]] = None,
                       policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    处理单个纯文本中的宏，返回处理后的文本与变量表。
    - 按照与 process_messages 相同的规则，支持 {{...}} 与 <<...>>
    - 严格模式默认：未定义 getvar 输出 [UndefinedVar:{name}]
    - 不提供对话上下文（lastmessage 等历史相关宏将返回空）
    """
    init_state: Dict[str, Any] = dict(variables or {})
    state: Dict[str, Any] = dict(init_state)
    pol: Dict[str, Any] = dict(DEFAULT_POLICY)
    if isinstance(policy, dict):
        pol.update(policy)
    out_text = _process_text(text, state, pol, [], 0)
    return {
        "text": out_text,
        "variables": {
            "initial": init_state,
            "final": state,
        }
    }