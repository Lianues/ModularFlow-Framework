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
        "triggered_worldbook_ids": [2],  # 示例：cond id，可留空
        "world_books": world_books_doc,
        "presets_doc": presets_doc,
        # charDescription 需要 description，这里示例数据 description 为空也可
        "character": {"name": character_doc.get("name"), "description": character_doc.get("description", "")},
        "persona": persona_doc,
    }
    res_raw = core.call_api("smarttraven/framing_prompt/assemble", payload_raw, method="POST", namespace="modules")
    assert isinstance(res_raw, dict), "assemble 返回结果应为字典"

    prefix_msgs = res_raw.get("messages", [])
    norm_hist = res_raw.get("normalized_history", [])
    assert isinstance(prefix_msgs, list) and isinstance(norm_hist, list), "messages/normalized_history 应为数组"
    assert len(norm_hist) >= 1, "normalized_history 不应为空"
    assert isinstance(norm_hist[0].get("source"), dict), "历史第一条应包含 source 对象"
    assert norm_hist[0]["source"].get("type") == "history" and norm_hist[0]["source"].get("id") == "history_0", \
        "history[0] 的 source 应为 history_0"

    # 用例 2：history 已含 source → 期望透传 source 而不覆盖
    processed_history = [
        {"role": "user", "content": "你好", "source": {"type": "history", "id": "history_0", "index": 0}}
    ]
    payload_processed = {
        "history": processed_history,
        "triggered_worldbook_ids": [],
        "world_books": world_books_doc,
        "presets_doc": presets_doc,
    }
    res_proc = core.call_api("smarttraven/framing_prompt/assemble", payload_processed, method="POST", namespace="modules")
    norm_hist2 = res_proc.get("normalized_history", [])
    assert isinstance(norm_hist2, list) and len(norm_hist2) == 1
    assert norm_hist2[0]["source"].get("id") == "history_0" and norm_hist2[0]["source"].get("type") == "history"

    # 展示少量结果（保持键顺序显示）
    print(json.dumps({
        "prefix_count": len(prefix_msgs),
        "first_prefix": prefix_msgs[0] if prefix_msgs else None,
        "first_history": norm_hist[0] if norm_hist else None
    }, ensure_ascii=False, indent=2, sort_keys=False))

    print("OK: framing_prompt tests passed")


if __name__ == "__main__":
    main()