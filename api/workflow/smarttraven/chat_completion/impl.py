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
    llm_config_file: str,
) -> Dict[str, Any]:
    """
    非流式AI对话补全
    
    参数：
    - conversation_file: 对话文件路径（相对仓库根）
    - llm_config_file: LLM配置文件路径（相对仓库根）
    
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
        
        # 步骤3：调用LLM API
        llm_response = core.call_api(
            "llm_api/chat",
            {
                "provider": llm_config.get("provider", "openai"),
                "api_key": llm_config.get("api_key", ""),
                "base_url": llm_config.get("base_url", ""),
                "messages": messages,
                "stream": False,  # 非流式
                "model": llm_config.get("model"),
                "max_tokens": llm_config.get("max_tokens", 2048),
                "temperature": llm_config.get("temperature", 0.7),
                "top_p": llm_config.get("top_p"),
                "presence_penalty": llm_config.get("presence_penalty"),
                "frequency_penalty": llm_config.get("frequency_penalty"),
            },
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
        # 生成新节点ID
        new_node_id = f"n_ass{int(time.time() * 1000)}"
        
        # 获取当前对话文档以确定父节点
        # 从 messages_result 中获取 path（active_path）
        active_path = messages_result.get("path", [])
        if not active_path:
            raise ValueError("No active_path found in conversation")
        
        parent_id = active_path[-1]
        
        # 调用 append_message 保存AI响应
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
            "doc": append_result  # 返回更新后的文档
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time
        }


def chat_completion_streaming(
    conversation_file: str,
    llm_config_file: str,
) -> Iterator[Dict[str, Any]]:
    """
    流式AI对话补全
    
    参数：
    - conversation_file: 对话文件路径（相对仓库根）
    - llm_config_file: LLM配置文件路径（相对仓库根）
    
    生成器yield：
      {"type": "chunk", "content": str}
      {"type": "finish", "finish_reason": str}
      {"type": "usage", "usage": dict}
      {"type": "saved", "node_id": str, "doc": dict}  # 保存成功
      {"type": "error", "message": str}
      {"type": "end"}
    """
    try:
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
        
        # 步骤3：调用LLM API（流式）
        # 注意：llm_api/chat 在 stream=true 时返回 StreamingResponse (SSE)
        # 这里我们需要直接调用实现层的 stream_chat_chunks
        from api.modules.llm_api.impl import stream_chat_chunks
        
        chunk_iter = stream_chat_chunks(
            provider=llm_config.get("provider", "openai"),
            api_key=llm_config.get("api_key", ""),
            base_url=llm_config.get("base_url", ""),
            messages=messages,
            model=llm_config.get("model"),
            max_tokens=llm_config.get("max_tokens", 2048),
            temperature=llm_config.get("temperature", 0.7),
            top_p=llm_config.get("top_p"),
            presence_penalty=llm_config.get("presence_penalty"),
            frequency_penalty=llm_config.get("frequency_penalty"),
        )
        
        # 收集完整响应用于保存
        full_content = ""
        finish_reason = None
        usage = None
        
        for chunk in chunk_iter:
            if chunk.content:
                full_content += chunk.content
                yield {"type": "chunk", "content": chunk.content}
            
            if chunk.finish_reason:
                finish_reason = chunk.finish_reason
                yield {"type": "finish", "finish_reason": chunk.finish_reason}
            
            if chunk.usage:
                usage = chunk.usage
                yield {"type": "usage", "usage": chunk.usage}
        
        # 步骤4：保存完整响应到对话文件
        if full_content:
            new_node_id = f"n_ass{int(time.time() * 1000)}"
            
            try:
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