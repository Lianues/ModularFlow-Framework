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
    time.sleep(0.3)  # 稍等网关就绪
    return gateway


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    _ensure_gateway()

    # 准备 data/ 下的示例文档
    presets_doc = _read_json("backend_projects/SmartTraven/data/presets/Default.json")
    world_books_doc = _read_json("backend_projects/SmartTraven/data/world_books/参考用main_world.json")
    conversation_doc = _read_json("backend_projects/SmartTraven/data/conversations/111.json")
    character_doc = _read_json("backend_projects/SmartTraven/data/characters/心与露.json")
    persona_doc = _read_json("backend_projects/SmartTraven/data/persona/用户2.json")

    # 用例 1：history 为原始 OpenAI messages（无 source）→ 期望 normalized_history 自动补齐 source
    payload_raw = {
        "history": conversation_doc,
        "world_books": world_books_doc,
        "presets_doc": presets_doc,
        # charDescription 需要 description，这里示例数据 description 为空也可
        "character": {"name": character_doc.get("name"), "description": character_doc.get("description", "")},
        "persona": persona_doc,
    }
    res_raw = core.call_api("smarttraven/framing_prompt/assemble", payload_raw, method="POST", namespace="modules")
    assert isinstance(res_raw, dict), "assemble 返回结果应为字典"

    prefix_msgs = res_raw.get("messages", [])
    assert isinstance(prefix_msgs, list) and len(prefix_msgs) >= 1, "messages 不应为空"
    # 断言：应在“最终 messages”中检测到 history_0
    history0 = next((m for m in prefix_msgs
                     if isinstance(m.get("source"), dict)
                     and m["source"].get("type") == "history"
                     and m["source"].get("id") == "history_0"), None)
    assert history0 is not None, "应包含带来源的 history_0"
 
    # 断言：应在“最终 messages”中以顺序形式包含各项（如存在 world_book/relative 条目）
    combined = list(prefix_msgs)
    first_history_index = next((idx for idx, m in enumerate(combined)
                                if isinstance(m.get("source"), dict) and m["source"].get("type") == "history"), None)
    assert first_history_index is not None, "应当存在至少一条历史消息"

    # 用例 2：history 已含 source → 期望透传 source 而不覆盖
    processed_history = [
        {"role": "user", "content": "你好艾拉", "source": {"type": "history", "id": "history_0", "index": 0}}
    ]
    payload_processed = {
        "history": processed_history,
        "world_books": world_books_doc,
        "presets_doc": presets_doc,
    }
    res_proc = core.call_api("smarttraven/framing_prompt/assemble", payload_processed, method="POST", namespace="modules")
    proc_msgs = res_proc.get("messages", [])
    assert isinstance(proc_msgs, list) and len(proc_msgs) >= 1
    h0 = next((m for m in proc_msgs
               if isinstance(m.get("source"), dict)
               and m["source"].get("id") == "history_0"
               and m["source"].get("type") == "history"), None)
    assert h0 is not None, "已含 source 的 history_0 应被透传"

    # 直接打印完整 API 响应
    print(json.dumps({"res_raw": res_raw}, ensure_ascii=False, indent=2, sort_keys=False))

    # 用例 2 的完整响应
    print(json.dumps({"res_proc": res_proc}, ensure_ascii=False, indent=2, sort_keys=False))

    print("OK: framing_prompt tests passed")


if __name__ == "__main__":
    main()