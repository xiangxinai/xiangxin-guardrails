from typing import Optional, Dict
from sqlalchemy.orm import Session
from database.models import RiskTypeConfig, Tenant
from utils.logger import setup_logger

logger = setup_logger()

class RiskConfigService:
    """风险类型配置服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_risk_config(self, tenant_id: str) -> Optional[RiskTypeConfig]:
        """获取用户风险配置"""
        try:
            config = self.db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant_id
            ).first()
            return config
        except Exception as e:
            logger.error(f"Failed to get user risk config for {tenant_id}: {e}")
            return None
    
    def create_default_risk_config(self, tenant_id: str) -> RiskTypeConfig:
        """为用户创建默认风险配置（所有类型默认启用）"""
        try:
            config = RiskTypeConfig(tenant_id=tenant_id)
            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)
            logger.info(f"Created default risk config for user {tenant_id}")
            return config
        except Exception as e:
            logger.error(f"Failed to create default risk config for {tenant_id}: {e}")
            self.db.rollback()
            raise
    
    def update_risk_config(self, tenant_id: str, config_data: Dict) -> Optional[RiskTypeConfig]:
        """更新用户风险配置"""
        try:
            config = self.get_user_risk_config(tenant_id)
            if not config:
                config = self.create_default_risk_config(tenant_id)
            
            # 更新配置字段
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
        """获取用户启用的风险类型映射"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            # 如果没有配置，返回默认全部启用
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
    
    def is_risk_type_enabled(self, tenant_id: str, risk_type: str) -> bool:
        """检查指定风险类型是否启用"""
        enabled_types = self.get_enabled_risk_types(tenant_id)
        return enabled_types.get(risk_type, True)  # 默认启用
    
    def get_risk_config_dict(self, tenant_id: str) -> Dict:
        """获取用户风险配置的字典格式"""
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
        """更新用户敏感度阈值配置"""
        try:
            config = self.get_user_risk_config(tenant_id)
            if not config:
                config = self.create_default_risk_config(tenant_id)

            # 更新敏感度阈值字段
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
        """获取用户敏感度阈值配置的字典格式"""
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
        """获取用户敏感度阈值映射"""
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
        """获取用户敏感度触发等级"""
        config = self.get_user_risk_config(tenant_id)
        if not config:
            return "medium"
        return config.sensitivity_trigger_level or "medium"