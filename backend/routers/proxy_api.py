"""
反向代理API路由 - OpenAI兼容的护栏代理接口
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
import httpx
import json
import time
import asyncio
import uuid
from datetime import datetime

from models.requests import ProxyCompletionRequest
from models.responses import ProxyCompletionResponse, ProxyModelListResponse
from services.proxy_service import proxy_service
from services.detection_guardrail_service import detection_guardrail_service
from utils.logger import setup_logger
from enum import Enum

router = APIRouter()
logger = setup_logger()

class DetectionMode(Enum):
    """检测模式枚举"""
    ASYNC_BYPASS = "async_bypass"  # 异步旁路检测，不阻断
    SYNC_SERIAL = "sync_serial"    # 同步串行检测，阻断

def get_detection_mode(model_config, detection_type: str) -> DetectionMode:
    """根据模型配置和检测类型确定检测模式
    
    Args:
        model_config: 模型配置
        detection_type: 检测类型 ('input' | 'output')
        
    Returns:
        DetectionMode: 检测模式
    """
    if detection_type == 'input':
        # 输入检测：如果配置了阻断则使用串行模式，否则使用旁路模式
        return DetectionMode.SYNC_SERIAL if model_config.block_on_input_risk else DetectionMode.ASYNC_BYPASS
    elif detection_type == 'output':
        # 输出检测：如果配置了阻断则使用串行模式，否则使用旁路模式
        return DetectionMode.SYNC_SERIAL if model_config.block_on_output_risk else DetectionMode.ASYNC_BYPASS
    else:
        # 默认使用旁路模式
        return DetectionMode.ASYNC_BYPASS

async def perform_input_detection(model_config, input_messages: list, user_id: str, request_id: str):
    """执行输入检测 - 根据配置选择异步或同步模式"""
    detection_mode = get_detection_mode(model_config, 'input')
    
    if detection_mode == DetectionMode.ASYNC_BYPASS:
        # 异步旁路模式：不阻塞，同时启动检测和上游调用
        return await _async_input_detection(input_messages, user_id, request_id)
    else:
        # 同步串行模式：先检测，再决定是否调用上游
        return await _sync_input_detection(model_config, input_messages, user_id, request_id)

async def _async_input_detection(input_messages: list, user_id: str, request_id: str):
    """异步输入检测 - 启动后台检测任务，立即返回通过结果"""
    # 启动后台检测任务
    asyncio.create_task(_background_input_detection(input_messages, user_id, request_id))
    
    # 立即返回通过状态，允许请求继续处理
    return {
        'blocked': False,
        'detection_id': f"{request_id}_input_async",
        'suggest_answer': None
    }

async def _background_input_detection(input_messages: list, user_id: str, request_id: str):
    """后台输入检测任务 - 仅记录结果，不影响请求处理"""
    try:
        detection_result = await detection_guardrail_service.detect_messages(
            messages=input_messages,
            user_id=user_id,
            request_id=f"{request_id}_input_async"
        )
        
        # 记录检测结果但不阻断
        if detection_result.get('suggest_action') in ['拒答', '代答']:
            logger.info(f"异步输入检测发现风险但未阻断 - request {request_id}")
            logger.info(f"检测结果: {detection_result}")
            
    except Exception as e:
        logger.error(f"后台输入检测失败: {e}")

async def _sync_input_detection(model_config, input_messages: list, user_id: str, request_id: str):
    """同步输入检测 - 检测完成后再决定是否继续"""
    try:
        detection_result = await detection_guardrail_service.detect_messages(
            messages=input_messages,
            user_id=user_id,
            request_id=f"{request_id}_input_sync"
        )
        
        detection_id = detection_result.get('request_id')
        
        # 检查是否需要阻断
        if model_config.block_on_input_risk and detection_result.get('suggest_action') in ['拒答', '代答']:
            logger.warning(f"同步输入检测阻断请求 - request {request_id}")
            logger.warning(f"检测结果: {detection_result}")
            
            # 返回完整的检测结果，并添加阻断标记
            result = detection_result.copy()
            result['blocked'] = True
            # 确保detection_id字段存在（用于向后兼容）
            if 'detection_id' not in result:
                result['detection_id'] = detection_id
            return result
        
        # 检测通过
        return {
            'blocked': False,
            'detection_id': detection_id,
            'suggest_answer': None
        }
        
    except Exception as e:
        logger.error(f"同步输入检测失败: {e}")
        # 检测失败时默认通过（避免服务不可用）
        return {
            'blocked': False,
            'detection_id': f"{request_id}_input_error",
            'suggest_answer': None
        }

async def perform_output_detection(model_config, input_messages: list, response_content: str, user_id: str, request_id: str):
    """执行输出检测 - 根据配置选择异步或同步模式"""
    detection_mode = get_detection_mode(model_config, 'output')
    
    if detection_mode == DetectionMode.ASYNC_BYPASS:
        # 异步旁路模式：启动后台检测，立即返回通过结果
        return await _async_output_detection(input_messages, response_content, user_id, request_id)
    else:
        # 同步串行模式：检测完成后再返回结果
        return await _sync_output_detection(model_config, input_messages, response_content, user_id, request_id)

async def _async_output_detection(input_messages: list, response_content: str, user_id: str, request_id: str):
    """异步输出检测 - 启动后台检测任务，立即返回通过结果"""
    # 启动后台检测任务
    asyncio.create_task(_background_output_detection(input_messages, response_content, user_id, request_id))
    
    # 立即返回通过状态，允许响应直接返回给用户
    return {
        'blocked': False,
        'detection_id': f"{request_id}_output_async",
        'suggest_answer': None,
        'response_content': response_content  # 原始响应内容
    }

async def _background_output_detection(input_messages: list, response_content: str, user_id: str, request_id: str):
    """后台输出检测任务 - 仅记录结果，不影响响应"""
    try:
        # 构造检测messages: input + response
        detection_messages = input_messages.copy()
        detection_messages.append({
            "role": "assistant",
            "content": response_content
        })
        
        detection_result = await detection_guardrail_service.detect_messages(
            messages=detection_messages,
            user_id=user_id,
            request_id=f"{request_id}_output_async"
        )
        
        # 记录检测结果但不阻断
        if detection_result.get('suggest_action') in ['拒答', '代答']:
            logger.info(f"异步输出检测发现风险但未阻断 - request {request_id}")
            logger.info(f"检测结果: {detection_result}")
            
    except Exception as e:
        logger.error(f"后台输出检测失败: {e}")

async def _sync_output_detection(model_config, input_messages: list, response_content: str, user_id: str, request_id: str):
    """同步输出检测 - 检测完成后再决定返回内容"""
    try:
        # 构造检测messages: input + response
        detection_messages = input_messages.copy()
        detection_messages.append({
            "role": "assistant", 
            "content": response_content
        })
        
        detection_result = await detection_guardrail_service.detect_messages(
            messages=detection_messages,
            user_id=user_id,
            request_id=f"{request_id}_output_sync"
        )
        
        detection_id = detection_result.get('request_id')
        
        # 检查是否需要阻断输出
        if model_config.block_on_output_risk and detection_result.get('suggest_action') in ['拒答', '代答']:
            logger.warning(f"同步输出检测阻断响应 - request {request_id}")
            logger.warning(f"检测结果: {detection_result}")
            
            # 返回替代内容
            suggest_answer = detection_result.get('suggest_answer', '抱歉，生成的内容包含不当信息。')
            return {
                'blocked': True,
                'detection_id': detection_id,
                'suggest_answer': suggest_answer,
                'response_content': suggest_answer  # 替换后的内容
            }
        
        # 检测通过，返回原始内容
        return {
            'blocked': False,
            'detection_id': detection_id,
            'suggest_answer': None,
            'response_content': response_content  # 原始响应内容
        }
        
    except Exception as e:
        logger.error(f"同步输出检测失败: {e}")
        # 检测失败时默认通过（避免服务不可用）
        return {
            'blocked': False,
            'detection_id': f"{request_id}_output_error",
            'suggest_answer': None,
            'response_content': response_content  # 原始响应内容
        }

class StreamChunkDetector:
    """流式输出检测器 - 支持异步旁路和同步串行两种模式"""
    def __init__(self, detection_mode: DetectionMode = DetectionMode.ASYNC_BYPASS):
        self.chunks_buffer = []
        self.chunk_count = 0
        self.full_content = ""
        self.risk_detected = False
        self.should_stop = False
        self.detection_mode = detection_mode
        
        # 串行模式特有的状态
        self.last_chunk_held = None  # 保留的最后一个chunk
        self.all_chunks_safe = False  # 是否所有chunk都已检测安全
        self.pending_detections = set()  # 待完成的检测任务ID
        self.detection_result = None
    
    async def add_chunk(self, chunk_content: str, reasoning_content: str, model_config, input_messages: list, 
                       user_id: str, request_id: str) -> bool:
        """添加chunk并检测，返回是否应该停止流"""
        if not chunk_content.strip() and not reasoning_content.strip():
            return False
            
        self.chunks_buffer.append(chunk_content)
        # 只有在启用推理检测且有推理内容时才添加
        if reasoning_content.strip() and getattr(model_config, 'enable_reasoning_detection', True):
            self.chunks_buffer.append(f"[推理过程]{reasoning_content}")
        self.chunk_count += 1
        self.full_content += chunk_content
        # 只有在启用推理检测且有推理内容时才添加
        if reasoning_content.strip() and getattr(model_config, 'enable_reasoning_detection', True):
            self.full_content += f"\n[推理过程]{reasoning_content}"
        
        # 检查是否达到检测阈值（使用用户配置的值）
        detection_threshold = getattr(model_config, 'stream_chunk_size', 50)  # 使用配置的chunk检测间隔
        if self.chunk_count >= detection_threshold:
            if self.detection_mode == DetectionMode.ASYNC_BYPASS:
                # 异步旁路模式：启动检测但不阻塞
                asyncio.create_task(self._async_detection(model_config, input_messages, user_id, request_id))
                return False  # 不阻断流
            else:
                # 串行模式：同步检测
                return await self._sync_detection(model_config, input_messages, user_id, request_id)
        
        return False
    
    async def final_detection(self, model_config, input_messages: list, 
                            user_id: str, request_id: str) -> bool:
        """最终检测剩余chunks"""
        if self.chunks_buffer and not self.risk_detected:
            if self.detection_mode == DetectionMode.ASYNC_BYPASS:
                # 异步旁路模式：启动最终检测但不阻塞
                asyncio.create_task(self._async_detection(model_config, input_messages, user_id, request_id, is_final=True))
                return False
            else:
                # 串行模式：同步最终检测，并检查是否可以释放最后的chunk
                should_stop = await self._sync_final_detection(model_config, input_messages, user_id, request_id)
                
                # 在串行模式下，最终检测完成后标记所有chunk都安全
                if not should_stop:
                    self.all_chunks_safe = True
                
                return should_stop
        return False

    def can_release_last_chunk(self) -> bool:
        """检查是否可以释放最后保留的chunk"""
        if self.detection_mode == DetectionMode.ASYNC_BYPASS:
            # 异步模式：立即释放
            return True
        else:
            # 串行模式：只有当所有chunk都检测完成且安全时才释放
            return self.all_chunks_safe and not self.risk_detected

    def set_last_chunk(self, chunk_data: str):
        """在串行模式下设置最后保留的chunk"""
        if self.detection_mode == DetectionMode.SYNC_SERIAL:
            self.last_chunk_held = chunk_data

    def get_and_clear_last_chunk(self) -> str:
        """获取并清除最后保留的chunk"""
        chunk = self.last_chunk_held
        self.last_chunk_held = None
        return chunk

    async def _async_detection(self, model_config, input_messages: list, 
                              user_id: str, request_id: str, is_final: bool = False):
        """异步旁路检测 - 不阻塞流，仅记录检测结果"""
        if not self.chunks_buffer:
            return
            
        try:
            # 构造检测messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # 异步检测 - 结果仅用于记录
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                user_id=user_id,
                request_id=f"{request_id}_stream_async_{self.chunk_count}"
            )
            
            # 记录检测结果但不采取阻断行动
            if detection_result.get('suggest_action') in ['拒答', '代答']:
                logger.info(f"异步检测发现风险但未阻断 - chunk {self.chunk_count}, request {request_id}")
                logger.info(f"检测结果: {detection_result}")
            
            # 清空buffer为下次检测做准备
            self.chunks_buffer = []
            self.chunk_count = 0
            
        except Exception as e:
            logger.error(f"异步检测失败: {e}")

    async def _sync_detection(self, model_config, input_messages: list, 
                             user_id: str, request_id: str, is_final: bool = False) -> bool:
        """同步串行检测 - 可能阻塞流"""
        if not self.chunks_buffer:
            return False
            
        try:
            # 构造检测messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # 同步检测
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                user_id=user_id,
                request_id=f"{request_id}_stream_sync_{self.chunk_count}"
            )
            
            # 检查风险并决定是否阻断
            if detection_result.get('suggest_action') in ['拒答', '代答']:
                logger.warning(f"同步检测发现风险并阻断 - chunk {self.chunk_count}, request {request_id}")
                logger.warning(f"检测结果: {detection_result}")
                self.risk_detected = True
                self.should_stop = True
                self.detection_result = detection_result  # 保存检测结果
                return True
            
            # 清空buffer为下次检测做准备
            self.chunks_buffer = []
            self.chunk_count = 0
            return False
            
        except Exception as e:
            logger.error(f"同步检测失败: {e}")
            return False

    async def _sync_final_detection(self, model_config, input_messages: list, 
                                   user_id: str, request_id: str) -> bool:
        """同步最终检测 - 用于流结束时的检测"""
        if not self.chunks_buffer:
            return False
            
        try:
            # 构造检测messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # 同步检测
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                user_id=user_id,
                request_id=f"{request_id}_stream_final_{self.chunk_count}"
            )
            
            # 检查风险并决定是否阻断
            if detection_result.get('suggest_action') in ['拒答', '代答']:
                logger.warning(f"同步最终检测发现风险并阻断 - chunk {self.chunk_count}, request {request_id}")
                logger.warning(f"检测结果: {detection_result}")
                self.risk_detected = True
                self.should_stop = True
                self.detection_result = detection_result  # 保存检测结果
                return True
            
            # 清空buffer
            self.chunks_buffer = []
            self.chunk_count = 0
            return False
            
        except Exception as e:
            logger.error(f"同步最终检测失败: {e}")
            return False
    


async def _handle_streaming_chat_completion(
    model_config, request_data, request_id: str, user_id: str,
    input_messages: list, input_detection_id: str, input_blocked: bool, start_time: float
):
    """处理流式聊天补全"""
    try:
        # 根据配置选择检测模式
        output_detection_mode = get_detection_mode(model_config, 'output')
        detector = StreamChunkDetector(output_detection_mode)
        
        # 创建流式响应生成器
        async def stream_generator():
            try:
                # 转发流式请求（此时输入已经通过检测）
                chunks_queue = []  # 用于保存chunks的队列
                stream_ended = False
                
                async for chunk in proxy_service.forward_streaming_chat_completion(
                    model_config=model_config,
                    request_data=request_data,
                    request_id=request_id
                ):
                    chunks_queue.append(chunk)
                    
                    # 解析chunk内容
                    chunk_content = _extract_chunk_content(chunk, "content")
                    reasoning_content = ""
                    
                    # 根据配置决定是否进行reasoning检测
                    if getattr(model_config, 'enable_reasoning_detection', True):
                        try:
                            reasoning_content = _extract_chunk_content(chunk, "reasoning_content")
                        except Exception as e:
                            # 如果模型不支持reasoning字段，不会崩溃，只是记录日志
                            logger.debug(f"Model does not support reasoning_content field: {e}")
                            reasoning_content = ""
                    
                    if chunk_content or reasoning_content:
                        # 检测chunk（包含reasoning内容）
                        should_stop = await detector.add_chunk(
                            chunk_content, reasoning_content, model_config, input_messages, user_id, request_id
                        )
                        
                        if should_stop:
                            # 发送风险阻断消息并停止
                            stop_chunk = _create_stop_chunk(request_id, detector.detection_result)
                            yield f"data: {json.dumps(stop_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            break
                    
                    # 在串行模式下，保留最后一个chunk；在异步模式下，立即输出
                    if detector.detection_mode == DetectionMode.ASYNC_BYPASS:
                        # 异步模式：立即输出所有chunk
                        yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        # 串行模式：输出除最后一个chunk之外的所有chunk
                        if len(chunks_queue) > 1:
                            # 输出倒数第二个chunk
                            previous_chunk = chunks_queue[-2]
                            yield f"data: {json.dumps(previous_chunk)}\n\n"
                        
                        # 最后一个chunk先hold住，等检测完成
                        detector.set_last_chunk(json.dumps(chunk))
                
                stream_ended = True
                
                # 最终检测
                if not detector.should_stop and stream_ended:
                    should_stop = await detector.final_detection(
                        model_config, input_messages, user_id, request_id
                    )
                    if should_stop:
                        stop_chunk = _create_stop_chunk(request_id, detector.detection_result)
                        yield f"data: {json.dumps(stop_chunk)}\n\n"
                    else:
                        # 检测安全，释放最后保留的chunk（如果有的话）
                        if detector.can_release_last_chunk():
                            last_chunk_data = detector.get_and_clear_last_chunk()
                            if last_chunk_data:
                                yield f"data: {last_chunk_data}\n\n"
                
                # 正常结束
                if not detector.should_stop:
                    yield "data: [DONE]\n\n"
                    
            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                logger.error(f"Stream generation error: {e}")
                logger.error(f"Full traceback: {error_traceback}")
                error_chunk = _create_error_chunk(request_id, str(e))
                yield f"data: {json.dumps(error_chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            finally:
                # 记录日志
                await proxy_service.log_proxy_request(
                    request_id=request_id,
                    user_id=user_id,
                    proxy_config_id=str(model_config.id),
                    model_requested=request_data.model,
                    model_used=model_config.model_name,
                    provider=get_provider_from_url(model_config.api_base_url),
                    input_detection_id=input_detection_id,
                    input_blocked=input_blocked,
                    output_blocked=detector.risk_detected,
                    status="stream_blocked" if detector.should_stop else "stream_success",
                    response_time_ms=int((time.time() - start_time) * 1000)
                )
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain"
            }
        )
        
    except Exception as e:
        logger.error(f"Streaming completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "streaming_error"}}
        )


def _extract_chunk_content(chunk: dict, content_field: str = "content") -> str:
    """从SSE chunk中提取内容，支持不同的内容字段"""
    try:
        if 'choices' in chunk and chunk['choices']:
            choice = chunk['choices'][0]
            if 'delta' in choice:
                # 尝试提取指定字段的内容
                if content_field in choice['delta']:
                    return choice['delta'][content_field] or ""
                # 如果指定字段不存在，回退到content字段
                elif 'content' in choice['delta']:
                    return choice['delta']['content'] or ""
    except Exception:
        pass
    return ""


def _create_stop_chunk(request_id: str, detection_result: dict = None) -> dict:
    """创建风险阻断chunk，包含详细的检测信息"""
    chunk = {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "choices": [{
            "index": 0,
            "delta": {"content": ""},
            "finish_reason": "content_filter"
        }]
    }
    
    # 添加检测结果信息到chunk中，供客户端使用
    if detection_result:
        chunk["detection_info"] = {
            "suggest_action": detection_result.get('suggest_action'),
            "suggest_answer": detection_result.get('suggest_answer'),
            "overall_risk_level": detection_result.get('overall_risk_level'),
            "compliance_result": detection_result.get('compliance_result'),
            "security_result": detection_result.get('security_result'),
            "request_id": detection_result.get('request_id')
        }
    else:
        chunk["detection_info"] = {
            "suggest_action": "拒答",
            "suggest_answer": "抱歉，无法回答您的问题。",
            "overall_risk_level": "高风险",
            "compliance_result": None,
            "security_result": None,
            "request_id": "unknown"
        }
    
    return chunk


def _create_error_chunk(request_id: str, error_msg: str) -> dict:
    """创建错误chunk"""
    return {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion.chunk", 
        "created": int(time.time()),
        "choices": [{
            "index": 0,
            "delta": {"content": f"\n\n[错误: {error_msg}]"},
            "finish_reason": "stop"
        }]
    }

def get_provider_from_url(api_base_url: str) -> str:
    """从API base URL推断提供商名称"""
    try:
        if '//' in api_base_url:
            domain = api_base_url.split('//')[1].split('/')[0].split('.')[0]
            return domain
        return "unknown"
    except:
        return "unknown"

class OpenAIMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, int]] = None
    user: Optional[str] = None
    # OpenAI SDK额外参数支持
    extra_body: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # 允许额外的字段透传

class CompletionRequest(BaseModel):
    model: str
    prompt: Union[str, List[str]]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = 1
    stream: Optional[bool] = False
    logprobs: Optional[int] = None
    echo: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    best_of: Optional[int] = None
    logit_bias: Optional[Dict[str, int]] = None
    user: Optional[str] = None
    # OpenAI SDK额外参数支持
    extra_body: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # 允许额外的字段透传

@router.get("/v1/models")
async def list_models(request: Request):
    """列出用户配置的模型"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = auth_ctx['data']['user_id']
        models = await proxy_service.get_user_models(user_id)
        
        return {
            "object": "list",
            "data": [
                {
                    "id": model.config_name,
                    "object": "model",
                    "created": int(model.created_at.timestamp()),
                    "owned_by": model.api_base_url.split('//')[1].split('.')[0] if '//' in model.api_base_url else "unknown",
                    "permission": [],
                    "root": model.config_name,
                    "parent": None,
                    "display_name": model.config_name
                }
                for model in models
            ]
        }
    except Exception as e:
        logger.error(f"List models error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "internal_error"}}
        )

@router.post("/v1/chat/completions")
async def create_chat_completion(
    request_data: ChatCompletionRequest,
    request: Request
):
    """创建聊天补全"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = auth_ctx['data']['user_id']
        request_id = str(uuid.uuid4())
        
        logger.info(f"Chat completion request {request_id} from user {user_id} for model {request_data.model}")
        
        # 获取用户的模型配置
        model_config = await proxy_service.get_user_model_config(user_id, request_data.model)
        if not model_config:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "message": f"Model '{request_data.model}' not found. Please configure this model first.",
                        "type": "model_not_found"
                    }
                }
            )
        
        # 构造messages结构用于上下文感知检测
        input_messages = [{"role": msg.role, "content": msg.content} for msg in request_data.messages]
        
        start_time = time.time()
        input_blocked = False
        output_blocked = False
        input_detection_id = None
        output_detection_id = None
        
        try:
            # 输入检测 - 根据配置选择异步/同步模式
            input_detection_result = await perform_input_detection(
                model_config, input_messages, user_id, request_id
            )
            
            input_detection_id = input_detection_result.get('detection_id')
            input_blocked = input_detection_result.get('blocked', False)
            suggest_answer = input_detection_result.get('suggest_answer')
            
            # 如果输入被阻断，记录日志并返回
            if input_blocked:
                # 记录日志
                await proxy_service.log_proxy_request(
                        request_id=request_id,
                        user_id=user_id,
                        proxy_config_id=str(model_config.id),
                        model_requested=request_data.model,
                        model_used=model_config.model_name,
                        provider=get_provider_from_url(model_config.api_base_url),
                        input_detection_id=input_detection_id,
                        input_blocked=True,
                        status="blocked",
                        response_time_ms=int((time.time() - start_time) * 1000)
                )
                
                response = {
                    "id": f"chatcmpl-{request_id}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": request_data.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": suggest_answer
                            },
                            "finish_reason": "content_filter"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
                # 添加检测信息用于调试和用户处理
                response["detection_info"] = {
                    "suggest_action": input_detection_result.get('suggest_action'),
                    "suggest_answer": input_detection_result.get('suggest_answer'),
                    "overall_risk_level": input_detection_result.get('overall_risk_level'),
                    "compliance_result": input_detection_result.get('compliance_result'),
                    "security_result": input_detection_result.get('security_result'),
                    "request_id": input_detection_result.get('request_id')
                }
                
                # 对于流式请求，也需要直接返回阻断信息
                if request_data.stream:
                    # 为流式请求创建阻断响应生成器
                    async def blocked_stream_generator():
                        blocked_chunk = {
                            "id": f"chatcmpl-{request_id}",
                            "object": "chat.completion.chunk", 
                            "created": int(time.time()),
                            "model": request_data.model,
                            "choices": [{
                                "index": 0,
                                "delta": {"content": suggest_answer},
                                "finish_reason": "content_filter"
                            }]
                        }
                        # 添加检测信息到chunk中
                        blocked_chunk["detection_info"] = {
                            "suggest_action": input_detection_result.get('suggest_action'),
                            "suggest_answer": input_detection_result.get('suggest_answer'),
                            "overall_risk_level": input_detection_result.get('overall_risk_level'),
                            "compliance_result": input_detection_result.get('compliance_result'),
                            "security_result": input_detection_result.get('security_result'),
                            "request_id": input_detection_result.get('request_id')
                        }
                        
                        yield f"data: {json.dumps(blocked_chunk)}\n\n"
                        yield "data: [DONE]\n\n"
                    
                    return StreamingResponse(
                        blocked_stream_generator(),
                        media_type="text/plain",
                        headers={
                            "Cache-Control": "no-cache",
                            "Connection": "keep-alive",
                            "Content-Type": "text/plain"
                        }
                    )
                
                # 非流式请求返回正常响应
                return response
            
            # 检查是否为流式请求
            if request_data.stream:
                # 流式请求处理（输入未被阻断的情况）
                return await _handle_streaming_chat_completion(
                    model_config, request_data, request_id, user_id, 
                    input_messages, input_detection_id, input_blocked, start_time
                )
            
            # 转发请求到目标模型
            model_response = await proxy_service.forward_chat_completion(
                model_config=model_config,
                request_data=request_data,
                request_id=request_id
            )
            
            # 输出检测 - 根据配置选择异步/同步模式
            if model_response.get('choices'):
                output_content = model_response['choices'][0]['message']['content']
                
                # 执行输出检测
                output_detection_result = await perform_output_detection(
                    model_config, input_messages, output_content, user_id, request_id
                )
                
                output_detection_id = output_detection_result.get('detection_id')
                output_blocked = output_detection_result.get('blocked', False)
                final_content = output_detection_result.get('response_content', output_content)
                
                # 更新响应内容
                model_response['choices'][0]['message']['content'] = final_content
                if output_blocked:
                    model_response['choices'][0]['finish_reason'] = 'content_filter'
            
            # 记录成功的请求日志
            usage = model_response.get('usage', {})
            await proxy_service.log_proxy_request(
                request_id=request_id,
                user_id=user_id,
                proxy_config_id=str(model_config.id),
                model_requested=request_data.model,
                model_used=model_config.model_name,
                provider=get_provider_from_url(model_config.api_base_url),
                input_detection_id=input_detection_id,
                output_detection_id=output_detection_id,
                input_blocked=input_blocked,
                output_blocked=output_blocked,
                request_tokens=usage.get('prompt_tokens', 0),
                response_tokens=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0),
                status="success",
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return model_response
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Proxy request {request_id} failed: {e}")
            logger.error(f"Full traceback: {error_traceback}")
            
            # 记录错误日志
            await proxy_service.log_proxy_request(
                request_id=request_id,
                user_id=user_id,
                proxy_config_id=str(model_config.id),
                model_requested=request_data.model,
                model_used=model_config.model_name,
                provider=get_provider_from_url(model_config.api_base_url),
                input_detection_id=input_detection_id,
                output_detection_id=output_detection_id,
                input_blocked=input_blocked,
                output_blocked=output_blocked,
                status="error",
                error_message=str(e),
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Failed to process request",
                        "type": "api_error"
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "internal_error"}}
        )

@router.post("/v1/completions")
async def create_completion(
    request_data: CompletionRequest,
    request: Request
):
    """创建文本补全（兼容旧版OpenAI API）"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        user_id = auth_ctx['data']['user_id']
        request_id = str(uuid.uuid4())
        
        logger.info(f"Completion request {request_id} from user {user_id} for model {request_data.model}")
        
        # 获取用户的模型配置
        model_config = await proxy_service.get_user_model_config(user_id, request_data.model)
        if not model_config:
            return JSONResponse(
                status_code=404,
                content={
                    "error": {
                        "message": f"Model '{request_data.model}' not found. Please configure this model first.",
                        "type": "model_not_found"
                    }
                }
            )
        
        # 处理prompt（可能是字符串或字符串列表）并构造messages结构
        if isinstance(request_data.prompt, str):
            prompt_text = request_data.prompt
        else:
            prompt_text = "\n".join(request_data.prompt)
        
        # 为completions API构造messages结构（兼容传统的prompt格式）
        input_messages = [{"role": "user", "content": prompt_text}]
        
        start_time = time.time()
        input_blocked = False
        output_blocked = False
        input_detection_id = None
        output_detection_id = None
        
        try:
            # 输入检测 - 根据配置选择异步/同步模式
            input_detection_result = await perform_input_detection(
                model_config, input_messages, user_id, request_id
            )
            
            input_detection_id = input_detection_result.get('detection_id')
            input_blocked = input_detection_result.get('blocked', False)
            suggest_answer = input_detection_result.get('suggest_answer')
            
            # 如果输入被阻断，记录日志并返回
            if input_blocked:
                # 记录日志
                await proxy_service.log_proxy_request(
                    request_id=request_id,
                    user_id=user_id,
                    proxy_config_id=str(model_config.id),
                    model_requested=request_data.model,
                    model_used=model_config.model_name,
                    provider=get_provider_from_url(model_config.api_base_url),
                    input_detection_id=input_detection_id,
                    input_blocked=True,
                    status="blocked",
                    response_time_ms=int((time.time() - start_time) * 1000)
                )
                
                return {
                    "id": f"cmpl-{request_id}",
                    "object": "text_completion",
                    "created": int(time.time()),
                    "model": request_data.model,
                    "choices": [
                        {
                            "text": suggest_answer,
                            "index": 0,
                            "logprobs": None,
                            "finish_reason": "content_filter"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
            
            # 转发请求到目标模型
            model_response = await proxy_service.forward_completion(
                model_config=model_config,
                request_data=request_data,
                request_id=request_id
            )
            
            # 输出检测 - 根据配置选择异步/同步模式
            if model_response.get('choices'):
                output_text = model_response['choices'][0]['text']
                
                # 执行输出检测
                output_detection_result = await perform_output_detection(
                    model_config, input_messages, output_text, user_id, request_id
                )
                
                output_detection_id = output_detection_result.get('detection_id')
                output_blocked = output_detection_result.get('blocked', False)
                final_content = output_detection_result.get('response_content', output_text)
                
                # 更新响应内容
                model_response['choices'][0]['text'] = final_content
                if output_blocked:
                    model_response['choices'][0]['finish_reason'] = 'content_filter'
            
            # 记录成功的请求日志
            usage = model_response.get('usage', {})
            await proxy_service.log_proxy_request(
                request_id=request_id,
                user_id=user_id,
                proxy_config_id=str(model_config.id),
                model_requested=request_data.model,
                model_used=model_config.model_name,
                provider=get_provider_from_url(model_config.api_base_url),
                input_detection_id=input_detection_id,
                output_detection_id=output_detection_id,
                input_blocked=input_blocked,
                output_blocked=output_blocked,
                request_tokens=usage.get('prompt_tokens', 0),
                response_tokens=usage.get('completion_tokens', 0),
                total_tokens=usage.get('total_tokens', 0),
                status="success",
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return model_response
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            logger.error(f"Proxy request {request_id} failed: {e}")
            logger.error(f"Full traceback: {error_traceback}")
            
            # 记录错误日志
            await proxy_service.log_proxy_request(
                request_id=request_id,
                user_id=user_id,
                proxy_config_id=str(model_config.id),
                model_requested=request_data.model,
                model_used=model_config.model_name,
                provider=get_provider_from_url(model_config.api_base_url),
                input_detection_id=input_detection_id,
                output_detection_id=output_detection_id,
                input_blocked=input_blocked,
                output_blocked=output_blocked,
                status="error",
                error_message=str(e),
                response_time_ms=int((time.time() - start_time) * 1000)
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Failed to process request",
                        "type": "api_error"
                    }
                }
            )
    
    except Exception as e:
        logger.error(f"Completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "internal_error"}}
        )

