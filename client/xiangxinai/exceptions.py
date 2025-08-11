"""
异常定义
"""


class XiangxinAIError(Exception):
    """象信AI安全护栏基础异常类"""
    pass


class AuthenticationError(XiangxinAIError):
    """认证错误"""
    pass


class RateLimitError(XiangxinAIError):
    """速率限制错误"""
    pass


class ValidationError(XiangxinAIError):
    """输入验证错误"""
    pass


class NetworkError(XiangxinAIError):
    """网络错误"""
    pass


class ServerError(XiangxinAIError):
    """服务器错误"""
    pass