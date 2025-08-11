from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Optional, List
from sqlalchemy.orm import Session

from database.connection import get_db
import uuid
from database.models import User
from services.admin_service import admin_service
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Admin"])

def get_current_user(request: Request) -> User:
    """从请求上下文获取当前用户"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # 管理员接口：如果存在切换会话，则使用原始管理员身份
    data = auth_context['data']
    user_id = str(data.get('original_admin_id') or data.get('user_id'))
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user context")
    
    # 从数据库获取用户信息
    db = next(get_db())
    try:
        # 将字符串ID转换为UUID进行查询
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid user context")

        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    finally:
        db.close()

@router.get("/admin/users")
async def get_all_users(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取所有用户列表（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only super admin can access this endpoint")
        
        users = admin_service.get_all_users(db, current_user)
        
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

@router.post("/admin/switch-user/{target_user_id}")
async def switch_to_user(
    target_user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    超级管理员切换到指定用户视角
    """
    try:
        current_user = get_current_user(request)
        
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Only super admin can switch user view")
        
        session_token = admin_service.switch_to_user(db, current_user, target_user_id)
        
        # 获取目标用户信息
        try:
            target_user_uuid = uuid.UUID(target_user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")

        target_user = db.query(User).filter(User.id == target_user_uuid).first()
        
        return {
            "status": "success",
            "message": f"Switched to user {target_user.email}",
            "switch_session_token": session_token,
            "target_user": {
                "id": str(target_user.id),
                "email": target_user.email,
                "api_key": target_user.api_key
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
    获取当前用户切换状态信息
    """
    try:
        if not x_switch_session:
            return {
                "is_switched": False,
                "admin_user": None,
                "target_user": None
            }
        
        # 获取切换的用户
        switched_user = admin_service.get_switched_user(db, x_switch_session)
        if not switched_user:
            return {
                "is_switched": False,
                "admin_user": None,
                "target_user": None
            }
        
        # 获取原始管理员用户
        admin_user = admin_service.get_current_admin_from_switch(db, x_switch_session)
        
        return {
            "is_switched": True,
            "admin_user": {
                "id": str(admin_user.id),
                "email": admin_user.email
            } if admin_user else None,
            "target_user": {
                "id": str(switched_user.id),
                "email": switched_user.email,
                "api_key": switched_user.api_key
            }
        }
        
    except Exception as e:
        logger.error(f"Get current switch info error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# 添加限速管理API
from services.rate_limiter import RateLimitService
from pydantic import BaseModel

class SetRateLimitRequest(BaseModel):
    user_id: str
    requests_per_second: int  # 0表示无限制

class RateLimitResponse(BaseModel):
    user_id: str
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
    获取所有用户限速配置（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        rate_limit_service = RateLimitService(db)
        rate_limits = rate_limit_service.list_user_rate_limits(skip, limit)
        
        result = []
        for rate_limit in rate_limits:
            result.append(RateLimitResponse(
                user_id=str(rate_limit.user_id),
                email=rate_limit.user.email,
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
    设置用户限速（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        if request_data.requests_per_second < 0:
            raise HTTPException(status_code=400, detail="requests_per_second must be >= 0")
        
        rate_limit_service = RateLimitService(db)
        rate_limit_config = rate_limit_service.set_user_rate_limit(
            request_data.user_id,
            request_data.requests_per_second
        )
        
        return {
            "status": "success",
            "message": f"Rate limit set for user {request_data.user_id}: {request_data.requests_per_second} rps",
            "data": {
                "user_id": str(rate_limit_config.user_id),
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

@router.delete("/admin/rate-limits/{user_id}")
async def remove_user_rate_limit(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    移除用户限速（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        rate_limit_service = RateLimitService(db)
        rate_limit_service.disable_user_rate_limit(user_id)
        
        return {
            "status": "success",
            "message": f"Rate limit removed for user {user_id}"
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
    创建用户（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == request_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # 创建用户
        from utils.auth import get_password_hash, generate_api_key
        
        new_user = User(
            email=request_data.email,
            password_hash=get_password_hash(request_data.password),
            is_active=request_data.is_active,
            is_verified=request_data.is_verified,
            # 强制普通用户；仅 .env 用户是超级管理员
            is_super_admin=False,
            api_key=generate_api_key()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User created: {request_data.email}")
        return {
            "status": "success",
            "message": f"User {request_data.email} created successfully",
            "data": {
                "user_id": str(new_user.id),
                "email": new_user.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Create user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/admin/users/{user_id}")
async def update_user(
    user_id: str,
    request_data: UpdateUserRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    更新用户信息（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        # 获取要更新的用户
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 禁止修改任何用户的超级管理员属性（由 .env 控制），忽略该字段
        if request_data.is_super_admin is not None:
            logger.warning("Attempt to change is_super_admin ignored; controlled by .env only.")
            request_data.is_super_admin = None
        
        # 更新用户信息
        update_data = request_data.dict(exclude_unset=True)
        update_data.pop('is_super_admin', None)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        
        logger.info(f"User updated: {user.email}")
        return {
            "status": "success",
            "message": f"User {user.email} updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    删除用户（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        # 获取要删除的用户
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 不允许删除自己
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # 删除用户
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user.email}")
        return {
            "status": "success",
            "message": f"User {user.email} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/users/{user_id}/reset-api-key")
async def reset_user_api_key(
    user_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    重置用户API Key（仅超级管理员可访问）
    """
    try:
        current_user = get_current_user(request)
        if not admin_service.is_super_admin(current_user):
            raise HTTPException(status_code=403, detail="Access denied: Super admin required")
        
        # 获取用户
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        
        user = db.query(User).filter(User.id == user_uuid).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 重置API Key
        from utils.auth import generate_api_key
        user.api_key = generate_api_key()
        db.commit()
        
        logger.info(f"API key reset for user: {user.email}")
        return {
            "status": "success",
            "message": f"API key reset for user {user.email}",
            "data": {
                "new_api_key": user.api_key
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Reset API key error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")