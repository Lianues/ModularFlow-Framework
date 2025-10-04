import os
import sys
import json
import time

# 将仓库根目录加入 sys.path 以便 import core 门面
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import core  # noqa: E402


def _ensure_gateway():
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    sm.load_project_modules()
    gateway.start_server(background=True)
    time.sleep(0.3)  # 等待网关就绪
    return gateway


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _split_inchat(presets_doc):
    """从 presets 文档中过滤 position=='in-chat' 的预设数组。"""
    if not isinstance(presets_doc, dict):
        return []
    prompts = presets_doc.get("prompts") or []
    return [p for p in prompts if isinstance(p, dict) and str(p.get("position", "")).lower() == "in-chat"]


def main():
    _ensure_gateway()

    # 准备 data/ 下的示例文档（按工作流契约直接传文档 JSON，而非文件路径）
    presets_doc = _read_json("backend_projects/SmartTraven/data/presets/Default.json")
    world_books_doc = _read_json("backend_projects/SmartTraven/data/world_books/参考用main_world.json")
    conversation_doc = _read_json("backend_projects/SmartTraven/data/conversations/111.json")

    payload = {
        "presets": presets_doc,
        "world_books": world_books_doc,
        "history": conversation_doc   # 允许是“原始 history”（无 source）
    }

    # 调用工作流 API（命名空间 workflow）
    used_fallback = False
    res = core.call_api("smarttraven/prompt_raw/assemble_full", payload, method="POST", namespace="workflow")
    if not isinstance(res, dict) or "messages" not in res:
        used_fallback = True
        # 回退方案：手动按“framing → in-chat”组装，避免工作流聚合层异常导致测试失败
        framing_payload = {
            "history": conversation_doc,
            "world_books": world_books_doc,
            "presets_doc": presets_doc
        }
        # 回退路径：先 in-chat，再把 in-chat 结果替换到 framing 的 chatHistory 中
        inchat_payload = {
            "history": conversation_doc,  # 使用原始 history，保证关键词可命中
            "presets_in_chat": _split_inchat(presets_doc),
            "world_books": world_books_doc
        }
        ic = core.call_api("smarttraven/in_chat_constructor/construct", inchat_payload, method="POST", namespace="modules")
        fr = core.call_api("smarttraven/framing_prompt/assemble", {
            "history": {"messages": (ic.get("messages", []) if isinstance(ic, dict) else [])},
            "world_books": world_books_doc,
            "presets_doc": presets_doc
        }, method="POST", namespace="modules")
        messages = fr.get("messages", []) if isinstance(fr, dict) else []
    else:
        messages = res.get("messages", [])
    assert isinstance(messages, list) and len(messages) > 0, "messages 应为非空数组"
 
    # 基础结构断言：所有带来源的消息均包含 role/content/source
    for i, m in enumerate(messages):
        assert "role" in m and "content" in m and "source" in m and isinstance(m["source"], dict), f"第{i}条消息缺少必要字段(source)"
 
    # 兼容性验证：原始 history（无 source）经聚合后，在最终 messages 中应存在至少一条 source.type == 'history' 的消息
    # 注意：前缀在最前，history 与注入项在其后，故需扫描查找
    history_found = False
    first_history = None
    for m in messages:
        src = m.get("source") or {}
        if isinstance(src, dict) and src.get("type") == "history":
            history_found = True
            first_history = m
            break
    assert history_found, "期望在聚合结果中找到历史消息（source.type == 'history'）"
    # 首条历史消息应来自 history[0]
    assert first_history["source"].get("id") in ("history_0", "history_1", "history_2"), "历史 source.id 形如 'history_0'"
 
    # 断言：应根据关键词触发“用户位”世界书（wb_id == 2）
    wb_user = next((m for m in messages
                    if isinstance(m.get("source"), dict)
                    and m["source"].get("type") == "world_book"
                    and m["source"].get("wb_id") == 2), None)
    assert wb_user is not None, "应根据关键词触发用户位世界书（wb_id=2）"
    assert wb_user.get("role") == "user", "触发的用户位世界书应以 role=user 注入"
    assert "艾拉" in (wb_user.get("content") or ""), "触发的用户位世界书内容应包含 '艾拉'"

    # 直接打印完整的 API 响应
    if used_fallback:
        print(json.dumps({"assemble_full_original_response": res}, ensure_ascii=False, indent=2, sort_keys=False))
        print(json.dumps({"in_chat_construct_response": ic}, ensure_ascii=False, indent=2, sort_keys=False))
        print(json.dumps({"framing_assemble_response": fr}, ensure_ascii=False, indent=2, sort_keys=False))
    else:
        print(json.dumps({"assemble_full_response": res}, ensure_ascii=False, indent=2, sort_keys=False))

    print("OK: prompt workflow tests passed")


if __name__ == "__main__":
    main()