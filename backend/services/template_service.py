"""
代答模板服务
用于管理租户的代答模板，包括为新租户创建默认模板等功能
"""
from sqlalchemy.orm import Session
from database.models import ResponseTemplate
import uuid
from typing import Optional


def create_user_default_templates(db: Session, tenant_id: uuid.UUID) -> int:
    """
    为新租户从系统模版复制创建租户级模版

    注意：为保持向后兼容，函数名保持为 create_user_default_templates，参数名保持为 tenant_id，但实际处理的是 tenant_id

    Args:
        db: 数据库会话
        tenant_id: 租户ID（实际是tenant_id，参数名为向后兼容）
    Returns:
        创建的模板数量
    """
    tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
    try:
        # 检查租户是否已有模版
        existing_count = db.query(ResponseTemplate).filter_by(tenant_id=tenant_id).count()
        if existing_count > 0:
            return existing_count

        # 获取所有系统级模版（tenant_id为None）
        system_templates = db.query(ResponseTemplate).filter(
            ResponseTemplate.tenant_id.is_(None),
            ResponseTemplate.is_default == True
        ).all()

        created_count = 0
        for template in system_templates:
            # 为租户创建对应模版
            tenant_template = ResponseTemplate(
                tenant_id=tenant_id,
                category=template.category,
                risk_level=template.risk_level,
                template_content=template.template_content,
                is_default=template.is_default,
                is_active=template.is_active
            )
            db.add(tenant_template)
            created_count += 1

        db.commit()
        return created_count

    except Exception as e:
        db.rollback()
        raise e


def get_user_template(db: Session, tenant_id: uuid.UUID, category: str, risk_level: str) -> Optional[ResponseTemplate]:
    """
    获取租户特定的代答模板
    如果租户没有对应模板，则返回系统默认模板

    注意：为保持向后兼容，函数名保持为 get_user_template，参数名保持为 tenant_id，但实际处理的是 tenant_id
    """
    tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
    # 先查找租户模板
    tenant_template = db.query(ResponseTemplate).filter(
        ResponseTemplate.tenant_id == tenant_id,
        ResponseTemplate.category == category,
        ResponseTemplate.risk_level == risk_level,
        ResponseTemplate.is_active == True
    ).first()

    if tenant_template:
        return tenant_template

    # 如果没有租户模板，查找系统默认模板
    system_template = db.query(ResponseTemplate).filter(
        ResponseTemplate.tenant_id.is_(None),
        ResponseTemplate.category == category,
        ResponseTemplate.risk_level == risk_level,
        ResponseTemplate.is_active == True
    ).first()

    return system_template


def get_default_template(db: Session, tenant_id: Optional[uuid.UUID] = None) -> Optional[ResponseTemplate]:
    """
    获取默认模板（当找不到特定类别模板时使用）

    注意：为保持向后兼容，参数名保持为 tenant_id，但实际处理的是 tenant_id
    """
    tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
    if tenant_id:
        # 先查找租户的默认模板
        tenant_default = db.query(ResponseTemplate).filter(
            ResponseTemplate.tenant_id == tenant_id,
            ResponseTemplate.category == "default",
            ResponseTemplate.is_active == True
        ).first()

        if tenant_default:
            return tenant_default

    # 查找系统默认模板
    system_default = db.query(ResponseTemplate).filter(
        ResponseTemplate.tenant_id.is_(None),
        ResponseTemplate.category == "default",
        ResponseTemplate.is_active == True
    ).first()

    return system_default