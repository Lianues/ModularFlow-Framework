"""
API 封装层：模块能力对外接口 (api/modules)
为 Smarttraven.image_binding 提供统一的 @register_api 注册入口，并在路由层自动添加 '/modules' 前缀。
注意：此层仅作为对外 API 适配，实际实现位于本包 impl.py
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from core.api_registry import register_api
from .impl import ImageBindingModule
from .variables import FILE_TYPE_TAGS


@register_api(
    name="smarttraven.image_binding.embed_files_to_image",
    inputs=["image_path", "file_paths", "output_path"],
    outputs=["success", "message", "output_path", "relative_path"],
    description="将文件嵌入到PNG图片中"
)
def embed_files_to_image(image_path: str, file_paths: List[str], output_path: Optional[str] = None) -> Dict[str, Any]:
    try:
        ibm = ImageBindingModule()
        result_path = ibm.embed_files_to_image(
            image_path=str(Path(image_path)),
            file_paths=[str(Path(p)) for p in file_paths],
            output_path=str(Path(output_path)) if output_path else None
        )

        shared_dir = Path("shared/SmartTavern")
        rel_path = os.path.relpath(result_path, start=str(shared_dir)) if str(result_path).startswith(str(shared_dir)) else result_path
        return {"success": True, "message": "文件已成功嵌入到图片中", "output_path": result_path, "relative_path": rel_path}
    except Exception as e:
        return {"success": False, "message": f"嵌入文件失败: {str(e)}"}


@register_api(
    name="smarttraven.image_binding.extract_files_from_image",
    inputs=["image_path", "output_dir", "filter_types"],
    outputs=["success", "message", "files"],
    description="从PNG图片中提取文件"
)
def extract_files_from_image(image_path: str, output_dir: Optional[str] = None, filter_types: Optional[List[str]] = None) -> Dict[str, Any]:
    try:
        ibm = ImageBindingModule()
        out_dir = str(Path(output_dir)) if output_dir else None
        files = ibm.extract_files_from_image(
            image_path=str(Path(image_path)),
            output_dir=out_dir,
            filter_types=filter_types
        )
        return {"success": True, "message": f"成功从图片中提取了 {len(files)} 个文件", "files": files}
    except Exception as e:
        return {"success": False, "message": f"提取文件失败: {str(e)}", "files": []}


@register_api(
    name="smarttraven.image_binding.get_embedded_files_info",
    inputs=["image_path"],
    outputs=["success", "message", "files_info"],
    description="获取PNG图片中嵌入的文件信息"
)
def get_embedded_files_info(image_path: str) -> Dict[str, Any]:
    try:
        ibm = ImageBindingModule()
        info = ibm.get_embedded_files_info(str(Path(image_path)))
        return {"success": True, "message": f"图片包含 {len(info)} 个嵌入文件", "files_info": info}
    except Exception as e:
        return {"success": False, "message": f"获取文件信息失败: {str(e)}", "files_info": []}


@register_api(
    name="smarttraven.image_binding.is_image_with_embedded_files",
    inputs=["image_path"],
    outputs=["success", "has_embedded_files", "message"],
    description="检查PNG图片是否包含嵌入文件"
)
def is_image_with_embedded_files(image_path: str) -> Dict[str, Any]:
    try:
        ibm = ImageBindingModule()
        has = ibm.is_image_with_embedded_files(str(Path(image_path)))
        return {"success": True, "has_embedded_files": has, "message": "图片包含嵌入文件" if has else "图片不包含嵌入文件"}
    except Exception as e:
        return {"success": False, "has_embedded_files": False, "message": f"检查图片失败: {str(e)}"}


@register_api(
    name="smarttraven.image_binding.get_file_type_tags",
    outputs=["success", "file_type_tags"],
    description="获取所有支持的文件类型标签"
)
def get_file_type_tags() -> Dict[str, Any]:
    try:
        return {"success": True, "file_type_tags": FILE_TYPE_TAGS}
    except Exception as e:
        return {"success": False, "message": f"获取文件类型标签失败: {str(e)}"}