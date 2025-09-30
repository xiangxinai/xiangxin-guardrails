import asyncio
import httpx
import json
import math
from typing import List, Tuple, Optional
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

class ModelService:
    """模型服务类"""

    def __init__(self):
        # 创建复用的HTTP客户端以提高性能
        timeout = httpx.Timeout(30.0, connect=5.0)  # 连接超时5秒，总超时30秒
        limits = httpx.Limits(max_keepalive_connections=100, max_connections=200)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            # 关闭 HTTP/2 以避免未安装 h2 依赖导致导入错误
            http2=False
        )
        self._headers = {
            "Authorization": f"Bearer {settings.guardrails_model_api_key}",
            "Content-Type": "application/json"
        }
        self._api_url = f"{settings.guardrails_model_api_url}/chat/completions"

        # 多模态模型配置
        self._vl_headers = {
            "Authorization": f"Bearer {settings.guardrails_vl_model_api_key}",
            "Content-Type": "application/json"
        }
        self._vl_api_url = f"{settings.guardrails_vl_model_api_url}/chat/completions"
    
    async def check_messages(self, messages: List[dict]) -> str:
        """检测内容安全性"""

        try:
            return await self._call_model_api(messages)

        except Exception as e:
            logger.error(f"Model service error: {e}")
            # 返回安全的默认结果
            return "无风险"

    async def check_messages_with_confidence(self, messages: List[dict]) -> Tuple[str, Optional[float]]:
        """检测内容安全性并返回敏感度分数"""

        try:
            return await self._call_model_api_with_logprobs(messages)

        except Exception as e:
            logger.error(f"Model service error: {e}")
            # 返回安全的默认结果
            return "无风险", None

    async def check_messages_with_sensitivity(self, messages: List[dict], use_vl_model: bool = False) -> Tuple[str, Optional[float]]:
        """检测内容安全性并返回敏感度分数"""

        try:
            if use_vl_model:
                return await self._call_vl_model_api_with_logprobs(messages)
            else:
                return await self._call_model_api_with_logprobs(messages)

        except Exception as e:
            logger.error(f"Model service error: {e}")
            # 返回安全的默认结果
            return "无风险", None
    
    async def _call_model_api(self, messages: List[dict]) -> str:
        """调用模型API（使用复用的客户端）"""
        try:
            logger.debug("Calling model API...")  # 降低日志级别，减少I/O
            
            payload = {
                "model": settings.guardrails_model_name,
                "messages": messages,
                "temperature": 0.0
            }
            
            # 使用复用的客户端，避免重复创建连接
            response = await self._client.post(
                self._api_url,
                json=payload,
                headers=self._headers
            )
            
            if response.status_code == 200:
                result_data = response.json()
                result = result_data["choices"][0]["message"]["content"].strip()
                logger.debug(f"Model response: {result}")
                return result
            else:
                logger.error(f"Model API error: {response.status_code} - {response.text}")
                raise Exception(f"API call failed with status {response.status_code}")
        
        except Exception as e:
            logger.error(f"Model API error: {e}")
            raise

    async def _call_model_api_with_logprobs(self, messages: List[dict]) -> Tuple[str, Optional[float]]:
        """调用模型API并获取logprobs来计算敏感度"""
        try:
            logger.debug("Calling model API with logprobs...")

            payload = {
                "model": settings.guardrails_model_name,
                "messages": messages,
                "temperature": 0.0,
                "logprobs": True
            }

            # 使用复用的客户端，避免重复创建连接
            response = await self._client.post(
                self._api_url,
                json=payload,
                headers=self._headers
            )

            if response.status_code == 200:
                result_data = response.json()
                result = result_data["choices"][0]["message"]["content"].strip()

                # 提取敏感度分数
                confidence_score = None
                if "logprobs" in result_data["choices"][0] and result_data["choices"][0]["logprobs"]:
                    logprobs_data = result_data["choices"][0]["logprobs"]
                    if "content" in logprobs_data and logprobs_data["content"]:
                        # 获取第一个token的logprob
                        first_token_logprob = logprobs_data["content"][0]["logprob"]
                        # 转换为概率
                        confidence_score = math.exp(first_token_logprob)

                logger.debug(f"Model response: {result}, confidence: {confidence_score}")
                return result, confidence_score
            else:
                logger.error(f"Model API error: {response.status_code} - {response.text}")
                raise Exception(f"API call failed with status {response.status_code}")

        except Exception as e:
            logger.error(f"Model API error: {e}")
            raise

    async def _call_vl_model_api_with_logprobs(self, messages: List[dict]) -> Tuple[str, Optional[float]]:
        """调用多模态模型API并获取logprobs来计算敏感度"""
        try:
            logger.debug("Calling VL model API with logprobs...")

            payload = {
                "model": settings.guardrails_vl_model_name,
                "messages": messages,
                "temperature": 0.0,
                "logprobs": True
            }

            # 使用复用的客户端，避免重复创建连接
            response = await self._client.post(
                self._vl_api_url,
                json=payload,
                headers=self._vl_headers
            )

            if response.status_code == 200:
                result_data = response.json()
                result = result_data["choices"][0]["message"]["content"].strip()

                # 提取敏感度分数
                confidence_score = None
                if "logprobs" in result_data["choices"][0] and result_data["choices"][0]["logprobs"]:
                    logprobs_data = result_data["choices"][0]["logprobs"]
                    if "content" in logprobs_data and logprobs_data["content"]:
                        # 获取第一个token的logprob
                        first_token_logprob = logprobs_data["content"][0]["logprob"]
                        # 转换为概率
                        confidence_score = math.exp(first_token_logprob)

                logger.debug(f"VL Model response: {result}, confidence: {confidence_score}")
                return result, confidence_score
            else:
                logger.error(f"VL Model API error: {response.status_code} - {response.text}")
                raise Exception(f"API call failed with status {response.status_code}")

        except Exception as e:
            logger.error(f"VL Model API error: {e}")
            raise

    def _has_image_content(self, messages: List[dict]) -> bool:
        """检查消息中是否包含图片内容"""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "image_url":
                        return True
        return False

    async def close(self):
        """关闭HTTP客户端"""
        if self._client:
            await self._client.aclose()

# 全局模型服务实例
model_service = ModelService()