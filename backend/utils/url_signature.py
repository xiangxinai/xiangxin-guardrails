"""
URL签名工具

用于生成和验证带时效性的URL签名，保护媒体资源访问安全
"""
import hmac
import hashlib
import time
from typing import Optional
from config import settings


def generate_media_url_signature(
    tenant_id: str,
    filename: str,
    expires_in_seconds: int = 3600
) -> tuple[str, int]:
    """
    生成媒体文件访问的签名和过期时间

    Args:
        tenant_id: 用户ID
        filename: 文件名
        expires_in_seconds: 签名有效期（秒），默认1小时

    Returns:
        (signature, expires_timestamp) 元组
    """
    expires = int(time.time()) + expires_in_seconds

    # 构建签名字符串: tenant_id|filename|expires
    message = f"{tenant_id}|{filename}|{expires}"

    # 使用HMAC-SHA256生成签名
    signature = hmac.new(
        settings.jwt_secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    return signature, expires


def verify_media_url_signature(
    tenant_id: str,
    filename: str,
    signature: str,
    expires: int
) -> bool:
    """
    验证媒体文件访问签名

    Args:
        tenant_id: 用户ID
        filename: 文件名
        signature: 签名
        expires: 过期时间戳

    Returns:
        验证是否通过
    """
    # 检查是否过期
    if int(time.time()) > expires:
        return False

    # 重新计算签名
    message = f"{tenant_id}|{filename}|{expires}"
    expected_signature = hmac.new(
        settings.jwt_secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    # 使用恒定时间比较防止时序攻击
    return hmac.compare_digest(signature, expected_signature)


def generate_signed_media_url(
    tenant_id: str,
    filename: str,
    base_url: str = "/api/v1/media/image",
    expires_in_seconds: int = 3600
) -> str:
    """
    生成带签名的完整媒体URL

    Args:
        tenant_id: 用户ID
        filename: 文件名
        base_url: 基础URL路径
        expires_in_seconds: 签名有效期（秒）

    Returns:
        带签名的完整URL
    """
    signature, expires = generate_media_url_signature(
        tenant_id, filename, expires_in_seconds
    )

    return f"{base_url}/{tenant_id}/{filename}?token={signature}&expires={expires}"