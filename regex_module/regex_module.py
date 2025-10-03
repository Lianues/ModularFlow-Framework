#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
正则模块 (Regex Module)

提供基于规则的正则表达式替换功能。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable

from core.function_registry import register_function
from modules.SmartTavern.macro_module.macro_module import get_macro_processor

# ==============================================================================
# 数据类定义 (迁移自 data_models.py)
# ==============================================================================

@dataclass
class RegexRule:
    """正则表达式替换规则的数据类"""
    id: str
    name: str
    find_regex: str
    replace_regex: str
    enabled: bool = True
    targets: List[str] = field(default_factory=lambda: ["user", "assistant", "world_book", "preset", "assistant_thinking"])
    min_depth: Optional[int] = None
    max_depth: Optional[int] = None
    min_order: Optional[int] = None
    max_order: Optional[int] = None
    placement: str = "after_macro"
    views: List[str] = field(default_factory=list)
    description: str = ""
    enabled_expression: Any = None

# ==============================================================================
# 核心逻辑 (迁移自 RegexRuleManager)
# ==============================================================================

class RegexProcessor:
    """正则表达式规则处理器"""

    def __init__(self, rules_data: List[Dict[str, Any]], macro_evaluator: Optional[Callable] = None):
        """
        初始化处理器
        
        Args:
            rules_data: 包含规则数据的字典列表
            macro_evaluator: 用于处理宏表达式的函数
        """
        self.rules: List[RegexRule] = []
        self.compiled_rules: Dict[str, Dict[str, Any]] = {}
        self.macro_evaluator = macro_evaluator
        self._load_rules_from_data(rules_data)

    def _load_rules_from_data(self, rules_data: List[Dict[str, Any]]) -> None:
        """从字典列表加载、编译和排序规则"""
        for rule_data in rules_data:
            try:
                rule = RegexRule(
                    id=rule_data.get("id", f"rule_{len(self.rules)}"),
                    name=rule_data.get("name", "未命名规则"),
                    enabled=rule_data.get("enabled", True),
                    find_regex=rule_data.get("find_regex", ""),
                    replace_regex=rule_data.get("replace_regex", ""),
                    targets=rule_data.get("targets", ["user", "assistant", "world_book", "preset", "assistant_thinking"]),
                    min_depth=rule_data.get("min_depth"),
                    max_depth=rule_data.get("max_depth"),
                    min_order=rule_data.get("min_order"),
                    max_order=rule_data.get("max_order"),
                    placement=rule_data.get("placement", "after_macro"),
                    views=rule_data.get("views", []),
                    description=rule_data.get("description", ""),
                    enabled_expression=rule_data.get("enabled_expression")
                )
                self.rules.append(rule)
            except Exception as e:
                print(f"⚠️ 创建规则失败: {e}")
        
        self._compile_rules()
        self._sort_rules()

    def _compile_rules(self) -> None:
        """编译所有已启用规则的正则表达式"""
        self.compiled_rules = {}
        for rule in self.rules:
            if not rule.enabled:
                continue
            try:
                compiled_regex = re.compile(rule.find_regex)
                self.compiled_rules[rule.id] = {
                    "pattern": compiled_regex,
                    "replace": rule.replace_regex
                }
            except Exception as e:
                print(f"⚠️ 正则表达式编译失败 [{rule.id}]: {e}")

    def _sort_rules(self) -> None:
        """按targets数量和id排序规则"""
        self.rules.sort(key=lambda r: (len(r.targets), r.id))

    def _filter_applicable_rules(self, source_type: str, depth: Optional[int], order: Optional[int]) -> List[RegexRule]:
        """根据条件筛选适用的规则"""
        applicable = []
        for rule in self.rules:
            # 动态 enabled 检查
            is_enabled = rule.enabled
            if isinstance(is_enabled, str) and self.macro_evaluator:
                is_enabled = self.macro_evaluator(is_enabled, 'temp')
            
            if not is_enabled: continue
            if source_type not in rule.targets: continue

            if depth is not None:
                if rule.min_depth is not None and depth < rule.min_depth: continue
                if rule.max_depth is not None and depth > rule.max_depth: continue
            
            if order is not None:
                if rule.min_order is not None and order < rule.min_order: continue
                if rule.max_order is not None and order > rule.max_order: continue
            
            applicable.append(rule)
        return applicable

    def apply(self, before_macro_text: str, after_macro_text: str, source_type: str, current_view: str, depth: Optional[int] = None, order: Optional[int] = None) -> str:
        """
        将适用的正则表达式规则应用到内容
        
        Args:
            before_macro_text: 宏处理前的原始文本
            after_macro_text: 宏处理后的文本
            source_type: 内容的来源类型
            current_view: 当前视图 ('user_view' or 'assistant_view')
            depth: 内容的depth值
            order: 内容的order值

        Returns:
            处理后的内容
        """
        if not self.rules:
            return after_macro_text

        applicable_rules = self._filter_applicable_rules(source_type, depth, order)
        if not applicable_rules:
            return after_macro_text

        # 默认从宏处理后的文本开始
        processed_content = after_macro_text
        
        for rule in applicable_rules:
            if rule.id not in self.compiled_rules:
                continue
            
            # 只有当规则的views包含当前视图时，才执行替换
            if current_view in rule.views:
                # 根据 placement 选择要处理的文本
                # 注意：这里的逻辑意味着，一个规则的输出会成为下一个规则的输入
                # 如果一个宏前规则作用了，它的结果会继续被后续规则（无论是宏前还是宏后）处理
                target_text = before_macro_text if rule.placement == "before_macro" else processed_content
                
                try:
                    compiled_pattern = self.compiled_rules[rule.id]["pattern"]
                    replace_pattern = self.compiled_rules[rule.id]["replace"]
                    processed_content = compiled_pattern.sub(replace_pattern, target_text)
                except Exception as e:
                    print(f"⚠️ 应用规则失败 [{rule.id}]: {e}")
                    
        return processed_content

# ==============================================================================
# 注册函数
# ==============================================================================

@register_function(name="apply_regex_rules", outputs=["processed_text"])
def apply_regex_rules(
    before_macro_text: str,
    after_macro_text: str,
    rules: List[Dict[str, Any]],
    source_type: str,
    current_view: str,
    depth: Optional[int] = None,
    order: Optional[int] = None
) -> Dict[str, Any]:
    """
    应用一组正则表达式规则到输入文本上。

    Args:
        before_macro_text (str): 宏处理前的原始文本。
        after_macro_text (str): 宏处理后的文本。
        rules (List[Dict[str, Any]]): 一个包含正则规则对象的列表。
        source_type (str): 内容的来源类型 (e.g., 'user', 'assistant_response')。
        current_view (str): 当前视图 ('user_view' or 'assistant_view')。
        depth (Optional[int]): 内容的深度。
        order (Optional[int]): 内容的次序。

    Returns:
        Dict[str, Any]: 包含处理后文本的字典。
    """
    if not rules:
        return {"processed_text": after_macro_text}

    try:
        macro_processor = get_macro_processor()
        processor = RegexProcessor(rules, macro_evaluator=macro_processor._evaluate_enabled_expression)
        processed_text = processor.apply(
            before_macro_text=before_macro_text,
            after_macro_text=after_macro_text,
            source_type=source_type,
            current_view=current_view,
            depth=depth,
            order=order
        )
        return {"processed_text": processed_text}
    except Exception as e:
        print(f"⚠️ 正则模块执行失败: {e}")
        return {"processed_text": after_macro_text}

