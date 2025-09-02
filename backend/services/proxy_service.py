"""
代理服务 - 反向代理核心业务逻辑
"""
import httpx
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64
import os
from contextlib import asynccontextmanager

# 导入数据库相关模块
from database.connection import get_admin_db_session
from database.models import ProxyModelConfig, ProxyRequestLog
from utils.logger import setup_logger

logger = setup_logger()

class ProxyService:
    def __init__(self):
        # 初始化加密密钥
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # 高性能HTTP客户端连接池
        self.http_client = None
        self._setup_http_client()
        
    def _get_or_create_encryption_key(self) -> bytes:
        """获取或创建加密密钥"""
        from config import settings
        key_file = f"{settings.data_dir}/proxy_encryption.key"
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _setup_http_client(self):
        """设置高性能HTTP客户端"""
        # 连接池配置 - 针对高并发优化
        limits = httpx.Limits(
            max_keepalive_connections=50,  # 保持连接数
            max_connections=200,           # 最大连接数
            keepalive_expiry=30.0          # 连接保持时间
        )
        
        # 超时配置 - 为代理模型增加更长的超时时间
        timeout = httpx.Timeout(
            connect=15.0,    # 连接超时
            read=300.0,      # 读取超时增加到5分钟
            write=15.0,      # 写入超时
            pool=10.0        # 连接池超时
        )
        
        self.http_client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True,      # 启用HTTP/2
            verify=True      # SSL验证
        )
    
    async def close(self):
        """关闭HTTP客户端"""
        if self.http_client:
            await self.http_client.aclose()
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return self.cipher_suite.encrypt(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_api_key: str) -> str:
        """解密API密钥"""
        return self.cipher_suite.decrypt(encrypted_api_key.encode()).decode()
    
    async def get_user_models(self, user_id: str) -> List[ProxyModelConfig]:
        """获取用户的模型配置列表"""
        db = get_admin_db_session()
        try:
            models = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.user_id == user_id,
                ProxyModelConfig.enabled == True
            ).order_by(ProxyModelConfig.created_at).all()
            return models
        finally:
            db.close()
    
    async def get_user_model_config(self, user_id: str, model_name: str) -> Optional[ProxyModelConfig]:
        """获取用户的特定模型配置"""
        db = get_admin_db_session()
        try:
            # 先按config_name精确匹配
            model = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.user_id == user_id,
                ProxyModelConfig.config_name == model_name,
                ProxyModelConfig.enabled == True
            ).first()
            
            # 如果没找到，尝试获取第一个启用的模型
            if not model:
                model = db.query(ProxyModelConfig).filter(
                    ProxyModelConfig.user_id == user_id,
                    ProxyModelConfig.enabled == True
                ).first()
            
            return model
        finally:
            db.close()
    
    async def create_user_model(self, user_id: str, model_data: Dict[str, Any]) -> ProxyModelConfig:
        """创建用户模型配置"""
        db = get_admin_db_session()
        try:
            # 验证必要字段
            required_fields = ['config_name', 'api_base_url', 'api_key', 'model_name']
            for field in required_fields:
                if field not in model_data or not model_data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # 检查配置名称是否已存在
            existing = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.user_id == user_id,
                ProxyModelConfig.config_name == model_data['config_name']
            ).first()
            if existing:
                raise ValueError(f"Model configuration '{model_data['config_name']}' already exists")
            
            # 加密API密钥
            encrypted_api_key = self._encrypt_api_key(model_data['api_key'])
            
            model_config = ProxyModelConfig(
                user_id=user_id,
                config_name=model_data['config_name'],
                api_base_url=model_data['api_base_url'].rstrip('/'),
                api_key_encrypted=encrypted_api_key,
                model_name=model_data['model_name'],
                enabled=model_data.get('enabled', True),
                block_on_input_risk=model_data.get('block_on_input_risk', False),
                block_on_output_risk=model_data.get('block_on_output_risk', False),
                enable_reasoning_detection=model_data.get('enable_reasoning_detection', True)
            )
            

            
            db.add(model_config)
            db.commit()
            db.refresh(model_config)
            
            logger.info(f"Created proxy model config '{model_config.config_name}' for user {user_id}")
            return model_config
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def update_user_model(self, user_id: str, model_id: str, model_data: Dict[str, Any]) -> ProxyModelConfig:
        """更新用户模型配置"""
        db = get_admin_db_session()
        try:
            model_config = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.id == model_id,
                ProxyModelConfig.user_id == user_id
            ).first()
            
            if not model_config:
                raise ValueError(f"Model configuration not found")
            
            # 更新字段
            for field, value in model_data.items():
                if field == 'api_key' and value:
                    model_config.api_key_encrypted = self._encrypt_api_key(value)
                elif field in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']:
                    if value is not None:
                        setattr(model_config, field, str(value))
                elif hasattr(model_config, field):
                    setattr(model_config, field, value)
            

            
            db.commit()
            db.refresh(model_config)
            
            logger.info(f"Updated proxy model config '{model_config.config_name}' for user {user_id}")
            return model_config
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def delete_user_model(self, user_id: str, model_id: str):
        """删除用户模型配置"""
        db = get_admin_db_session()
        try:
            model_config = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.id == model_id,
                ProxyModelConfig.user_id == user_id
            ).first()
            
            if not model_config:
                raise ValueError(f"Model configuration not found")
            
            db.delete(model_config)
            db.commit()
            
            logger.info(f"Deleted proxy model config '{model_config.config_name}' for user {user_id}")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
    
    async def forward_streaming_chat_completion(
        self,
        model_config: ProxyModelConfig,
        request_data: Any,
        request_id: str
    ):
        """转发流式聊天完成请求到目标模型"""
        api_key = self._decrypt_api_key(model_config.api_key_encrypted)
        
        # 构造请求URL
        url = f"{model_config.api_base_url}/chat/completions"
        
        # 构造请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构造请求体 - 完全透传用户参数
        payload = request_data.dict(exclude_unset=True)  # 只包含用户实际传递的参数
        payload["model"] = model_config.model_name  # 替换为实际的模型名
        payload["messages"] = [{"role": msg.role, "content": msg.content} for msg in request_data.messages]
        payload["stream"] = True  # 强制开启流模式
        
        # 处理extra_body参数
        if hasattr(request_data, 'extra_body') and request_data.extra_body:
            payload.update(request_data.extra_body)
        
        try:
            async with self.http_client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.strip():
                        if line.startswith("data: "):
                            line = line[6:]  # 移除"data: "前缀
                            
                            if line.strip() == "[DONE]":
                                break
                                
                            try:
                                chunk_data = json.loads(line)
                                yield chunk_data
                            except json.JSONDecodeError:
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error forwarding streaming to {model_config.api_base_url}: {e}")
            # 安全地获取响应文本，避免未读取响应内容的错误
            try:
                error_detail = await e.response.aread() if hasattr(e.response, 'aread') else str(e)
                if isinstance(error_detail, bytes):
                    error_detail = error_detail.decode('utf-8', errors='ignore')
            except Exception:
                error_detail = f"Status code: {e.response.status_code}"
            raise Exception(f"Model API streaming error: {error_detail}")
        except httpx.RequestError as e:
            logger.error(f"Request error forwarding streaming to {model_config.api_base_url}: {e}")
            raise Exception(f"Failed to connect to model API for streaming: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in streaming request: {e}")
            raise Exception(f"Streaming request failed: {str(e)}")

    async def forward_chat_completion(
        self, 
        model_config: ProxyModelConfig, 
        request_data: Any, 
        request_id: str
    ) -> Dict[str, Any]:
        """转发聊天完成请求到目标模型"""
        api_key = self._decrypt_api_key(model_config.api_key_encrypted)
        
        # 构造请求URL
        url = f"{model_config.api_base_url}/chat/completions"
        
        # 构造请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构造请求体 - 完全透传用户参数
        payload = request_data.dict(exclude_unset=True)  # 只包含用户实际传递的参数
        payload["model"] = model_config.model_name  # 替换为实际的模型名
        payload["messages"] = [{"role": msg.role, "content": msg.content} for msg in request_data.messages]
        
        # 处理extra_body参数
        if hasattr(request_data, 'extra_body') and request_data.extra_body:
            payload.update(request_data.extra_body)
        
        # 使用共享的HTTP客户端发送请求
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # 统一返回格式，确保有id字段
            if 'id' not in result:
                result['id'] = f"chatcmpl-{request_id}"
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error forwarding to {model_config.api_base_url}: {e}")
            # 记录详细错误到日志，但只返回通用错误信息给客户端
            if hasattr(e, 'response'):
                logger.error(f"Upstream API response: {e.response.text}")
            if e.response.status_code == 401:
                raise Exception("Invalid API credentials")
            elif e.response.status_code == 403:
                raise Exception("Access forbidden by upstream API")
            elif e.response.status_code == 429:
                raise Exception("Rate limit exceeded")
            elif e.response.status_code >= 500:
                raise Exception("Upstream API service unavailable")
            else:
                raise Exception("Request failed")
        except httpx.RequestError as e:
            logger.error(f"Request error forwarding to {model_config.api_base_url}: {e}")
            raise Exception("Failed to connect to model API")
    
    async def forward_completion(
        self, 
        model_config: ProxyModelConfig, 
        request_data: Any, 
        request_id: str
    ) -> Dict[str, Any]:
        """转发文本完成请求到目标模型"""
        api_key = self._decrypt_api_key(model_config.api_key_encrypted)
        
        # 构造请求URL
        url = f"{model_config.api_base_url}/completions"
        
        # 构造请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 构造请求体
        payload = {
            "model": model_config.model_name,
            "prompt": request_data.prompt
        }
        
        # 添加可选参数
        optional_params = [
            'temperature', 'top_p', 'n', 'stream', 'logprobs', 'echo', 
            'stop', 'max_tokens', 'presence_penalty', 'frequency_penalty', 
            'best_of', 'logit_bias', 'user'
        ]
        
        for param in optional_params:
            value = getattr(request_data, param, None)
            if value is not None:
                payload[param] = value
            elif hasattr(model_config, param) and getattr(model_config, param):
                if param in ['temperature', 'top_p', 'frequency_penalty', 'presence_penalty']:
                    payload[param] = float(getattr(model_config, param))
                elif param == 'max_tokens':
                    payload[param] = model_config.max_tokens
        
        # 使用共享的HTTP客户端发送请求
        try:
            response = await self.http_client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # 统一返回格式，确保有id字段
            if 'id' not in result:
                result['id'] = f"cmpl-{request_id}"
            
            return result
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error forwarding to {model_config.api_base_url}: {e}")
            # 记录详细错误到日志，但只返回通用错误信息给客户端
            if hasattr(e, 'response'):
                logger.error(f"Upstream API response: {e.response.text}")
            if e.response.status_code == 401:
                raise Exception("Invalid API credentials")
            elif e.response.status_code == 403:
                raise Exception("Access forbidden by upstream API")
            elif e.response.status_code == 429:
                raise Exception("Rate limit exceeded")
            elif e.response.status_code >= 500:
                raise Exception("Upstream API service unavailable")
            else:
                raise Exception("Request failed")
        except httpx.RequestError as e:
            logger.error(f"Request error forwarding to {model_config.api_base_url}: {e}")
            raise Exception("Failed to connect to model API")
    
    async def log_proxy_request(
        self,
        request_id: str,
        user_id: str,
        proxy_config_id: str,
        model_requested: str,
        model_used: str,
        provider: str,
        input_detection_id: Optional[str] = None,
        output_detection_id: Optional[str] = None,
        input_blocked: bool = False,
        output_blocked: bool = False,
        request_tokens: int = 0,
        response_tokens: int = 0,
        total_tokens: int = 0,
        status: str = "success",
        error_message: Optional[str] = None,
        response_time_ms: int = 0
    ):
        """记录代理请求日志"""
        db = get_admin_db_session()
        try:
            log_entry = ProxyRequestLog(
                request_id=request_id,
                user_id=user_id,
                proxy_config_id=proxy_config_id,
                model_requested=model_requested,
                model_used=model_used,
                provider=provider,
                input_detection_id=input_detection_id,
                output_detection_id=output_detection_id,
                input_blocked=input_blocked,
                output_blocked=output_blocked,
                request_tokens=request_tokens,
                response_tokens=response_tokens,
                total_tokens=total_tokens,
                status=status,
                error_message=error_message,
                response_time_ms=response_time_ms
            )
            
            db.add(log_entry)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log proxy request {request_id}: {e}")
            db.rollback()
        finally:
            db.close()

# 创建全局实例
proxy_service = ProxyService()