from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from services.guardrail_service import GuardrailService
from services.ban_policy_service import BanPolicyService
from models.requests import GuardrailRequest, InputGuardrailRequest, OutputGuardrailRequest, Message
from models.responses import GuardrailResponse
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Guardrails"])


async def check_user_ban_status(tenant_id: str, user_id: str):
    """检查用户封禁状态，如果被封禁则抛出异常"""
    if not user_id:
        return None

    ban_record = await BanPolicyService.check_user_banned(tenant_id, user_id)
    if ban_record:
        ban_until = ban_record['ban_until'].isoformat() if ban_record['ban_until'] else ''
        raise HTTPException(
            status_code=403,
            detail={
                "error": "用户已被封禁",
                "user_id": user_id,
                "ban_until": ban_until,
                "reason": ban_record.get('reason', '触发封禁策略')
            }
        )
    return None

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

        # 获取租户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        tenant_id = None
        if auth_context:
            tenant_id = str(auth_context['data'].get('tenant_id') or auth_context['data'].get('tenant_id'))

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant ID not found in auth context")

        # 获取用户ID
        user_id = None
        if request_data.extra_body:
            user_id = request_data.extra_body.get('xxai_app_user_id')

        # 如果没有 user_id，使用 tenant_id 作为 fallback
        if not user_id:
            user_id = tenant_id

        # 检查用户是否被封禁
        await check_user_ban_status(tenant_id, user_id)

        # 创建护栏服务
        guardrail_service = GuardrailService(db)

        # 执行检测（将 tenant_id 传入以实现按租户隔离的黑白名单和代答）
        result = await guardrail_service.check_guardrails(
            request_data,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id
        )

        # 检查并应用封禁策略
        logger.info(f"Checking ban policy: overall_risk_level={result.overall_risk_level}, user_id={user_id}, tenant_id={tenant_id}")
        if result.overall_risk_level in ['中风险', '高风险']:
            logger.info(f"Ban policy check triggered for user_id={user_id}, risk_level={result.overall_risk_level}")
            try:
                await BanPolicyService.check_and_apply_ban_policy(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    risk_level=result.overall_risk_level,
                    detection_result_id=result.id
                )
                logger.info(f"Ban policy check completed for user_id={user_id}")
            except Exception as e:
                logger.error(f"Ban policy check failed for user_id={user_id}: {e}", exc_info=True)
        else:
            logger.info(f"Ban policy check skipped: risk_level={result.overall_risk_level}")

        logger.info(f"Guardrail check completed: {result.id}, action: {result.suggest_action}, user_id: {user_id}")

        return result

    except HTTPException:
        raise
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

@router.post("/guardrails/input", response_model=GuardrailResponse)
async def check_input_guardrails(
    request_data: InputGuardrailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    输入检测API - 适用于dify/coze等智能体平台插件

    检测用户输入是否存在安全风险或合规问题。
    将输入转换为messages格式进行检测。
    """
    try:
        # 将输入转换为messages格式
        messages = [Message(role="user", content=request_data.input)]

        # 构造标准的GuardrailRequest
        guardrail_request = GuardrailRequest(
            model=request_data.model,
            messages=messages
        )

        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 获取租户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        tenant_id = None
        if auth_context:
            tenant_id = str(auth_context['data'].get('tenant_id') or auth_context['data'].get('tenant_id'))

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant ID not found in auth context")

        # 获取用户ID
        user_id = request_data.xxai_app_user_id if request_data.xxai_app_user_id else tenant_id

        # 检查用户是否被封禁
        await check_user_ban_status(tenant_id, user_id)

        # 创建护栏服务
        guardrail_service = GuardrailService(db)

        # 执行检测
        result = await guardrail_service.check_guardrails(
            guardrail_request,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id
        )

        # 检查并应用封禁策略
        logger.info(f"Checking ban policy: overall_risk_level={result.overall_risk_level}, user_id={user_id}, tenant_id={tenant_id}")
        if result.overall_risk_level in ['中风险', '高风险']:
            logger.info(f"Ban policy check triggered for user_id={user_id}, risk_level={result.overall_risk_level}")
            try:
                await BanPolicyService.check_and_apply_ban_policy(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    risk_level=result.overall_risk_level,
                    detection_result_id=result.id
                )
                logger.info(f"Ban policy check completed for user_id={user_id}")
            except Exception as e:
                logger.error(f"Ban policy check failed for user_id={user_id}: {e}", exc_info=True)
        else:
            logger.info(f"Ban policy check skipped: risk_level={result.overall_risk_level}")

        logger.info(f"Input guardrail check completed: {result.id}, action: {result.suggest_action}, user_id: {user_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Input guardrail API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/guardrails/output", response_model=GuardrailResponse)
async def check_output_guardrails(
    request_data: OutputGuardrailRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    输出检测API - 适用于dify/coze等智能体平台插件

    检测用户输入和模型输出是否存在安全风险或合规问题。
    将输入输出转换为messages格式进行检测。
    """
    try:
        # 将输入输出转换为messages格式
        messages = [
            Message(role="user", content=request_data.input),
            Message(role="assistant", content=request_data.output)
        ]

        # 构造标准的GuardrailRequest
        guardrail_request = GuardrailRequest(
            model="Xiangxin-Guardrails-Text",
            messages=messages
        )

        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 获取租户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        tenant_id = None
        if auth_context:
            tenant_id = str(auth_context['data'].get('tenant_id') or auth_context['data'].get('tenant_id'))

        if not tenant_id:
            raise HTTPException(status_code=401, detail="Tenant ID not found in auth context")

        # 获取用户ID
        user_id = request_data.xxai_app_user_id if request_data.xxai_app_user_id else tenant_id

        # 检查用户是否被封禁
        await check_user_ban_status(tenant_id, user_id)

        # 创建护栏服务
        guardrail_service = GuardrailService(db)

        # 执行检测
        result = await guardrail_service.check_guardrails(
            guardrail_request,
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id
        )

        # 检查并应用封禁策略
        if result.overall_risk_level in ['中风险', '高风险']:
            await BanPolicyService.check_and_apply_ban_policy(
                tenant_id=tenant_id,
                user_id=user_id,
                risk_level=result.overall_risk_level,
                detection_result_id=result.id
            )

        logger.info(f"Output guardrail check completed: {result.id}, action: {result.suggest_action}, user_id: {user_id}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Output guardrail API error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")