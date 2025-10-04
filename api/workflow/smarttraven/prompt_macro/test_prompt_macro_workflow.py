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

    # 可选：角色与用户画像文档（用于 charDescription / personaDescription）
    char_doc_path = "backend_projects/SmartTraven/data/characters/许莲笙.json"
    persona_doc_path = "backend_projects/SmartTraven/data/persona/用户2.json"
    character_doc = _read_json(char_doc_path) if os.path.exists(char_doc_path) else {}
    persona_doc = _read_json(persona_doc_path) if os.path.exists(persona_doc_path) else {}

    # 宏系统所需的系统变量（最小必要集）
    variables_initial = {
        "character_name": "许莲笙",
        "user_name": "用户2",
    }

    payload = {
        "variables": variables_initial,
        "presets": presets_doc,
        "world_books": world_books_doc,
        "history": conversation_doc,  # 允许是“原始 history”（无 source）
        "character": character_doc,
        "persona": persona_doc,
    }

    # 调用新工作流 API（命名空间 workflow）
    res = core.call_api("smarttraven/prompt_macro/run", payload, method="POST", namespace="workflow")

    # 调试输出：原始响应类型与内容摘要
    try:
        print("[test_prompt_macro] res_type:", type(res).__name__)
        if isinstance(res, dict):
            print("[test_prompt_macro] res_keys:", list(res.keys()))
        else:
            print("[test_prompt_macro] res_raw:", (res if isinstance(res, str) else str(res))[:800])
    except Exception as _e:
        print("[test_prompt_macro] print_error:", _e)

    # 若返回为字符串，尝试解析 JSON
    if isinstance(res, str):
        try:
            res_parsed = json.loads(res)
            print("[test_prompt_macro] parsed_res_type:", type(res_parsed).__name__)
            if isinstance(res_parsed, dict):
                print("[test_prompt_macro] parsed_res_keys:", list(res_parsed.keys()))
                res = res_parsed
        except Exception as _e:
            print("[test_prompt_macro] json.loads failed:", _e)

    assert isinstance(res, dict), f"响应应为对象，实际类型: {type(res).__name__}"
    assert "messages" in res and "variables" in res, f"返回应包含 messages 与 variables，现有键: {list(res.keys()) if isinstance(res, dict) else 'N/A'}"

    messages = res.get("messages", [])
    variables = res.get("variables", {})
    assert isinstance(messages, list) and len(messages) > 0, "messages 应为非空数组"
    assert isinstance(variables, dict) and "initial" in variables and "final" in variables, "variables 应包含 initial/final"

    # 基础结构断言：所有消息保留 role/content/source（宏处理仅替换 content，不移除 source）
    for i, m in enumerate(messages):
        assert "role" in m and "content" in m, f"第{i}条消息缺少 role/content"
        # source 字段可能在部分前缀/历史中出现（应被保留），对存在者进行校验
        if "source" in m:
            assert isinstance(m["source"], dict), f"第{i}条消息的 source 应为对象"

    # 宏替换验证：默认预设中 enable==true 的 relative（例如 enhanceDefinitions）包含 {{char}}，应被替换为 variables.character_name
    found_macro_effect = any("许莲笙" in (m.get("content") or "") for m in messages)
    assert found_macro_effect, "期望在宏处理后的对话中出现角色名“许莲笙”（用于验证 {{char}} → character_name 的替换）"

    # 打印摘要
    print(json.dumps({
        "messages_count": len(messages),
        "variables": variables,
        "sample_contents": [m.get("content") for m in messages[:5]]
    }, ensure_ascii=False, indent=2))

    print("OK: prompt_macro workflow tests passed")


if __name__ == "__main__":
    main()