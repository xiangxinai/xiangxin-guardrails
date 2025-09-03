#!/usr/bin/env python3
"""
反向代理服务 - OpenAI兼容的代理护栏服务
提供完整的OpenAI API兼容层，支持多模型配置和安全检测
"""
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from contextlib import asynccontextmanager
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
import uvicorn
import os
import uuid
from pathlib import Path
import asyncio

from config import settings
# 导入完整的代理服务实现
from routers import proxy_api
from services.async_logger import async_detection_logger
from utils.logger import setup_logger

# 设置安全验证
security = HTTPBearer()

# 导入并发控制中间件
from middleware.concurrent_limit_middleware import ConcurrentLimitMiddleware

class AuthContextMiddleware(BaseHTTPMiddleware):
    """认证上下文中间件 - 代理服务版本"""
    
    async def dispatch(self, request: Request, call_next):
        # 处理OpenAI兼容API路由
        if request.url.path.startswith('/v1/'):
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
        """获取认证上下文（代理服务专用 - 支持API key验证）"""
        from utils.auth_cache import auth_cache
        from utils.auth import verify_token
        
        # 检查缓存
        cached_auth = auth_cache.get(token)
        if cached_auth:
            return cached_auth
        
        auth_context = None
        
        try:
            # 首先尝试JWT验证
            user_data = verify_token(token)
            raw_user_id = user_data.get('user_id') or user_data.get('sub')
            
            if isinstance(raw_user_id, str):
                try:
                    user_uuid = uuid.UUID(raw_user_id)
                    auth_context = {
                        "type": "jwt", 
                        "data": {
                            "user_id": raw_user_id,
                            "email": user_data.get('email', 'unknown')
                        }
                    }
                except ValueError:
                    pass
        except:
            # JWT验证失败，尝试API key验证
            try:
                from database.connection import get_admin_db_session
                from utils.user import get_user_by_api_key
                
                db = get_admin_db_session()
                try:
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
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"API key verification failed: {e}")
        
        # 如果所有验证都失败，不创建匿名用户上下文
        # 这样会触发401错误，符合API的预期行为
        
        # 缓存认证结果
        if auth_context:
            auth_cache.set(token, auth_context)
        
        return auth_context

# 创建FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段
    os.makedirs(settings.data_dir, exist_ok=True)
    os.makedirs(settings.log_dir, exist_ok=True)
    os.makedirs(settings.detection_log_dir, exist_ok=True)

    # 代理服务不初始化数据库，专注高并发代理功能

    # 启动异步日志服务
    await async_detection_logger.start()

    logger.info(f"{settings.app_name} Proxy Service started")
    logger.info(f"Proxy API running on port {settings.proxy_port}")
    logger.info("OpenAI-compatible proxy service with guardrails protection")
    
    try:
        yield
    finally:
        # 关闭阶段
        await async_detection_logger.stop()
        from services.model_service import model_service
        await model_service.close()
        
        # 关闭HTTP客户端连接池
        from services.proxy_service import proxy_service
        await proxy_service.close()
        
        logger.info("Proxy service shutdown completed")

app = FastAPI(
    title=f"{settings.app_name} - Proxy Service",
    version=settings.app_version,
    description="象信AI安全护栏代理服务 - OpenAI兼容的反向代理",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 添加并发控制中间件（优先级最高，最后添加）
app.add_middleware(ConcurrentLimitMiddleware, service_type="proxy", max_concurrent=settings.proxy_max_concurrent_requests)

# 性能优化中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

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
        "name": f"{settings.app_name} - Proxy Service",
        "version": settings.app_version,
        "status": "running",
        "service_type": "proxy",
        "api_compatibility": "OpenAI v1",
        "supported_endpoints": [
            "POST /v1/chat/completions",
            "POST /v1/completions", 
            "GET /v1/models"
        ],
        "base_url": f"http://localhost:{settings.proxy_port}",
        "workers": settings.proxy_uvicorn_workers,
        "max_concurrent": settings.proxy_max_concurrent_requests
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "version": settings.app_version,
        "service": "proxy"
    }

# 用户认证函数
async def verify_user_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
    request: Request = None,
):
    """验证用户认证（代理服务专用）"""
    # 使用中间件解析的认证上下文
    if request is not None:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if auth_ctx:
            return auth_ctx
    
    raise HTTPException(status_code=401, detail="Invalid API key")

# 注册代理路由 - 路由中已包含/v1前缀，无需重复添加
app.include_router(proxy_api.router, dependencies=[Depends(verify_user_auth)])

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Proxy service exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"message": "Proxy service internal error", "type": "internal_error"}}
    )

if __name__ == "__main__":
    uvicorn.run(
        "proxy_service:app",
        host=settings.host,
        port=settings.proxy_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.proxy_uvicorn_workers if not settings.debug else 1
    )