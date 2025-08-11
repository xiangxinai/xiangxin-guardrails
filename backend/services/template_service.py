"""
代答模板服务
用于管理用户的代答模板，包括为新用户创建默认模板等功能
"""
from sqlalchemy.orm import Session
from database.models import ResponseTemplate
import uuid
from typing import Optional


def create_user_default_templates(db: Session, user_id: uuid.UUID) -> int:
    """
    为新用户从系统模版复制创建用户级模版
    Args:
        db: 数据库会话
        user_id: 用户ID
    Returns:
        创建的模板数量
    """
    try:
        # 检查用户是否已有模版
        existing_count = db.query(ResponseTemplate).filter_by(user_id=user_id).count()
        if existing_count > 0:
            return existing_count
        
        # 获取所有系统级模版（user_id为None）
        system_templates = db.query(ResponseTemplate).filter(
            ResponseTemplate.user_id.is_(None),
            ResponseTemplate.is_default == True
        ).all()
        
        created_count = 0
        for template in system_templates:
            # 为用户创建对应模版
            user_template = ResponseTemplate(
                user_id=user_id,
                category=template.category,
                risk_level=template.risk_level,
                template_content=template.template_content,
                is_default=template.is_default,
                is_active=template.is_active
            )
            db.add(user_template)
            created_count += 1
        
        db.commit()
        return created_count
        
    except Exception as e:
        db.rollback()
        raise e


def get_user_template(db: Session, user_id: uuid.UUID, category: str, risk_level: str) -> Optional[ResponseTemplate]:
    """
    获取用户特定的代答模板
    如果用户没有对应模板，则返回系统默认模板
    """
    # 先查找用户模板
    user_template = db.query(ResponseTemplate).filter(
        ResponseTemplate.user_id == user_id,
        ResponseTemplate.category == category,
        ResponseTemplate.risk_level == risk_level,
        ResponseTemplate.is_active == True
    ).first()
    
    if user_template:
        return user_template
    
    # 如果没有用户模板，查找系统默认模板
    system_template = db.query(ResponseTemplate).filter(
        ResponseTemplate.user_id.is_(None),
        ResponseTemplate.category == category,
        ResponseTemplate.risk_level == risk_level,
        ResponseTemplate.is_active == True
    ).first()
    
    return system_template


def get_default_template(db: Session, user_id: Optional[uuid.UUID] = None) -> Optional[ResponseTemplate]:
    """
    获取默认模板（当找不到特定类别模板时使用）
    """
    if user_id:
        # 先查找用户的默认模板
        user_default = db.query(ResponseTemplate).filter(
            ResponseTemplate.user_id == user_id,
            ResponseTemplate.category == "default",
            ResponseTemplate.is_active == True
        ).first()
        
        if user_default:
            return user_default
    
    # 查找系统默认模板
    system_default = db.query(ResponseTemplate).filter(
        ResponseTemplate.user_id.is_(None),
        ResponseTemplate.category == "default",
        ResponseTemplate.is_active == True
    ).first()
    
    return system_default