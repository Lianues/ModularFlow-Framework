#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：SmartTavern.data_catalog 模块
- 启动 API 网关（后台）
- 通过 core.call_api 调用：
  • smarttavern/data_catalog/list_presets
  • smarttavern/data_catalog/list_world_books
  • smarttavern/data_catalog/list_characters
  • smarttavern/data_catalog/list_personas
  • smarttavern/data_catalog/list_regex_rules
- 校验返回结构、数量与关键样例文件的字段
"""

import sys
import time
import json
from pathlib import Path

# 将仓库根目录加入 sys.path 以便 import core 门面
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core  # noqa: E402


def _ensure_gateway():
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    sm.load_project_modules()  # 自动发现并导入 api/modules 下的模块（含 data_catalog 包）
    gateway.start_server(background=True)
    time.sleep(0.4)  # 稍等网关就绪/注册完成
    return gateway


# ---------- 通用结构校验 ----------

def _assert_basic_structure(res: dict):
    assert isinstance(res, dict), "返回结果应为 dict"
    assert "folder" in res and isinstance(res["folder"], str)
    assert "total" in res and isinstance(res["total"], int)
    assert "items" in res and isinstance(res["items"], list)
    assert res["total"] == len(res["items"]), "total 应与 items 数量一致"


def _print_section(title: str, data: dict):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"[print_error] {e}")
        print(str(data))


# ---------- 预设（presets） ----------

def test_list_presets_basic_and_contains_default():
    res = core.call_api(
        "smarttavern/data_catalog/list_presets",
        {},
        method="POST",
        namespace="modules",
    )
    _assert_basic_structure(res)
    print(f"✓ list_presets 基本结构 OK (total={res['total']})")
    _print_section("list_presets response", res)

    want_path = "backend_projects/SmartTavern/data/presets/Default.json"
    items = res.get("items", [])
    default_item = next((x for x in items if str(x.get("file")) == want_path), None)
    assert default_item is not None, f"未找到 {want_path} 条目"
    assert default_item.get("name") == "默认预设", "Default.json 的 name 字段不匹配"
    assert default_item.get("description") == "这是默认预设的描述", "Default.json 的 description 字段不匹配"
    print("✓ list_presets 包含 Default.json 且字段正确")


# ---------- 世界书（world_books） ----------

def test_list_world_books_contains_sample():
    res = core.call_api(
        "smarttavern/data_catalog/list_world_books",
        {},
        method="POST",
        namespace="modules",
    )
    _assert_basic_structure(res)
    print(f"✓ list_world_books 基本结构 OK (total={res['total']})")
    _print_section("list_world_books response", res)

    want_path = "backend_projects/SmartTavern/data/world_books/参考用main_world.json"
    items = res.get("items", [])
    item = next((x for x in items if str(x.get("file")) == want_path), None)
    assert item is not None, f"未找到 {want_path} 条目"
    assert item.get("name") == "参考用main_world", "world_book 的 name 字段不匹配"
    assert item.get("description") == "这是世界书的描述", "world_book 的 description 字段不匹配"
    print("✓ list_world_books 包含参考用main_world.json 且字段正确")


# ---------- 角色卡（characters） ----------

def test_list_characters_contains_sample():
    res = core.call_api(
        "smarttavern/data_catalog/list_characters",
        {},
        method="POST",
        namespace="modules",
    )
    _assert_basic_structure(res)
    print(f"✓ list_characters 基本结构 OK (total={res['total']})")
    _print_section("list_characters response", res)

    want_path = "backend_projects/SmartTavern/data/characters/许莲笙.json"
    items = res.get("items", [])
    item = next((x for x in items if str(x.get("file")) == want_path), None)
    assert item is not None, f"未找到 {want_path} 条目"
    assert item.get("name") == "许莲笙", "角色卡 name 字段不匹配"
    desc = item.get("description")
    assert isinstance(desc, str) and len(desc) > 0, "角色卡 description 应为非空字符串"
    print("✓ list_characters 包含 许莲笙.json 且字段正确")


# ---------- 用户（persona） ----------

def test_list_personas_contains_sample():
    res = core.call_api(
        "smarttavern/data_catalog/list_personas",
        {},
        method="POST",
        namespace="modules",
    )
    _assert_basic_structure(res)
    print(f"✓ list_personas 基本结构 OK (total={res['total']})")
    _print_section("list_personas response", res)

    want_path = "backend_projects/SmartTavern/data/persona/用户2.json"
    items = res.get("items", [])
    item = next((x for x in items if str(x.get("file")) == want_path), None)
    assert item is not None, f"未找到 {want_path} 条目"
    assert item.get("name") == "用户2", "persona name 字段不匹配"
    assert item.get("description") == "新建的用户角色", "persona description 字段不匹配"
    print("✓ list_personas 包含 用户2.json 且字段正确")


# ---------- 正则规则（regex_rules） ----------

def test_list_regex_rules_contains_sample():
    res = core.call_api(
        "smarttavern/data_catalog/list_regex_rules",
        {},
        method="POST",
        namespace="modules",
    )
    _assert_basic_structure(res)
    print(f"✓ list_regex_rules 基本结构 OK (total={res['total']})")
    _print_section("list_regex_rules response", res)

    want_path = "backend_projects/SmartTavern/data/regex_rules/remove_xml_tags.json"
    items = res.get("items", [])
    item = next((x for x in items if str(x.get("file")) == want_path), None)
    assert item is not None, f"未找到 {want_path} 条目"
    # 注：样例文件当前的 name/description 使用了世界书的文案
    assert item.get("name") == "参考用main_world", "regex_rules name 字段不匹配"
    assert item.get("description") == "这是世界书的描述", "regex_rules description 字段不匹配"
    print("✓ list_regex_rules 包含 remove_xml_tags.json 且字段正确")


# ---------- 读取单个预设详情 ----------

def test_get_preset_detail_default():
    res = core.call_api(
        "smarttavern/data_catalog/get_preset_detail",
        {"file": "backend_projects/SmartTavern/data/presets/Default.json"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict), "返回结果应为 dict"
    assert res.get("file") == "backend_projects/SmartTavern/data/presets/Default.json"
    assert "content" in res and isinstance(res["content"], dict), "应返回完整 JSON 内容至 content 字段"
    assert res.get("name") == "默认预设", "name 字段不匹配"
    assert res.get("description") == "这是默认预设的描述", "description 字段不匹配"
    _print_section("get_preset_detail response", res)
    print("✓ get_preset_detail 读取 Default.json 正确")


# ---------- 读取其他类型详情 ----------

def test_get_world_book_detail_sample():
    res = core.call_api(
        "smarttavern/data_catalog/get_world_book_detail",
        {"file": "backend_projects/SmartTavern/data/world_books/参考用main_world.json"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict)
    assert res.get("file") == "backend_projects/SmartTavern/data/world_books/参考用main_world.json"
    assert "content" in res and isinstance(res["content"], dict)
    assert res.get("name") == "参考用main_world"
    assert res.get("description") == "这是世界书的描述"
    _print_section("get_world_book_detail response", res)
    print("✓ get_world_book_detail 读取参考用main_world.json 正确")


def test_get_character_detail_sample():
    res = core.call_api(
        "smarttavern/data_catalog/get_character_detail",
        {"file": "backend_projects/SmartTavern/data/characters/许莲笙.json"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict)
    assert res.get("file") == "backend_projects/SmartTavern/data/characters/许莲笙.json"
    assert "content" in res and isinstance(res["content"], dict)
    assert res.get("name") == "许莲笙"
    desc = res.get("description")
    assert isinstance(desc, str) and len(desc) > 0
    _print_section("get_character_detail response", res)
    print("✓ get_character_detail 读取 许莲笙.json 正确")


def test_get_persona_detail_sample():
    res = core.call_api(
        "smarttavern/data_catalog/get_persona_detail",
        {"file": "backend_projects/SmartTavern/data/persona/用户2.json"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict)
    assert res.get("file") == "backend_projects/SmartTavern/data/persona/用户2.json"
    assert "content" in res and isinstance(res["content"], dict)
    assert res.get("name") == "用户2"
    assert res.get("description") == "新建的用户角色"
    _print_section("get_persona_detail response", res)
    print("✓ get_persona_detail 读取 用户2.json 正确")


def test_get_regex_rule_detail_sample():
    res = core.call_api(
        "smarttavern/data_catalog/get_regex_rule_detail",
        {"file": "backend_projects/SmartTavern/data/regex_rules/remove_xml_tags.json"},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict)
    assert res.get("file") == "backend_projects/SmartTavern/data/regex_rules/remove_xml_tags.json"
    assert "content" in res and isinstance(res["content"], dict)
    # 注：样例中的 name/description 使用世界书文案
    assert res.get("name") == "参考用main_world"
    assert res.get("description") == "这是世界书的描述"
    _print_section("get_regex_rule_detail response", res)
    print("✓ get_regex_rule_detail 读取 remove_xml_tags.json 正确")


# ---------- 保存（创建/更新）端到端测试（仅对部分类型做回归） ----------

def _cleanup_file(rel_path: str):
    try:
        (ROOT / rel_path).unlink()
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"[cleanup_warning] {e}")


def test_update_preset_file_roundtrip():
    rel = "backend_projects/SmartTavern/data/presets/__tmp_update_preset.json"
    _cleanup_file(rel)

    payload_v1 = {
        "file": rel,
        "name": "保存测试-预设",
        "description": "v1 描述",
        "content": {
            "name": "should be overridden",  # 将被 name 覆盖
            "description": "should be overridden",  # 将被 description 覆盖
            "prompts": []
        }
    }
    res1 = core.call_api("smarttavern/data_catalog/update_preset_file", payload_v1, method="POST", namespace="modules")
    assert res1.get("file") == rel
    assert res1.get("name") == "保存测试-预设"
    assert res1.get("description") == "v1 描述"
    assert isinstance(res1.get("content"), dict)

    # 读取详情确认
    d1 = core.call_api("smarttavern/data_catalog/get_preset_detail", {"file": rel}, method="POST", namespace="modules")
    assert d1.get("name") == "保存测试-预设"
    assert d1.get("description") == "v1 描述"

    # 更新 v2
    payload_v2 = {
        "file": rel,
        "name": "保存测试-预设-v2",
        "description": "v2 描述",
        "content": {
            "prompts": [{"identifier": "main", "name": "Main", "position": "relative", "enabled": True, "role": "system", "content": "hi"}]
        }
    }
    res2 = core.call_api("smarttavern/data_catalog/update_preset_file", payload_v2, method="POST", namespace="modules")
    assert res2.get("name") == "保存测试-预设-v2"
    d2 = core.call_api("smarttavern/data_catalog/get_preset_detail", {"file": rel}, method="POST", namespace="modules")
    assert d2.get("name") == "保存测试-预设-v2"

    _cleanup_file(rel)


def test_update_world_book_file_roundtrip():
    rel = "backend_projects/SmartTavern/data/world_books/__tmp_update_world.json"
    _cleanup_file(rel)

    payload_v1 = {
        "file": rel,
        "name": "保存测试-世界书",
        "description": "world v1",
        "content": {
            "entries": [
                {"id": "w1", "name": "条目1", "content": "内容", "enabled": True, "mode": "always", "position": "before_char", "order": 1}
            ]
        }
    }
    res1 = core.call_api("smarttavern/data_catalog/update_world_book_file", payload_v1, method="POST", namespace="modules")
    assert res1.get("file") == rel
    assert res1.get("name") == "保存测试-世界书"

    d1 = core.call_api("smarttavern/data_catalog/get_world_book_detail", {"file": rel}, method="POST", namespace="modules")
    assert d1.get("name") == "保存测试-世界书"
    assert "entries" in (d1.get("content") or {})

    _cleanup_file(rel)


def test_update_regex_rule_file_roundtrip():
    rel = "backend_projects/SmartTavern/data/regex_rules/__tmp_update_regex.json"
    _cleanup_file(rel)

    payload = {
        "file": rel,
        "name": "保存测试-正则",
        "description": "regex v1",
        "content": {
            "name": "xx",
            "description": "yy",
            "regex_rules": [
                {"id": "r1", "name": "rule1", "enabled": True, "find_regex": "a+", "replace_regex": "a", "targets": [], "placement": "after_macro", "views": []}
            ]
        }
    }
    res = core.call_api("smarttavern/data_catalog/update_regex_rule_file", payload, method="POST", namespace="modules")
    assert res.get("file") == rel
    assert res.get("name") == "保存测试-正则"

    d1 = core.call_api("smarttavern/data_catalog/get_regex_rule_detail", {"file": rel}, method="POST", namespace="modules")
    assert d1.get("name") == "保存测试-正则"
    assert isinstance((d1.get("content") or {}).get("regex_rules"), list)

    _cleanup_file(rel)


def main():
    _ensure_gateway()
    test_list_presets_basic_and_contains_default()
    test_list_world_books_contains_sample()
    test_list_characters_contains_sample()
    test_list_personas_contains_sample()
    test_list_regex_rules_contains_sample()
    test_get_preset_detail_default()
    test_get_world_book_detail_sample()
    test_get_character_detail_sample()
    test_get_persona_detail_sample()
    test_get_regex_rule_detail_sample()
    # new: update tests
    test_update_preset_file_roundtrip()
    test_update_world_book_file_roundtrip()
    test_update_regex_rule_file_roundtrip()
    print("OK: data_catalog all tests passed")


if __name__ == "__main__":
    main()