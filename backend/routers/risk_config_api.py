from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict
import uuid
from database.connection import get_db
from database.models import Tenant
from services.risk_config_service import RiskConfigService
from services.risk_config_cache import risk_config_cache
from services.admin_service import admin_service
from utils.logger import setup_logger
from utils.auth import verify_token
from pydantic import BaseModel, Field

logger = setup_logger()
router = APIRouter(prefix="/api/v1/config", tags=["Risk type configuration"])

def get_current_user_from_request(request: Request, db: Session) -> Tenant:
    """Get current user from request (support user switch)"""
    # 1) Priority check if there is user switch session
    switch_token = request.headers.get('x-switch-session')
    if switch_token:
        switched_user = admin_service.get_switched_user(db, switch_token)
        if switched_user:
            return switched_user

    # 2) Get user from auth context
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context or 'data' not in auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = auth_context['data']
    tenant_id_value = data.get('tenant_id')
    user_email_value = data.get('email')

    # 2a) Try to parse tenant_id as UUID and query
    if tenant_id_value:
        try:
            tenant_uuid = uuid.UUID(str(tenant_id_value))
            user = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
            if user:
                return user
        except ValueError:
            pass

    # 2b) Fall back to using email find
    if user_email_value:
        user = db.query(Tenant).filter(Tenant.email == user_email_value).first()
        if user:
            return user

    # 2c) Last resort: parse JWT in Authorization header, try again
    auth_header = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = verify_token(token)
            raw_tenant_id = payload.get('tenant_id') or payload.get('sub')
            if raw_tenant_id:
                try:
                    tenant_uuid = uuid.UUID(str(raw_tenant_id))
                    user = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
                    if user:
                        return user
                except ValueError:
                    pass
            email_claim = payload.get('email') or payload.get('username')
            if email_claim:
                user = db.query(Tenant).filter(Tenant.email == email_claim).first()
                if user:
                    return user
        except Exception:
            pass

    # Unable to locate valid user
    raise HTTPException(status_code=401, detail="User not found or invalid context")

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

class RiskConfigListItem(BaseModel):
    """Risk config list item for selection"""
    id: int
    name: str
    tenant_id: str
    is_default: bool

    class Config:
        from_attributes = True

class CreateRiskConfigRequest(BaseModel):
    """Request to create a new risk config"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(None, max_length=500)
    is_default: bool = False
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
    high_sensitivity_threshold: float = Field(0.40, ge=0.0, le=1.0)
    medium_sensitivity_threshold: float = Field(0.60, ge=0.0, le=1.0)
    low_sensitivity_threshold: float = Field(0.95, ge=0.0, le=1.0)
    sensitivity_trigger_level: str = Field("medium", pattern="^(low|medium|high)$")

class UpdateRiskConfigRequest(BaseModel):
    """Request to update a risk config"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(None, max_length=500)
    is_default: bool = False
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
    high_sensitivity_threshold: float = Field(0.40, ge=0.0, le=1.0)
    medium_sensitivity_threshold: float = Field(0.60, ge=0.0, le=1.0)
    low_sensitivity_threshold: float = Field(0.95, ge=0.0, le=1.0)
    sensitivity_trigger_level: str = Field("medium", pattern="^(low|medium|high)$")

class CloneConfigRequest(BaseModel):
    """Request to clone a config"""
    new_name: str = Field(..., min_length=1, max_length=100)

class RiskConfigDetailResponse(BaseModel):
    """Detailed risk config response"""
    id: int
    name: str
    description: str = None
    tenant_id: str
    is_default: bool
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
    high_sensitivity_threshold: float
    medium_sensitivity_threshold: float
    low_sensitivity_threshold: float
    sensitivity_trigger_level: str

    class Config:
        from_attributes = True

class SensitivityThresholdRequest(BaseModel):
    high_sensitivity_threshold: float = Field(..., ge=0.0, le=1.0)
    medium_sensitivity_threshold: float = Field(..., ge=0.0, le=1.0)
    low_sensitivity_threshold: float = Field(..., ge=0.0, le=1.0)
    sensitivity_trigger_level: str = Field(..., pattern="^(low|medium|high)$")

class SensitivityThresholdResponse(BaseModel):
    high_sensitivity_threshold: float
    medium_sensitivity_threshold: float
    low_sensitivity_threshold: float
    sensitivity_trigger_level: str

    class Config:
        from_attributes = True

@router.get("/risk-configs", response_model=list[RiskConfigDetailResponse])
async def list_risk_configs(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all risk configurations for the current tenant with full details"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        configs = risk_service.list_user_risk_configs(str(current_user.id))
        return [
            RiskConfigDetailResponse(
                id=config.id,
                name=config.name,
                description=config.description,
                tenant_id=str(config.tenant_id),
                is_default=config.is_default,
                s1_enabled=config.s1_enabled,
                s2_enabled=config.s2_enabled,
                s3_enabled=config.s3_enabled,
                s4_enabled=config.s4_enabled,
                s5_enabled=config.s5_enabled,
                s6_enabled=config.s6_enabled,
                s7_enabled=config.s7_enabled,
                s8_enabled=config.s8_enabled,
                s9_enabled=config.s9_enabled,
                s10_enabled=config.s10_enabled,
                s11_enabled=config.s11_enabled,
                s12_enabled=config.s12_enabled,
                high_sensitivity_threshold=config.high_sensitivity_threshold,
                medium_sensitivity_threshold=config.medium_sensitivity_threshold,
                low_sensitivity_threshold=config.low_sensitivity_threshold,
                sensitivity_trigger_level=config.sensitivity_trigger_level
            )
            for config in configs
        ]
    except Exception as e:
        logger.error(f"Failed to list risk configs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list risk configs")

@router.post("/risk-configs", response_model=RiskConfigDetailResponse, status_code=201)
async def create_risk_config(
    config_request: CreateRiskConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new risk configuration template"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        config_data = config_request.dict()
        name = config_data.pop('name')

        config = risk_service.create_risk_config(str(current_user.id), name, config_data)

        return RiskConfigDetailResponse(
            id=config.id,
            name=config.name,
            tenant_id=str(config.tenant_id),
            is_default=config.is_default,
            s1_enabled=config.s1_enabled,
            s2_enabled=config.s2_enabled,
            s3_enabled=config.s3_enabled,
            s4_enabled=config.s4_enabled,
            s5_enabled=config.s5_enabled,
            s6_enabled=config.s6_enabled,
            s7_enabled=config.s7_enabled,
            s8_enabled=config.s8_enabled,
            s9_enabled=config.s9_enabled,
            s10_enabled=config.s10_enabled,
            s11_enabled=config.s11_enabled,
            s12_enabled=config.s12_enabled,
            high_sensitivity_threshold=config.high_sensitivity_threshold,
            medium_sensitivity_threshold=config.medium_sensitivity_threshold,
            low_sensitivity_threshold=config.low_sensitivity_threshold,
            sensitivity_trigger_level=config.sensitivity_trigger_level
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to create risk config")

@router.get("/risk-configs/{config_id}", response_model=RiskConfigDetailResponse)
async def get_risk_config_detail(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get detailed risk configuration"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        config = risk_service.get_risk_config_by_id(config_id, str(current_user.id))
        if not config:
            raise HTTPException(status_code=404, detail="Risk config not found")

        return RiskConfigDetailResponse(
            id=config.id,
            name=config.name,
            tenant_id=str(config.tenant_id),
            is_default=config.is_default,
            s1_enabled=config.s1_enabled,
            s2_enabled=config.s2_enabled,
            s3_enabled=config.s3_enabled,
            s4_enabled=config.s4_enabled,
            s5_enabled=config.s5_enabled,
            s6_enabled=config.s6_enabled,
            s7_enabled=config.s7_enabled,
            s8_enabled=config.s8_enabled,
            s9_enabled=config.s9_enabled,
            s10_enabled=config.s10_enabled,
            s11_enabled=config.s11_enabled,
            s12_enabled=config.s12_enabled,
            high_sensitivity_threshold=config.high_sensitivity_threshold,
            medium_sensitivity_threshold=config.medium_sensitivity_threshold,
            low_sensitivity_threshold=config.low_sensitivity_threshold,
            sensitivity_trigger_level=config.sensitivity_trigger_level
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk config")

@router.put("/risk-configs/{config_id}", response_model=RiskConfigDetailResponse)
async def update_risk_config_detail(
    config_id: int,
    config_request: UpdateRiskConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update a risk configuration template"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        config_data = config_request.dict()
        name = config_data.pop('name')

        config = risk_service.update_risk_config_by_id(config_id, str(current_user.id), name, config_data)

        # Clear cache
        await risk_config_cache.invalidate_user_cache(str(current_user.id))

        return RiskConfigDetailResponse(
            id=config.id,
            name=config.name,
            tenant_id=str(config.tenant_id),
            is_default=config.is_default,
            s1_enabled=config.s1_enabled,
            s2_enabled=config.s2_enabled,
            s3_enabled=config.s3_enabled,
            s4_enabled=config.s4_enabled,
            s5_enabled=config.s5_enabled,
            s6_enabled=config.s6_enabled,
            s7_enabled=config.s7_enabled,
            s8_enabled=config.s8_enabled,
            s9_enabled=config.s9_enabled,
            s10_enabled=config.s10_enabled,
            s11_enabled=config.s11_enabled,
            s12_enabled=config.s12_enabled,
            high_sensitivity_threshold=config.high_sensitivity_threshold,
            medium_sensitivity_threshold=config.medium_sensitivity_threshold,
            low_sensitivity_threshold=config.low_sensitivity_threshold,
            sensitivity_trigger_level=config.sensitivity_trigger_level
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update risk config")

@router.delete("/risk-configs/{config_id}", status_code=204)
async def delete_risk_config_template(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a risk configuration template"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        risk_service.delete_risk_config(config_id, str(current_user.id))

        # Clear cache
        await risk_config_cache.invalidate_user_cache(str(current_user.id))

        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete risk config")

@router.post("/risk-configs/{config_id}/clone", response_model=RiskConfigDetailResponse, status_code=201)
async def clone_risk_config(
    config_id: int,
    clone_request: CloneConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Clone an existing config set with a new name"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        cloned_config = risk_service.clone_risk_config(
            config_id=config_id,
            tenant_id=str(current_user.id),
            new_name=clone_request.new_name
        )

        return RiskConfigDetailResponse(
            id=cloned_config.id,
            name=cloned_config.name,
            description=cloned_config.description,
            tenant_id=str(cloned_config.tenant_id),
            is_default=cloned_config.is_default,
            s1_enabled=cloned_config.s1_enabled,
            s2_enabled=cloned_config.s2_enabled,
            s3_enabled=cloned_config.s3_enabled,
            s4_enabled=cloned_config.s4_enabled,
            s5_enabled=cloned_config.s5_enabled,
            s6_enabled=cloned_config.s6_enabled,
            s7_enabled=cloned_config.s7_enabled,
            s8_enabled=cloned_config.s8_enabled,
            s9_enabled=cloned_config.s9_enabled,
            s10_enabled=cloned_config.s10_enabled,
            s11_enabled=cloned_config.s11_enabled,
            s12_enabled=cloned_config.s12_enabled,
            high_sensitivity_threshold=cloned_config.high_sensitivity_threshold,
            medium_sensitivity_threshold=cloned_config.medium_sensitivity_threshold,
            low_sensitivity_threshold=cloned_config.low_sensitivity_threshold,
            sensitivity_trigger_level=cloned_config.sensitivity_trigger_level
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to clone risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to clone risk config")

@router.get("/risk-configs/{config_id}/associations")
async def get_config_associations(
    config_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all associated configurations for a config set"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)

        associations = risk_service.get_config_associations(config_id, str(current_user.id))
        return associations
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get config associations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get config associations")

@router.get("/risk-types", response_model=RiskConfigResponse)
async def get_risk_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user default risk type configuration"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        config_dict = risk_service.get_risk_config_dict(str(current_user.id))
        return RiskConfigResponse(**config_dict)
    except Exception as e:
        logger.error(f"Failed to get risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get risk config")

@router.put("/risk-types", response_model=RiskConfigResponse)
async def update_risk_config(
    config_request: RiskConfigRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update user risk type configuration"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        config_data = config_request.dict()

        updated_config = risk_service.update_risk_config(str(current_user.id), config_data)
        if not updated_config:
            raise HTTPException(status_code=500, detail="Failed to update risk config")
        
        # Clear the user's cache, force reload
        await risk_config_cache.invalidate_user_cache(str(current_user.id))

        # Return updated configuration
        config_dict = risk_service.get_risk_config_dict(str(current_user.id))
        logger.info(f"Updated risk config for user {current_user.id}")
        
        return RiskConfigResponse(**config_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update risk config")

@router.get("/risk-types/enabled", response_model=Dict[str, bool])
async def get_enabled_risk_types(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user enabled risk type mapping"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        enabled_types = risk_service.get_enabled_risk_types(str(current_user.id))
        return enabled_types
    except Exception as e:
        logger.error(f"Failed to get enabled risk types: {e}")
        raise HTTPException(status_code=500, detail="Failed to get enabled risk types")

@router.post("/risk-types/reset")
async def reset_risk_config(
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset risk type configuration to default (all enabled)"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        default_config = {
            's1_enabled': True, 's2_enabled': True, 's3_enabled': True, 's4_enabled': True,
            's5_enabled': True, 's6_enabled': True, 's7_enabled': True, 's8_enabled': True,
            's9_enabled': True, 's10_enabled': True, 's11_enabled': True, 's12_enabled': True
        }

        updated_config = risk_service.update_risk_config(str(current_user.id), default_config)
        if not updated_config:
            raise HTTPException(status_code=500, detail="Failed to reset risk config")

        # Clear the user's cache
        await risk_config_cache.invalidate_user_cache(str(current_user.id))

        logger.info(f"Reset risk config to default for user {current_user.id}")
        return {"message": "Risk config has been reset to default"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset risk config: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset risk config")

@router.get("/sensitivity-thresholds", response_model=SensitivityThresholdResponse)
async def get_sensitivity_thresholds(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user sensitivity threshold configuration"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        config_dict = risk_service.get_sensitivity_threshold_dict(str(current_user.id))
        return SensitivityThresholdResponse(**config_dict)
    except Exception as e:
        logger.error(f"Failed to get sensitivity thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sensitivity thresholds")

@router.put("/sensitivity-thresholds", response_model=SensitivityThresholdResponse)
async def update_sensitivity_thresholds(
    threshold_request: SensitivityThresholdRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Update user sensitivity threshold configuration"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        threshold_data = threshold_request.dict()

        updated_config = risk_service.update_sensitivity_thresholds(str(current_user.id), threshold_data)
        if not updated_config:
            raise HTTPException(status_code=500, detail="Failed to update sensitivity thresholds")

        # Clear the user's sensitivity cache, force reload
        await risk_config_cache.invalidate_sensitivity_cache(str(current_user.id))

        # Return updated configuration
        config_dict = risk_service.get_sensitivity_threshold_dict(str(current_user.id))
        logger.info(f"Updated sensitivity thresholds for user {current_user.id}")

        return SensitivityThresholdResponse(**config_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update sensitivity thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to update sensitivity thresholds")

@router.post("/sensitivity-thresholds/reset")
async def reset_sensitivity_thresholds(
    request: Request,
    db: Session = Depends(get_db)
):
    """Reset sensitivity threshold configuration to default"""
    try:
        current_user = get_current_user_from_request(request, db)
        risk_service = RiskConfigService(db)
        default_config = {
            'high_sensitivity_threshold': 0.40,
            'medium_sensitivity_threshold': 0.60,
            'low_sensitivity_threshold': 0.95,
            'sensitivity_trigger_level': 'medium'
        }

        updated_config = risk_service.update_sensitivity_thresholds(str(current_user.id), default_config)
        if not updated_config:
            raise HTTPException(status_code=500, detail="Failed to reset sensitivity thresholds")

        # Clear the user's sensitivity cache
        await risk_config_cache.invalidate_sensitivity_cache(str(current_user.id))

        logger.info(f"Reset sensitivity thresholds to default for user {current_user.id}")
        return {"message": "Sensitivity thresholds have been reset to default"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset sensitivity thresholds: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset sensitivity thresholds")