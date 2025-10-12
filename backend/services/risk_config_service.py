from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from database.models import RiskTypeConfig, Tenant
from utils.logger import setup_logger

logger = setup_logger()

class RiskConfigService:
    """Protection Config Template Service

    Manages protection config templates which group all protection settings:
    - Risk type switches (S1-S12)
    - Sensitivity thresholds (high, medium, low)
    - Associated configurations (data security, blacklist/whitelist, ban policies, knowledge bases)

    Each API key is associated with a specific protection config template.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_risk_config(self, tenant_id: str) -> Optional[RiskTypeConfig]:
        """Get tenant's default protection config template"""
        try:
            config = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant_id,
                RiskTypeConfig.is_default == True
            ).first()
            return config
        except Exception as e:
            logger.error(f"Failed to get user risk config for {tenant_id}: {e}")
            return None

    def list_user_risk_configs(self, tenant_id: str) -> List[RiskTypeConfig]:
        """List all risk configs for a tenant"""
        try:
            configs = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant_id
            ).order_by(RiskTypeConfig.is_default.desc(), RiskTypeConfig.id).all()
            return configs
        except Exception as e:
            logger.error(f"Failed to list risk configs for {tenant_id}: {e}")
            return []

    def get_risk_config_by_id(self, config_id: int, tenant_id: str) -> Optional[RiskTypeConfig]:
        """Get a specific risk config by ID"""
        try:
            config = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.id == config_id,
                RiskTypeConfig.tenant_id == tenant_id
            ).first()
            return config
        except Exception as e:
            logger.error(f"Failed to get risk config {config_id} for {tenant_id}: {e}")
            return None
    
    def create_default_risk_config(self, tenant_id: str) -> RiskTypeConfig:
        """Create default risk config for user (all types default enabled)"""
        try:
            config = RiskTypeConfig(
                tenant_id=tenant_id,
                name="Default Config",
                is_default=True
            )
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Created default risk config for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to create default risk config for {tenant_id}: {e}")
            self.db.rollback()
            raise

    def create_risk_config(self, tenant_id: str, name: str, config_data: Dict) -> RiskTypeConfig:
        """Create a new risk config template"""
        try:
            # Check if name already exists for this tenant
            existing = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant_id,
                RiskTypeConfig.name == name
            ).first()
            if existing:
                raise ValueError(f"Risk config with name '{name}' already exists")

            config = RiskTypeConfig(
                tenant_id=tenant_id,
                name=name,
                is_default=config_data.get('is_default', False)
            )

            # Set risk type switches
            for field, value in config_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)

            # If this is set as default, unset other defaults
            if config.is_default:
                self.db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.tenant_id == tenant_id,
                    RiskTypeConfig.is_default == True
                ).update({'is_default': False})

            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Created risk config '{name}' for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to create risk config for {tenant_id}: {e}")
            self.db.rollback()
            raise

    def update_risk_config_by_id(self, config_id: int, tenant_id: str, name: str, config_data: Dict) -> Optional[RiskTypeConfig]:
        """Update a specific risk config"""
        try:
            config = self.get_risk_config_by_id(config_id, tenant_id)
            if not config:
                raise ValueError(f"Risk config {config_id} not found")

            # Check if new name conflicts with existing configs (excluding current)
            if name != config.name:
                existing = self.db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.tenant_id == tenant_id,
                    RiskTypeConfig.name == name,
                    RiskTypeConfig.id != config_id
                ).first()
                if existing:
                    raise ValueError(f"Risk config with name '{name}' already exists")

            config.name = name

            # Update config fields
            for field, value in config_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)

            # If this is set as default, unset other defaults
            if config.is_default:
                self.db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.tenant_id == tenant_id,
                    RiskTypeConfig.id != config_id,
                    RiskTypeConfig.is_default == True
                ).update({'is_default': False})

            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Updated risk config {config_id} for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to update risk config {config_id} for {tenant_id}: {e}")
            self.db.rollback()
            raise

    def delete_risk_config(self, config_id: int, tenant_id: str) -> bool:
        """Delete a risk config template"""
        try:
            config = self.get_risk_config_by_id(config_id, tenant_id)
            if not config:
                raise ValueError(f"Risk config {config_id} not found")

            # Prevent deleting the default config if it's the only one
            if config.is_default:
                count = self.db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.tenant_id == tenant_id
                ).count()
                if count <= 1:
                    raise ValueError("Cannot delete the only risk config")

            # Check if any API keys are using this config
            from database.models import TenantApiKey
            api_keys_using = self.db.query(TenantApiKey).filter(
                TenantApiKey.risk_config_id == config_id
            ).count()
            if api_keys_using > 0:
                raise ValueError(f"Cannot delete config: {api_keys_using} API key(s) are using it")

            self.db.delete(config)
            self.db.commit()
            logger.info(f"Deleted risk config {config_id} for user {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete risk config {config_id} for {tenant_id}: {e}")
            self.db.rollback()
            raise
    
    def update_risk_config(self, tenant_id: str, config_data: Dict) -> Optional[RiskTypeConfig]:
        """Update user risk config"""
        try:
            config = self.get_user_risk_config(tenant_id)
            if not config:
                config = self.create_default_risk_config(tenant_id)
            
            # Update config fields
            for field, value in config_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)
            
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Updated risk config for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to update risk config for {tenant_id}: {e}")
            self.db.rollback()
            return None
    
    def get_enabled_risk_types(self, tenant_id: str) -> Dict[str, bool]:
        """Get user enabled risk type mapping"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            # Return default all enabled when user has no configuration
            return {
                'S1': True, 'S2': True, 'S3': True, 'S4': True,
                'S5': True, 'S6': True, 'S7': True, 'S8': True,
                'S9': True, 'S10': True, 'S11': True, 'S12': True
            }
        
        return {
            'S1': config.s1_enabled,
            'S2': config.s2_enabled,
            'S3': config.s3_enabled,
            'S4': config.s4_enabled,
            'S5': config.s5_enabled,
            'S6': config.s6_enabled,
            'S7': config.s7_enabled,
            'S8': config.s8_enabled,
            'S9': config.s9_enabled,
            'S10': config.s10_enabled,
            'S11': config.s11_enabled,
            'S12': config.s12_enabled,
        }
    
    def is_risk_type_enabled(self, tenant_id: str, risk_type: str, risk_config_id: Optional[int] = None) -> bool:
        """Check if specified risk type is enabled

        Args:
            tenant_id: Tenant ID (fallback if risk_config_id not provided)
            risk_type: Risk type code (e.g., 'S1', 'S2')
            risk_config_id: Specific risk config ID to check (for API key specific configs)

        Returns:
            True if enabled, False otherwise
        """
        if risk_config_id:
            # Use specific risk config
            enabled_types = self.get_enabled_risk_types_by_config_id(risk_config_id)
        else:
            # Fall back to tenant's default config
            enabled_types = self.get_enabled_risk_types(tenant_id)
        return enabled_types.get(risk_type, True)  # Default enabled

    def get_enabled_risk_types_by_config_id(self, risk_config_id: int) -> Dict[str, bool]:
        """Get enabled risk types by config ID

        Args:
            risk_config_id: Risk config ID

        Returns:
            Dictionary mapping risk type codes to enabled status
        """
        try:
            config = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.id == risk_config_id
            ).first()

            if not config:
                # If config not found, return all enabled
                return {
                    'S1': True, 'S2': True, 'S3': True, 'S4': True,
                    'S5': True, 'S6': True, 'S7': True, 'S8': True,
                    'S9': True, 'S10': True, 'S11': True, 'S12': True
                }

            return {
                'S1': config.s1_enabled,
                'S2': config.s2_enabled,
                'S3': config.s3_enabled,
                'S4': config.s4_enabled,
                'S5': config.s5_enabled,
                'S6': config.s6_enabled,
                'S7': config.s7_enabled,
                'S8': config.s8_enabled,
                'S9': config.s9_enabled,
                'S10': config.s10_enabled,
                'S11': config.s11_enabled,
                'S12': config.s12_enabled,
            }
        except Exception as e:
            logger.error(f"Failed to get enabled risk types for config {risk_config_id}: {e}")
            # Return all enabled on error
            return {
                'S1': True, 'S2': True, 'S3': True, 'S4': True,
                'S5': True, 'S6': True, 'S7': True, 'S8': True,
                'S9': True, 'S10': True, 'S11': True, 'S12': True
            }
    
    def get_risk_config_dict(self, tenant_id: str) -> Dict:
        """Get user risk config dictionary format"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            return {
                's1_enabled': True, 's2_enabled': True, 's3_enabled': True, 's4_enabled': True,
                's5_enabled': True, 's6_enabled': True, 's7_enabled': True, 's8_enabled': True,
                's9_enabled': True, 's10_enabled': True, 's11_enabled': True, 's12_enabled': True
            }
        
        return {
            's1_enabled': config.s1_enabled,
            's2_enabled': config.s2_enabled,
            's3_enabled': config.s3_enabled,
            's4_enabled': config.s4_enabled,
            's5_enabled': config.s5_enabled,
            's6_enabled': config.s6_enabled,
            's7_enabled': config.s7_enabled,
            's8_enabled': config.s8_enabled,
            's9_enabled': config.s9_enabled,
            's10_enabled': config.s10_enabled,
            's11_enabled': config.s11_enabled,
            's12_enabled': config.s12_enabled,
        }

    def update_sensitivity_thresholds(self, tenant_id: str, threshold_data: Dict) -> Optional[RiskTypeConfig]:
        """Update user sensitivity threshold configuration"""
        try:
            config = self.get_user_risk_config(tenant_id)
            if not config:
                config = self.create_default_risk_config(tenant_id)

            # Update sensitivity threshold fields
            for field, value in threshold_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)

            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Updated sensitivity thresholds for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to update sensitivity thresholds for {tenant_id}: {e}")
            self.db.rollback()
            return None

    def get_sensitivity_threshold_dict(self, tenant_id: str) -> Dict:
        """Get user sensitivity threshold configuration dictionary format"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            return {
                'low_sensitivity_threshold': 0.95,
                'medium_sensitivity_threshold': 0.60,
                'high_sensitivity_threshold': 0.40,
                'sensitivity_trigger_level': "medium"
            }

        return {
            'low_sensitivity_threshold': config.low_sensitivity_threshold or 0.95,
            'medium_sensitivity_threshold': config.medium_sensitivity_threshold or 0.60,
            'high_sensitivity_threshold': config.high_sensitivity_threshold or 0.40,
            'sensitivity_trigger_level': config.sensitivity_trigger_level or "medium",
        }

    def get_sensitivity_thresholds(self, tenant_id: str) -> Dict[str, float]:
        """Get user sensitivity threshold mapping"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            return {
                'low': 0.95,
                'medium': 0.60,
                'high': 0.40
            }

        return {
            'low': config.low_sensitivity_threshold or 0.95,
            'medium': config.medium_sensitivity_threshold or 0.60,
            'high': config.high_sensitivity_threshold or 0.40
        }

    def get_sensitivity_trigger_level(self, tenant_id: str) -> str:
        """Get user sensitivity trigger level"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            return "medium"
        return config.sensitivity_trigger_level or "medium"

    def clone_risk_config(self, config_id: int, tenant_id: str, new_name: str) -> RiskTypeConfig:
        """Clone an existing config set with a new name

        Args:
            config_id: ID of the config to clone
            tenant_id: Tenant ID
            new_name: Name for the new cloned config

        Returns:
            The newly created cloned config

        Raises:
            ValueError: If source config not found or new name already exists
        """
        try:
            # Get source config
            source_config = self.get_risk_config_by_id(config_id, tenant_id)
            if not source_config:
                raise ValueError(f"Source config {config_id} not found")

            # Check if new name already exists
            existing = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant_id,
                RiskTypeConfig.name == new_name
            ).first()
            if existing:
                raise ValueError(f"Config with name '{new_name}' already exists")

            # Create new config with same settings
            new_config = RiskTypeConfig(
                tenant_id=tenant_id,
                name=new_name,
                description=source_config.description,
                is_default=False,  # Cloned config is never default
                s1_enabled=source_config.s1_enabled,
                s2_enabled=source_config.s2_enabled,
                s3_enabled=source_config.s3_enabled,
                s4_enabled=source_config.s4_enabled,
                s5_enabled=source_config.s5_enabled,
                s6_enabled=source_config.s6_enabled,
                s7_enabled=source_config.s7_enabled,
                s8_enabled=source_config.s8_enabled,
                s9_enabled=source_config.s9_enabled,
                s10_enabled=source_config.s10_enabled,
                s11_enabled=source_config.s11_enabled,
                s12_enabled=source_config.s12_enabled,
                high_sensitivity_threshold=source_config.high_sensitivity_threshold,
                medium_sensitivity_threshold=source_config.medium_sensitivity_threshold,
                low_sensitivity_threshold=source_config.low_sensitivity_threshold,
                sensitivity_trigger_level=source_config.sensitivity_trigger_level
            )

            self.db.add(new_config)
            self.db.commit()
            self.db.refresh(new_config)
            logger.info(f"Cloned config {config_id} to '{new_name}' for tenant {tenant_id}")
            return new_config

        except Exception as e:
            logger.error(f"Failed to clone config {config_id}: {e}")
            self.db.rollback()
            raise

    def get_config_associations(self, config_id: int, tenant_id: str) -> Dict:
        """Get all associations for a config set

        Returns a dictionary containing lists of associated:
        - blacklists
        - whitelists
        - response_templates
        - knowledge_bases
        - data_security_entities
        - ban_policies
        - api_keys
        """
        try:
            from database.models import (
                Blacklist, Whitelist, ResponseTemplate, KnowledgeBase,
                DataSecurityEntityType, BanPolicy, TenantApiKey
            )

            # Verify config belongs to tenant
            config = self.get_risk_config_by_id(config_id, tenant_id)
            if not config:
                raise ValueError(f"Config {config_id} not found")

            # Get associated blacklists
            blacklists = self.db.query(Blacklist).filter(
                Blacklist.template_id == config_id,
                Blacklist.tenant_id == tenant_id
            ).all()

            # Get associated whitelists
            whitelists = self.db.query(Whitelist).filter(
                Whitelist.template_id == config_id,
                Whitelist.tenant_id == tenant_id
            ).all()

            # Get associated response templates
            response_templates = self.db.query(ResponseTemplate).filter(
                ResponseTemplate.template_id == config_id,
                ResponseTemplate.tenant_id == tenant_id
            ).all()

            # Get associated knowledge bases
            knowledge_bases = self.db.query(KnowledgeBase).filter(
                KnowledgeBase.template_id == config_id,
                KnowledgeBase.tenant_id == tenant_id
            ).all()

            # Get associated data security entities
            data_security_entities = self.db.query(DataSecurityEntityType).filter(
                DataSecurityEntityType.template_id == config_id,
                DataSecurityEntityType.tenant_id == tenant_id
            ).all()

            # Get associated ban policies
            ban_policies = self.db.query(BanPolicy).filter(
                BanPolicy.template_id == config_id,
                BanPolicy.tenant_id == tenant_id
            ).all()

            # Get API keys using this config
            api_keys = self.db.query(TenantApiKey).filter(
                TenantApiKey.template_id == config_id,
                TenantApiKey.tenant_id == tenant_id
            ).all()

            return {
                'blacklists': [{'id': b.id, 'name': b.name, 'is_active': b.is_active} for b in blacklists],
                'whitelists': [{'id': w.id, 'name': w.name, 'is_active': w.is_active} for w in whitelists],
                'response_templates': [{'id': r.id, 'category': r.category, 'is_active': r.is_active} for r in response_templates],
                'knowledge_bases': [{'id': k.id, 'name': k.name, 'is_active': k.is_active} for k in knowledge_bases],
                'data_security_entities': [{'id': d.id, 'entity_type': d.entity_type, 'is_active': d.is_active} for d in data_security_entities],
                'ban_policies': [{'id': b.id, 'enabled': b.enabled} for b in ban_policies],
                'api_keys': [{'id': str(a.id), 'name': a.name, 'is_active': a.is_active} for a in api_keys]
            }

        except Exception as e:
            logger.error(f"Failed to get config associations for {config_id}: {e}")
            raise


def create_user_default_risk_config(db: Session, tenant_id: str) -> int:
    """Create default risk config for new tenant

    Note: For backward compatibility, function name remains create_user_default_risk_config, parameter name tenant_id

    Args:
        db: Database session
        tenant_id: Tenant ID
    Returns:
        Number of created configs (0 if already exists, 1 if created)
    """
    try:
        # Check if tenant already has risk configs
        existing_count = db.query(RiskTypeConfig).filter_by(tenant_id=tenant_id).count()
        if existing_count > 0:
            return existing_count

        # Create default config with all risk types enabled
        config = RiskTypeConfig(
            tenant_id=tenant_id,
            name="Default Config",
            is_default=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        logger.info(f"Created default risk config for tenant {tenant_id}")
        return 1

    except Exception as e:
        logger.error(f"Failed to create default risk config for tenant {tenant_id}: {e}")
        db.rollback()
        raise e