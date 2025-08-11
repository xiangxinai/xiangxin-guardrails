from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from config import settings
import secrets
import string

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)

def generate_api_key() -> str:
    """生成API密钥"""
    # 生成 64 位字符的 API key，格式为 sk-xxai-[52位随机字符]
    prefix = "sk-xxai-"
    key_length = 52
    characters = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(characters) for _ in range(key_length))
    return prefix + random_part

def authenticate_admin(username: str, password: str) -> bool:
    """验证管理员账号"""
    if username != settings.super_admin_username:
        return False
    if password != settings.super_admin_password:
        return False
    return True

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """验证令牌"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject: str = payload.get("sub")
        role: str = payload.get("role", "user")

        if subject is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 管理员token保留原有结构
        if role == "admin":
            return {"username": subject, "role": role}

        # 普通用户：确保返回包含user_id（UUID字符串），兼容旧token仅有sub的情况
        user_id = payload.get("user_id")
        if user_id is None:
            # 兼容旧token：将sub作为user_id（字符串）
            user_id = subject

        return {
            "user_id": user_id,
            "sub": subject,
            "email": payload.get("email"),
            "role": role,
            "is_super_admin": payload.get("is_super_admin", False),
        }
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )