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