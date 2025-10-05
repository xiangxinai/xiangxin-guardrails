import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext

from database.models import Tenant, TenantSwitch, DetectionResult
from utils.user import generate_api_key
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

class AdminService:
    """超级管理员服务"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_super_admin_if_not_exists(self, db: Session) -> Tenant:
        """创建超级管理员租户（如果不存在）。
        如果已存在，则确保其密码与 .env 中配置一致，且账号为激活、验证状态。
        """
        try:
            # 检查是否已存在超级管理员
            existing_admin = db.query(Tenant).filter(
                Tenant.email == settings.super_admin_username,
                Tenant.is_super_admin == True
            ).first()
            
            if existing_admin:
                # 确保状态为激活、已验证
                desired_hash = self.pwd_context.hash(settings.super_admin_password)
                # 仅当密码不匹配时才更新以避免重复哈希
                try:
                    password_mismatch = not self.pwd_context.verify(settings.super_admin_password, existing_admin.password_hash)
                except Exception:
                    password_mismatch = True

                updated = False
                if password_mismatch:
                    existing_admin.password_hash = desired_hash
                    updated = True
                if not existing_admin.is_active:
                    existing_admin.is_active = True
                    updated = True
                if not existing_admin.is_verified:
                    existing_admin.is_verified = True
                    updated = True
                if not existing_admin.is_super_admin:
                    existing_admin.is_super_admin = True
                    updated = True

                if updated:
                    db.commit()
                    db.refresh(existing_admin)
                    logger.info("Super admin ensured active/verified and password synced to .env")
                
                # 检查并为超级管理员创建默认代答模板（如果还没有的话）
                try:
                    from services.template_service import create_user_default_templates
                    template_count = create_user_default_templates(db, existing_admin.id)
                    if template_count > 0:
                        logger.info(f"为现有超级管理员 {existing_admin.email} 创建了 {template_count} 个默认代答模板")
                except Exception as e:
                    logger.error(f"为现有超级管理员 {existing_admin.email} 创建默认代答模板失败: {e}")
                    # 不影响超级管理员运行，只是记录错误
                
                if not updated:
                    logger.info("Super admin already exists and up to date")
                return existing_admin
            
            # 生成API key
            api_key = self._generate_api_key()

            # 创建超级管理员租户
            super_admin = Tenant(
                email=settings.super_admin_username,
                password_hash=self.pwd_context.hash(settings.super_admin_password),
                is_active=True,
                is_verified=True,
                is_super_admin=True,
                api_key=api_key
            )
            
            db.add(super_admin)
            db.commit()
            db.refresh(super_admin)
            
            # 为超级管理员创建默认代答模板
            try:
                from services.template_service import create_user_default_templates
                template_count = create_user_default_templates(db, super_admin.id)
                logger.info(f"为超级管理员 {super_admin.email} 创建了 {template_count} 个默认代答模板")
            except Exception as e:
                logger.error(f"为超级管理员 {super_admin.email} 创建默认代答模板失败: {e}")
                # 不影响超级管理员创建过程，只是记录错误
            
            logger.info(f"Super admin created: {super_admin.email} (API Key: {api_key})")
            return super_admin
            
        except Exception as e:
            logger.error(f"Error creating super admin: {e}")
            db.rollback()
            raise
    
    def _generate_api_key(self) -> str:
        """生成唯一的API key（统一 sk-xxai- 前缀）"""
        return generate_api_key()
    
    def is_super_admin(self, tenant: Tenant) -> bool:
        """检查租户是否为超级管理员（基于.env配置的邮箱）"""
        if not tenant:
            return False
        return tenant.email == settings.super_admin_username
    
    def get_all_users(self, db: Session, admin_tenant: Tenant) -> List[Dict[str, Any]]:
        """获取所有租户列表（仅超级管理员可访问）"""
        if not self.is_super_admin(admin_tenant):
            raise PermissionError("Only super admin can access all tenants")

        # 获取租户及其检测次数
        tenants_with_counts = db.query(
            Tenant,
            func.count(DetectionResult.id).label('detection_count')
        ).outerjoin(DetectionResult, Tenant.id == DetectionResult.tenant_id).group_by(Tenant.id).all()

        return [{
            "id": str(tenant.id),
            "email": tenant.email,
            "is_active": tenant.is_active,
            # 只认 .env 中配置的超级管理员账号
            "is_super_admin": self.is_super_admin(tenant),
            "is_verified": tenant.is_verified,
            "api_key": tenant.api_key,
            "detection_count": detection_count,  # 新增检测次数
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "updated_at": tenant.updated_at.isoformat() if tenant.updated_at else None
        } for tenant, detection_count in tenants_with_counts]
    
    def switch_to_user(self, db: Session, admin_tenant: Tenant, target_tenant_id: Union[str, uuid.UUID]) -> str:
        """超级管理员切换到指定租户视角"""
        if not self.is_super_admin(admin_tenant):
            raise PermissionError("Only super admin can switch tenant view")

        # 确保target_tenant_id是UUID对象
        if isinstance(target_tenant_id, str):
            try:
                target_tenant_id = uuid.UUID(target_tenant_id)
            except ValueError:
                raise ValueError("Invalid tenant ID format")

        # 检查目标租户是否存在
        target_tenant = db.query(Tenant).filter(
            Tenant.id == target_tenant_id,
            Tenant.is_active == True
        ).first()

        if not target_tenant:
            raise ValueError("Target tenant not found or inactive")

        # 生成切换会话token
        session_token = secrets.token_urlsafe(64)
        expires_at = datetime.now() + timedelta(hours=2)  # 2小时过期

        # 清除旧的切换记录
        db.query(TenantSwitch).filter(
            TenantSwitch.admin_tenant_id == admin_tenant.id,
            TenantSwitch.is_active == True
        ).update({"is_active": False})

        # 创建新的切换记录
        user_switch = TenantSwitch(
            admin_tenant_id=admin_tenant.id,
            target_tenant_id=target_tenant_id,
            session_token=session_token,
            expires_at=expires_at
        )

        db.add(user_switch)
        db.commit()

        logger.info(f"Super admin {admin_tenant.email} switched to tenant {target_tenant.email}")

        return session_token
    
    def get_switched_user(self, db: Session, session_token: str) -> Optional[Tenant]:
        """根据切换会话token获取当前切换的租户"""
        user_switch = db.query(TenantSwitch).filter(
            TenantSwitch.session_token == session_token,
            TenantSwitch.is_active == True,
            TenantSwitch.expires_at > datetime.now()
        ).first()

        if not user_switch:
            return None

        return db.query(Tenant).filter(Tenant.id == user_switch.target_tenant_id).first()
    
    def exit_user_switch(self, db: Session, session_token: str) -> bool:
        """退出用户切换，回到管理员视角"""
        result = db.query(TenantSwitch).filter(
            TenantSwitch.session_token == session_token,
            TenantSwitch.is_active == True
        ).update({"is_active": False})
        
        db.commit()
        
        return result > 0
    
    def get_current_admin_from_switch(self, db: Session, session_token: str) -> Optional[Tenant]:
        """从切换会话中获取原始管理员租户"""
        user_switch = db.query(TenantSwitch).filter(
            TenantSwitch.session_token == session_token,
            TenantSwitch.is_active == True
        ).first()

        if not user_switch:
            return None

        return db.query(Tenant).filter(Tenant.id == user_switch.admin_tenant_id).first()

# 全局实例
admin_service = AdminService()