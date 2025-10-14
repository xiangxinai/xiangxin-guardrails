"""
Application Management Service

Handles CRUD operations for applications and their associated API keys.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import (
    Application, APIKey, Tenant,
    RiskTypeConfig, Blacklist, Whitelist, ResponseTemplate,
    KnowledgeBase, DataSecurityEntityType, TestModelConfig, ProxyModelConfig
)
from utils.api_key import generate_api_key, hash_api_key, get_api_key_prefix
from utils.logger import setup_logger
import uuid
from datetime import datetime

logger = setup_logger()

class ApplicationService:
    """Service for managing applications"""

    @staticmethod
    def get_applications_by_tenant(db: Session, tenant_id: str) -> List[Application]:
        """
        Get all applications for a tenant

        Args:
            db: Database session
            tenant_id: Tenant ID

        Returns:
            List of applications
        """
        return db.query(Application).filter(
            Application.tenant_id == tenant_id
        ).order_by(Application.created_at.desc()).all()

    @staticmethod
    def get_application_by_id(db: Session, application_id: str, tenant_id: str) -> Optional[Application]:
        """
        Get application by ID (with tenant ownership verification)

        Args:
            db: Database session
            application_id: Application ID
            tenant_id: Tenant ID for ownership verification

        Returns:
            Application if found and owned by tenant, None otherwise
        """
        return db.query(Application).filter(
            Application.id == application_id,
            Application.tenant_id == tenant_id
        ).first()

    @staticmethod
    def create_application(
        db: Session,
        tenant_id: str,
        name: str,
        description: Optional[str] = None,
        copy_from_application_id: Optional[str] = None
    ) -> tuple[Application, str]:
        """
        Create a new application

        Args:
            db: Database session
            tenant_id: Tenant ID
            name: Application name
            description: Application description
            copy_from_application_id: Optional application ID to copy configuration from

        Returns:
            Tuple of (Application, first_api_key_string)
        """
        # Create application
        app = Application(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_active=True
        )
        db.add(app)
        db.flush()  # Get the app ID

        # Initialize configuration
        if copy_from_application_id:
            ApplicationService._copy_application_config(
                db, copy_from_application_id, app.id
            )
        else:
            ApplicationService._init_default_application_config(db, app.id, tenant_id)

        # Create first API key
        api_key_str = generate_api_key()
        key_hash = hash_api_key(api_key_str)
        key_prefix = get_api_key_prefix(api_key_str)

        api_key = APIKey(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            application_id=app.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name="Default Key",
            is_active=True
        )
        db.add(api_key)

        db.commit()
        db.refresh(app)

        logger.info(f"Created application {app.id} for tenant {tenant_id}")
        return app, api_key_str

    @staticmethod
    def update_application(
        db: Session,
        application_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[Application]:
        """
        Update an application

        Args:
            db: Database session
            application_id: Application ID
            tenant_id: Tenant ID for ownership verification
            name: New name (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated application if successful, None otherwise
        """
        app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
        if not app:
            return None

        if name is not None:
            app.name = name
        if description is not None:
            app.description = description
        if is_active is not None:
            app.is_active = is_active

        db.commit()
        db.refresh(app)

        logger.info(f"Updated application {app.id}")
        return app

    @staticmethod
    def delete_application(db: Session, application_id: str, tenant_id: str) -> bool:
        """
        Delete an application (with safety checks)

        Args:
            db: Database session
            application_id: Application ID
            tenant_id: Tenant ID for ownership verification

        Returns:
            True if deleted successfully, False otherwise
        """
        # Check if this is the last application
        app_count = db.query(Application).filter(
            Application.tenant_id == tenant_id
        ).count()

        if app_count <= 1:
            logger.warning(f"Cannot delete last application for tenant {tenant_id}")
            return False

        # Get and delete the application (cascade delete will handle configs and keys)
        app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
        if not app:
            return False

        db.delete(app)
        db.commit()

        logger.info(f"Deleted application {application_id}")
        return True

    @staticmethod
    def get_api_key_count(db: Session, application_id: str) -> int:
        """
        Get the number of API keys for an application

        Args:
            db: Database session
            application_id: Application ID

        Returns:
            Number of API keys
        """
        return db.query(APIKey).filter(
            APIKey.application_id == application_id
        ).count()

    @staticmethod
    def _init_default_application_config(db: Session, application_id: str, tenant_id: str):
        """
        Initialize default configuration for a new application

        Args:
            db: Database session
            application_id: Application ID
            tenant_id: Tenant ID
        """
        # Create default risk type config
        risk_config = RiskTypeConfig(
            application_id=application_id,
            tenant_id=tenant_id,  # Keep for backward compatibility
            # All S1-S12 enabled by default (default values in model)
            high_sensitivity_threshold=0.40,
            medium_sensitivity_threshold=0.60,
            low_sensitivity_threshold=0.95,
            sensitivity_trigger_level="medium"
        )
        db.add(risk_config)

        logger.info(f"Initialized default config for application {application_id}")

    @staticmethod
    def _copy_application_config(db: Session, source_app_id: str, target_app_id: str):
        """
        Copy configuration from one application to another

        Args:
            db: Database session
            source_app_id: Source application ID
            target_app_id: Target application ID
        """
        # Get source application's tenant_id for new records
        source_app = db.query(Application).filter(Application.id == source_app_id).first()
        if not source_app:
            logger.warning(f"Source application {source_app_id} not found, using default config")
            return

        tenant_id = str(source_app.tenant_id)

        # Copy RiskTypeConfig
        source_risk_config = db.query(RiskTypeConfig).filter(
            RiskTypeConfig.application_id == source_app_id
        ).first()

        if source_risk_config:
            new_risk_config = RiskTypeConfig(
                application_id=target_app_id,
                tenant_id=tenant_id,
                s1_enabled=source_risk_config.s1_enabled,
                s2_enabled=source_risk_config.s2_enabled,
                s3_enabled=source_risk_config.s3_enabled,
                s4_enabled=source_risk_config.s4_enabled,
                s5_enabled=source_risk_config.s5_enabled,
                s6_enabled=source_risk_config.s6_enabled,
                s7_enabled=source_risk_config.s7_enabled,
                s8_enabled=source_risk_config.s8_enabled,
                s9_enabled=source_risk_config.s9_enabled,
                s10_enabled=source_risk_config.s10_enabled,
                s11_enabled=source_risk_config.s11_enabled,
                s12_enabled=source_risk_config.s12_enabled,
                high_sensitivity_threshold=source_risk_config.high_sensitivity_threshold,
                medium_sensitivity_threshold=source_risk_config.medium_sensitivity_threshold,
                low_sensitivity_threshold=source_risk_config.low_sensitivity_threshold,
                sensitivity_trigger_level=source_risk_config.sensitivity_trigger_level
            )
            db.add(new_risk_config)

        # Copy Blacklists
        source_blacklists = db.query(Blacklist).filter(
            Blacklist.application_id == source_app_id
        ).all()

        for bl in source_blacklists:
            new_bl = Blacklist(
                application_id=target_app_id,
                tenant_id=tenant_id,
                name=bl.name + " (copy)",
                keywords=bl.keywords,
                description=bl.description,
                is_active=bl.is_active
            )
            db.add(new_bl)

        # Copy Whitelists
        source_whitelists = db.query(Whitelist).filter(
            Whitelist.application_id == source_app_id
        ).all()

        for wl in source_whitelists:
            new_wl = Whitelist(
                application_id=target_app_id,
                tenant_id=tenant_id,
                name=wl.name + " (copy)",
                keywords=wl.keywords,
                description=wl.description,
                is_active=wl.is_active
            )
            db.add(new_wl)

        # Copy ResponseTemplates (only application-specific ones)
        source_templates = db.query(ResponseTemplate).filter(
            ResponseTemplate.application_id == source_app_id
        ).all()

        for tmpl in source_templates:
            new_tmpl = ResponseTemplate(
                application_id=target_app_id,
                tenant_id=tenant_id,
                category=tmpl.category,
                risk_level=tmpl.risk_level,
                template_content=tmpl.template_content,
                is_default=False,
                is_active=tmpl.is_active
            )
            db.add(new_tmpl)

        logger.info(f"Copied config from application {source_app_id} to {target_app_id}")


# ==================== API Key Service ====================

class APIKeyService:
    """Service for managing API keys"""

    @staticmethod
    def get_api_keys_by_application(db: Session, application_id: str) -> List[APIKey]:
        """
        Get all API keys for an application

        Args:
            db: Database session
            application_id: Application ID

        Returns:
            List of API keys
        """
        return db.query(APIKey).filter(
            APIKey.application_id == application_id
        ).order_by(APIKey.created_at.desc()).all()

    @staticmethod
    def create_api_key(
        db: Session,
        application_id: str,
        tenant_id: str,
        name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> tuple[APIKey, str]:
        """
        Create a new API key

        Args:
            db: Database session
            application_id: Application ID
            tenant_id: Tenant ID
            name: Key name/note
            expires_at: Expiration datetime

        Returns:
            Tuple of (APIKey, api_key_string)
        """
        # Generate API key
        api_key_str = generate_api_key()
        key_hash = hash_api_key(api_key_str)
        key_prefix = get_api_key_prefix(api_key_str)

        # Ensure uniqueness
        while db.query(APIKey).filter(APIKey.key_hash == key_hash).first():
            api_key_str = generate_api_key()
            key_hash = hash_api_key(api_key_str)
            key_prefix = get_api_key_prefix(api_key_str)

        api_key = APIKey(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            application_id=application_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            is_active=True,
            expires_at=expires_at
        )

        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        logger.info(f"Created API key {api_key.id} for application {application_id}")
        return api_key, api_key_str

    @staticmethod
    def update_api_key(
        db: Session,
        api_key_id: str,
        application_id: str,
        name: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Optional[APIKey]:
        """
        Update an API key

        Args:
            db: Database session
            api_key_id: API key ID
            application_id: Application ID for ownership verification
            name: New name (optional)
            is_active: New active status (optional)

        Returns:
            Updated API key if successful, None otherwise
        """
        api_key = db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.application_id == application_id
        ).first()

        if not api_key:
            return None

        if name is not None:
            api_key.name = name
        if is_active is not None:
            api_key.is_active = is_active

        db.commit()
        db.refresh(api_key)

        logger.info(f"Updated API key {api_key_id}")
        return api_key

    @staticmethod
    def delete_api_key(db: Session, api_key_id: str, application_id: str) -> bool:
        """
        Delete an API key (with safety checks)

        Args:
            db: Database session
            api_key_id: API key ID
            application_id: Application ID for ownership verification

        Returns:
            True if deleted successfully, False otherwise
        """
        # Check if this is the last active key
        active_key_count = db.query(APIKey).filter(
            APIKey.application_id == application_id,
            APIKey.is_active == True
        ).count()

        if active_key_count <= 1:
            logger.warning(f"Cannot delete last active API key for application {application_id}")
            return False

        # Get and delete the key
        api_key = db.query(APIKey).filter(
            APIKey.id == api_key_id,
            APIKey.application_id == application_id
        ).first()

        if not api_key:
            return False

        db.delete(api_key)
        db.commit()

        logger.info(f"Deleted API key {api_key_id}")
        return True
