"""
Reverse proxy API route - OpenAI compatible guardrail proxy interface
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
from services.ban_policy_service import BanPolicyService
from utils.i18n import get_language_from_request
from utils.logger import setup_logger
from enum import Enum

router = APIRouter()
logger = setup_logger()


async def check_user_ban_status_proxy(tenant_id: str, user_id: str):
    """Check user ban status (proxy service专用)"""
    if not user_id:
        return None

    ban_record = await BanPolicyService.check_user_banned(tenant_id, user_id)
    if ban_record:
        ban_until = ban_record['ban_until'].isoformat() if ban_record['ban_until'] else ''
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "message": "User has been banned",
                    "type": "user_banned",
                    "user_id": user_id,
                    "ban_until": ban_until,
                    "reason": ban_record.get('reason', 'Trigger ban policy')
                }
            }
        )
    return None

class DetectionMode(Enum):
    """Detection mode enumeration"""
    ASYNC_BYPASS = "async_bypass"  # Asynchronous bypass detection, no blocking
    SYNC_SERIAL = "sync_serial"    # Synchronous serial detection, blocking

def get_detection_mode(model_config, detection_type: str) -> DetectionMode:
    """Determine detection mode based on model configuration and detection type
    
    Args:
        model_config: Model configuration
        detection_type: Detection type ('input' | 'output')
        
    Returns:
        DetectionMode: Detection mode
    """
    if detection_type == 'input':
        # Input detection: if blocking is configured, use serial mode, otherwise use bypass mode
        return DetectionMode.SYNC_SERIAL if model_config.block_on_input_risk else DetectionMode.ASYNC_BYPASS
    elif detection_type == 'output':
        # Output detection: if blocking is configured, use serial mode, otherwise use bypass mode
        return DetectionMode.SYNC_SERIAL if model_config.block_on_output_risk else DetectionMode.ASYNC_BYPASS
    else:
        # Default use bypass mode
        return DetectionMode.ASYNC_BYPASS

async def perform_input_detection(model_config, input_messages: list, tenant_id: str, request_id: str, user_id: str = None):
    """Perform input detection - select asynchronous or synchronous mode based on configuration"""
    detection_mode = get_detection_mode(model_config, 'input')

    if detection_mode == DetectionMode.ASYNC_BYPASS:
        # Asynchronous bypass mode: not blocking, start detection and upstream call simultaneously
        return await _async_input_detection(input_messages, tenant_id, request_id, model_config, user_id)
    else:
        # Synchronous serial mode: first detect, then decide whether to call upstream
        return await _sync_input_detection(model_config, input_messages, tenant_id, request_id, user_id)

async def _async_input_detection(input_messages: list, tenant_id: str, request_id: str, model_config=None, user_id: str = None):
    """Asynchronous input detection - start background detection task, immediately return pass result"""
    # Start background detection task
    asyncio.create_task(_background_input_detection(input_messages, tenant_id, request_id, model_config, user_id))

    # Immediately return pass status, allow request to continue processing
    return {
        'blocked': False,
        'detection_id': f"{request_id}_input_async",
        'suggest_answer': None
    }

async def _background_input_detection(input_messages: list, tenant_id: str, request_id: str, model_config=None, user_id: str = None):
    """Background input detection task - only record result,不影响请求处理"""
    try:
        detection_result = await detection_guardrail_service.detect_messages(
            messages=input_messages,
            tenant_id=tenant_id,
            request_id=f"{request_id}_input_async"
        )

        # Record detection result but not block
        if detection_result.get('suggest_action') in ['reject', 'replace']:
            logger.info(f"Asynchronous input detection found risk but not blocked - request {request_id}")
            logger.info(f"Detection result: {detection_result}")

        # Asynchronous record risk trigger (for ban policy)
        if user_id and detection_result.get('overall_risk_level') in ['medium_risk', 'high_risk']:
            asyncio.create_task(
                BanPolicyService.check_and_apply_ban_policy(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    risk_level=detection_result.get('overall_risk_level'),
                    detection_result_id=detection_result.get('request_id'),
                    language='zh'  # Proxy service uses default Chinese
                )
            )

    except Exception as e:
        logger.error(f"Background input detection failed: {e}")

async def _sync_input_detection(model_config, input_messages: list, tenant_id: str, request_id: str, user_id: str = None):
    """Synchronous input detection - detect completed后再决定是否继续"""
    try:
        detection_result = await detection_guardrail_service.detect_messages(
            messages=input_messages,
            tenant_id=tenant_id,
            request_id=f"{request_id}_input_sync"
        )

        detection_id = detection_result.get('request_id')

        # Synchronous record risk trigger and apply ban policy
        if user_id and detection_result.get('overall_risk_level') in ['medium_risk', 'high_risk']:
            await BanPolicyService.check_and_apply_ban_policy(
                tenant_id=tenant_id,
                user_id=user_id,
                risk_level=detection_result.get('overall_risk_level'),
                detection_result_id=detection_id,
                language='zh'  # Proxy service uses default Chinese
            )

        # Check if blocking is needed
        if model_config.block_on_input_risk and detection_result.get('suggest_action') in ['reject', 'replace']:
            logger.warning(f"同步输入检测阻断请求 - request {request_id}")
            logger.warning(f"检测结果: {detection_result}")

            # Return complete detection result, and add blocking mark
            result = detection_result.copy()
            result['blocked'] = True
            # Ensure detection_id field exists (for backward compatibility)
            if 'detection_id' not in result:
                result['detection_id'] = detection_id
            return result

        # Detection passed
        return {
            'blocked': False,
            'detection_id': detection_id,
            'suggest_answer': None
        }

    except Exception as e:
        logger.error(f"Synchronous input detection failed: {e}")
        # Default pass when detection fails (to avoid service unavailable)
        return {
            'blocked': False,
            'detection_id': f"{request_id}_input_error",
            'suggest_answer': None
        }

async def perform_output_detection(model_config, input_messages: list, response_content: str, tenant_id: str, request_id: str, user_id: str = None):
    """Perform output detection - select asynchronous or synchronous mode based on configuration"""
    detection_mode = get_detection_mode(model_config, 'output')

    if detection_mode == DetectionMode.ASYNC_BYPASS:
        # Asynchronous bypass mode: start background detection, immediately return pass result
        return await _async_output_detection(input_messages, response_content, tenant_id, request_id, model_config, user_id)
    else:
        # Synchronous serial mode: detect completed后再返回结果
        return await _sync_output_detection(model_config, input_messages, response_content, tenant_id, request_id, user_id)

async def _async_output_detection(input_messages: list, response_content: str, tenant_id: str, request_id: str, model_config=None, user_id: str = None):
    """Asynchronous output detection - start background detection task, immediately return pass result"""
    # Start background detection task
    asyncio.create_task(_background_output_detection(input_messages, response_content, tenant_id, request_id, model_config, user_id))

    # Immediately return pass status, allow response to be returned directly to user
    return {
        'blocked': False,
        'detection_id': f"{request_id}_output_async",
        'suggest_answer': None,
        'response_content': response_content  # Original response content
    }

async def _background_output_detection(input_messages: list, response_content: str, tenant_id: str, request_id: str, model_config=None, user_id: str = None):
    """Background output detection task - only record result,不影响响应"""
    try:
        # Construct detection messages: input + response
        detection_messages = input_messages.copy()
        detection_messages.append({
            "role": "assistant",
            "content": response_content
        })

        detection_result = await detection_guardrail_service.detect_messages(
            messages=detection_messages,
            tenant_id=tenant_id,
            request_id=f"{request_id}_output_async"
        )

        detection_id = detection_result.get('request_id')

        # Asynchronous record risk trigger and apply ban policy (not block response)
        if user_id and detection_result.get('overall_risk_level') in ['medium_risk', 'high_risk']:
            asyncio.create_task(
                BanPolicyService.check_and_apply_ban_policy(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    risk_level=detection_result.get('overall_risk_level'),
                    detection_result_id=detection_id,
                    language='zh'  # Proxy service uses default Chinese
                )
            )

        # Record detection result but not block
        if detection_result.get('suggest_action') in ['reject', 'replace']:
            logger.info(f"Asynchronous output detection found risk but not blocked - request {request_id}")
            logger.info(f"检测结果: {detection_result}")

    except Exception as e:
        logger.error(f"Background output detection failed: {e}")

async def _sync_output_detection(model_config, input_messages: list, response_content: str, tenant_id: str, request_id: str, user_id: str = None):
    """Synchronous output detection - detect completed后再决定返回内容"""
    try:
        # 构造检测messages: input + response
        detection_messages = input_messages.copy()
        detection_messages.append({
            "role": "assistant",
            "content": response_content
        })

        detection_result = await detection_guardrail_service.detect_messages(
            messages=detection_messages,
            tenant_id=tenant_id,
            request_id=f"{request_id}_output_sync"
        )

        detection_id = detection_result.get('request_id')

        # Synchronous record risk trigger and apply ban policy
        if user_id and detection_result.get('overall_risk_level') in ['medium_risk', 'high_risk']:
            await BanPolicyService.check_and_apply_ban_policy(
                tenant_id=tenant_id,
                user_id=user_id,
                risk_level=detection_result.get('overall_risk_level'),
                detection_result_id=detection_id,
                language='zh'  # Proxy service uses default Chinese
            )

        # Check if blocking is needed
        if model_config.block_on_output_risk and detection_result.get('suggest_action') in ['reject', 'replace']:
            logger.warning(f"Synchronous output detection block response - request {request_id}")
            logger.warning(f"Detection result: {detection_result}")

            # Return alternative content
            suggest_answer = detection_result.get('suggest_answer', 'Sorry, the generated content contains inappropriate information.')
            return {
                'blocked': True,
                'detection_id': detection_id,
                'suggest_answer': suggest_answer,
                'response_content': suggest_answer  # Alternative content
            }

        # Detection passed, return original content
        return {
            'blocked': False,
            'detection_id': detection_id,
            'suggest_answer': None,
            'response_content': response_content  # Original response content
        }

    except Exception as e:
        logger.error(f"Synchronous output detection failed: {e}")
        # Default pass when detection fails (to avoid service unavailable)
        return {
            'blocked': False,
            'detection_id': f"{request_id}_output_error",
            'suggest_answer': None,
            'response_content': response_content  # Original response content
        }

class StreamChunkDetector:
    """Stream output detector - support asynchronous bypass and synchronous serial two modes"""
    def __init__(self, detection_mode: DetectionMode = DetectionMode.ASYNC_BYPASS):
        self.chunks_buffer = []
        self.chunk_count = 0
        self.full_content = ""
        self.risk_detected = False
        self.should_stop = False
        self.detection_mode = detection_mode
        
        # Serial mode specific state
        self.last_chunk_held = None  # Held last chunk
        self.all_chunks_safe = False  # Whether all chunks are detected safe
        self.pending_detections = set()  # Pending detection task ID
        self.detection_result = None
    
    async def add_chunk(self, chunk_content: str, reasoning_content: str, model_config, input_messages: list, 
                       tenant_id: str, request_id: str) -> bool:
        """Add chunk and detect, return whether to stop stream"""
        if not chunk_content.strip() and not reasoning_content.strip():
            return False
            
        self.chunks_buffer.append(chunk_content)
        # Only add when reasoning detection is enabled and there is reasoning content
        if reasoning_content.strip() and getattr(model_config, 'enable_reasoning_detection', True):
            self.chunks_buffer.append(f"[推理过程]{reasoning_content}")
        self.chunk_count += 1
        self.full_content += chunk_content
        # Only add when reasoning detection is enabled and there is reasoning content
        if reasoning_content.strip() and getattr(model_config, 'enable_reasoning_detection', True):
            self.full_content += f"\n[推理过程]{reasoning_content}"
        
        # Check if detection threshold is reached (using user configured value)
        detection_threshold = getattr(model_config, 'stream_chunk_size', 50)  # Using configured chunk detection interval
        if self.chunk_count >= detection_threshold:
            if self.detection_mode == DetectionMode.ASYNC_BYPASS:
                # Asynchronous bypass mode: start detection but not block
                asyncio.create_task(self._async_detection(model_config, input_messages, tenant_id, request_id))
                return False  # Not block stream
            else:
                # Serial mode: synchronous detection
                return await self._sync_detection(model_config, input_messages, tenant_id, request_id)
        
        return False
    
    async def final_detection(self, model_config, input_messages: list, 
                            tenant_id: str, request_id: str) -> bool:
        """Final detection remaining chunks"""
        if self.chunks_buffer and not self.risk_detected:
            if self.detection_mode == DetectionMode.ASYNC_BYPASS:
                # Asynchronous bypass mode: start final detection but not block
                asyncio.create_task(self._async_detection(model_config, input_messages, tenant_id, request_id, is_final=True))
                return False
            else:
                # Serial mode: synchronous final detection, and check if last chunk can be released
                should_stop = await self._sync_final_detection(model_config, input_messages, tenant_id, request_id)
                
                # In serial mode, mark all chunks safe after final detection
                if not should_stop:
                    self.all_chunks_safe = True
                
                return should_stop
        return False

    def can_release_last_chunk(self) -> bool:
        """Check if last chunk can be released"""
        if self.detection_mode == DetectionMode.ASYNC_BYPASS:
            # Asynchronous mode: immediately release
            return True
        else:
            # Serial mode: only release when all chunks are detected safe
            return self.all_chunks_safe and not self.risk_detected

    def set_last_chunk(self, chunk_data: str):
        """Set last chunk in serial mode"""
        if self.detection_mode == DetectionMode.SYNC_SERIAL:
            self.last_chunk_held = chunk_data

    def get_and_clear_last_chunk(self) -> str:
        """Get and clear last chunk"""
        chunk = self.last_chunk_held
        self.last_chunk_held = None
        return chunk

    async def _async_detection(self, model_config, input_messages: list, 
                              tenant_id: str, request_id: str, is_final: bool = False):
        """Asynchronous bypass detection - not block stream, only record detection result"""
        if not self.chunks_buffer:
            return
            
        try:
            # Construct detection messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # Asynchronous detection - result only for recording
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                tenant_id=tenant_id,
                request_id=f"{request_id}_stream_async_{self.chunk_count}"
            )
            
            # Record detection result but not take blocking action
            if detection_result.get('suggest_action') in ['reject', 'replace']:
                logger.info(f"Asynchronous detection found risk but not blocked - chunk {self.chunk_count}, request {request_id}")
                logger.info(f"Detection result: {detection_result}")
            
            # Clear buffer for next detection
            self.chunks_buffer = []
            self.chunk_count = 0
            
        except Exception as e:
            logger.error(f"Asynchronous detection failed: {e}")

    async def _sync_detection(self, model_config, input_messages: list, 
                             tenant_id: str, request_id: str, is_final: bool = False) -> bool:
        """Synchronous serial detection - may block stream"""
        if not self.chunks_buffer:
            return False
            
        try:
            # Construct detection messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # Synchronous detection
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                tenant_id=tenant_id,
                request_id=f"{request_id}_stream_sync_{self.chunk_count}"
            )
            
            # Check risk and decide whether to block
            if detection_result.get('suggest_action') in ['reject', 'replace']:
                logger.warning(f"Synchronous detection found risk and block - chunk {self.chunk_count}, request {request_id}")
                logger.warning(f"Detection result: {detection_result}")
                self.risk_detected = True
                self.should_stop = True
                self.detection_result = detection_result  # Save detection result
                return True
            
            # Clear buffer for next detection
            self.chunks_buffer = []
            self.chunk_count = 0
            return False
            
        except Exception as e:
            logger.error(f"Synchronous detection failed: {e}")
            return False

    async def _sync_final_detection(self, model_config, input_messages: list, 
                                   tenant_id: str, request_id: str) -> bool:
        """Synchronous final detection - used for detection at stream end"""
        if not self.chunks_buffer:
            return False
            
        try:
            # Construct detection messages
            accumulated_content = ''.join(self.chunks_buffer)
            detection_messages = input_messages.copy()
            detection_messages.append({
                "role": "assistant", 
                "content": accumulated_content
            })
            
            # Synchronous detection
            detection_result = await detection_guardrail_service.detect_messages(
                messages=detection_messages,
                tenant_id=tenant_id,
                request_id=f"{request_id}_stream_final_{self.chunk_count}"
            )
            
            # Check risk and decide whether to block
            if detection_result.get('suggest_action') in ['reject', 'replace']:
                logger.warning(f"Synchronous final detection found risk and block - chunk {self.chunk_count}, request {request_id}")
                logger.warning(f"Detection result: {detection_result}")
                self.risk_detected = True
                self.should_stop = True
                self.detection_result = detection_result  # Save detection result
                return True
            
            # Clear buffer
            self.chunks_buffer = []
            self.chunk_count = 0
            return False
            
        except Exception as e:
            logger.error(f"Synchronous final detection failed: {e}")
            return False
    


async def _handle_streaming_chat_completion(
    model_config, request_data, request_id: str, tenant_id: str,
    input_messages: list, input_detection_id: str, input_blocked: bool, start_time: float
):
    """Handle streaming chat completion"""
    try:
        # Select detection mode based on configuration
        output_detection_mode = get_detection_mode(model_config, 'output')
        detector = StreamChunkDetector(output_detection_mode)
        
        # Create streaming response generator
        async def stream_generator():
            try:
                # Forward streaming request (input has already passed detection)
                chunks_queue = []  # Queue to save chunks
                stream_ended = False
                
                async for chunk in proxy_service.forward_streaming_chat_completion(
                    model_config=model_config,
                    request_data=request_data,
                    request_id=request_id
                ):
                    chunks_queue.append(chunk)
                    
                    # Parse chunk content
                    chunk_content = _extract_chunk_content(chunk, "content")
                    reasoning_content = ""
                    
                    # Decide whether to perform reasoning detection based on configuration
                    if getattr(model_config, 'enable_reasoning_detection', True):
                        try:
                            reasoning_content = _extract_chunk_content(chunk, "reasoning_content")
                        except Exception as e:
                            # If model does not support reasoning field, it will not crash, just log
                            logger.debug(f"Model does not support reasoning_content field: {e}")
                            reasoning_content = ""
                    
                    if chunk_content or reasoning_content:
                        # Detect chunk (including reasoning content)
                        should_stop = await detector.add_chunk(
                            chunk_content, reasoning_content, model_config, input_messages, tenant_id, request_id
                        )
                        
                        if should_stop:
                            # Send risk blocking message and stop
                            stop_chunk = _create_stop_chunk(request_id, detector.detection_result)
                            yield f"data: {json.dumps(stop_chunk)}\n\n"
                            yield "data: [DONE]\n\n"
                            break
                    
                    # In serial mode, keep last chunk; in asynchronous mode, output immediately
                    if detector.detection_mode == DetectionMode.ASYNC_BYPASS:
                        # Asynchronous mode: output all chunks immediately
                        yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        # Serial mode: output all chunks except last chunk
                        if len(chunks_queue) > 1:
                            # Output second last chunk
                            previous_chunk = chunks_queue[-2]
                            yield f"data: {json.dumps(previous_chunk)}\n\n"
                        
                        # Last chunk held, wait for detection to complete
                        detector.set_last_chunk(json.dumps(chunk))
                
                stream_ended = True
                
                # Final detection
                if not detector.should_stop and stream_ended:
                    should_stop = await detector.final_detection(
                        model_config, input_messages, tenant_id, request_id
                    )
                    if should_stop:
                        stop_chunk = _create_stop_chunk(request_id, detector.detection_result)
                        yield f"data: {json.dumps(stop_chunk)}\n\n"
                    else:
                        # Detection safe, release last retained chunk (if any)
                        if detector.can_release_last_chunk():
                            last_chunk_data = detector.get_and_clear_last_chunk()
                            if last_chunk_data:
                                yield f"data: {last_chunk_data}\n\n"
                
                # Normal end
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
                # Record log
                await proxy_service.log_proxy_request(
                    request_id=request_id,
                    tenant_id=tenant_id,
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
    """Extract content from SSE chunk, support different content fields"""
    try:
        if 'choices' in chunk and chunk['choices']:
            choice = chunk['choices'][0]
            if 'delta' in choice:
                # Try to extract content from specified field
                if content_field in choice['delta']:
                    return choice['delta'][content_field] or ""
                # If specified field does not exist, fallback to content field
                elif 'content' in choice['delta']:
                    return choice['delta']['content'] or ""
    except Exception:
        pass
    return ""


def _create_stop_chunk(request_id: str, detection_result: dict = None) -> dict:
    """Create risk blocking chunk, include detailed detection information"""
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
    
    # Add detection result information to chunk for client use
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
            "suggest_action": "Reject",
            "suggest_answer": "Sorry, I cannot answer your question.",
            "overall_risk_level": "high_risk",
            "compliance_result": None,
            "security_result": None,
            "request_id": "unknown"
        }
    
    return chunk


def _create_error_chunk(request_id: str, error_msg: str) -> dict:
    """Create error chunk"""
    return {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion.chunk", 
        "created": int(time.time()),
        "choices": [{
            "index": 0,
            "delta": {"content": f"\n\n[Error: {error_msg}]"},
            "finish_reason": "stop"
        }]
    }

def get_provider_from_url(api_base_url: str) -> str:
    """Infer provider name from API base URL"""
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
    # OpenAI SDK extra parameters support
    extra_body: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow extra fields to pass through

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
    # OpenAI SDK extra parameters support
    extra_body: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow extra fields to pass through

@router.get("/v1/models")
async def list_models(request: Request):
    """List models configured for tenant"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = auth_ctx['data'].get('tenant_id') or auth_ctx['data'].get('tenant_id')
        models = await proxy_service.get_user_models(tenant_id)
        
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
    """Create chat completion"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = auth_ctx['data'].get('tenant_id') or auth_ctx['data'].get('tenant_id')
        request_id = str(uuid.uuid4())

        # Get user ID
        user_id = None
        if request_data.extra_body:
            user_id = request_data.extra_body.get('xxai_app_user_id')

        # If no user_id, use tenant_id as fallback
        if not user_id:
            user_id = tenant_id

        logger.info(f"Chat completion request {request_id} from tenant {tenant_id} for model {request_data.model}, user_id: {user_id}")

        # Check if user is banned
        await check_user_ban_status_proxy(tenant_id, user_id)

        # Get tenant's model configuration
        model_config = await proxy_service.get_user_model_config(tenant_id, request_data.model)
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
        
        # Construct messages structure for context-aware detection
        input_messages = [{"role": msg.role, "content": msg.content} for msg in request_data.messages]

        start_time = time.time()
        input_blocked = False
        output_blocked = False
        input_detection_id = None
        output_detection_id = None

        try:
            # Input detection - select asynchronous/synchronous mode based on configuration
            input_detection_result = await perform_input_detection(
                model_config, input_messages, tenant_id, request_id, user_id
            )
            
            input_detection_id = input_detection_result.get('detection_id')
            input_blocked = input_detection_result.get('blocked', False)
            suggest_answer = input_detection_result.get('suggest_answer')
            
            # If input is blocked, record log and return
            if input_blocked:
                # Record log
                await proxy_service.log_proxy_request(
                        request_id=request_id,
                        tenant_id=tenant_id,
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
                
                # Add detection information for debugging and user handling
                response["detection_info"] = {
                    "suggest_action": input_detection_result.get('suggest_action'),
                    "suggest_answer": input_detection_result.get('suggest_answer'),
                    "overall_risk_level": input_detection_result.get('overall_risk_level'),
                    "compliance_result": input_detection_result.get('compliance_result'),
                    "security_result": input_detection_result.get('security_result'),
                    "request_id": input_detection_result.get('request_id')
                }
                
                # For streaming requests, also return blocking information directly
                if request_data.stream:
                    # Create blocking response generator for streaming requests
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
                        # Add detection information to chunk
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
                
                # Non-streaming request returns normal response
                return response
            
            # Check if it is a streaming request
            if request_data.stream:
                # Streaming request handling (input is not blocked)
                return await _handle_streaming_chat_completion(
                    model_config, request_data, request_id, tenant_id, 
                    input_messages, input_detection_id, input_blocked, start_time
                )
            
            # Forward request to target model
            model_response = await proxy_service.forward_chat_completion(
                model_config=model_config,
                request_data=request_data,
                request_id=request_id
            )
            
            # Output detection - select asynchronous/synchronous mode based on configuration
            if model_response.get('choices'):
                output_content = model_response['choices'][0]['message']['content']
                
                # Perform output detection
                output_detection_result = await perform_output_detection(
                    model_config, input_messages, output_content, tenant_id, request_id, user_id
                )

                output_detection_id = output_detection_result.get('detection_id')
                output_blocked = output_detection_result.get('blocked', False)
                final_content = output_detection_result.get('response_content', output_content)
                
                # Update response content
                model_response['choices'][0]['message']['content'] = final_content
                if output_blocked:
                    model_response['choices'][0]['finish_reason'] = 'content_filter'
            
            # Record successful request log
            usage = model_response.get('usage', {})
            await proxy_service.log_proxy_request(
                request_id=request_id,
                tenant_id=tenant_id,
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
            
            # Record error log
            await proxy_service.log_proxy_request(
                request_id=request_id,
                tenant_id=tenant_id,
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
    
    except HTTPException:
        # Re-raise HTTPException to preserve status codes (e.g., 403 for banned users)
        raise
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
    """Create text completion (compatible with old OpenAI API)"""
    try:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if not auth_ctx:
            raise HTTPException(status_code=401, detail="Authentication required")

        tenant_id = auth_ctx['data'].get('tenant_id') or auth_ctx['data'].get('tenant_id')
        request_id = str(uuid.uuid4())

        # Get user ID
        user_id = None
        if request_data.extra_body:
            user_id = request_data.extra_body.get('xxai_app_user_id')

        # If no user_id, use tenant_id as fallback
        if not user_id:
            user_id = tenant_id

        logger.info(f"Completion request {request_id} from tenant {tenant_id} for model {request_data.model}, user_id: {user_id}")

        # Check if user is banned
        await check_user_ban_status_proxy(tenant_id, user_id)

        # Get tenant's model configuration
        model_config = await proxy_service.get_user_model_config(tenant_id, request_data.model)
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
        
        # Process prompt (string or string list) and construct messages structure
        if isinstance(request_data.prompt, str):
            prompt_text = request_data.prompt
        else:
            prompt_text = "\n".join(request_data.prompt)
        
        # Construct messages structure for completions API (compatible with traditional prompt format)
        input_messages = [{"role": "user", "content": prompt_text}]

        start_time = time.time()
        input_blocked = False
        output_blocked = False
        input_detection_id = None
        output_detection_id = None

        try:
            # Input detection - select asynchronous/synchronous mode based on configuration
            input_detection_result = await perform_input_detection(
                model_config, input_messages, tenant_id, request_id, user_id
            )
            
            input_detection_id = input_detection_result.get('detection_id')
            input_blocked = input_detection_result.get('blocked', False)
            suggest_answer = input_detection_result.get('suggest_answer')
            
            # If input is blocked, record log and return
            if input_blocked:
                # Record log
                await proxy_service.log_proxy_request(
                    request_id=request_id,
                    tenant_id=tenant_id,
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
            
            # Forward request to target model
            model_response = await proxy_service.forward_completion(
                model_config=model_config,
                request_data=request_data,
                request_id=request_id
            )
            
            # Output detection - select asynchronous/synchronous mode based on configuration
            if model_response.get('choices'):
                output_text = model_response['choices'][0]['text']
                
                # Perform output detection
                output_detection_result = await perform_output_detection(
                    model_config, input_messages, output_text, tenant_id, request_id, user_id
                )

                output_detection_id = output_detection_result.get('detection_id')
                output_blocked = output_detection_result.get('blocked', False)
                final_content = output_detection_result.get('response_content', output_text)
                
                # Update response content
                model_response['choices'][0]['text'] = final_content
                if output_blocked:
                    model_response['choices'][0]['finish_reason'] = 'content_filter'
            
            # Record successful request log
            usage = model_response.get('usage', {})
            await proxy_service.log_proxy_request(
                request_id=request_id,
                tenant_id=tenant_id,
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
            
            # Record error log
            await proxy_service.log_proxy_request(
                request_id=request_id,
                tenant_id=tenant_id,
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

    except HTTPException:
        # Re-raise HTTPException to preserve status codes (e.g., 403 for banned users)
        raise
    except Exception as e:
        logger.error(f"Completion error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": str(e), "type": "internal_error"}}
        )

