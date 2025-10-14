import hashlib
import secrets
import string
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import APIKey, Application, Tenant

def generate_api_key() -> str:
    """
    Generate API key (starts with sk-xxai-, total length 64)

    Format: sk-xxai-{56 random characters}
    """
    prefix = 'sk-xxai-'
    alphabet = string.ascii_letters + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(56))
    return prefix + random_part

def hash_api_key(api_key: str) -> str:
    """
    Hash API key using SHA256

    Args:
        api_key: The plain text API key

    Returns:
        The SHA256 hash of the API key
    """
    return hashlib.sha256(api_key.encode()).hexdigest()

def get_api_key_prefix(api_key: str) -> str:
    """
    Get API key prefix for display

    Args:
        api_key: The plain text API key

    Returns:
        First 20 characters of the API key (sk-xxai-xxxxx...)
    """
    return api_key[:20] if len(api_key) >= 20 else api_key

def verify_api_key(db: Session, api_key: str) -> Optional[dict]:
    """
    Verify API key and return associated context

    Args:
        db: Database session
        api_key: The plain text API key to verify

    Returns:
        Dict with tenant_id, application_id, api_key_id if valid, None otherwise
    """
    # Hash the provided key
    key_hash = hash_api_key(api_key)

    # Find the API key record
    api_key_record = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()

    if not api_key_record:
        return None

    # Check if expired
    if api_key_record.expires_at and api_key_record.expires_at < datetime.utcnow():
        return None

    # Check if tenant is active
    tenant = db.query(Tenant).filter(
        Tenant.id == api_key_record.tenant_id,
        Tenant.is_active == True,
        Tenant.is_verified == True
    ).first()

    if not tenant:
        return None

    # Check if application is active
    application = db.query(Application).filter(
        Application.id == api_key_record.application_id,
        Application.is_active == True
    ).first()

    if not application:
        return None

    return {
        "tenant_id": str(tenant.id),
        "application_id": str(application.id),
        "api_key_id": str(api_key_record.id),
        "tenant_email": tenant.email
    }

async def update_api_key_last_used(db: Session, api_key_id: str):
    """
    Update the last used timestamp for an API key

    Args:
        db: Database session
        api_key_id: The API key ID
    """
    try:
        api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            db.commit()
    except Exception:
        # Don't fail the request if updating last_used_at fails
        db.rollback()
