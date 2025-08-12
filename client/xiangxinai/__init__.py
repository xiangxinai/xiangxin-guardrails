"""
象信AI安全护栏 Python 客户端

基于LLM的上下文感知AI安全护栏，能够理解对话上下文进行安全检测。

这个包提供了与象信AI安全护栏API交互的Python客户端库。

Example:
    基本用法:
    
    from xiangxinai import XiangxinAI
    
    # 使用云端API
    client = XiangxinAI("your-api-key")
    
    # 检测提示词
    result = client.check_prompt("用户的问题")
    
    # 检测对话上下文（用户+助手回答）
    messages = [
        {"role": "user", "content": "用户问题"},
        {"role": "assistant", "content": "助手回答"}
    ]
    result = client.check_conversation(messages)
    print(result.overall_risk_level)  # 输出: 无风险/高风险/中风险/低风险
    print(result.suggest_action)  # 输出: 通过/代答/阻断
"""

from .client import XiangxinAI, AsyncXiangxinAI
from .models import (
    GuardrailRequest,
    GuardrailResponse,
    GuardrailResult,
    ComplianceResult,
    SecurityResult,
    Message
)
from .exceptions import (
    XiangxinAIError,
    AuthenticationError,
    RateLimitError,
    ValidationError
)

__version__ = "1.1.0"
__author__ = "XiangxinAI"
__email__ = "wanglei@xiangxinai.cn"

__all__ = [
    "XiangxinAI",
    "AsyncXiangxinAI",
    "GuardrailRequest",
    "GuardrailResponse", 
    "GuardrailResult",
    "ComplianceResult",
    "SecurityResult",
    "Message",
    "XiangxinAIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
]