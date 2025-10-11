# -*- coding: utf-8 -*-
"""
API 封装层：SmartTavern.data_catalog

说明
- 遵循 DEVELOPMENT_NOTES：封装层仅做 API 注册与入参/出参契约定义；实现放在 impl.py
- 当前提供以下查询接口，返回每个文件的 name 与 description 字段（若存在）：
  • 预设（presets）
  • 世界书（world_books）
  • 角色卡（characters）
  • 用户（persona）
  • 正则规则（regex_rules）
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import core
from .impl import (
    list_presets_impl,
    list_world_books_impl,
    list_characters_impl,
    list_personas_impl,
    list_regex_rules_impl,
)


# ---------- 预设（presets） ----------

@core.register_api(
    path="smarttavern/data_catalog/list_presets",
    name="列出预设清单（名称与描述）",
    description="扫描 backend_projects/SmartTavern/data/presets 下的 JSON 文件，返回文件相对路径与其 name/description 字段（若存在）。",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "folder": {"type": "string"},
            "total": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["file"],
                    "additionalProperties": True
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": ["string", "null"]},
                        "error": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        },
        "required": ["folder", "total", "items"],
        "additionalProperties": False
    },
)
def list_presets(base_dir: Optional[str] = None,
                 fields: Optional[List[str]] = None) -> Dict[str, Any]:
    # 忽略入参，统一返回内置目录与全部字段
    return list_presets_impl()


# ---------- 世界书（world_books） ----------

@core.register_api(
    path="smarttavern/data_catalog/list_world_books",
    name="列出世界书清单（名称与描述）",
    description="扫描 backend_projects/SmartTavern/data/world_books 下的 JSON 文件，返回文件相对路径与其 name/description 字段（若存在）。",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "folder": {"type": "string"},
            "total": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["file"],
                    "additionalProperties": True
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": ["string", "null"]},
                        "error": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        },
        "required": ["folder", "total", "items"],
        "additionalProperties": False
    },
)
def list_world_books(base_dir: Optional[str] = None,
                     fields: Optional[List[str]] = None) -> Dict[str, Any]:
    # 忽略入参，统一返回内置目录与全部字段
    return list_world_books_impl()


# ---------- 角色卡（characters） ----------

@core.register_api(
    path="smarttavern/data_catalog/list_characters",
    name="列出角色卡清单（名称与描述）",
    description="扫描 backend_projects/SmartTavern/data/characters 下的 JSON 文件，返回文件相对路径与其 name/description 字段（若存在）。",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "folder": {"type": "string"},
            "total": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["file"],
                    "additionalProperties": True
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": ["string", "null"]},
                        "error": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        },
        "required": ["folder", "total", "items"],
        "additionalProperties": False
    },
)
def list_characters(base_dir: Optional[str] = None,
                    fields: Optional[List[str]] = None) -> Dict[str, Any]:
    # 忽略入参，统一返回内置目录与全部字段
    return list_characters_impl()


# ---------- 用户（persona） ----------

@core.register_api(
    path="smarttavern/data_catalog/list_personas",
    name="列出用户清单（名称与描述）",
    description="扫描 backend_projects/SmartTavern/data/persona 下的 JSON 文件，返回文件相对路径与其 name/description 字段（若存在）。",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "folder": {"type": "string"},
            "total": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["file"],
                    "additionalProperties": True
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": ["string", "null"]},
                        "error": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        },
        "required": ["folder", "total", "items"],
        "additionalProperties": False
    },
)
def list_personas(base_dir: Optional[str] = None,
                  fields: Optional[List[str]] = None) -> Dict[str, Any]:
    # 忽略入参，统一返回内置目录与全部字段
    return list_personas_impl()


# ---------- 正则规则（regex_rules） ----------

@core.register_api(
    path="smarttavern/data_catalog/list_regex_rules",
    name="列出正则规则清单（名称与描述）",
    description="扫描 backend_projects/SmartTavern/data/regex_rules 下的 JSON 文件，返回文件相对路径与其 name/description 字段（若存在）。",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "folder": {"type": "string"},
            "total": {"type": "integer"},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string"},
                        "name": {"type": ["string", "null"]},
                        "description": {"type": ["string", "null"]}
                    },
                    "required": ["file"],
                    "additionalProperties": True
                }
            },
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file": {"type": ["string", "null"]},
                        "error": {"type": "string"}
                    },
                    "required": ["error"]
                }
            }
        },
        "required": ["folder", "total", "items"],
        "additionalProperties": False
    },
)
def list_regex_rules(base_dir: Optional[str] = None,
                     fields: Optional[List[str]] = None) -> Dict[str, Any]:
    return list_regex_rules_impl()


# ---------- 获取预设详情（读取单个文件） ----------

@core.register_api(
    path="smarttavern/data_catalog/get_preset_detail",
    name="获取预设详情",
    description="读取 backend_projects/SmartTavern/data/presets 下指定 JSON 文件，返回完整内容与基础字段。",
    input_schema={
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "列表接口返回的 file 相对路径（POSIX 风格），例如 backend_projects/SmartTavern/data/presets/Default.json"
            }
        },
        "required": ["file"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "content": {"type": ["object", "array", "null"]},
            "error": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": [],
        "additionalProperties": True
    },
)
def get_preset_detail(file: str) -> Dict[str, Any]:
    # 延迟导入，避免在顶层修改 import 列表导致潜在循环
    from .impl import get_preset_detail_impl
    return get_preset_detail_impl(file=file)

# ---------- 获取世界书详情（读取单个文件） ----------

@core.register_api(
    path="smarttavern/data_catalog/get_world_book_detail",
    name="获取世界书详情",
    description="读取 backend_projects/SmartTavern/data/world_books 下指定 JSON 文件，返回完整内容与基础字段。",
    input_schema={
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "列表接口返回的 file 相对路径（POSIX 风格），例如 backend_projects/SmartTavern/data/world_books/参考用main_world.json"
            }
        },
        "required": ["file"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "content": {"type": ["object", "array", "null"]},
            "error": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": [],
        "additionalProperties": True
    },
)
def get_world_book_detail(file: str) -> Dict[str, Any]:
    from .impl import get_world_book_detail_impl
    return get_world_book_detail_impl(file=file)


# ---------- 获取角色卡详情（读取单个文件） ----------

@core.register_api(
    path="smarttavern/data_catalog/get_character_detail",
    name="获取角色卡详情",
    description="读取 backend_projects/SmartTavern/data/characters 下指定 JSON 文件，返回完整内容与基础字段。",
    input_schema={
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "列表接口返回的 file 相对路径（POSIX 风格），例如 backend_projects/SmartTavern/data/characters/许莲笙.json"
            }
        },
        "required": ["file"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "content": {"type": ["object", "array", "null"]},
            "error": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": [],
        "additionalProperties": True
    },
)
def get_character_detail(file: str) -> Dict[str, Any]:
    from .impl import get_character_detail_impl
    return get_character_detail_impl(file=file)


# ---------- 获取用户画像详情（读取单个文件） ----------

@core.register_api(
    path="smarttavern/data_catalog/get_persona_detail",
    name="获取用户画像详情",
    description="读取 backend_projects/SmartTavern/data/persona 下指定 JSON 文件，返回完整内容与基础字段。",
    input_schema={
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "列表接口返回的 file 相对路径（POSIX 风格），例如 backend_projects/SmartTavern/data/persona/用户2.json"
            }
        },
        "required": ["file"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "content": {"type": ["object", "array", "null"]},
            "error": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": [],
        "additionalProperties": True
    },
)
def get_persona_detail(file: str) -> Dict[str, Any]:
    from .impl import get_persona_detail_impl
    return get_persona_detail_impl(file=file)


# ---------- 获取正则规则详情（读取单个文件） ----------

@core.register_api(
    path="smarttavern/data_catalog/get_regex_rule_detail",
    name="获取正则规则详情",
    description="读取 backend_projects/SmartTavern/data/regex_rules 下指定 JSON 文件，返回完整内容与基础字段。",
    input_schema={
        "type": "object",
        "properties": {
            "file": {
                "type": "string",
                "description": "列表接口返回的 file 相对路径（POSIX 风格），例如 backend_projects/SmartTavern/data/regex_rules/remove_xml_tags.json"
            }
        },
        "required": ["file"],
        "additionalProperties": False
    },
    output_schema={
        "type": "object",
        "properties": {
            "file": {"type": "string"},
            "name": {"type": ["string", "null"]},
            "description": {"type": ["string", "null"]},
            "content": {"type": ["object", "array", "null"]},
            "error": {"type": "string"},
            "message": {"type": "string"}
        },
        "required": [],
        "additionalProperties": True
    },
)
def get_regex_rule_detail(file: str) -> Dict[str, Any]:
    from .impl import get_regex_rule_detail_impl
    return get_regex_rule_detail_impl(file=file)