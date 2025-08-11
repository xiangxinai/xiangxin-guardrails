from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from services.guardrail_service import GuardrailService
from models.requests import GuardrailRequest
from models.responses import GuardrailResponse
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Guardrails"])

@router.post("/guardrails", response_model=GuardrailResponse)
async def check_guardrails(
    request_data: GuardrailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    护栏检测API - 兼容OpenAI格式
    
    检测输入内容是否存在安全风险或合规问题。
    """
    try:
        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")
        
        # 创建护栏服务
        guardrail_service = GuardrailService(db)
        
        # 执行检测（将 user_id 传入以实现按用户隔离的黑白名单和代答）
        result = await guardrail_service.check_guardrails(
            request_data, 
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id
        )
        
        logger.info(f"Guardrail check completed: {result.id}, action: {result.suggest_action}")
        
        return result
        
    except Exception as e:
        logger.error(f"Guardrail API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/guardrails/health")
async def health_check():
    """护栏服务健康检查"""
    return {
        "status": "healthy",
        "service": "guardrails",
        "timestamp": "2025-01-01T00:00:00Z"
    }

@router.get("/guardrails/models")
async def list_models():
    """列出可用的模型"""
    return {
        "object": "list",
        "data": [
            {
                "id": "Xiangxin-Guardrails-Text",
                "object": "model",
                "created": 1640995200,
                "owned_by": "xiangxinai",
                "permission": [],
                "root": "Xiangxin-Guardrails-Text",
                "parent": None,
            }
        ]
    }