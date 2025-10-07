#!/usr/bin/env python3
# 测试：SmartTavern.in_chat_constructor 模块

import json
import pprint
import sys
from pathlib import Path

# 兼容从子目录运行：将仓库根目录加入 sys.path
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core

def main():
    # 启动 API 网关并加载模块
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    loaded = sm.load_project_modules()
    print(f"已加载模块数: {loaded}")
    gateway.start_server(background=True)

    # 准备示例数据
    history = [
        {"role": "system", "content": "系统开场"},
        {"role": "user", "content": "你好"}
    ]

    # 读取预设（仅 in-chat）
    with open("backend_projects/SmartTavern/data/presets/Default.json", "r", encoding="utf-8") as f:
        preset_doc = json.load(f)
    presets = [p for p in (preset_doc.get("prompts") or []) if str(p.get("position")) == "in-chat"]

    # 读取世界书（支持嵌套数组）
    with open("backend_projects/SmartTavern/data/world_books/参考用main_world.json", "r", encoding="utf-8") as f:
        world_books_doc = json.load(f)

    payload = {
        "history": history,
        "presets_in_chat": presets,
        "world_books": world_books_doc
    }

    print("调用 API: modules/smarttavern/in_chat_constructor/construct")
    result = core.call_api("smarttavern/in_chat_constructor/construct", payload, method="POST", namespace="modules")
    print("返回：")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=False))

    # 基本断言
    assert isinstance(result, dict), "返回必须为字典"
    assert "messages" in result, "返回必须包含 messages"
    msgs = result["messages"]
    assert isinstance(msgs, list) and len(msgs) >= 2, "messages 至少包含2条"
    for i, m in enumerate(msgs):
        assert "role" in m and "content" in m, f"第{i}条消息缺少 role/content"
        assert "source" in m and isinstance(m["source"], dict), f"第{i}条消息缺少来源字段 source"

    # 不再返回 trace，来源信息已包含在每条消息的 source 字段

    print("✓ in_chat_constructor 构造测试通过")

if __name__ == "__main__":
    main()