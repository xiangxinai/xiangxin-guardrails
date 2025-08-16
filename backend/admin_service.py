#!/usr/bin/env python3
"""
管理服务 - 低并发管理平台API
专门处理 /api/v1/* 管理界面请求，优化资源使用
"""
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
import os
import uuid
from pathlib import Path

from config import settings
from database.connection import init_db, create_admin_engine
from routers import dashboard, config_api, results, auth, user, sync, admin, online_test, test_models
from services.data_sync_service import data_sync_service
from utils.logger import setup_logger
from services.admin_service import admin_service

# 设置安全验证
security = HTTPBearer()

class AuthContextMiddleware(BaseHTTPMiddleware):
    """认证上下文中间件 - 管理服务版本（完整版）"""
    
    async def dispatch(self, request: Request, call_next):
        # 处理管理API路由
        if request.url.path.startswith('/api/v1/'):
            auth_header = request.headers.get('authorization')
            switch_session = request.headers.get('x-switch-session')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    auth_context = await self._get_auth_context(token, switch_session)
                    request.state.auth_context = auth_context
                except:
                    request.state.auth_context = None
            else:
                request.state.auth_context = None
        
        response = await call_next(request)
        return response
    
    async def _get_auth_context(self, token: str, switch_session: str = None):
        """获取认证上下文（完整版，支持用户切换）"""
        from utils.auth_cache import auth_cache
        
        # 生成缓存键
        cache_key = f"{token}:{switch_session or ''}"
        
        # 检查缓存
        cached_auth = auth_cache.get(cache_key)
        if cached_auth:
            return cached_auth
        
        from database.connection import get_admin_db_session
        from database.models import User
        from utils.user import get_user_by_api_key
        from utils.auth import verify_token
        
        db = get_admin_db_session()
        try:
            auth_context = None
            
            # JWT验证
            try:
                user_data = verify_token(token)
                role = user_data.get('role')
                
                if role == 'admin':
                    subject_email = user_data.get('username') or user_data.get('sub')
                    admin_user = db.query(User).filter(User.email == subject_email).first()
                    if admin_user:
                        auth_context = {
                            "type": "jwt_admin",
                            "data": {
                                "user_id": str(admin_user.id),
                                "email": admin_user.email,
                                "is_super_admin": admin_service.is_super_admin(admin_user)
                            }
                        }
                else:
                    raw_user_id = user_data.get('user_id') or user_data.get('sub')
                    user_uuid = None
                    if isinstance(raw_user_id, str):
                        try:
                            user_uuid = uuid.UUID(raw_user_id)
                        except ValueError:
                            pass
                    
                    user = db.query(User).filter(User.id == user_uuid).first() if user_uuid else None
                    if user:
                        # 检查用户切换
                        if switch_session and admin_service.is_super_admin(user):
                            switched_user = admin_service.get_switched_user(db, switch_session)
                            if switched_user:
                                auth_context = {
                                    "type": "jwt_switched",
                                    "data": {
                                        "user_id": str(switched_user.id),
                                        "email": switched_user.email,
                                        "original_admin_id": str(user.id),
                                        "original_admin_email": user.email,
                                        "switch_session": switch_session
                                    }
                                }
                        
                        if not auth_context:
                            auth_context = {
                                "type": "jwt", 
                                "data": {
                                    "user_id": str(user.id),
                                    "email": user.email,
                                    "is_super_admin": admin_service.is_super_admin(user)
                                }
                            }
            except:
                # API key验证
                user = get_user_by_api_key(db, token)
                if user:
                    # 检查用户切换
                    if switch_session and admin_service.is_super_admin(user):
                        switched_user = admin_service.get_switched_user(db, switch_session)
                        if switched_user:
                            auth_context = {
                                "type": "api_key_switched",
                                "data": {
                                    "user_id": str(switched_user.id),
                                    "email": switched_user.email,
                                    "api_key": switched_user.api_key,
                                    "original_admin_id": str(user.id),
                                    "original_admin_email": user.email,
                                    "switch_session": switch_session
                                }
                            }
                    
                    if not auth_context:
                        auth_context = {
                            "type": "api_key", 
                            "data": {
                                "user_id": str(user.id),
                                "email": user.email,
                                "api_key": user.api_key,
                                "is_super_admin": admin_service.is_super_admin(user)
                            }
                        }
            
            # 缓存认证结果
            if auth_context:
                auth_cache.set(cache_key, auth_context)
            
            return auth_context
            
        finally:
            db.close()

# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.log_dir, exist_ok=True)

    # 初始化数据库（管理服务需要完整初始化）
    await init_db(minimal=False)

    # 启动数据同步服务
    await data_sync_service.start()
    from services.cache_cleaner import cache_cleaner
    await cache_cleaner.start()
    
    # 根据配置决定是否启动日志导入数据库服务
    if settings.store_detection_results:
        from services.log_to_db_service import log_to_db_service
        await log_to_db_service.start()
        logger.info("Log to DB service started (STORE_DETECTION_RESULTS=true)")
    else:
        logger.info("Log to DB service disabled (STORE_DETECTION_RESULTS=false)")

    logger.info(f"{settings.app_name} Admin Service started")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info("Admin service optimized for management operations")
    
    try:
        yield
    finally:
        # 关闭阶段
        await data_sync_service.stop()
        from services.cache_cleaner import cache_cleaner
        await cache_cleaner.stop()
        if settings.store_detection_results:
            from services.log_to_db_service import log_to_db_service
            await log_to_db_service.stop()
        logger.info("Admin service shutdown completed")

app = FastAPI(
    title=f"{settings.app_name} - Admin Service",
    version=settings.app_version,
    description="象信AI安全护栏管理服务 - 管理平台API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 添加认证上下文中间件
app.add_middleware(AuthContextMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 设置日志
logger = setup_logger()

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": f"{settings.app_name} - Admin Service",
        "version": settings.app_version,
        "status": "running",
        "service_type": "admin",
        "support_email": settings.support_email,
        "workers": settings.admin_uvicorn_workers
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "service": "admin"
    }

# 用户认证函数（完整版）
async def verify_user_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
    request: Request = None,
):
    """验证用户认证（管理服务专用）"""
    # 使用中间件解析的认证上下文
    if request is not None:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if auth_ctx:
            return auth_ctx
    
    # 如果中间件未解析，进行完整验证
    token = credentials.credentials
    from database.connection import get_admin_db_session
    from database.models import User
    from utils.user import get_user_by_api_key
    from utils.auth import verify_token
    
    db = get_admin_db_session()
    try:
        # JWT验证
        try:
            user_data = verify_token(token)
            raw_user_id = user_data.get('user_id') or user_data.get('sub')
            if isinstance(raw_user_id, str):
                try:
                    user_uuid = uuid.UUID(raw_user_id)
                    user = db.query(User).filter(User.id == user_uuid).first()
                    if user and user.is_active:
                        return {
                            "type": "jwt", 
                            "data": {
                                "user_id": str(user.id),
                                "email": user.email,
                                "is_super_admin": admin_service.is_super_admin(user)
                            }
                        }
                except ValueError:
                    pass
        except:
            pass
        
        # API key验证
        user = get_user_by_api_key(db, token)
        if user:
            return {
                "type": "api_key", 
                "data": {
                    "user_id": str(user.id),
                    "email": user.email,
                    "api_key": user.api_key,
                    "is_super_admin": admin_service.is_super_admin(user)
                }
            }
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    finally:
        db.close()

# 注册管理路由
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(user.router, prefix="/api/v1/users")
app.include_router(dashboard.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(config_api.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(results.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(sync.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(admin.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(online_test.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(test_models.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Admin service exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Admin service internal error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "admin_service:app",
        host=settings.host,
        port=settings.admin_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.admin_uvicorn_workers if not settings.debug else 1
    )