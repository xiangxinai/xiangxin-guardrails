from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict
from database.connection import get_db
from services.risk_config_service import RiskConfigService
from services.risk_config_cache import risk_config_cache
from utils.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger()
router = APIRouter(prefix="/api/v1/config", tags=["风险类型配置"])

def get_current_user_id(request: Request) -> str:
    """从请求上下文获取当前用户ID"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = str(auth_context['data'].get('user_id'))
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in auth context")
    
    return user_id

class RiskConfigRequest(BaseModel):
    s1_enabled: bool = True
    s2_enabled: bool = True
    s3_enabled: bool = True
    s4_enabled: bool = True
    s5_enabled: bool = True
    s6_enabled: bool = True
    s7_enabled: bool = True
    s8_enabled: bool = True
    s9_enabled: bool = True
    s10_enabled: bool = True
    s11_enabled: bool = True
    s12_enabled: bool = True

class RiskConfigResponse(BaseModel):
    s1_enabled: bool
    s2_enabled: bool
    s3_enabled: bool
    s4_enabled: bool
    s5_enabled: bool
    s6_enabled: bool
    s7_enabled: bool
    s8_enabled: bool
    s9_enabled: bool
    s10_enabled: bool
    s11_enabled: bool
    s12_enabled: bool
    
    class Config:
        from_attributes = True

@router.get("/risk-types", response_model=RiskConfigResponse)
async def get_risk_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取用户风险类型配置"""
    try:
        current_user_id = get_current_user_id(request)
        risk_service = RiskConfigService(db)
        config_dict = risk_service.get_risk_config_dict(current_user_id)
        return RiskConfigResponse(**config_dict)
    except Exception as e:
        logger.error(f"Failed to get risk config for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="获取风险配置失败")

@router.put("/risk-types", response_model=RiskConfigResponse)
async def update_risk_config(
    config_request: RiskConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新用户风险类型配置"""
    try:
        current_user_id = get_current_user_id(request)
        risk_service = RiskConfigService(db)
        config_data = config_request.dict()
        
        updated_config = risk_service.update_risk_config(current_user_id, config_data)
        if not updated_config:
            raise HTTPException(status_code=500, detail="更新风险配置失败")
        
        # 清空该用户的缓存，强制重新加载
        await risk_config_cache.invalidate_user_cache(current_user_id)
        
        # 返回更新后的配置
        config_dict = risk_service.get_risk_config_dict(current_user_id)
        logger.info(f"Updated risk config for user {current_user_id}")
        
        return RiskConfigResponse(**config_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update risk config for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="更新风险配置失败")

@router.get("/risk-types/enabled", response_model=Dict[str, bool])
async def get_enabled_risk_types(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取用户启用的风险类型映射"""
    try:
        current_user_id = get_current_user_id(request)
        risk_service = RiskConfigService(db)
        enabled_types = risk_service.get_enabled_risk_types(current_user_id)
        return enabled_types
    except Exception as e:
        logger.error(f"Failed to get enabled risk types for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="获取启用风险类型失败")

@router.post("/risk-types/reset")
async def reset_risk_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """重置风险类型配置为默认值（全部启用）"""
    try:
        current_user_id = get_current_user_id(request)
        risk_service = RiskConfigService(db)
        default_config = {
            's1_enabled': True, 's2_enabled': True, 's3_enabled': True, 's4_enabled': True,
            's5_enabled': True, 's6_enabled': True, 's7_enabled': True, 's8_enabled': True,
            's9_enabled': True, 's10_enabled': True, 's11_enabled': True, 's12_enabled': True
        }
        
        updated_config = risk_service.update_risk_config(current_user_id, default_config)
        if not updated_config:
            raise HTTPException(status_code=500, detail="重置风险配置失败")
        
        # 清空该用户的缓存
        await risk_config_cache.invalidate_user_cache(current_user_id)
        
        logger.info(f"Reset risk config to default for user {current_user_id}")
        return {"message": "风险配置已重置为默认值"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset risk config for user {current_user_id}: {e}")
        raise HTTPException(status_code=500, detail="重置风险配置失败")