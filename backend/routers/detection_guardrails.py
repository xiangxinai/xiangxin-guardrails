from fastapi import APIRouter, Depends, Request, HTTPException
from services.detection_guardrail_service import DetectionGuardrailService
from models.requests import GuardrailRequest
from models.responses import GuardrailResponse
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Detection Guardrails"])

@router.post("/guardrails", response_model=GuardrailResponse)
async def check_guardrails(
    request_data: GuardrailRequest,
    request: Request
):
    """
    护栏检测API - 检测服务专用版本（只写日志，不写数据库）
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
        
        # 创建检测服务（不需要数据库连接）
        guardrail_service = DetectionGuardrailService()
        
        # 执行检测（只写日志文件）
        result = await guardrail_service.check_guardrails(
            request_data, 
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id
        )
        
        logger.info(f"Detection completed: {result.id}, action: {result.suggest_action}")
        
        return result
        
    except Exception as e:
        logger.error(f"Detection API error: {e}")
        raise HTTPException(status_code=500, detail="Detection service error")

@router.get("/guardrails/health")
async def health_check():
    """检测服务健康检查"""
    return {
        "status": "healthy",
        "service": "detection_guardrails",
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