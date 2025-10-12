"""
API Key Management Service

Handles CRUD operations for tenant API keys
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from database.models import TenantApiKey, Tenant, RiskTypeConfig, Blacklist, ApiKeyBlacklistAssociation
from utils.user import generate_api_key
from utils.logger import setup_logger
import uuid
from datetime import datetime

logger = setup_logger()


class ApiKeyService:
    """Service for managing tenant API keys"""

    @staticmethod
    def create_api_key(
        db: Session,
        tenant_id: str,
        name: str,
        template_id: Optional[int] = None,
        is_default: bool = False
    ) -> TenantApiKey:
        """Create a new API key for a tenant

        Args:
            db: Database session
            tenant_id: Tenant UUID
            name: Name/description for the API key
            template_id: Optional protection config template ID to associate
            is_default: Whether this is the default key

        Returns:
            Created TenantApiKey object

        Raises:
            ValueError: If tenant not found or name already exists
        """
        # Validate tenant exists
        tenant = db.query(Tenant).filter(Tenant.id == uuid.UUID(tenant_id)).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Check if name already exists for this tenant
        existing = db.query(TenantApiKey).filter(
            TenantApiKey.tenant_id == uuid.UUID(tenant_id),
            TenantApiKey.name == name
        ).first()
        if existing:
            raise ValueError(f"API key with name '{name}' already exists for this tenant")

        # If is_default=True, unset other default keys
        if is_default:
            db.query(TenantApiKey).filter(
                TenantApiKey.tenant_id == uuid.UUID(tenant_id),
                TenantApiKey.is_default == True
            ).update({"is_default": False})

        # Generate unique API key
        api_key = generate_api_key()
        while db.query(TenantApiKey).filter(TenantApiKey.api_key == api_key).first():
            api_key = generate_api_key()

        # Create new API key
        new_key = TenantApiKey(
            tenant_id=uuid.UUID(tenant_id),
            api_key=api_key,
            name=name,
            template_id=template_id,
            is_active=True,
            is_default=is_default
        )

        db.add(new_key)
        db.commit()
        db.refresh(new_key)

        logger.info(f"Created API key '{name}' for tenant {tenant_id}")
        return new_key

    @staticmethod
    def list_api_keys(db: Session, tenant_id: str) -> List[Dict]:
        """List all API keys for a tenant

        Args:
            db: Database session
            tenant_id: Tenant UUID

        Returns:
            List of API key dictionaries with metadata
        """
        keys = db.query(TenantApiKey).filter(
            TenantApiKey.tenant_id == uuid.UUID(tenant_id)
        ).order_by(TenantApiKey.is_default.desc(), TenantApiKey.created_at.desc()).all()

        result = []
        for key in keys:
            # Get protection template name if associated
            template_name = None
            if key.template_id:
                template = db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.id == key.template_id
                ).first()
                if template:
                    template_name = template.name

            # Get associated blacklists
            blacklist_associations = db.query(ApiKeyBlacklistAssociation).filter(
                ApiKeyBlacklistAssociation.api_key_id == key.id
            ).all()
            blacklist_ids = [assoc.blacklist_id for assoc in blacklist_associations]

            result.append({
                "id": str(key.id),
                "name": key.name,
                "api_key": key.api_key,
                "is_active": key.is_active,
                "is_default": key.is_default,
                "template_id": key.template_id,
                "template_name": template_name,
                "blacklist_ids": blacklist_ids,
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "created_at": key.created_at.isoformat(),
                "updated_at": key.updated_at.isoformat()
            })

        return result

    @staticmethod
    def get_api_key(db: Session, api_key_id: str, tenant_id: str) -> Optional[TenantApiKey]:
        """Get a specific API key

        Args:
            db: Database session
            api_key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            TenantApiKey object or None
        """
        return db.query(TenantApiKey).filter(
            TenantApiKey.id == uuid.UUID(api_key_id),
            TenantApiKey.tenant_id == uuid.UUID(tenant_id)
        ).first()

    @staticmethod
    def update_api_key(
        db: Session,
        api_key_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        template_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        is_default: Optional[bool] = None
    ) -> TenantApiKey:
        """Update an API key

        Args:
            db: Database session
            api_key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)
            name: New name (optional)
            template_id: New protection config template ID (optional)
            is_active: New active status (optional)
            is_default: New default status (optional)

        Returns:
            Updated TenantApiKey object

        Raises:
            ValueError: If key not found or name conflict
        """
        key = ApiKeyService.get_api_key(db, api_key_id, tenant_id)
        if not key:
            raise ValueError(f"API key {api_key_id} not found")

        # Check name uniqueness if changing name
        if name and name != key.name:
            existing = db.query(TenantApiKey).filter(
                TenantApiKey.tenant_id == uuid.UUID(tenant_id),
                TenantApiKey.name == name,
                TenantApiKey.id != uuid.UUID(api_key_id)
            ).first()
            if existing:
                raise ValueError(f"API key with name '{name}' already exists")
            key.name = name

        if template_id is not None:
            key.template_id = template_id

        if is_active is not None:
            key.is_active = is_active

        if is_default is not None and is_default:
            # Unset other default keys
            db.query(TenantApiKey).filter(
                TenantApiKey.tenant_id == uuid.UUID(tenant_id),
                TenantApiKey.is_default == True,
                TenantApiKey.id != uuid.UUID(api_key_id)
            ).update({"is_default": False})
            key.is_default = True
        elif is_default is not None and not is_default:
            key.is_default = False

        db.commit()
        db.refresh(key)

        logger.info(f"Updated API key {api_key_id} for tenant {tenant_id}")
        return key

    @staticmethod
    def delete_api_key(db: Session, api_key_id: str, tenant_id: str) -> bool:
        """Delete an API key

        Args:
            db: Database session
            api_key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete the only key or default key
        """
        key = ApiKeyService.get_api_key(db, api_key_id, tenant_id)
        if not key:
            return False

        # Check if this is the only key
        key_count = db.query(TenantApiKey).filter(
            TenantApiKey.tenant_id == uuid.UUID(tenant_id)
        ).count()

        if key_count <= 1:
            raise ValueError("Cannot delete the only API key. Create another key first.")

        # Prevent deletion of default key unless it's being replaced
        if key.is_default:
            raise ValueError("Cannot delete the default API key. Set another key as default first.")

        db.delete(key)
        db.commit()

        logger.info(f"Deleted API key {api_key_id} for tenant {tenant_id}")
        return True

    @staticmethod
    def regenerate_api_key(db: Session, api_key_id: str, tenant_id: str) -> str:
        """Regenerate the API key string

        Args:
            db: Database session
            api_key_id: API key UUID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            New API key string

        Raises:
            ValueError: If key not found
        """
        key = ApiKeyService.get_api_key(db, api_key_id, tenant_id)
        if not key:
            raise ValueError(f"API key {api_key_id} not found")

        # Generate unique API key
        api_key = generate_api_key()
        while db.query(TenantApiKey).filter(TenantApiKey.api_key == api_key).first():
            api_key = generate_api_key()

        key.api_key = api_key
        db.commit()
        db.refresh(key)

        logger.info(f"Regenerated API key {api_key_id} for tenant {tenant_id}")
        return api_key

    @staticmethod
    def associate_blacklist(db: Session, api_key_id: str, blacklist_id: int, tenant_id: str) -> bool:
        """Associate a blacklist with an API key

        Args:
            db: Database session
            api_key_id: API key UUID
            blacklist_id: Blacklist ID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            True if associated, False if already exists

        Raises:
            ValueError: If key or blacklist not found, or blacklist belongs to different tenant
        """
        key = ApiKeyService.get_api_key(db, api_key_id, tenant_id)
        if not key:
            raise ValueError(f"API key {api_key_id} not found")

        blacklist = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
        if not blacklist:
            raise ValueError(f"Blacklist {blacklist_id} not found")

        if str(blacklist.tenant_id) != tenant_id:
            raise ValueError("Blacklist belongs to a different tenant")

        # Check if already associated
        existing = db.query(ApiKeyBlacklistAssociation).filter(
            ApiKeyBlacklistAssociation.api_key_id == uuid.UUID(api_key_id),
            ApiKeyBlacklistAssociation.blacklist_id == blacklist_id
        ).first()

        if existing:
            return False

        # Create association
        association = ApiKeyBlacklistAssociation(
            api_key_id=uuid.UUID(api_key_id),
            blacklist_id=blacklist_id
        )
        db.add(association)
        db.commit()

        logger.info(f"Associated blacklist {blacklist_id} with API key {api_key_id}")
        return True

    @staticmethod
    def disassociate_blacklist(db: Session, api_key_id: str, blacklist_id: int, tenant_id: str) -> bool:
        """Remove blacklist association from an API key

        Args:
            db: Database session
            api_key_id: API key UUID
            blacklist_id: Blacklist ID
            tenant_id: Tenant UUID (for authorization)

        Returns:
            True if removed, False if not found
        """
        key = ApiKeyService.get_api_key(db, api_key_id, tenant_id)
        if not key:
            raise ValueError(f"API key {api_key_id} not found")

        association = db.query(ApiKeyBlacklistAssociation).filter(
            ApiKeyBlacklistAssociation.api_key_id == uuid.UUID(api_key_id),
            ApiKeyBlacklistAssociation.blacklist_id == blacklist_id
        ).first()

        if not association:
            return False

        db.delete(association)
        db.commit()

        logger.info(f"Disassociated blacklist {blacklist_id} from API key {api_key_id}")
        return True

    @staticmethod
    def update_last_used(db: Session, api_key: str):
        """Update the last_used_at timestamp for an API key

        Args:
            db: Database session
            api_key: API key string
        """
        try:
            key = db.query(TenantApiKey).filter(TenantApiKey.api_key == api_key).first()
            if key:
                key.last_used_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update last_used_at for API key: {e}")
            db.rollback()
