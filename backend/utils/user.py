import secrets
import string
import uuid
from typing import Optional, Union
from sqlalchemy.orm import Session
from database.models import Tenant, EmailVerification
from utils.auth import get_password_hash
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger()

def generate_api_key() -> str:
    """Generate API key (starts with sk-xxai-, total length <= 64)"""
    # Uniform specification: starts with sk-xxai- as fixed prefix, database column length is 64
    # Therefore the prefix length is 8, the random part generates 56 bits of letters and numbers, ensuring the total length is 64
    prefix = 'sk-xxai-'
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(56))
    return prefix + random_part

def create_user(db: Session, email: str, password: str) -> Tenant:
    """Create new tenant"""
    hashed_password = get_password_hash(password)
    api_key = generate_api_key()

    # Ensure API key is unique
    while db.query(Tenant).filter(Tenant.api_key == api_key).first():
        api_key = generate_api_key()

    tenant = Tenant(
        email=email,
        password_hash=hashed_password,
        api_key=api_key,
        is_active=False,  # Need email verification
        is_verified=False
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant

def verify_user_email(db: Session, email: str, verification_code: str) -> bool:
    """Verify tenant email"""
    # Find valid verification code
    verification = db.query(EmailVerification).filter(
        EmailVerification.email == email,
        EmailVerification.verification_code == verification_code,
        EmailVerification.is_used == False,
        EmailVerification.expires_at > datetime.utcnow()
    ).first()

    if not verification:
        return False

    # Mark verification code as used
    verification.is_used = True

    # Activate tenant
    tenant = db.query(Tenant).filter(Tenant.email == email).first()
    if tenant:
        tenant.is_active = True
        tenant.is_verified = True

    # First commit the user activation to ensure it's saved
    db.commit()

    # Then try to create default configurations (these are not critical for user activation)
    if tenant:
        # Create default reply templates for new tenant
        try:
            from services.template_service import create_user_default_templates
            template_count = create_user_default_templates(db, tenant.id)
            print(f"Created {template_count} default reply templates for tenant {tenant.email}")
        except Exception as e:
            print(f"Failed to create default reply templates for tenant {tenant.email}: {e}")
            # Not affect tenant activation process, just record error

        # Create default entity type configuration for new tenant
        try:
            from services.data_security_service import create_user_default_entity_types
            entity_count = create_user_default_entity_types(db, str(tenant.id))
            print(f"Created {entity_count} default entity type configurations for tenant {tenant.email}")
        except Exception as e:
            print(f"Failed to create default entity type configurations for tenant {tenant.email}: {e}")
            # Not affect tenant activation process, just record error

    return True

def regenerate_api_key(db: Session, tenant_id: Union[str, uuid.UUID]) -> Optional[str]:
    """Regenerate tenant API key"""
    if isinstance(tenant_id, str):
        try:
            tenant_id = uuid.UUID(tenant_id)
        except ValueError:
            return None
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None

    new_api_key = generate_api_key()

    # Ensure API key is unique
    while db.query(Tenant).filter(Tenant.api_key == new_api_key).first():
        new_api_key = generate_api_key()

    tenant.api_key = new_api_key
    db.commit()
    db.refresh(tenant)

    return new_api_key

def get_user_by_api_key(db: Session, api_key: str) -> Optional[Tenant]:
    """Get tenant by API key (only return verified tenant)"""
    return db.query(Tenant).filter(
        Tenant.api_key == api_key,
        Tenant.is_verified == True,
        Tenant.is_active == True
    ).first()

def get_user_by_email(db: Session, email: str) -> Optional[Tenant]:
    """Get tenant by email"""
    return db.query(Tenant).filter(Tenant.email == email).first()

def record_login_attempt(db: Session, email: str, ip_address: str, user_agent: str, success: bool):
    """Record login attempt"""
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
    
    # If email failure count exceeds limit, reject
    return email_failures < max_attempts

def cleanup_old_login_attempts(db: Session, days_to_keep: int = 30):
    """Clean up old login attempt records"""
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
    """Emergency clear rate limit (used to solve the problem of accidental blocking)"""
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