#!/usr/bin/env python3
"""
检测服务 - 高并发护栏检测API
专门处理 /v1/guardrails 检测请求，优化高并发性能
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
from database.connection import init_db, create_detection_engine
from routers import detection_guardrails
from services.async_logger import async_detection_logger
from utils.logger import setup_logger

# 设置安全验证
security = HTTPBearer()

class AuthContextMiddleware(BaseHTTPMiddleware):
    """认证上下文中间件 - 检测服务版本（简化版）"""
    
    async def dispatch(self, request: Request, call_next):
        # 只处理检测API路由
        if request.url.path.startswith('/v1/guardrails'):
            auth_header = request.headers.get('authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                try:
                    auth_context = await self._get_auth_context(token)
                    request.state.auth_context = auth_context
                except:
                    request.state.auth_context = None
            else:
                request.state.auth_context = None
        
        response = await call_next(request)
        return response
    
    async def _get_auth_context(self, token: str):
        """获取认证上下文（优化版）"""
        from utils.auth_cache import auth_cache
        
        # 检查缓存
        cached_auth = auth_cache.get(token)
        if cached_auth:
            return cached_auth
        
        # 缓存未命中，验证token
        from database.connection import get_detection_db_session
        from database.models import User
        from utils.user import get_user_by_api_key
        from utils.auth import verify_token
        
        db = get_detection_db_session()
        try:
            auth_context = None
            
            # JWT验证
            try:
                user_data = verify_token(token)
                raw_user_id = user_data.get('user_id') or user_data.get('sub')
                
                if isinstance(raw_user_id, str):
                    try:
                        user_uuid = uuid.UUID(raw_user_id)
                        user = db.query(User).filter(User.id == user_uuid).first()
                        if user:
                            auth_context = {
                                "type": "jwt", 
                                "data": {
                                    "user_id": str(user.id),
                                    "email": user.email
                                }
                            }
                    except ValueError:
                        pass
            except:
                # API key验证
                user = get_user_by_api_key(db, token)
                if user:
                    auth_context = {
                        "type": "api_key", 
                        "data": {
                            "user_id": str(user.id),
                            "email": user.email,
                            "api_key": user.api_key
                        }
                    }
            
            # 缓存认证结果
            if auth_context:
                auth_cache.set(token, auth_context)
            
            return auth_context
            
        finally:
            db.close()

# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.log_dir, exist_ok=True)
    os.makedirs(settings.detection_log_dir, exist_ok=True)

    # 初始化数据库（检测服务不需要完整初始化）
    await init_db(minimal=True)

    # 启动异步日志服务
    await async_detection_logger.start()

    logger.info(f"{settings.app_name} Detection Service started")
    logger.info(f"Detection API URL: {settings.guardrails_model_api_url}")
    logger.info("Detection service optimized for high concurrency")
    
    try:
        yield
    finally:
        # 关闭阶段
        await async_detection_logger.stop()
        from services.model_service import model_service
        await model_service.close()
        logger.info("Detection service shutdown completed")

app = FastAPI(
    title=f"{settings.app_name} - Detection Service",
    version=settings.app_version,
    description="象信AI安全护栏检测服务 - 高并发检测API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 添加限速中间件
from middleware.rate_limit_middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# 添加认证上下文中间件
app.add_middleware(AuthContextMiddleware)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 设置日志
logger = setup_logger()

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": f"{settings.app_name} - Detection Service",
        "version": settings.app_version,
        "status": "running",
        "service_type": "detection",
        "model_api_url": settings.guardrails_model_api_url,
        "workers": settings.detection_uvicorn_workers,
        "max_concurrent": settings.detection_max_concurrent_requests
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "service": "detection"
    }

# 用户认证函数（简化版）
async def verify_user_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
    request: Request = None,
):
    """验证用户认证（检测服务专用）"""
    # 使用中间件解析的认证上下文
    if request is not None:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if auth_ctx:
            return auth_ctx
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

# 注册检测路由（专用版本）
app.include_router(detection_guardrails.router, prefix="/v1", dependencies=[Depends(verify_user_auth)])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Detection service exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Detection service internal error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "detection_service:app",
        host=settings.host,
        port=settings.detection_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.detection_uvicorn_workers if not settings.debug else 1
    )