"""
象信AI安全护栏客户端
"""
import requests
import time
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, Union
from .models import GuardrailRequest, GuardrailResponse, Message, GuardrailResult, ComplianceResult, SecurityResult
from .exceptions import (
    XiangxinAIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)


class XiangxinAI:
    """象信AI安全护栏客户端 - 基于LLM的上下文感知AI安全护栏
    
    这个客户端提供了与象信AI安全护栏API交互的简单接口。
    护栏采用上下文感知技术，能够理解对话上下文进行安全检测。
    
    Args:
        api_key: API密钥
        base_url: API基础URL，默认为云端服务
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        
    Example:
        >>> client = XiangxinAI(api_key="your-api-key")
        >>> # 检测提示词
        >>> result = client.check_prompt("用户问题")
        >>> # 检测对话上下文
        >>> messages = [{"role": "user", "content": "问题"}, {"role": "assistant", "content": "回答"}]
        >>> result = client.check_conversation(messages)
        >>> print(result.overall_risk_level)  # "高风险/中风险/低风险/无风险"
        >>> print(result.suggest_action)  # "通过/阻断/代答"
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.xiangxinai.cn/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"xiangxinai-python/1.0.0"
        })
    
    def _create_safe_response(self) -> GuardrailResponse:
        """创建无风险的默认响应"""
        return GuardrailResponse(
            id="guardrails-safe-default",
            result=GuardrailResult(
                compliance=ComplianceResult(
                    risk_level="无风险",
                    categories=[]
                ),
                security=SecurityResult(
                    risk_level="无风险", 
                    categories=[]
                )
            ),
            overall_risk_level="无风险",
            suggest_action="通过",
            suggest_answer=None
        )
    
    def check_prompt(
        self,
        content: str,
        model: str = "Xiangxin-Guardrails-Text"
    ) -> GuardrailResponse:
        """检测提示词的安全性
        
        Args:
            content: 要检测的提示词内容
            model: 使用的模型名称
            
        Returns:
            GuardrailResponse: 检测结果，格式为：
            {
                "id": "guardrails-xxx",
                "result": {
                    "compliance": {
                        "risk_level": "高风险/中风险/低风险/无风险",
                        "categories": ["暴力犯罪", "敏感政治话题"]
                    },
                    "security": {
                        "risk_level": "高风险/中风险/低风险/无风险",
                        "categories": ["提示词攻击"]
                    }
                },
                "overall_risk_level": "高风险/中风险/低风险/无风险",
                "suggest_action": "通过/阻断/代答",
                "suggest_answer": "建议回答内容"
            }
            
        Raises:
            ValidationError: 输入参数无效
            AuthenticationError: 认证失败
            RateLimitError: 超出速率限制
            XiangxinAIError: 其他API错误
            
        Example:
            >>> result = client.check_prompt("我想学习编程")
            >>> print(result.overall_risk_level)  # "无风险"
            >>> print(result.suggest_action)  # "通过"
            >>> print(result.result.compliance.risk_level)  # "安全"
        """
        # 如果content是空字符串，直接返回无风险
        if not content or not content.strip():
            return self._create_safe_response()
        
        request_data = GuardrailRequest(
            model=model,
            messages=[Message(role="user", content=content.strip())],
        )
        
        return self._make_request("POST", "/guardrails", request_data.dict())
    
    def check_conversation(
        self,
        messages: List[Dict[str, str]],
        model: str = "Xiangxin-Guardrails-Text"
    ) -> GuardrailResponse:
        """检测对话上下文的安全性 - 上下文感知检测
        
        这是护栏的核心功能，能够理解完整的对话上下文进行安全检测。
        不是分别检测每条消息，而是分析整个对话的安全性。
        
        Args:
            messages: 对话消息列表，包含用户和助手的完整对话
                     每个消息包含role('user'或'assistant')和content
            model: 使用的模型名称
            
        Returns:
            GuardrailResponse: 基于对话上下文的检测结果，格式与check_prompt相同：
            {
                "id": "guardrails-xxx",
                "result": {
                    "compliance": {
                        "risk_level": "高风险/中风险/低风险/无风险",
                        "categories": ["暴力犯罪", "敏感政治话题"]
                    },
                    "security": {
                        "risk_level": "高风险/中风险/低风险/无风险",
                        "categories": ["提示词攻击"]
                    }
                },
                "overall_risk_level": "高风险/中风险/低风险/无风险",
                "suggest_action": "通过/阻断/代答",
                "suggest_answer": "建议回答内容"
            }
            
        Example:
            >>> # 检测用户问题和助手回答的对话安全性
            >>> messages = [
            ...     {"role": "user", "content": "用户问题"},
            ...     {"role": "assistant", "content": "助手回答"}
            ... ]
            >>> print(result.overall_risk_level)  # "无风险"
            >>> result = client.check_conversation(messages)
            >>> print(result.suggest_action)  # 基于对话上下文的建议
        """
        if not messages:
            raise ValidationError("Messages cannot be empty")
        
        # 验证消息格式
        validated_messages = []
        all_empty = True  # 标记是否所有content都为空
        
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise ValidationError("Each message must have 'role' and 'content' fields")
            
            content = msg["content"]
            # 检查是否有非空content
            if content and content.strip():
                all_empty = False
                # 只添加非空消息到validated_messages
                validated_messages.append(Message(role=msg["role"], content=content))
        
        # 如果所有messages的content都是空的，直接返回无风险
        if all_empty:
            return self._create_safe_response()
        
        # 确保至少有一条消息
        if not validated_messages:
            return self._create_safe_response()
        
        request_data = GuardrailRequest(
            model=model,
            messages=validated_messages
        )
        
        return self._make_request("POST", "/guardrails", request_data.dict())
     
    def health_check(self) -> Dict[str, Any]:
        """检查API服务健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        return self._make_request("GET", "/guardrails/health")
    
    def get_models(self) -> Dict[str, Any]:
        """获取可用模型列表
        
        Returns:
            Dict: 模型列表信息
        """
        return self._make_request("GET", "/guardrails/models")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            
        Returns:
            响应数据
            
        Raises:
            XiangxinAIError: API请求失败
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    response = self._session.get(url, timeout=self.timeout)
                elif method.upper() == "POST":
                    response = self._session.post(url, json=data, timeout=self.timeout)
                else:
                    raise XiangxinAIError(f"Unsupported HTTP method: {method}")
                
                # 处理HTTP状态码
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # 如果是护栏检测请求，返回结构化响应
                    if endpoint == "/guardrails" and isinstance(result_data, dict):
                        return GuardrailResponse(**result_data)
                    
                    return result_data
                
                elif response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                
                elif response.status_code == 422:
                    error_detail = response.json().get("detail", "Validation error")
                    raise ValidationError(f"Validation error: {error_detail}")
                
                elif response.status_code == 429:
                    if attempt < self.max_retries:
                        # 指数退避重试
                        wait_time = (2 ** attempt) + 1
                        time.sleep(wait_time)
                        continue
                    raise RateLimitError("Rate limit exceeded")
                
                else:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("detail", error_msg)
                    except:
                        pass
                    
                    raise XiangxinAIError(
                        f"API request failed with status {response.status_code}: {error_msg}"
                    )
            
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                raise XiangxinAIError("Request timeout")
            
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                raise XiangxinAIError("Connection error")
            
            except (AuthenticationError, ValidationError, RateLimitError):
                # 这些错误不需要重试
                raise
            
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
                raise XiangxinAIError(f"Unexpected error: {str(e)}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if hasattr(self, '_session'):
            self._session.close()


class AsyncXiangxinAI:
    """象信AI安全护栏异步客户端 - 基于LLM的上下文感知AI安全护栏
    
    这个异步客户端提供了与象信AI安全护栏API交互的异步接口。
    护栏采用上下文感知技术，能够理解对话上下文进行安全检测。
    
    Args:
        api_key: API密钥
        base_url: API基础URL，默认为云端服务
        timeout: 请求超时时间（秒）
        max_retries: 最大重试次数
        
    Example:
        >>> async with AsyncXiangxinAI(api_key="your-api-key") as client:
        ...     result = await client.check_prompt("用户问题")
        ...     print(result.overall_risk_level)
        或:
        >>> client = AsyncXiangxinAI(api_key="your-api-key")
        >>> result = await client.check_prompt("用户问题") 
        >>> await client.close()
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.xiangxinai.cn/v1",
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"xiangxinai-python/1.0.0"
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建aiohttp会话"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=timeout
            )
        return self._session
    
    def _create_safe_response(self) -> GuardrailResponse:
        """创建无风险的默认响应"""
        return GuardrailResponse(
            id="guardrails-safe-default",
            result=GuardrailResult(
                compliance=ComplianceResult(
                    risk_level="无风险",
                    categories=[]
                ),
                security=SecurityResult(
                    risk_level="无风险", 
                    categories=[]
                )
            ),
            overall_risk_level="无风险",
            suggest_action="通过",
            suggest_answer=None
        )
    
    async def check_prompt(
        self,
        content: str,
        model: str = "Xiangxin-Guardrails-Text"
    ) -> GuardrailResponse:
        """异步检测提示词的安全性
        
        Args:
            content: 要检测的提示词内容
            model: 使用的模型名称
            
        Returns:
            GuardrailResponse: 检测结果，格式与同步版本相同
            
        Raises:
            ValidationError: 输入参数无效
            AuthenticationError: 认证失败
            RateLimitError: 超出速率限制
            XiangxinAIError: 其他API错误
            
        Example:
            >>> async with AsyncXiangxinAI("your-api-key") as client:
            ...     result = await client.check_prompt("我想学习编程")
            ...     print(result.overall_risk_level)  # "无风险"
        """
        # 如果content是空字符串，直接返回无风险
        if not content or not content.strip():
            return self._create_safe_response()
        
        request_data = GuardrailRequest(
            model=model,
            messages=[Message(role="user", content=content.strip())],
        )
        
        return await self._make_request("POST", "/guardrails", request_data.dict())
    
    async def check_conversation(
        self,
        messages: List[Dict[str, str]],
        model: str = "Xiangxin-Guardrails-Text"
    ) -> GuardrailResponse:
        """异步检测对话上下文的安全性 - 上下文感知检测
        
        这是护栏的核心功能，能够理解完整的对话上下文进行安全检测。
        不是分别检测每条消息，而是分析整个对话的安全性。
        
        Args:
            messages: 对话消息列表，包含用户和助手的完整对话
                     每个消息包含role('user'或'assistant')和content
            model: 使用的模型名称
            
        Returns:
            GuardrailResponse: 基于对话上下文的检测结果
            
        Example:
            >>> messages = [
            ...     {"role": "user", "content": "用户问题"},
            ...     {"role": "assistant", "content": "助手回答"}
            ... ]
            >>> async with AsyncXiangxinAI("your-api-key") as client:
            ...     result = await client.check_conversation(messages)
            ...     print(result.overall_risk_level)
        """
        if not messages:
            raise ValidationError("Messages cannot be empty")
        
        # 验证消息格式
        validated_messages = []
        all_empty = True  # 标记是否所有content都为空
        
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                raise ValidationError("Each message must have 'role' and 'content' fields")
            
            content = msg["content"]
            # 检查是否有非空content
            if content and content.strip():
                all_empty = False
                # 只添加非空消息到validated_messages
                validated_messages.append(Message(role=msg["role"], content=content))
        
        # 如果所有messages的content都是空的，直接返回无风险
        if all_empty:
            return self._create_safe_response()
        
        # 确保至少有一条消息
        if not validated_messages:
            return self._create_safe_response()
        
        request_data = GuardrailRequest(
            model=model,
            messages=validated_messages
        )
        
        return await self._make_request("POST", "/guardrails", request_data.dict())
     
    async def health_check(self) -> Dict[str, Any]:
        """异步检查API服务健康状态
        
        Returns:
            Dict: 健康状态信息
        """
        return await self._make_request("GET", "/guardrails/health")
    
    async def get_models(self) -> Dict[str, Any]:
        """异步获取可用模型列表
        
        Returns:
            Dict: 模型列表信息
        """
        return await self._make_request("GET", "/guardrails/models")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Any:
        """发送异步HTTP请求
        
        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            
        Returns:
            响应数据
            
        Raises:
            XiangxinAIError: API请求失败
        """
        url = f"{self.base_url}{endpoint}"
        session = await self._get_session()
        
        for attempt in range(self.max_retries + 1):
            try:
                if method.upper() == "GET":
                    async with session.get(url) as response:
                        return await self._handle_response(response, endpoint)
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        return await self._handle_response(response, endpoint)
                else:
                    raise XiangxinAIError(f"Unsupported HTTP method: {method}")
            
            except asyncio.TimeoutError:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                raise XiangxinAIError("Request timeout")
            
            except aiohttp.ClientError:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                raise XiangxinAIError("Connection error")
            
            except (AuthenticationError, ValidationError, RateLimitError):
                # 这些错误不需要重试
                raise
            
            except Exception as e:
                if attempt < self.max_retries:
                    await asyncio.sleep(1)
                    continue
                raise XiangxinAIError(f"Unexpected error: {str(e)}")
    
    async def _handle_response(
        self, 
        response: aiohttp.ClientResponse, 
        endpoint: str
    ) -> Any:
        """处理HTTP响应"""
        if response.status == 200:
            result_data = await response.json()
            
            # 如果是护栏检测请求，返回结构化响应
            if endpoint == "/guardrails" and isinstance(result_data, dict):
                return GuardrailResponse(**result_data)
            
            return result_data
        
        elif response.status == 401:
            raise AuthenticationError("Invalid API key")
        
        elif response.status == 422:
            error_data = await response.json()
            error_detail = error_data.get("detail", "Validation error")
            raise ValidationError(f"Validation error: {error_detail}")
        
        elif response.status == 429:
            # 指数退避重试
            wait_time = (2 ** 0) + 1  # 第一次重试等待2秒
            await asyncio.sleep(wait_time)
            raise RateLimitError("Rate limit exceeded")
        
        else:
            error_msg = await response.text()
            try:
                error_data = await response.json()
                error_msg = error_data.get("detail", error_msg)
            except:
                pass
            
            raise XiangxinAIError(
                f"API request failed with status {response.status}: {error_msg}"
            )
    
    async def close(self):
        """关闭异步会话"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()