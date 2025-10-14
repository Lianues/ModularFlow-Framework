# -*- coding: utf-8 -*-
"""
SmartTavern AI 对话补全工作流 - 实现层

工作流程：
1. 读取对话文件，调用 chat_branches/openai_messages 获取 messages
2. 读取 LLM 配置文件
3. 调用 llm_api/chat 进行 AI 对话（支持流式/非流式）
4. 保存 AI 响应到对话文件（调用 chat_branches/append_message）
"""
from pathlib import Path
from typing import Any, Dict, Iterator, Optional
import json
import time

import core


def _repo_root() -> Path:
    """返回仓库根目录"""
    return Path(__file__).resolve().parents[4]


def _safe_read_json(file_path: str) -> Dict[str, Any]:
    """安全读取JSON文件"""
    root = _repo_root()
    target = (root / Path(file_path)).resolve()
    
    # 检查文件是否在 llm_configs 目录内
    llm_configs_dir = root / "backend_projects" / "SmartTavern" / "data" / "llm_configs"
    try:
        target.relative_to(llm_configs_dir)
    except ValueError:
        raise ValueError(f"LLM config file must be within llm_configs directory: {file_path}")
    
    if not target.exists():
        raise FileNotFoundError(f"LLM config file not found: {file_path}")
    
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def chat_completion_non_streaming(
    conversation_file: str,
    llm_config_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    非流式AI对话补全
    
    参数：
    - conversation_file: 对话文件路径（相对仓库根）
    - llm_config_file: LLM配置文件路径（可选，若不提供则从settings.json自动读取）
    
    返回：
      {
        "success": bool,
        "node_id": str,  # 新创建的assistant消息节点ID
        "content": str,  # AI响应内容
        "usage": dict,   # token使用统计
        "response_time": float,
        "model_used": str,
        "error": str (可选)
      }
    """
    start_time = time.time()
    
    try:
        # 步骤0：如果未提供 llm_config_file，从 settings.json 读取
        if not llm_config_file:
            settings_result = core.call_api(
                "smarttavern/chat_branches/settings",
                {"action": "get", "file": conversation_file},
                method="POST",
                namespace="modules"
            )
            if not settings_result or "settings" not in settings_result:
                raise ValueError("Failed to get settings from conversation")
            
            llm_config_file = settings_result["settings"].get("llm_config")
            if not llm_config_file:
                raise ValueError("No llm_config found in conversation settings")
        
        # 步骤1：获取对话messages
        messages_result = core.call_api(
            "smarttavern/chat_branches/openai_messages",
            {"file": conversation_file},
            method="POST",
            namespace="modules"
        )
        
        if not messages_result or "messages" not in messages_result:
            raise ValueError("Failed to get messages from conversation file")
        
        messages = messages_result["messages"]
        
        # 步骤2：读取LLM配置
        llm_config = _safe_read_json(llm_config_file)
        
        # 步骤3：调用LLM API（只使用配置文件的值，不提供默认值）
        llm_params = {
            "provider": llm_config.get("provider"),
            "api_key": llm_config.get("api_key"),
            "base_url": llm_config.get("base_url"),
            "messages": messages,
            "stream": False,  # 非流式
        }
        
        # 只添加配置文件中存在的参数
        if "model" in llm_config and llm_config["model"]:
            llm_params["model"] = llm_config["model"]
        if "max_tokens" in llm_config and llm_config["max_tokens"] is not None:
            llm_params["max_tokens"] = llm_config["max_tokens"]
        if "temperature" in llm_config and llm_config["temperature"] is not None:
            llm_params["temperature"] = llm_config["temperature"]
        if "top_p" in llm_config and llm_config["top_p"] is not None:
            llm_params["top_p"] = llm_config["top_p"]
        if "presence_penalty" in llm_config and llm_config["presence_penalty"] is not None:
            llm_params["presence_penalty"] = llm_config["presence_penalty"]
        if "frequency_penalty" in llm_config and llm_config["frequency_penalty"] is not None:
            llm_params["frequency_penalty"] = llm_config["frequency_penalty"]
        if "timeout" in llm_config and llm_config["timeout"] is not None:
            llm_params["timeout"] = llm_config["timeout"]
        if "connect_timeout" in llm_config and llm_config["connect_timeout"] is not None:
            llm_params["connect_timeout"] = llm_config["connect_timeout"]
        if "enable_logging" in llm_config:
            llm_params["enable_logging"] = llm_config["enable_logging"]
        if "custom_params" in llm_config and llm_config["custom_params"]:
            llm_params["custom_params"] = llm_config["custom_params"]
        if "safety_settings" in llm_config and llm_config["safety_settings"]:
            llm_params["safety_settings"] = llm_config["safety_settings"]
        
        llm_response = core.call_api(
            "llm_api/chat",
            llm_params,
            method="POST",
            namespace="modules"
        )
        
        if not llm_response.get("success"):
            return {
                "success": False,
                "error": llm_response.get("error", "LLM API call failed"),
                "response_time": time.time() - start_time
            }
        
        ai_content = llm_response.get("content", "")
        
        # 步骤4：保存AI响应到对话文件
        # 从 messages_result 中获取 path（active_path）
        active_path = messages_result.get("path", [])
        if not active_path:
            raise ValueError("No active_path found in conversation")
        
        parent_id = active_path[-1]
        last_node_id = active_path[-1]
        
        # 读取对话文档获取节点信息
        root = _repo_root()
        conv_file_path = (root / Path(conversation_file)).resolve()
        with conv_file_path.open("r", encoding="utf-8") as f:
            conv_doc = json.load(f)
        
        nodes = conv_doc.get("nodes", {})
        last_node = nodes.get(last_node_id, {})
        
        # 判断是否是空的 assistant 节点（重试创建的占位节点）
        is_empty_assistant = (
            last_node.get("role") == "assistant" and
            last_node.get("content", "").strip() == ""
        )
        
        if is_empty_assistant:
            # 更新现有节点
            update_result = core.call_api(
                "smarttavern/chat_branches/update_message",
                {
                    "file": conversation_file,
                    "node_id": last_node_id,
                    "content": ai_content
                },
                method="POST",
                namespace="modules"
            )
            
            return {
                "success": True,
                "node_id": last_node_id,
                "content": ai_content,
                "usage": llm_response.get("usage"),
                "response_time": time.time() - start_time,
                "model_used": llm_response.get("model_used"),
                "doc": update_result
            }
        else:
            # 创建新节点
            new_node_id = f"n_ass{int(time.time() * 1000)}"
            
            append_result = core.call_api(
                "smarttavern/chat_branches/append_message",
                {
                    "file": conversation_file,
                    "node_id": new_node_id,
                    "pid": parent_id,
                    "role": "assistant",
                    "content": ai_content
                },
                method="POST",
                namespace="modules"
            )
            
            return {
                "success": True,
                "node_id": new_node_id,
                "content": ai_content,
                "usage": llm_response.get("usage"),
                "response_time": time.time() - start_time,
                "model_used": llm_response.get("model_used"),
                "doc": append_result
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time
        }


def chat_completion_streaming(
    conversation_file: str,
    llm_config_file: Optional[str] = None,
) -> Iterator[Dict[str, Any]]:
    """
    流式AI对话补全
    
    参数：
    - conversation_file: 对话文件路径（相对仓库根）
    - llm_config_file: LLM配置文件路径（可选，若不提供则从settings.json自动读取）
    
    生成器yield：
      {"type": "chunk", "content": str}
      {"type": "finish", "finish_reason": str}
      {"type": "usage", "usage": dict}
      {"type": "saved", "node_id": str, "doc": dict}  # 保存成功
      {"type": "error", "message": str}
      {"type": "end"}
    """
    try:
        # 步骤0：如果未提供 llm_config_file，从 settings.json 读取
        if not llm_config_file:
            settings_result = core.call_api(
                "smarttavern/chat_branches/settings",
                {"action": "get", "file": conversation_file},
                method="POST",
                namespace="modules"
            )
            if not settings_result or "settings" not in settings_result:
                yield {"type": "error", "message": "Failed to get settings from conversation"}
                yield {"type": "end"}
                return
            
            llm_config_file = settings_result["settings"].get("llm_config")
            if not llm_config_file:
                yield {"type": "error", "message": "No llm_config found in conversation settings"}
                yield {"type": "end"}
                return
        
        # 步骤1：获取对话messages
        messages_result = core.call_api(
            "smarttavern/chat_branches/openai_messages",
            {"file": conversation_file},
            method="POST",
            namespace="modules"
        )
        
        if not messages_result or "messages" not in messages_result:
            yield {"type": "error", "message": "Failed to get messages from conversation file"}
            yield {"type": "end"}
            return
        
        messages = messages_result["messages"]
        active_path = messages_result.get("path", [])
        
        if not active_path:
            yield {"type": "error", "message": "No active_path found in conversation"}
            yield {"type": "end"}
            return
        
        parent_id = active_path[-1]
        
        # 步骤2：读取LLM配置
        llm_config = _safe_read_json(llm_config_file)
        
        # 步骤3：调用LLM API（流式，只使用配置文件的值）
        from api.modules.llm_api.impl import stream_chat_chunks
        
        # 构建参数（只使用配置文件中存在的值）
        stream_params = {
            "provider": llm_config.get("provider"),
            "api_key": llm_config.get("api_key"),
            "base_url": llm_config.get("base_url"),
            "messages": messages,
        }
        
        # 只添加配置文件中存在的参数
        if "model" in llm_config and llm_config["model"]:
            stream_params["model"] = llm_config["model"]
        if "max_tokens" in llm_config and llm_config["max_tokens"] is not None:
            stream_params["max_tokens"] = llm_config["max_tokens"]
        if "temperature" in llm_config and llm_config["temperature"] is not None:
            stream_params["temperature"] = llm_config["temperature"]
        if "top_p" in llm_config and llm_config["top_p"] is not None:
            stream_params["top_p"] = llm_config["top_p"]
        if "presence_penalty" in llm_config and llm_config["presence_penalty"] is not None:
            stream_params["presence_penalty"] = llm_config["presence_penalty"]
        if "frequency_penalty" in llm_config and llm_config["frequency_penalty"] is not None:
            stream_params["frequency_penalty"] = llm_config["frequency_penalty"]
        if "timeout" in llm_config and llm_config["timeout"] is not None:
            stream_params["timeout"] = llm_config["timeout"]
        if "connect_timeout" in llm_config and llm_config["connect_timeout"] is not None:
            stream_params["connect_timeout"] = llm_config["connect_timeout"]
        if "enable_logging" in llm_config:
            stream_params["enable_logging"] = llm_config["enable_logging"]
        if "custom_params" in llm_config and llm_config["custom_params"]:
            stream_params["custom_params"] = llm_config["custom_params"]
        if "safety_settings" in llm_config and llm_config["safety_settings"]:
            stream_params["safety_settings"] = llm_config["safety_settings"]
        
        chunk_iter = stream_chat_chunks(**stream_params)
        
        # 收集完整响应用于保存
        full_content = ""
        finish_reason = None
        usage = None
        has_error = False
        
        for chunk in chunk_iter:
            # 检查是否是错误
            if chunk.finish_reason == "error":
                # 错误情况：content 包含错误信息
                error_msg = chunk.content or "未知错误"
                has_error = True
                yield {"type": "error", "message": error_msg}
                yield {"type": "finish", "finish_reason": "error"}
                # 直接结束，不保存
                yield {"type": "end"}
                return
            
            if chunk.content:
                full_content += chunk.content
                yield {"type": "chunk", "content": chunk.content}
            
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason
                yield {"type": "finish", "finish_reason": chunk.finish_reason}
            
            if chunk.usage:
                usage = chunk.usage
                yield {"type": "usage", "usage": chunk.usage}
        
        # 步骤4：仅在无错误且有内容时才保存
        if not has_error and full_content:
            try:
                # 检查 active_path 末尾节点是否是空的 assistant 节点（重试场景）
                # 如果是，更新该节点；否则创建新节点
                last_node_id = active_path[-1]
                
                # 读取对话文档获取节点信息
                doc_result = core.call_api(
                    "smarttavern/chat_branches/openai_messages",
                    {"file": conversation_file},
                    method="POST",
                    namespace="modules"
                )
                
                # 从完整文档中获取节点信息（需要读取原始文件）
                import json
                root = _repo_root()
                conv_file_path = (root / Path(conversation_file)).resolve()
                with conv_file_path.open("r", encoding="utf-8") as f:
                    conv_doc = json.load(f)
                
                nodes = conv_doc.get("nodes", {})
                last_node = nodes.get(last_node_id, {})
                
                # 判断是否是空的 assistant 节点（重试创建的占位节点）
                is_empty_assistant = (
                    last_node.get("role") == "assistant" and
                    last_node.get("content", "").strip() == ""
                )
                
                if is_empty_assistant:
                    # 更新现有节点
                    update_result = core.call_api(
                        "smarttavern/chat_branches/update_message",
                        {
                            "file": conversation_file,
                            "node_id": last_node_id,
                            "content": full_content
                        },
                        method="POST",
                        namespace="modules"
                    )
                    
                    yield {
                        "type": "saved",
                        "node_id": last_node_id,
                        "doc": update_result,
                        "usage": usage
                    }
                else:
                    # 创建新节点
                    new_node_id = f"n_ass{int(time.time() * 1000)}"
                    
                    append_result = core.call_api(
                        "smarttavern/chat_branches/append_message",
                        {
                            "file": conversation_file,
                            "node_id": new_node_id,
                            "pid": parent_id,
                            "role": "assistant",
                            "content": full_content
                        },
                        method="POST",
                        namespace="modules"
                    )
                    
                    yield {
                        "type": "saved",
                        "node_id": new_node_id,
                        "doc": append_result,
                        "usage": usage
                    }
                    
            except Exception as e:
                yield {"type": "error", "message": f"Failed to save response: {str(e)}"}
        
        yield {"type": "end"}
        
    except Exception as e:
        yield {"type": "error", "message": str(e)}
        yield {"type": "end"}