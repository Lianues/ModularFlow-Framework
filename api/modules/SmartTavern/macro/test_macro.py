#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 测试：SmartTavern.macro 模块

import json
import sys
from pathlib import Path

# 兼容从子目录运行：将仓库根目录加入 sys.path
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core


def call_process(messages, variables=None):
    payload = {"messages": messages}
    if variables is not None:
        payload["variables"] = variables
    return core.call_api("smarttavern/macro/process", payload, method="POST", namespace="modules")

def call_process_text(text, variables=None):
    payload = {"text": text}
    if variables is not None:
        payload["variables"] = variables
    return core.call_api("smarttavern/macro/process_text", payload, method="POST", namespace="modules")


def main():
    # 启动 API 网关并加载模块
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    loaded = sm.load_project_modules()
    print(f"已加载模块数: {loaded}")
    gateway.start_server(background=True)

    messages = [
        {"role": "system", "content": "Start"},
        {"role": "user", "content": "Set x: {{setvar:x:1}}"},
        {"role": "assistant", "content": "x = {{getvar:x}}"},
        {"role": "assistant", "content": "undef: {{getvar:y}}"},
        {"role": "user", "content": "Nested A {{setvar:a:<<python:1+1>>}} B {{getvar:a}}"},
        {"role": "assistant", "content": "Sum <<python:3+4>>"},
    ]

    res = call_process(messages, variables={"pre": "v"})
    print(json.dumps({"macro_process_response": res}, ensure_ascii=False, indent=2, sort_keys=False))

    assert isinstance(res, dict), "返回必须为字典"
    assert "messages" in res and "variables" in res, "返回必须包含 messages 与 variables"
    out_msgs = res["messages"]
    vars_obj = res["variables"]
    assert isinstance(out_msgs, list) and len(out_msgs) == len(messages), "消息数量应该一致"
    assert isinstance(vars_obj, dict) and "initial" in vars_obj and "final" in vars_obj

    # 断言内容替换
    assert out_msgs[0]["content"] == "Start"
    assert out_msgs[1]["content"] == "Set x: ", "setvar 应被替换为空串"
    assert out_msgs[2]["content"] == "x = 1", "getvar 应读取到 set 的值"
    assert out_msgs[3]["content"] == "undef: [UndefinedVar:y]", "未定义变量应输出占位词"
    assert out_msgs[4]["content"] == "Nested A  B 2", "嵌套 python + setvar + getvar 顺序应正确"
    assert out_msgs[5]["content"] == "Sum 7", "<< >> 定界符应正常求值"

    # 断言变量表
    assert vars_obj["initial"].get("pre") == "v"
    assert vars_obj["final"].get("x") == "1"
    assert vars_obj["final"].get("a") == "2"

    print("✓ macro 顺序宏处理测试通过")

    # 新增：测试纯文本宏处理 API（默认严格模式，无 policy 输入）
    text = "a={{setvar:x:1}} b={{getvar:x}} c={{getvar:y}} d=<<python:3+4>>"
    res_text = call_process_text(text, variables={"pre": "v"})
    print(json.dumps({"macro_process_text_response": res_text}, ensure_ascii=False, indent=2, sort_keys=False))

    assert isinstance(res_text, dict) and "text" in res_text and "variables" in res_text, "返回必须包含 text 与 variables"
    assert res_text["text"] == "a= b=1 c=[UndefinedVar:y] d=7", "纯文本宏替换结果不符合预期"
    assert res_text["variables"]["initial"].get("pre") == "v", "初始变量未正确回显"
    assert res_text["variables"]["final"].get("x") == "1", "setvar 应写入变量表"

    print("✓ macro 纯文本宏处理测试通过")


if __name__ == "__main__":
    main()