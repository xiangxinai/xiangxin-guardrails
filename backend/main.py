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
from database.connection import init_db
from routers import guardrails, dashboard, config_api, results, auth, user, sync, admin, online_test, test_models, media, data_security, risk_config_api, proxy_management
from services.async_logger import async_detection_logger
from services.data_sync_service import data_sync_service
from utils.logger import setup_logger
from services.admin_service import admin_service

# 设置安全验证
security = HTTPBearer()

class AuthContextMiddleware(BaseHTTPMiddleware):
    """认证上下文中间件"""
    
    async def dispatch(self, request: Request, call_next):
        # 对需要认证的路由添加用户上下文
        if request.url.path.startswith('/v1/guardrails') or request.url.path.startswith('/api/v1/'):
            auth_header = request.headers.get('authorization')
            switch_session = request.headers.get('x-switch-session')  # 用户切换会话
            
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
        """获取认证上下文（带缓存优化）"""
        from utils.auth_cache import auth_cache
        
        # 生成缓存键（包含switch_session信息）
        cache_key = f"{token}:{switch_session or ''}"
        
        # 尝试从缓存获取
        cached_auth = auth_cache.get(cache_key)
        if cached_auth:
            return cached_auth
        
        # 缓存未命中，执行原有逻辑
        from database.connection import get_db_session
        from database.models import Tenant
        from utils.user import get_user_by_api_key
        from utils.auth import verify_token
        
        
        db = get_db_session()
        try:
            auth_context = None
            
            # 首先尝试JWT验证
            try:
                user_data = verify_token(token)
                role = user_data.get('role')
                # 管理员token：通过邮箱查找管理员用户
                if role == 'admin':
                    subject_email = user_data.get('username') or user_data.get('sub')
                    admin_user = db.query(Tenant).filter(Tenant.email == subject_email).first()
                    if admin_user:
                        auth_context = {
                            "type": "jwt_admin",
                            "data": {
                                "tenant_id": str(admin_user.id),
                                "email": admin_user.email,
                                "is_super_admin": admin_service.is_super_admin(admin_user)
                            }
                        }
                    else:
                        # 未在DB找到时，仍然标记为admin上下文但无user_id（后续依赖可再校验）
                        auth_context = {
                            "type": "jwt_admin",
                            "data": {
                                "tenant_id": None,
                                "email": subject_email,
                                "is_super_admin": True
                            }
                        }
                else:
                    # 普通用户：从token解析 tenant_id
                    raw_tenant_id = user_data.get('tenant_id') or user_data.get('sub')
                    tenant_uuid = None
                    if isinstance(raw_tenant_id, uuid.UUID):
                        tenant_uuid = raw_tenant_id
                    elif isinstance(raw_tenant_id, str):
                        try:
                            tenant_uuid = uuid.UUID(raw_tenant_id)
                        except ValueError:
                            tenant_uuid = None
                    user = db.query(Tenant).filter(Tenant.id == tenant_uuid).first() if tenant_uuid else None
                    if user:
                        # 检查是否有用户切换会话
                        if switch_session and admin_service.is_super_admin(user):
                            switched_user = admin_service.get_switched_user(db, switch_session)
                            if switched_user:
                                auth_context = {
                                    "type": "jwt_switched",
                                    "data": {
                                        "tenant_id": str(switched_user.id),
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
                                    "tenant_id": str(user.id),
                                    "email": user.email,
                                    # 仅依据 .env 判断超级管理员
                                    "is_super_admin": admin_service.is_super_admin(user)
                                }
                            }
                    else:
                        # 数据库未找到用户时，退化为基于token声明的上下文
                        auth_context = {
                            "type": "jwt",
                            "data": {
                                "tenant_id": str(raw_tenant_id) if raw_tenant_id else None,
                                "email": user_data.get('email'),
                                "is_super_admin": bool(user_data.get('is_super_admin', False))
                            }
                        }
            except:
                # JWT验证失败，尝试API key验证
                user = get_user_by_api_key(db, token)
                if user:
                    # 检查是否有用户切换会话
                    if switch_session and admin_service.is_super_admin(user):
                        switched_user = admin_service.get_switched_user(db, switch_session)
                        if switched_user:
                            auth_context = {
                                "type": "api_key_switched",
                                "data": {
                                    "tenant_id": str(switched_user.id),
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
                                "tenant_id": str(user.id),
                                "email": user.email,
                                "api_key": user.api_key,
                                # 仅依据 .env 判断超级管理员
                                "is_super_admin": admin_service.is_super_admin(user)
                            }
                        }
            
            # 如果认证成功，缓存结果
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
    os.makedirs(settings.detection_log_dir, exist_ok=True)

    # 初始化数据库
    await init_db()

    # 启动异步日志服务与后台任务
    await async_detection_logger.start()
    await data_sync_service.start()
    from services.cache_cleaner import cache_cleaner
    await cache_cleaner.start()

    logger.info(f"{settings.app_name} {settings.app_version} started")
    logger.info(f"Data directory: {settings.data_dir}")
    logger.info(f"Model API URL: {settings.guardrails_model_api_url}")
    logger.info("Async logging, data sync and cache cleaner services started")
    try:
        yield
    finally:
        # 关闭阶段
        await async_detection_logger.stop()
        await data_sync_service.stop()
        from services.cache_cleaner import cache_cleaner
        await cache_cleaner.stop()
        from services.model_service import model_service
        await model_service.close()
        logger.info("Application shutdown completed")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="象信AI安全护栏平台 - 为LLM应用提供全面的安全防护",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# 添加限速中间件 - 必须先添加（会后执行）
from middleware.rate_limit_middleware import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)

# 添加认证上下文中间件 - 后添加（会先执行）
app.add_middleware(AuthContextMiddleware)

# 配置CORS - 支持SSH端口映射
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 设置日志
logger = setup_logger()

# 生命周期已通过 lifespan 管理

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "model_api_url": settings.guardrails_model_api_url,
        "support_email": settings.support_email,
        "huggingface_model": settings.huggingface_model
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.app_version}

# 注册路由
# 认证和用户路由不需要API key验证
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(user.router, prefix="/api/v1/users")

# 其他路由需要JWT认证或API key验证
from routers.auth import get_current_admin

async def verify_user_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
    request: Request = None,
):
    """验证用户认证（JWT token或API key）"""
    from database.connection import get_db_session
    from database.models import Tenant
    from utils.user import get_user_by_api_key
    from utils.auth import verify_token
    
    # 若中间件已解析出认证上下文，则直接信任（避免重复解析差异带来的401）
    if request is not None:
        auth_ctx = getattr(request.state, 'auth_context', None)
        if auth_ctx:
            return auth_ctx

    token = credentials.credentials
    db = get_db_session()
    
    try:
        # 首先尝试JWT验证
        try:
            user_data = verify_token(token)
            role = user_data.get('role')
            if role == 'admin':
                subject_email = user_data.get('username') or user_data.get('sub')
                admin_user = db.query(Tenant).filter(Tenant.email == subject_email).first()
                if admin_user and admin_user.is_active:
                    ctx = {
                        "type": "jwt_admin",
                        "data": {
                            "tenant_id": str(admin_user.id),
                            "email": admin_user.email,
                            "is_super_admin": admin_service.is_super_admin(admin_user)
                        }
                    }
                    if request is not None:
                        try:
                            request.state.auth_context = ctx
                        except Exception:
                            pass
                    return ctx
            else:
                # 兼容旧token：优先 tenant_id，回退 sub
                raw_tenant_id = user_data.get('tenant_id') or user_data.get('sub')
                tenant_uuid = None
                if isinstance(raw_tenant_id, uuid.UUID):
                    tenant_uuid = raw_tenant_id
                elif isinstance(raw_tenant_id, str):
                    try:
                        tenant_uuid = uuid.UUID(raw_tenant_id)
                    except ValueError:
                        tenant_uuid = None

                user = db.query(Tenant).filter(Tenant.id == tenant_uuid).first() if tenant_uuid else None
                if user and user.is_active:
                    ctx = {
                        "type": "jwt", 
                        "data": {
                            "tenant_id": str(user.id),
                            "email": user.email,
                            # 仅依据 .env 判断超级管理员
                            "is_super_admin": admin_service.is_super_admin(user)
                        }
                    }
                    if request is not None:
                        try:
                            request.state.auth_context = ctx
                        except Exception:
                            pass
                    return ctx
                else:
                    # Fallback: 接受token声明（即使DB未能查询到），避免误判401
                    ctx = {
                        "type": "jwt",
                        "data": {
                            "tenant_id": str(raw_tenant_id) if raw_tenant_id else None,
                            "email": user_data.get('email'),
                            "is_super_admin": bool(user_data.get('is_super_admin', False))
                        }
                    }
                    if request is not None:
                        try:
                            request.state.auth_context = ctx
                        except Exception:
                            pass
                    return ctx
        except:
            pass
        
        # JWT验证失败，尝试API key验证
        user = get_user_by_api_key(db, token)
        # 允许使用有效的 API Key 直接访问（不强制邮箱激活）
        if user:
            ctx = {
                "type": "api_key", 
                "data": {
                    "tenant_id": str(user.id),
                    "email": user.email,
                    "api_key": user.api_key,
                    # 仅依据 .env 判断超级管理员
                    "is_super_admin": admin_service.is_super_admin(user)
                }
            }
            if request is not None:
                try:
                    request.state.auth_context = ctx
                except Exception:
                    pass
            return ctx
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    finally:
        db.close()

app.include_router(guardrails.router, prefix="/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(dashboard.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(config_api.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(risk_config_api.router, dependencies=[Depends(verify_user_auth)])  # risk_config_api已在路由内定义prefix
app.include_router(proxy_management.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(results.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(sync.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(admin.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(online_test.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(test_models.router, prefix="/api/v1", dependencies=[Depends(verify_user_auth)])
app.include_router(data_security.router, dependencies=[Depends(verify_user_auth)])  # data_security已在路由内定义prefix
app.include_router(media.router, prefix="/api/v1")  # media路由的认证在各个接口中单独控制

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.admin_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.admin_uvicorn_workers if not settings.debug else 1
    )
