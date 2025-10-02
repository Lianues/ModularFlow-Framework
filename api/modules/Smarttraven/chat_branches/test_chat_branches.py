"""
测试脚本：验证 SmartTraven.chat_branches 模块的全部公共 API

运行方式（在仓库根目录）:
    python api/modules/SmartTraven/chat_branches/test_chat_branches.py

脚本会：
- 启动 API 网关（后台）
- 动态加载 api/* 模块（触发 @register_api 注册）
- 导入一个示例对话 (backend_projects/SmartTraven/data/conversations/branch_demo.json)
- 调用全部接口：列表/路径/追加/修剪/切分支/jn 指示/导出文件/OpenAI 消息/分支情况表
- 打印简要结果
"""
import json
import time
from pathlib import Path
import sys

try:
    import core
except ImportError:
    # 允许从仓库根目录外部运行时，尝试把仓库根加入 sys.path
    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    import core  # type: ignore


def pp(title: str, obj):
    print(f"\n=== {title} ===")
    if isinstance(obj, (dict, list)):
        try:
            print(json.dumps(obj, ensure_ascii=False, indent=2))
        except Exception:
            print(obj)
    else:
        print(obj)


def main():
    # 1) 启动网关 + 动态加载模块（会自动注册 API）
    gateway = core.get_api_gateway()
    svc = core.get_service_manager()
    loaded = svc.load_project_modules()
    print(f"[init] 已加载模块数量: {loaded}")
    gateway.start_server(background=True)
    time.sleep(1.0)  # 等待网关就绪

    # 2) 导入示例对话文件（chat-branches）
    demo_path = Path("backend_projects/SmartTraven/data/conversations/branch_demo.json")
    if not demo_path.exists():
        raise FileNotFoundError(f"示例文件不存在: {demo_path}")

    with demo_path.open("r", encoding="utf-8") as f:
        doc = json.load(f)

    imp = core.call_api(
        "smarttraven/chat_branches/import",
        {"doc": doc},
        method="POST",
        namespace="modules",
    )
    pp("import", imp)

    conv_id = imp["conversation_id"]
    session_id = imp["active_session_id"]

    # 3) 列表接口
    pp("list_conversations", core.call_api("smarttraven/chat_branches/list_conversations", None, method="GET", namespace="modules"))
    pp("list_sessions", core.call_api("smarttraven/chat_branches/list_sessions", {"conversation_id": conv_id}, method="GET", namespace="modules"))

    # 4) 路径与 OpenAI 消息、分支情况表
    pp("get_path", core.call_api("smarttraven/chat_branches/get_path", {"session_id": session_id}, method="GET", namespace="modules"))
    pp("openai_messages", core.call_api("smarttraven/chat_branches/openai_messages", {"session_id": session_id}, method="GET", namespace="modules"))
    pp("branch_table", core.call_api("smarttraven/chat_branches/branch_table", {"session_id": session_id}, method="GET", namespace="modules"))
    pp("branch_indicator(depth=2)", core.call_api("smarttraven/chat_branches/branch_indicator", {"session_id": session_id, "depth": 2}, method="GET", namespace="modules"))

    # 5) 追加消息 -> 修剪 -> 切分支
    pp("append", core.call_api("smarttraven/chat_branches/append", {"session_id": session_id, "role": "user", "content": "再解释下切分支"}, method="POST", namespace="modules"))
    pp("truncate", core.call_api("smarttraven/chat_branches/truncate", {"session_id": session_id, "keep_depth": 2}, method="POST", namespace="modules"))
    sw = core.call_api("smarttraven/chat_branches/switch", {"session_id": session_id, "at_depth": 2, "direction": "right"}, method="POST", namespace="modules")
    pp("switch(right at depth=2)", sw)

    new_session = sw["new_session_id"]
    pp("new_path", core.call_api("smarttraven/chat_branches/get_path", {"session_id": new_session}, method="GET", namespace="modules"))
    pp("new_branch_indicator(depth=2)", core.call_api("smarttraven/chat_branches/branch_indicator", {"session_id": new_session, "depth": 2}, method="GET", namespace="modules"))

    # 6) 导出为 chat-branches 文件
    pp("export", core.call_api("smarttraven/chat_branches/export", {"conversation_id": conv_id}, method="GET", namespace="modules"))

    print("\n[done] 全部接口测试完成。")


if __name__ == "__main__":
    main()