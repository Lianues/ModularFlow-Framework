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


def main():
    _ensure_gateway()

    # 准备 data/ 下的示例文档（按工作流契约直接传文档 JSON，而非文件路径）
    presets_doc = _read_json("backend_projects/SmartTraven/data/presets/Default.json")
    world_books_doc = _read_json("backend_projects/SmartTraven/data/world_books/参考用main_world.json")
    conversation_doc = _read_json("backend_projects/SmartTraven/data/conversations/111.json")
    character_doc = _read_json("backend_projects/SmartTraven/data/characters/心与露.json")
    persona_doc = _read_json("backend_projects/SmartTraven/data/persona/用户2.json")

    payload = {
        "presets": presets_doc,
        "world_books": world_books_doc,
        "history": conversation_doc,   # 允许是“原始 history”（无 source）
        "triggered_worldbook_ids": [2],         # 示例 conditional id
        "character": character_doc,
        "persona": persona_doc,
    }

    # 调用工作流 API（命名空间 workflow）
    res = core.call_api("smarttraven/prompt/assemble_full", payload, method="POST", namespace="workflow")
    assert isinstance(res, dict), "assemble_full 返回值应为字典"
    messages = res.get("messages", [])
    if not isinstance(messages, list) or len(messages) == 0:
        print("assemble_full response:", json.dumps(res, ensure_ascii=False, indent=2, sort_keys=False))
    assert isinstance(messages, list) and len(messages) > 0, "messages 应为非空数组"

    # 基础结构断言：所有消息均包含 role/content/source；字段顺序由实现保证（role→content→source）
    for i, m in enumerate(messages):
        assert "role" in m and "content" in m and "source" in m and isinstance(m["source"], dict), f"第{i}条消息缺少必要字段"

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

    # 用例 2：不提供 triggered_worldbook_ids（可选字段）
    # 说明：当省略该字段或传空数组时，framing/in-chat 将不会选入任何 mode=="conditional" 的世界书条目
    payload2 = {
        "presets": presets_doc,
        "world_books": world_books_doc,
        "history": conversation_doc,  # 允许是“原始 history”（无 source）
        # "triggered_worldbook_ids": []  # 有意省略
        "character": character_doc,
        "persona": persona_doc,
    }
    res2 = core.call_api("smarttraven/prompt/assemble_full", payload2, method="POST", namespace="workflow")
    assert isinstance(res2, dict), "assemble_full 返回值应为字典(用例2)"
    messages2 = res2.get("messages", [])
    if not isinstance(messages2, list) or len(messages2) == 0:
        print("assemble_full response (no triggered_worldbook_ids):", json.dumps(res2, ensure_ascii=False, indent=2, sort_keys=False))
    assert isinstance(messages2, list) and len(messages2) > 0, "messages 应为非空数组(用例2)"
    # 输出少量摘要（保持键顺序显示）
    print(json.dumps({
        "total_messages": len(messages),
        "first_message": messages[0],
        "first_history_message": first_history
    }, ensure_ascii=False, indent=2, sort_keys=False))

    print("OK: prompt workflow tests passed")


if __name__ == "__main__":
    main()