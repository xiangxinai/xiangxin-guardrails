from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from database.connection import get_db_session
from services.rate_limiter import rate_limiter
from utils.logger import setup_logger

logger = setup_logger()

class RateLimitMiddleware(BaseHTTPMiddleware):
    """限速中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.protected_paths = ["/v1/guardrails"]  # 需要限速的路径

    async def dispatch(self, request: Request, call_next):
        # 检查是否需要限速
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)

        # 获取租户ID
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            # 没有认证信息，跳过限速（让后续认证中间件处理）
            return await call_next(request)

        tenant_id = auth_context['data'].get('tenant_id')  
        if not tenant_id:
            return await call_next(request)

        # 检查限速
        db = get_db_session()
        try:
            if not await rate_limiter.is_allowed(str(tenant_id), db):
                logger.warning(f"Rate limit exceeded for tenant {tenant_id} on {request.url.path}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "message": "Rate limit exceeded. Too many requests.",
                            "type": "rate_limit_exceeded", 
                            "code": 429
                        }
                    },
                    headers={"Retry-After": "1"}
                )
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # 限速检查失败时允许请求通过，避免影响服务
        finally:
            db.close()
        
        return await call_next(request)