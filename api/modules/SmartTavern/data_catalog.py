# -*- coding: utf-8 -*-
"""
SmartTavern.data_catalog（封装层拆分说明）

本文件已精简为“转发/兼容层”，实际实现与 API 注册已迁移至：
- 实现：api/modules/SmartTavern/data_catalog/impl.py
- 注册：api/modules/SmartTavern/data_catalog/data_catalog.py

说明：
- 仅保留 import 以确保老入口仍能触发注册（避免重复注册）
- 新增模块请在 data_catalog/ 目录内按“impl.py + 注册脚本”方式编写
"""

# 兼容导入：导入注册脚本以触发 @core.register_api 装饰器
from .data_catalog.data_catalog import list_presets  # noqa: F401