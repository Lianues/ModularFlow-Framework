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
        # 嵌套变量路径：字典与列表
        {"role": "user", "content": "{{setvar:profile.name::Alice}}{{setvar:scores[1]::5}}{{setvar:scores[3]::9}}"},
        {"role": "assistant", "content": "P={{getvar:profile.name}} S1={{getvar:scores[1]}} S3={{getvar:scores[3]}}"},
        # 传统宏（incvar/addvar/setglobalvar）对嵌套路径的支持（经转译到 Python 沙盒）
        {"role": "user", "content": "{{setglobalvar:stats.hp::10}}{{incvar:stats.hp}}{{addvar:stats.hp::5}}"},
        {"role": "assistant", "content": "HP={{getvar:stats.hp}}"},
        # 传统宏 + 列表索引路径
        {"role": "user", "content": "{{setvar:counters[0]::1}}{{decvar:counters[0]}}"},
        {"role": "assistant", "content": "C0={{getvar:counters[0]}}"},
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
    assert out_msgs[7]["content"] == "P=Alice S1=5 S3=9", "嵌套路径 get/setvar 失败"
    assert out_msgs[9]["content"] == "HP=16.0", "嵌套路径 inc/add/setglobalvar 失败"
    assert out_msgs[11]["content"] == "C0=0.0", "嵌套路径 decvar + 索引失败"

    # 断言变量表
    assert vars_obj["initial"].get("pre") == "v"
    assert vars_obj["final"].get("x") == "1"
    assert vars_obj["final"].get("a") == "2"
    # 验证最终变量嵌套结构
    assert isinstance(vars_obj["final"].get("profile"), dict)
    assert vars_obj["final"]["profile"].get("name") == "Alice"
    assert isinstance(vars_obj["final"].get("scores"), list)
    assert vars_obj["final"]["scores"][1] == "5"
    assert vars_obj["final"]["scores"][3] == "9"
    # 验证传统宏对嵌套路径的最终变量效果
    assert isinstance(vars_obj["final"].get("stats"), dict)
    assert vars_obj["final"]["stats"].get("hp") == "16.0"
    assert isinstance(vars_obj["final"].get("counters"), list)
    assert vars_obj["final"]["counters"][0] == "0.0"

    print("[OK] macro 顺序宏处理测试通过")

    # 新增：测试纯文本宏处理 API（默认严格模式，无 policy 输入）
    text = "a={{setvar:x:1}} b={{getvar:x}} c={{getvar:y}} d=<<python:3+4>>"
    res_text = call_process_text(text, variables={"pre": "v"})
    print(json.dumps({"macro_process_text_response": res_text}, ensure_ascii=False, indent=2, sort_keys=False))

    assert isinstance(res_text, dict) and "text" in res_text and "variables" in res_text, "返回必须包含 text 与 variables"
    assert res_text["text"] == "a= b=1 c=[UndefinedVar:y] d=7", "纯文本宏替换结果不符合预期"
    assert res_text["variables"]["initial"].get("pre") == "v", "初始变量未正确回显"
    assert res_text["variables"]["final"].get("x") == "1", "setvar 应写入变量表"

    print("[OK] macro 纯文本宏处理测试通过")


if __name__ == "__main__":
    main()