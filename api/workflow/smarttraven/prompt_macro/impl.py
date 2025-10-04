"""
SmartTraven Prompt-Macro Workflow Implementation (impl.py)

说明:
- 仅包含实现逻辑，不做 API 注册
- 输入为 JSON 对象/数组，参考 backend_projects/SmartTraven/data 的结构，但不读取文件
- 流程：
  1) 调用 workflow/smarttraven/prompt_raw/assemble_full → 得到完整 messages（含 source）
  2) 若 RAW 失败则回退为 modules 组合（in_chat_constructor → framing_prompt）
  3) 调用 modules/smarttraven/macro/process 对 messages 执行宏处理，传入初始 variables 与 policy
  4) 返回宏处理后的 messages 与 {initial, final} 变量集（仅替换 content，保留 source 等）

调试日志：
- 使用 print 输出，前缀统一为 "[prompt_macro]"，便于在网关控制台检索
"""
from typing import Any, Dict, Optional, List
import asyncio
import json
import core


def _dbg(label: str, data: Any = None) -> None:
    """轻量日志（防止异常中断）"""
    try:
        prefix = "[prompt_macro] "
        if isinstance(data, (dict, list)):
            print(prefix + f"{label} = " + json.dumps(data, ensure_ascii=False)[:800])
        else:
            print(prefix + f"{label}: {data}")
    except Exception as e:
        try:
            print(f"[prompt_macro] log_error: {e}")
        except Exception:
            pass


def _split_inchat(presets: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从 presets 文档中过滤 position=='in-chat' 的预设数组。"""
    out: List[Dict[str, Any]] = []
    if isinstance(presets, dict):
        prompts = presets.get("prompts") or []
        if isinstance(prompts, list):
            for p in prompts:
                if isinstance(p, dict) and str(p.get("position", "")).lower() == "in-chat":
                    out.append(p)
    return out


async def _assemble_raw_or_fallback(
    presets: Dict[str, Any],
    world_books: Any,
    history: Any,
    character: Optional[Dict[str, Any]],
    persona: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """优先调用 RAW 工作流装配；失败时回退为“modules 直连组装”"""
    _dbg("raw.enter", True)
    raw_payload = {
        "presets": presets or {},
        "world_books": world_books if world_books is not None else [],
        "history": history or [],
        "character": character or {},
        "persona": persona or {},
    }
    try:
        raw_res = await asyncio.to_thread(
            core.call_api,
            "smarttraven/prompt_raw/assemble_full",
            raw_payload,
            method="POST",
            namespace="workflow",
        )
        _dbg("raw_res.type", type(raw_res).__name__)
        if isinstance(raw_res, dict):
            _dbg("raw_res.keys", list(raw_res.keys()))
            if isinstance(raw_res.get("messages"), list):
                return raw_res["messages"]
    except Exception as e:
        _dbg("raw.exception", repr(e))

    # 回退路径：先 in-chat，再把 in-chat 结果替换到 framing 的 chatHistory 中
    if isinstance(history, dict) and isinstance(history.get("messages"), list):
        history_for_inchat = history.get("messages") or []
    else:
        history_for_inchat = history or []

    in_chat_payload = {
        "history": history_for_inchat,
        "presets_in_chat": _split_inchat(presets),
        "world_books": world_books if world_books is not None else [],
    }
    _dbg("fallback.in_chat_payload.keys", list(in_chat_payload.keys()))
    ic = await asyncio.to_thread(
        core.call_api,
        "smarttraven/in_chat_constructor/construct",
        in_chat_payload,
        method="POST",
        namespace="modules",
    )
    in_chat_with_source = (ic.get("messages", []) if isinstance(ic, dict) else []) or []
    _dbg("fallback.in_chat.messages.count", len(in_chat_with_source))

    framing_payload = {
        "history": {"messages": in_chat_with_source},
        "world_books": world_books if world_books is not None else [],
        "presets_doc": presets or {},
        "character": character or {},
        "persona": persona or {},
    }
    _dbg("fallback.framing_payload.keys", list(framing_payload.keys()))
    fr = await asyncio.to_thread(
        core.call_api,
        "smarttraven/framing_prompt/assemble",
        framing_payload,
        method="POST",
        namespace="modules",
    )
    if isinstance(fr, dict) and isinstance(fr.get("messages"), list):
        _dbg("fallback.framing.messages.count", len(fr["messages"]))
        return fr["messages"]

    _dbg("fallback.result", "EMPTY_MESSAGES")
    return []


async def run(
    variables: Dict[str, Any],
    presets: Dict[str, Any],
    world_books: Any,
    history: Any,
    character: Optional[Dict[str, Any]] = None,
    persona: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    包装整个流程，确保任何异常情况下也返回规范结构：
    { "messages": [], "variables": { "initial": {...}, "final": {...} } }
    """
    try:
        # 输入快照
        _dbg("input.variables.keys", sorted(list((variables or {}).keys())))
        _dbg("input.presets.prompts_count", len((presets or {}).get("prompts", []) if isinstance(presets, dict) else []))
        _dbg("input.world_books.type", type(world_books).__name__)
        _dbg("input.history.type", type(history).__name__)

        # 1) 先装配 RAW（失败则回退）
        try:
            messages: List[Dict[str, Any]] = await _assemble_raw_or_fallback(
                presets=presets or {},
                world_books=world_books,
                history=history or [],
                character=character or {},
                persona=persona or {},
            )
        except Exception as e:
            _dbg("assemble_raw_or_fallback.exception", repr(e))
            # 手动回退：in-chat → framing
            try:
                if isinstance(history, dict) and isinstance(history.get("messages"), list):
                    history_for_inchat = history.get("messages") or []
                else:
                    history_for_inchat = history or []
                in_chat_payload = {
                    "history": history_for_inchat,
                    "presets_in_chat": _split_inchat(presets),
                    "world_books": world_books if world_books is not None else [],
                }
                ic = await asyncio.to_thread(
                    core.call_api,
                    "smarttraven/in_chat_constructor/construct",
                    in_chat_payload,
                    method="POST",
                    namespace="modules",
                )
                in_chat_with_source = (ic.get("messages", []) if isinstance(ic, dict) else []) or []
                framing_payload = {
                    "history": {"messages": in_chat_with_source},
                    "world_books": world_books if world_books is not None else [],
                    "presets_doc": presets or {},
                    "character": character or {},
                    "persona": persona or {},
                }
                fr = await asyncio.to_thread(
                    core.call_api,
                    "smarttraven/framing_prompt/assemble",
                    framing_payload,
                    method="POST",
                    namespace="modules",
                )
                messages = (fr.get("messages", []) if isinstance(fr, dict) else []) or []
            except Exception as e2:
                _dbg("fallback.manual.exception", repr(e2))
                messages = []

        _dbg("assembled.messages.count", len(messages))
        _dbg("assembled.sample.contents", [m.get("content") for m in messages[:2]])

        # 2) 顺序宏处理（仅替换 content，保留 source 等字段）
        macro_payload = {
            "messages": messages,
            "variables": variables or {},
        }
        _dbg("macro.payload.variables.keys", sorted(list((macro_payload["variables"] or {}).keys())))
        _dbg("macro.payload.messages.count", len(macro_payload["messages"]))

        try:
            macro_res = await asyncio.to_thread(
                core.call_api,
                "smarttraven/macro/process",
                macro_payload,
                method="POST",
                namespace="modules",
            )
        except Exception as e:
            _dbg("macro.exception", repr(e))
            macro_res = {"messages": messages, "variables": {"initial": variables or {}, "final": variables or {}}}

        _dbg("macro_res.type", type(macro_res).__name__)
        if isinstance(macro_res, dict):
            _dbg("macro_res.keys", list(macro_res.keys()))
            _dbg("macro_res.messages.count", len((macro_res.get("messages") or [])))
            _dbg("macro_res.variables.keys", list(((macro_res.get("variables") or {})).keys()))

        out_messages: List[Dict[str, Any]] = messages
        out_vars: Dict[str, Any] = {"initial": variables or {}, "final": variables or {}}

        if isinstance(macro_res, dict):
            msgs2 = macro_res.get("messages")
            if isinstance(msgs2, list):
                out_messages = msgs2
            vars2 = macro_res.get("variables")
            if isinstance(vars2, dict) and "initial" in vars2 and "final" in vars2:
                out_vars = vars2

        result = {
            "messages": out_messages,
            "variables": out_vars,
        }
        _dbg("result.messages.count", len(result["messages"]))
        _dbg("result.variables.initial.keys", sorted(list((result["variables"].get("initial") or {}).keys())))
        _dbg("result.variables.final.keys", sorted(list((result["variables"].get("final") or {}).keys())))
        return result

    except Exception as e:
        _dbg("run.exception", repr(e))
        # 确保即使异常也返回规范结构，避免上游断言失败
        safe = {
            "messages": [],
            "variables": {"initial": variables or {}, "final": variables or {}}
        }
        return safe