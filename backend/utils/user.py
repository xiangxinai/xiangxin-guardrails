import secrets
import string
import uuid
from typing import Optional, Union
from sqlalchemy.orm import Session
from database.models import User, EmailVerification
from utils.auth import get_password_hash
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()

def generate_api_key() -> str:
    """生成API密钥（以 sk-xxai- 开头，总长<=64）"""
    # 统一规范：以 sk-xxai- 作为固定前缀，数据库列长度为64
    # 因此前缀长度为8，随机部分生成56位字母数字，保证总长度为64
    prefix = 'sk-xxai-'
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(56))
    return prefix + random_part

def create_user(db: Session, email: str, password: str) -> User:
    """创建新用户"""
    hashed_password = get_password_hash(password)
    api_key = generate_api_key()
    
    # 确保API密钥唯一
    while db.query(User).filter(User.api_key == api_key).first():
        api_key = generate_api_key()
    
    user = User(
        email=email,
        password_hash=hashed_password,
        api_key=api_key,
        is_active=False,  # 需要邮箱验证
        is_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user_email(db: Session, email: str, verification_code: str) -> bool:
    """验证用户邮箱"""
    # 查找有效的验证码
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.verification_code == verification_code,
        EmailVerification.is_used == False,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()
    
    if not verification:
        return False
    
    # 标记验证码为已使用
    verification.is_used = True
    
    # 激活用户
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_active = True
        user.is_verified = True
        
        # 为新用户创建默认代答模板
        try:
            from services.template_service import create_user_default_templates
            template_count = create_user_default_templates(db, user.id)
            print(f"为用户 {user.email} 创建了 {template_count} 个默认代答模板")
        except Exception as e:
            print(f"为用户 {user.email} 创建默认代答模板失败: {e}")
            # 不影响用户激活过程，只是记录错误
    
    db.commit()
    return True

def regenerate_api_key(db: Session, user_id: Union[str, uuid.UUID]) -> Optional[str]:
    """重新生成用户API密钥"""
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return None
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    
    new_api_key = generate_api_key()
    
    # 确保API密钥唯一
    while db.query(User).filter(User.api_key == new_api_key).first():
        new_api_key = generate_api_key()
    
    user.api_key = new_api_key
    db.commit()
    db.refresh(user)
    
    return new_api_key

def get_user_by_api_key(db: Session, api_key: str) -> Optional[User]:
    """通过API密钥获取用户（允许未激活账号用于API访问）"""
    return db.query(User).filter(
        User.api_key == api_key
    ).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()

def record_login_attempt(db: Session, email: str, ip_address: str, user_agent: str, success: bool):
    """记录登录尝试"""
    from database.models import LoginAttempt
    
    attempt = LoginAttempt(
        email=email,
        ip_address=ip_address,
        user_agent=user_agent or "",
        success=success
    )
    db.add(attempt)
    db.commit()

def check_login_rate_limit(db: Session, email: str, ip_address: str, time_window_minutes: int = 15, max_attempts: int = 5) -> bool:
    from database.models import LoginAttempt
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    email_failures = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,
        LoginAttempt.attempted_at >= cutoff_time
    ).count()
    
    # 邮箱失败次数超过限制则拒绝
    return email_failures < max_attempts

def cleanup_old_login_attempts(db: Session, days_to_keep: int = 30):
    """清理旧的登录尝试记录"""
    from database.models import LoginAttempt
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
    
    try:
        deleted_count = db.query(LoginAttempt).filter(
            LoginAttempt.attempted_at < cutoff_time
        ).delete()
        db.commit()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old login attempts older than {days_to_keep} days")
        
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to cleanup old login attempts: {e}")
        db.rollback()
        return 0

def emergency_clear_rate_limit(db: Session, email: str = None, ip_address: str = None, time_window_minutes: int = 15):
    """紧急清理频率限制（用于解决误封问题）"""
    from database.models import LoginAttempt
    from datetime import datetime, timedelta
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
    
    try:
        query = db.query(LoginAttempt).filter(
            LoginAttempt.attempted_at >= cutoff_time,
            LoginAttempt.success == False
        )
        
        if email:
            query = query.filter(LoginAttempt.email == email)
        if ip_address:
            query = query.filter(LoginAttempt.ip_address == ip_address)
            
        deleted_count = query.delete()
        db.commit()
        
        logger.info(f"Emergency cleared {deleted_count} failed login attempts for email={email}, ip={ip_address}")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to emergency clear rate limit: {e}")
        db.rollback()
        return 0