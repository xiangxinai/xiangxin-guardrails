from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.connection import get_db
import uuid
from database.models import Tenant, DetectionResult
from services.admin_service import admin_service
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Admin"])

def get_current_user(request: Request) -> Tenant:
    """从请求上下文获取当前租户"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # 管理员接口：如果存在切换会话，则使用原始管理员身份
    data = auth_context['data']
    tenant_id = str(data.get('original_admin_id') or data.get('tenant_id') or data.get('tenant_id'))
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid tenant context")

    # 从数据库获取租户信息
    db = next(get_db())
    try:
        # 将字符串ID转换为UUID进行查询
        try:
            tenant_uuid = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid tenant context")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
        if not tenant:
            raise HTTPException(status_code=401, detail="Tenant not found")
        return tenant
    finally:
        db.close()

@router.get("/admin/stats")
async def get_admin_stats(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取管理员统计信息（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)

        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Only super admin can access this endpoint")

        # 获取租户总数
        total_users = db.query(Tenant).count()

        # 获取所有租户的检测总次数
        total_detections = db.query(DetectionResult).count()

        # 获取每个租户的检测次数
        user_detection_counts = db.query(
            Tenant.id.label('tenant_id'),
            Tenant.email.label('email'),
            func.count(DetectionResult.id).label('detection_count')
        ).outerjoin(DetectionResult, Tenant.id == DetectionResult.tenant_id).group_by(Tenant.id, Tenant.email).all()
        
        return {
            "status": "success",
            "data": {
                "total_users": total_users,
                "total_detections": total_detections,
                "user_detection_counts": [
                    {
                        "tenant_id": str(row.tenant_id),
                        "email": row.email,
                        "detection_count": row.detection_count
                    }
                    for row in user_detection_counts
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get admin stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/users")
async def get_all_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取所有租户列表（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)

        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Only super admin can access this endpoint")

        users = admin_service.get_all_users(db, current_tenant)
        
        return {
            "status": "success",
            "users": users,
            "total": len(users)
        }
        
    except HTTPException:
        # 透传显式的HTTP错误（例如403）
        raise
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Get all users error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/switch-user/{target_tenant_id}")
async def switch_to_user(
    target_tenant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    超级管理员切换到指定租户视角
    """
    try:
        current_tenant = get_current_user(request)

        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Only super admin can switch user view")

        session_token = admin_service.switch_to_user(db, current_tenant, target_tenant_id)

        # 获取目标租户信息
        try:
            target_tenant_uuid = uuid.UUID(target_tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID format")

        target_tenant = db.query(Tenant).filter(Tenant.id == target_tenant_uuid).first()
        
        return {
            "status": "success",
            "message": f"Switched to tenant {target_tenant.email}",
            "switch_session_token": session_token,
            "target_user": {
                "id": str(target_tenant.id),
                "email": target_tenant.email,
                "api_key": target_tenant.api_key
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Switch user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/exit-switch")
async def exit_user_switch(
    x_switch_session: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    退出用户切换，回到管理员视角
    """
    try:
        if not x_switch_session:
            raise HTTPException(status_code=400, detail="No switch session found")
        
        success = admin_service.exit_user_switch(db, x_switch_session)
        
        if not success:
            raise HTTPException(status_code=404, detail="Switch session not found or already expired")
        
        return {
            "status": "success",
            "message": "Exited user switch view"
        }
        
    except Exception as e:
        logger.error(f"Exit user switch error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/admin/current-switch")
async def get_current_switch_info(
    x_switch_session: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    获取当前租户切换状态信息
    """
    try:
        if not x_switch_session:
            return {
                "is_switched": False,
                "admin_user": None,
                "target_user": None
            }

        # 获取切换的租户
        switched_tenant = admin_service.get_switched_user(db, x_switch_session)
        if not switched_tenant:
            return {
                "is_switched": False,
                "admin_user": None,
                "target_user": None
            }

        # 获取原始管理员租户
        admin_tenant = admin_service.get_current_admin_from_switch(db, x_switch_session)

        return {
            "is_switched": True,
            "admin_user": {
                "id": str(admin_tenant.id),
                "email": admin_tenant.email
            } if admin_tenant else None,
            "target_user": {
                "id": str(switched_tenant.id),
                "email": switched_tenant.email,
                "api_key": switched_tenant.api_key
            }
        }
        
    except Exception as e:
        logger.error(f"Get current switch info error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 添加限速管理API
from services.rate_limiter import RateLimitService
from pydantic import BaseModel

class SetRateLimitRequest(BaseModel):
    tenant_id: str
    requests_per_second: int  # 0表示无限制

class RateLimitResponse(BaseModel):
    tenant_id: str
    email: str
    requests_per_second: int
    is_active: bool

@router.get("/admin/rate-limits")
async def get_all_rate_limits(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取所有租户限速配置（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        rate_limit_service = RateLimitService(db)
        rate_limits = rate_limit_service.list_user_rate_limits(skip, limit)
        
        result = []
        for rate_limit in rate_limits:
            result.append(RateLimitResponse(
                tenant_id=str(rate_limit.tenant_id),
                email=rate_limit.tenant.email,
                requests_per_second=rate_limit.requests_per_second,
                is_active=rate_limit.is_active
            ))
        
        return {
            "status": "success",
            "data": result,
            "total": len(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get rate limits error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/rate-limits")
async def set_user_rate_limit(
    request_data: SetRateLimitRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    设置租户限速（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        if request_data.requests_per_second < 0:
            raise HTTPException(status_code=400, detail="requests_per_second must be >= 0")
        
        rate_limit_service = RateLimitService(db)
        rate_limit_config = rate_limit_service.set_user_rate_limit(
            request_data.tenant_id,
            request_data.requests_per_second
        )
        
        return {
            "status": "success",
            "message": f"Rate limit set for user {request_data.tenant_id}: {request_data.requests_per_second} rps",
            "data": {
                "tenant_id": str(rate_limit_config.tenant_id),  # API返回字段保持user_id以兼容
                "requests_per_second": rate_limit_config.requests_per_second,
                "is_active": rate_limit_config.is_active
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Set rate limit error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/admin/rate-limits/{tenant_id}")
async def remove_user_rate_limit(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    移除租户限速（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        rate_limit_service = RateLimitService(db)
        rate_limit_service.disable_user_rate_limit(tenant_id)
        
        return {
            "status": "success",
            "message": f"Rate limit removed for user {tenant_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Remove rate limit error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 用户管理API
from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    is_active: bool = True
    is_verified: bool = False
    # 兼容字段，后端忽略该值；唯一超级管理员由 .env 指定
    is_super_admin: bool = False

class UpdateUserRequest(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_super_admin: Optional[bool] = None

@router.post("/admin/create-user")
async def create_user(
    request_data: CreateUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    创建租户（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")

        # 检查邮箱是否已存在
        existing_tenant = db.query(Tenant).filter(Tenant.email == request_data.email).first()
        if existing_tenant:
            raise HTTPException(status_code=400, detail="Email already exists")

        # 创建租户
        from utils.auth import get_password_hash, generate_api_key

        new_tenant = Tenant(
            email=request_data.email,
            password_hash=get_password_hash(request_data.password),
            is_active=request_data.is_active,
            is_verified=request_data.is_verified,
            # 强制普通租户；仅 .env 租户是超级管理员
            is_super_admin=False,
            api_key=generate_api_key()
        )

        db.add(new_tenant)
        db.commit()
        db.refresh(new_tenant)

        logger.info(f"Tenant created: {request_data.email}")
        return {
            "status": "success",
            "message": f"Tenant {request_data.email} created successfully",
            "data": {
                "tenant_id": str(new_tenant.id),
                "email": new_tenant.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/admin/users/{tenant_id}")
async def update_user(
    tenant_id: str,
    request_data: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    更新租户信息（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")

        # 获取要更新的租户
        try:
            tenant_uuid = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID format")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # 禁止修改任何租户的超级管理员属性（由 .env 控制），忽略该字段
        if request_data.is_super_admin is not None:
            logger.warning("Attempt to change is_super_admin ignored; controlled by .env only.")
            request_data.is_super_admin = None

        # 更新租户信息
        update_data = request_data.dict(exclude_unset=True)
        update_data.pop('is_super_admin', None)
        for field, value in update_data.items():
            setattr(tenant, field, value)

        db.commit()

        logger.info(f"Tenant updated: {tenant.email}")
        return {
            "status": "success",
            "message": f"Tenant {tenant.email} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/admin/users/{tenant_id}")
async def delete_user(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    删除租户（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")

        # 获取要删除的租户
        try:
            tenant_uuid = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID format")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # 不允许删除自己
        if tenant.id == current_tenant.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")

        # 删除租户
        db.delete(tenant)
        db.commit()

        logger.info(f"Tenant deleted: {tenant.email}")
        return {
            "status": "success",
            "message": f"Tenant {tenant.email} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/users/{tenant_id}/reset-api-key")
async def reset_user_api_key(
    tenant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    重置租户API Key（仅超级管理员可访问）
    """
    try:
        current_tenant = get_current_user(request)
        if not admin_service.is_super_admin(current_tenant):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")

        # 获取租户
        try:
            tenant_uuid = uuid.UUID(tenant_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid tenant ID format")

        tenant = db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # 重置API Key
        from utils.auth import generate_api_key
        tenant.api_key = generate_api_key()
        db.commit()

        logger.info(f"API key reset for tenant: {tenant.email}")
        return {
            "status": "success",
            "message": f"API key reset for tenant {tenant.email}",
            "data": {
                "new_api_key": tenant.api_key
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Reset API key error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")