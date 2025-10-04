"""
数据安全API路由 - 基于正则表达式的敏感数据检测和脱敏
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
import uuid
import logging

from database.connection import get_db
from database.models import User, DataSecurityEntityType
from services.data_security_service import DataSecurityService
from utils.auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/config/data-security", tags=["data-security"])

# Pydantic模型定义
class EntityTypeCreate(BaseModel):
    """创建实体类型配置"""
    entity_type: str = Field(..., description="实体类型代码，如 ID_CARD_NUMBER")
    display_name: str = Field(..., description="显示名称，如 身份证号")
    risk_level: str = Field(..., description="风险等级: 低、中、高")
    pattern: str = Field(..., description="正则表达式模式")
    anonymization_method: str = Field(default="replace", description="脱敏方法: replace, mask, hash, encrypt, shuffle, random")
    anonymization_config: Optional[Dict[str, Any]] = Field(default=None, description="脱敏配置")
    check_input: bool = Field(default=True, description="是否检测输入")
    check_output: bool = Field(default=True, description="是否检测输出")
    is_active: bool = Field(default=True, description="是否启用")

class EntityTypeUpdate(BaseModel):
    """更新实体类型配置"""
    display_name: Optional[str] = None
    risk_level: Optional[str] = None
    pattern: Optional[str] = None
    anonymization_method: Optional[str] = None
    anonymization_config: Optional[Dict[str, Any]] = None
    check_input: Optional[bool] = None
    check_output: Optional[bool] = None
    is_active: Optional[bool] = None

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """获取当前用户"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="未授权")

    user_id = auth_context.get("data", {}).get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="无效的用户ID")

    user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user

@router.post("/entity-types", response_model=Dict[str, Any])
async def create_entity_type(
    entity_data: EntityTypeCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建敏感数据类型配置"""
    current_user = get_current_user(request, db)

    # 检查是否已存在相同的实体类型
    existing = db.query(DataSecurityEntityType).filter(
        and_(
            DataSecurityEntityType.entity_type == entity_data.entity_type,
            DataSecurityEntityType.user_id == current_user.id
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该实体类型已存在")

    # 创建服务实例
    service = DataSecurityService(db)

    # 创建新配置
    entity_type = service.create_entity_type(
        user_id=str(current_user.id),
        entity_type=entity_data.entity_type,
        display_name=entity_data.display_name,
        risk_level=entity_data.risk_level,
        pattern=entity_data.pattern,
        anonymization_method=entity_data.anonymization_method,
        anonymization_config=entity_data.anonymization_config,
        check_input=entity_data.check_input,
        check_output=entity_data.check_output,
        is_global=False
    )

    recognition_config = entity_type.recognition_config or {}

    return {
        "id": str(entity_type.id),
        "entity_type": entity_type.entity_type,
        "display_name": entity_type.display_name,
        "risk_level": entity_type.category,
        "pattern": recognition_config.get('pattern', ''),
        "anonymization_method": entity_type.anonymization_method,
        "anonymization_config": entity_type.anonymization_config,
        "check_input": recognition_config.get('check_input', True),
        "check_output": recognition_config.get('check_output', True),
        "is_active": entity_type.is_active,
        "is_global": entity_type.is_global,
        "created_at": entity_type.created_at.isoformat(),
        "updated_at": entity_type.updated_at.isoformat()
    }

@router.get("/entity-types")
async def list_entity_types(
    risk_level: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取敏感数据类型配置列表（包括全局和用户自己的）"""
    current_user = get_current_user(request, db)

    # 创建服务实例
    service = DataSecurityService(db)

    # 获取实体类型列表
    entity_types = service.get_entity_types(
        user_id=str(current_user.id),
        risk_level=risk_level
    )

    items = []
    for et in entity_types:
        recognition_config = et.recognition_config or {}
        items.append({
            "id": str(et.id),
            "entity_type": et.entity_type,
            "display_name": et.display_name,
            "risk_level": et.category,
            "pattern": recognition_config.get('pattern', ''),
            "anonymization_method": et.anonymization_method,
            "anonymization_config": et.anonymization_config,
            "check_input": recognition_config.get('check_input', True),
            "check_output": recognition_config.get('check_output', True),
            "is_active": et.is_active,
            "is_global": et.is_global,
            "created_at": et.created_at.isoformat(),
            "updated_at": et.updated_at.isoformat()
        })

    return {
        "total": len(items),
        "items": items
    }

@router.get("/entity-types/{entity_type_id}")
async def get_entity_type(
    entity_type_id: str,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """获取单个敏感数据类型配置"""
    current_user = get_current_user(request, db)

    entity_type = db.query(DataSecurityEntityType).filter(
        DataSecurityEntityType.id == uuid.UUID(entity_type_id)
    ).first()

    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型配置不存在")

    # 检查权限：只能查看全局配置或自己的配置
    if not entity_type.is_global and entity_type.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该配置")

    recognition_config = entity_type.recognition_config or {}

    return {
        "id": str(entity_type.id),
        "entity_type": entity_type.entity_type,
        "display_name": entity_type.display_name,
        "risk_level": entity_type.category,
        "pattern": recognition_config.get('pattern', ''),
        "anonymization_method": entity_type.anonymization_method,
        "anonymization_config": entity_type.anonymization_config,
        "check_input": recognition_config.get('check_input', True),
        "check_output": recognition_config.get('check_output', True),
        "is_active": entity_type.is_active,
        "is_global": entity_type.is_global,
        "created_at": entity_type.created_at.isoformat(),
        "updated_at": entity_type.updated_at.isoformat()
    }

@router.put("/entity-types/{entity_type_id}")
async def update_entity_type(
    entity_type_id: str,
    update_data: EntityTypeUpdate,
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """更新敏感数据类型配置"""
    current_user = get_current_user(request, db)

    entity_type = db.query(DataSecurityEntityType).filter(
        DataSecurityEntityType.id == uuid.UUID(entity_type_id)
    ).first()

    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型配置不存在")

    # 检查权限
    if entity_type.is_global:
        # 只有管理员可以修改全局配置
        if not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改全局配置")
    elif entity_type.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改该配置")

    # 创建服务实例
    service = DataSecurityService(db)

    # 构建更新参数
    update_kwargs = {}
    if update_data.display_name is not None:
        update_kwargs['display_name'] = update_data.display_name
    if update_data.risk_level is not None:
        update_kwargs['risk_level'] = update_data.risk_level
    if update_data.pattern is not None:
        update_kwargs['pattern'] = update_data.pattern
    if update_data.anonymization_method is not None:
        update_kwargs['anonymization_method'] = update_data.anonymization_method
    if update_data.anonymization_config is not None:
        update_kwargs['anonymization_config'] = update_data.anonymization_config
    if update_data.check_input is not None:
        update_kwargs['check_input'] = update_data.check_input
    if update_data.check_output is not None:
        update_kwargs['check_output'] = update_data.check_output
    if update_data.is_active is not None:
        update_kwargs['is_active'] = update_data.is_active

    # 更新
    updated_entity = service.update_entity_type(
        entity_type_id=entity_type_id,
        user_id=str(current_user.id),
        **update_kwargs
    )

    if not updated_entity:
        raise HTTPException(status_code=404, detail="更新失败")

    recognition_config = updated_entity.recognition_config or {}

    return {
        "id": str(updated_entity.id),
        "entity_type": updated_entity.entity_type,
        "display_name": updated_entity.display_name,
        "risk_level": updated_entity.category,
        "pattern": recognition_config.get('pattern', ''),
        "anonymization_method": updated_entity.anonymization_method,
        "anonymization_config": updated_entity.anonymization_config,
        "check_input": recognition_config.get('check_input', True),
        "check_output": recognition_config.get('check_output', True),
        "is_active": updated_entity.is_active,
        "is_global": updated_entity.is_global,
        "created_at": updated_entity.created_at.isoformat(),
        "updated_at": updated_entity.updated_at.isoformat()
    }

@router.delete("/entity-types/{entity_type_id}")
async def delete_entity_type(
    entity_type_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """删除敏感数据类型配置"""
    current_user = get_current_user(request, db)

    entity_type = db.query(DataSecurityEntityType).filter(
        DataSecurityEntityType.id == uuid.UUID(entity_type_id)
    ).first()

    if not entity_type:
        raise HTTPException(status_code=404, detail="实体类型配置不存在")

    # 检查权限
    if entity_type.is_global:
        # 只有管理员可以删除全局配置
        if not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以删除全局配置")
    elif entity_type.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除该配置")

    # 创建服务实例
    service = DataSecurityService(db)

    # 删除
    success = service.delete_entity_type(entity_type_id, str(current_user.id))

    if not success:
        raise HTTPException(status_code=404, detail="删除失败")

    return {"message": "删除成功"}

@router.post("/global-entity-types", response_model=Dict[str, Any])
async def create_global_entity_type(
    entity_data: EntityTypeCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建全局敏感数据类型配置（仅管理员）"""
    current_user = get_current_user(request, db)

    # 检查是否是管理员
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="仅管理员可以创建全局配置")

    # 检查是否已存在相同的全局实体类型
    existing = db.query(DataSecurityEntityType).filter(
        and_(
            DataSecurityEntityType.entity_type == entity_data.entity_type,
            DataSecurityEntityType.is_global == True
        )
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该全局实体类型已存在")

    # 创建服务实例
    service = DataSecurityService(db)

    # 创建新的全局配置
    entity_type = service.create_entity_type(
        user_id=str(current_user.id),
        entity_type=entity_data.entity_type,
        display_name=entity_data.display_name,
        risk_level=entity_data.risk_level,
        pattern=entity_data.pattern,
        anonymization_method=entity_data.anonymization_method,
        anonymization_config=entity_data.anonymization_config,
        check_input=entity_data.check_input,
        check_output=entity_data.check_output,
        is_global=True
    )

    recognition_config = entity_type.recognition_config or {}

    return {
        "id": str(entity_type.id),
        "entity_type": entity_type.entity_type,
        "display_name": entity_type.display_name,
        "risk_level": entity_type.category,
        "pattern": recognition_config.get('pattern', ''),
        "anonymization_method": entity_type.anonymization_method,
        "anonymization_config": entity_type.anonymization_config,
        "check_input": recognition_config.get('check_input', True),
        "check_output": recognition_config.get('check_output', True),
        "is_active": entity_type.is_active,
        "is_global": entity_type.is_global,
        "created_at": entity_type.created_at.isoformat(),
        "updated_at": entity_type.updated_at.isoformat()
    }
