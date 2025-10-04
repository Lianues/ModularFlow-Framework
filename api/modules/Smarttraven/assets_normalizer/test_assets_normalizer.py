#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试：SmartTraven.assets_normalizer 模块（6个API）
- 允许使用仓库内样例数据进行集成测试
"""

import os
import sys
import json
import time
from pathlib import Path

# 将仓库根目录加入 sys.path 以便 import core 门面
ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import core  # noqa: E402


def _ensure_gateway():
    gateway = core.get_api_gateway()
    sm = core.get_service_manager()
    sm.load_project_modules()
    gateway.start_server(background=True)
    time.sleep(0.4)  # 稍等网关就绪
    return gateway


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_extract_preset_regex(preset_doc):
    res = core.call_api(
        "smarttraven/assets_normalizer/extract_preset_regex",
        {"preset": preset_doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict), "extract_preset_regex 返回应为 dict"
    assert "rules" in res and isinstance(res["rules"], list), "应包含 rules 数组"
    # Default.json 里有 1 条预设规则
    assert len(res["rules"]) == 1, f"预期 1 条预设规则，实际 {len(res['rules'])}"
    print("✓ extract_preset_regex OK")
    return res


def test_extract_character_world_book(character_doc):
    res = core.call_api(
        "smarttraven/assets_normalizer/extract_character_world_book",
        {"character": character_doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict) and "items" in res and isinstance(res["items"], list), "应包含 items 数组"
    assert len(res["items"]) >= 5, "角色卡 world_book.entries 应不少于 5 条"
    print(f"✓ extract_character_world_book OK (items={len(res['items'])})")
    return res


def test_extract_character_regex(character_doc):
    res = core.call_api(
        "smarttraven/assets_normalizer/extract_character_regex",
        {"character": character_doc},
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict) and "rules" in res and isinstance(res["rules"], list), "应包含 rules 数组"
    # 角色卡里有 5 条 regex_rules
    assert len(res["rules"]) == 5, f"预期 5 条角色卡规则，实际 {len(res['rules'])}"
    print("✓ extract_character_regex OK")
    return res


def test_merge_world_books(world_books_doc, char_wb_items):
    payload = {
        "world_books": world_books_doc,
        "character_world_book": {"items": char_wb_items}
    }
    res = core.call_api(
        "smarttraven/assets_normalizer/merge_world_books",
        payload,
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict) and "world_book" in res and isinstance(res["world_book"], list)
    merged = res["world_book"]
    assert len(merged) >= len(char_wb_items), "合并后 world_book 数量应不少于角色卡条目数"

    # 验证顺序：原世界书条目“未来都市”应在“核心”（角色卡条目）之前
    idx_future = next((i for i, x in enumerate(merged) if str(x.get("name", "")) == "未来都市"), -1)
    idx_core = next((i for i, x in enumerate(merged) if str(x.get("name", "")) == "核心"), -1)
    assert idx_future != -1 and idx_core != -1 and idx_future < idx_core, "合并顺序应为原世界书在前、角色卡在后"
    print(f"✓ merge_world_books OK (total={len(merged)})")
    return res


def test_merge_regex(independent_rules_doc, preset_rules, char_rules):
    payload = {
        "independent_regex": independent_rules_doc,   # 文件直接是数组
        "preset_regex": {"rules": preset_rules},
        "character_regex": {"rules": char_rules}
    }
    res = core.call_api(
        "smarttraven/assets_normalizer/merge_regex",
        payload,
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict) and "merged_regex" in res and isinstance(res["merged_regex"], dict)
    rules = res["merged_regex"].get("rules", [])
    assert isinstance(rules, list)
    # 期望合并总数= 2(独立) + 1(预设) + 5(角色卡) = 8（无重复 id）
    assert len(rules) == 8, f"预期 8 条合并规则，实际 {len(rules)}"
    print("✓ merge_regex OK (rules=8)")
    return res


def test_normalize_all(preset_doc, world_books_doc, character_doc, independent_rules_doc, char_wb_items, expected_rx_total):
    payload = {
        "preset": preset_doc,
        "world_books": world_books_doc,
        "character": character_doc,
        "regex_files": {"items": [independent_rules_doc]},  # 作为 {"items":[...]} 混合输入
    }
    res = core.call_api(
        "smarttraven/assets_normalizer/normalize",
        payload,
        method="POST",
        namespace="modules",
    )
    assert isinstance(res, dict)
    assert "world_book" in res and isinstance(res["world_book"], list)
    assert "merged_regex" in res and isinstance(res["merged_regex"], dict)
    # 合并的正则数量应与之前计算一致
    mrules = res["merged_regex"].get("rules", [])
    assert isinstance(mrules, list) and len(mrules) == expected_rx_total

    # 顺序断言同上（未来都市在核心之前）
    merged_wb = res["world_book"]
    idx_future = next((i for i, x in enumerate(merged_wb) if str(x.get("name", "")) == "未来都市"), -1)
    idx_core = next((i for i, x in enumerate(merged_wb) if str(x.get("name", "")) == "核心"), -1)
    assert idx_future != -1 and idx_core != -1 and idx_future < idx_core, "normalize 后世界书顺序应为原在前、角色卡在后"

    print(f"✓ normalize OK (world_book={len(merged_wb)}, merged_regex={len(mrules)})")
    return res


def main():
    _ensure_gateway()

    # 加载样例数据
    preset_doc = _read_json("backend_projects/SmartTraven/data/presets/Default.json")
    world_books_doc = _read_json("backend_projects/SmartTraven/data/world_books/参考用main_world.json")
    character_doc = _read_json("backend_projects/SmartTraven/data/characters/心与露.json")
    independent_rules_doc = _read_json("backend_projects/SmartTraven/data/regex_rules/remove_xml_tags.json")

    # 1) 提取
    ep = test_extract_preset_regex(preset_doc)
    ecw = test_extract_character_world_book(character_doc)
    ecr = test_extract_character_regex(character_doc)

    # 2) 合并（世界书）
    char_wb_items = ecw["items"]
    mwb = test_merge_world_books(world_books_doc, char_wb_items)

    # 3) 合并（正则）
    preset_rules = ep["rules"]
    char_rules = ecr["rules"]
    mrx = test_merge_regex(independent_rules_doc, preset_rules, char_rules)

    # 4) normalize（总入口）
    expected_rx_total = len(independent_rules_doc) + len(preset_rules) + len(char_rules)
    test_normalize_all(
        preset_doc,
        world_books_doc,
        character_doc,
        independent_rules_doc,
        char_wb_items,
        expected_rx_total,
    )

    print("OK: assets_normalizer all tests passed")


if __name__ == "__main__":
    main()