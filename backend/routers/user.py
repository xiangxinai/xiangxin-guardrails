from datetime import timedelta, datetime
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database.models import Tenant, EmailVerification
from utils.auth import create_access_token, verify_token, verify_password, get_password_hash
from utils.user import create_user, verify_user_email, regenerate_api_key, get_user_by_email, get_user_by_api_key, record_login_attempt, check_login_rate_limit
from utils.email import send_verification_email, generate_verification_code, get_verification_expiry
from config import settings
from services.admin_service import admin_service

router = APIRouter(tags=["User Management"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    
class VerifyEmailRequest(BaseModel):
    email: EmailStr
    verification_code: str

class ResendCodeRequest(BaseModel):
    email: EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    api_key: str
    tenant_id: str  # 改为字符串UUID
    is_super_admin: bool

class UserInfo(BaseModel):
    id: str  # 改为字符串UUID
    email: str
    api_key: str
    is_active: bool
    is_verified: bool
    is_super_admin: bool
    rate_limit: int  # 速度限制（每秒请求数，0表示无限制，默认为1）

class ApiKeyResponse(BaseModel):
    api_key: str

def get_current_user_from_token(credentials: HTTPAuthorizationCredentials, db: Session) -> Tenant:
    """从JWT token获取当前租户"""
    try:
        tenant_data = verify_token(credentials.credentials)
        tenant_id = tenant_data.get('tenant_id') or tenant_data.get('tenant_id') or tenant_data.get('sub')

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Invalid token: tenant ID not found")

        # 确保tenant_id是UUID对象或字符串
        if isinstance(tenant_id, str):
            try:
                import uuid
                tenant_id = uuid.UUID(tenant_id)
            except ValueError:
                raise HTTPException(status_code=401, detail="Invalid tenant ID format")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant or not tenant.is_active or not tenant.is_verified:
            raise HTTPException(status_code=401, detail="Tenant not found, inactive, or not verified")

        return tenant
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@router.post("/register")
async def register_user(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """租户注册"""
    # 检查邮箱是否已存在
    existing_tenant = get_user_by_email(db, register_data.email)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建租户
    try:
        tenant = create_user(db, register_data.email, register_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant"
        )
    
    # 生成验证码并发送邮件
    verification_code = generate_verification_code()
    verification_expiry = get_verification_expiry()
    
    # 保存验证码到数据库
    email_verification = EmailVerification(
        email=register_data.email,
        verification_code=verification_code,
        expires_at=verification_expiry
    )
    db.add(email_verification)
    db.commit()
    
    # 发送验证邮件
    try:
        if not send_verification_email(register_data.email, verification_code):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
    except Exception:
        # 如果邮件发送失败，仍然返回成功，但提示用户联系管理员
        return {"message": "Registration successful. Please contact administrator to verify your account."}
    
    return {"message": "Registration successful. Please check your email for verification code."}

@router.post("/verify-email")
async def verify_email(verify_data: VerifyEmailRequest, db: Session = Depends(get_db)):
    """验证邮箱"""
    if not verify_user_email(db, verify_data.email, verify_data.verification_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    return {"message": "Email verified successfully. You can now login."}

@router.post("/resend-verification-code")
async def resend_verification_code(resend_data: ResendCodeRequest, db: Session = Depends(get_db)):
    """重发邮箱验证码"""
    try:
        # 检查租户是否存在且未验证
        tenant = get_user_by_email(db, resend_data.email)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        if tenant.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        # 生成新验证码
        verification_code = generate_verification_code()
        verification_expiry = get_verification_expiry()
        
        # 保存新验证码
        email_verification = EmailVerification(
            email=resend_data.email,
            verification_code=verification_code,
            expires_at=verification_expiry
        )
        db.add(email_verification)
        db.commit()
        
        # 发送验证邮件
        try:
            if not send_verification_email(resend_data.email, verification_code):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send verification email"
                )
        except Exception as e:
            return {"message": "Verification code generated. Please contact administrator if you don't receive the email."}
        
        return {"message": "Verification code resent successfully. Please check your email."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification code"
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """租户登录"""
    # 获取客户端信息
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    # 检查登录速率限制
    if not check_login_rate_limit(db, login_data.email, client_ip):
        record_login_attempt(db, login_data.email, client_ip, user_agent, False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )

    # 统一租户登录
    tenant = get_user_by_email(db, login_data.email)
    if not tenant:
        record_login_attempt(db, login_data.email, client_ip, user_agent, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(login_data.password, tenant.password_hash):
        record_login_attempt(db, login_data.email, client_ip, user_agent, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # 检查账号是否已激活且邮箱已验证
    if not tenant.is_active or not tenant.is_verified:
        record_login_attempt(db, login_data.email, client_ip, user_agent, False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please check your email address and complete verification."
        )

    # 记录成功登录
    record_login_attempt(db, login_data.email, client_ip, user_agent, True)

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    is_super_admin = admin_service.is_super_admin(tenant)
    access_token = create_access_token(
        data={"sub": str(tenant.id), "email": tenant.email, "tenant_id": str(tenant.id), "user_id": str(tenant.id), "is_super_admin": is_super_admin},
        expires_delta=access_token_expires
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        api_key=tenant.api_key,
        tenant_id=str(tenant.id),
        is_super_admin=is_super_admin
    )

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """获取当前租户信息"""
    tenant = get_current_user_from_token(credentials, db)

    # 获取租户的速度限制配置
    try:
        from services.rate_limiter import RateLimitService
        from utils.logger import setup_logger
        logger = setup_logger()

        rate_limit_service = RateLimitService(db)
        rate_limit_config = rate_limit_service.get_user_rate_limit(str(tenant.id))
        # 如果有配置且激活，使用配置值；否则使用默认值1 RPS
        rate_limit = rate_limit_config.requests_per_second if rate_limit_config and rate_limit_config.is_active else 1
        logger.info(f"租户 {tenant.email} 的速度限制: {rate_limit} (配置存在: {rate_limit_config is not None})")
    except Exception as e:
        from utils.logger import setup_logger
        logger = setup_logger()
        logger.error(f"获取租户速度限制失败: {e}")
        rate_limit = 1  # 默认值

    return UserInfo(
        id=str(tenant.id),  # 转换为字符串格式
        email=tenant.email,
        api_key=tenant.api_key,
        is_active=tenant.is_active,
        is_verified=tenant.is_verified,
        is_super_admin=admin_service.is_super_admin(tenant),
        rate_limit=rate_limit
    )

@router.post("/regenerate-api-key", response_model=ApiKeyResponse)
async def regenerate_user_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """重新生成API密钥"""
    tenant = get_current_user_from_token(credentials, db)

    new_api_key = regenerate_api_key(db, tenant.id)
    if not new_api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    return ApiKeyResponse(api_key=new_api_key)

@router.post("/logout")
async def logout_user():
    """租户登出（前端处理token清除）"""
    return {"message": "Successfully logged out"}