#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 测试：SmartTraven.python_sandbox 模块

import json
import sys
from pathlib import Path

# 兼容从子目录运行：将仓库根目录加入 sys.path
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core


def call_eval(code, variables=None, policy=None):
    payload = {
        "code": code,
    }
    if variables is not None:
        payload["variables"] = variables
    if policy is not None:
        payload["policy"] = policy
    return core.call_api("smarttraven/python_sandbox/eval", payload, method="POST", namespace="modules")


def main():
    # 启动 API 网关并加载模块
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    loaded = sm.load_project_modules()
    print(f"已加载模块数: {loaded}")
    gateway.start_server(background=True)

    results = {}

    # 1) 简单表达式求值（字符串拼接 + 数值）
    res1 = call_eval("'Hello ' + str(1 + 2)")
    results["simple_eval"] = res1

    # 2) 初始变量 + getvar 读取
    res2 = call_eval("getvar('x')", variables={"x": "5"})
    results["getvar_defined"] = res2

    # 3) 未定义变量读取（默认占位词）
    res3 = call_eval("getvar('y')")
    results["getvar_undefined"] = res3

    # 4) vars[...] 读取已定义变量
    res4 = call_eval("vars['x']", variables={"x": "OK"})
    results["vars_subscript_defined"] = res4

    # 5) setvar 在表达式中使用（返回空串，但应更新变量）
    res5 = call_eval("setvar('y', 7)")
    results["setvar_mutation"] = res5

    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=False))

    # 断言
    assert isinstance(res1, dict) and res1.get("success") is True
    assert res1.get("result") == "Hello 3"

    assert isinstance(res2, dict) and res2.get("success") is True
    assert res2.get("result") == "5"

    assert isinstance(res3, dict) and res3.get("success") is True
    # 默认策略 undefined_get=error，error_token="[UndefinedVar:{name}]"
    assert res3.get("result") == "[UndefinedVar:y]"

    assert isinstance(res4, dict) and res4.get("success") is True
    assert res4.get("result") == "OK"

    assert isinstance(res5, dict) and res5.get("success") is True
    vf = ((res5.get("variables") or {}).get("final") or {})
    assert vf.get("y") == 7

    print("✓ python_sandbox 表达式沙盒测试通过")


if __name__ == "__main__":
    main()