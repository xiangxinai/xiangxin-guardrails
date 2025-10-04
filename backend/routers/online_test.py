from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Dict, Any, Optional
import asyncio
import uuid
import httpx
from sqlalchemy.orm import Session
from database.connection import get_db, get_admin_db_session
from services.guardrail_service import GuardrailService
from models.requests import GuardrailRequest, Message
from utils.logger import setup_logger
from openai import AsyncOpenAI
from config import settings
from services.proxy_service import proxy_service

logger = setup_logger()
router = APIRouter(tags=["Online Test"])

class ModelConfig(BaseModel):
    id: str
    name: str
    base_url: str
    api_key: str
    model_name: str
    enabled: bool = True
    # 允许以 model_ 开头的字段名
    model_config = ConfigDict(protected_namespaces=())

class ModelIdRequest(BaseModel):
    id: int
    enabled: bool = True

class OnlineTestRequest(BaseModel):
    content: str
    input_type: str  # 'question' or 'qa_pair'
    models: Optional[List[ModelIdRequest]] = []
    images: Optional[List[str]] = []  # base64编码的图片数据列表

class ModelResponse(BaseModel):
    content: Optional[str] = None
    error: Optional[str] = None

class OnlineTestResponse(BaseModel):
    guardrail: Dict[str, Any]
    models: Dict[str, ModelResponse] = {}
    original_responses: Dict[str, ModelResponse] = {}

class OnlineTestModelInfo(BaseModel):
    id: str
    config_name: str
    api_base_url: str
    model_name: str
    enabled: bool
    selected: bool = False  # 是否被选中用于在线测试
    
    # 允许以 model_ 开头的字段名
    model_config = ConfigDict(protected_namespaces=())

class UpdateModelSelectionRequest(BaseModel):
    model_selections: List[Dict[str, Any]]  # [{"id": "model_id", "selected": True/False}]
    
    # 允许以 model_ 开头的字段名
    model_config = ConfigDict(protected_namespaces=())

@router.get("/test/models", response_model=List[OnlineTestModelInfo])
async def get_online_test_models(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取在线测试可用的代理模型列表"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")
        
        # 获取用户UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="无效的用户ID格式")
        
        # 获取用户的代理模型配置
        from database.models import ProxyModelConfig, OnlineTestModelSelection
        proxy_models = db.query(ProxyModelConfig).filter(
            ProxyModelConfig.user_id == user_uuid,
            ProxyModelConfig.enabled == True
        ).all()
        
        # 获取用户的在线测试模型选择
        selections = db.query(OnlineTestModelSelection).filter(
            OnlineTestModelSelection.user_id == user_uuid
        ).all()
        
        # 创建选择映射
        selection_map = {str(sel.proxy_model_id): sel.selected for sel in selections}
        
        # 构造返回数据
        result = []
        for model in proxy_models:
            model_info = OnlineTestModelInfo(
                id=str(model.id),
                config_name=model.config_name,
                api_base_url=model.api_base_url,
                model_name=model.model_name,
                enabled=model.enabled,
                selected=selection_map.get(str(model.id), False)
            )
            result.append(model_info)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get online test models error: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.post("/test/models/selection")
async def update_model_selection(
    request_data: UpdateModelSelectionRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新在线测试模型选择"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")
        
        # 获取用户UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="无效的用户ID格式")
        
        from database.models import OnlineTestModelSelection, ProxyModelConfig
        
        # 更新每个模型的选择状态
        for selection in request_data.model_selections:
            model_id = selection['id']
            selected = selection['selected']
            
            # 验证模型ID格式
            try:
                proxy_model_uuid = uuid.UUID(model_id)
            except ValueError:
                logger.error(f"Invalid model_id format: {model_id}")
                continue
            
            # 验证模型是否属于该用户
            proxy_model = db.query(ProxyModelConfig).filter(
                ProxyModelConfig.id == proxy_model_uuid,
                ProxyModelConfig.user_id == user_uuid
            ).first()
            
            if not proxy_model:
                continue  # 跳过不属于该用户的模型
            
            # 查找现有的选择记录
            existing_selection = db.query(OnlineTestModelSelection).filter(
                OnlineTestModelSelection.user_id == user_uuid,
                OnlineTestModelSelection.proxy_model_id == proxy_model_uuid
            ).first()
            
            if existing_selection:
                # 更新现有记录
                existing_selection.selected = selected
            else:
                # 创建新记录
                new_selection = OnlineTestModelSelection(
                    user_id=user_uuid,
                    proxy_model_id=proxy_model_uuid,
                    selected=selected
                )
                db.add(new_selection)
        
        db.commit()
        return {"message": "模型选择已更新"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update model selection error: {e}")
        raise HTTPException(status_code=500, detail=f"更新模型选择失败: {str(e)}")

@router.post("/test/online", response_model=OnlineTestResponse)
async def online_test(
    request_data: OnlineTestRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    在线测试API
    
    支持测试护栏检测能力，同时可以测试被保护模型的响应
    """
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context:
            user_id = str(auth_context['data'].get('user_id'))
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in auth context")
        
        # 构造消息格式
        messages = []
        if request_data.input_type == 'question':
            # 检查是否有图片数据
            if request_data.images and len(request_data.images) > 0:
                # 多模态消息格式
                content = []
                # 添加文本内容（如果有）
                if request_data.content.strip():
                    content.append({"type": "text", "text": request_data.content})
                # 添加图片内容
                for image_base64 in request_data.images:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": image_base64}
                    })
                messages = [{"role": "user", "content": content}]
            else:
                # 纯文本消息格式
                messages = [{"role": "user", "content": request_data.content}]
        else:  # qa_pair
            # 解析问答对
            lines = request_data.content.split('\n')
            question = None
            answer = None
            
            for line in lines:
                if line.strip().startswith('Q:'):
                    question = line[2:].strip()
                elif line.strip().startswith('A:'):
                    answer = line[2:].strip()
            
            if not question or not answer:
                raise HTTPException(status_code=400, detail="问答对格式错误，请使用 Q: 问题\\nA: 回答 的格式")
            
            messages = [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer}
            ]
        
        # 获取用户API key
        user_api_key = None
        if auth_context and auth_context.get('type') in ['api_key', 'api_key_switched']:
            user_api_key = auth_context['data'].get('api_key')
        
        # 获取用户UUID
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            logger.error(f"Invalid user_id format: {user_id}")
            raise HTTPException(status_code=400, detail="无效的用户ID格式")
        
        if not user_api_key:
            # 如果是JWT登录，需要从数据库获取用户的API key
            from database.models import User
            user = db.query(User).filter(User.id == user_uuid).first()
            if user:
                user_api_key = user.api_key
        
        if not user_api_key:
            raise HTTPException(status_code=400, detail="用户API key未找到")
        
        # 使用用户API key调用护栏API
        has_images = request_data.images and len(request_data.images) > 0
        guardrail_dict = await call_guardrail_api(user_api_key, messages, user_uuid, db, has_images)
        
        # 如果是问题类型，获取用户选择的代理模型进行测试
        model_results = {}
        original_responses = {}
        if request_data.input_type == 'question':
            # 从数据库获取用户选择的代理模型配置
            from database.models import ProxyModelConfig, OnlineTestModelSelection
            
            # 如果请求中指定了模型，使用指定的模型，否则使用用户之前选择的模型
            if request_data.models:
                # 兼容原有的请求格式，但现在使用proxy_model_configs
                enabled_model_ids = [m.id for m in request_data.models if m.enabled]
                logger.info(f"Testing specific models: {enabled_model_ids}")
                
                db_models = db.query(ProxyModelConfig).filter(
                    ProxyModelConfig.id.in_(enabled_model_ids),
                    ProxyModelConfig.user_id == user_uuid,
                    ProxyModelConfig.enabled == True
                ).all()
            else:
                # 获取用户选择的代理模型
                selected_models_query = db.query(ProxyModelConfig).join(
                    OnlineTestModelSelection,
                    ProxyModelConfig.id == OnlineTestModelSelection.proxy_model_id
                ).filter(
                    ProxyModelConfig.user_id == user_uuid,
                    ProxyModelConfig.enabled == True,
                    OnlineTestModelSelection.selected == True
                )
                
                db_models = selected_models_query.all()
            
            logger.info(f"Found {len(db_models)} models in database")
            
            # 并行调用所有启用的模型获取原始响应（不经过护栏）
            original_tasks = []
            for db_model in db_models:
                # 解密API key
                try:
                    decrypted_api_key = proxy_service._decrypt_api_key(db_model.api_key_encrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt API key for model {db_model.id}: {e}")
                    continue
                
                # 创建ModelConfig对象
                model_config = ModelConfig(
                    id=str(db_model.id),
                    name=db_model.config_name,
                    base_url=db_model.api_base_url,
                    api_key=decrypted_api_key,
                    model_name=db_model.model_name,
                    enabled=db_model.enabled
                )
                # 直接调用模型获取原始响应
                original_task = test_model_api(model_config, messages)
                original_tasks.append((str(db_model.id), original_task))
            
            # 等待所有模型的原始响应
            if original_tasks:
                original_results = await asyncio.gather(
                    *[task for _, task in original_tasks], 
                    return_exceptions=True
                )
                
                for i, (model_id, _) in enumerate(original_tasks):
                    result = original_results[i]
                    if isinstance(result, Exception):
                        original_responses[model_id] = ModelResponse(
                            content=None,
                            error=f"请求失败: {str(result)}"
                        )
                    else:
                        original_responses[model_id] = result
            
            # 基于护栏结果生成护栏保护响应
            for model_id in original_responses:
                if (guardrail_dict.get('suggest_action', '') == '通过' or 
                    guardrail_dict.get('overall_risk_level', '') in ['无风险', 'safe']):
                    # 如果护栏通过，护栏保护响应直接使用原始响应
                    model_results[model_id] = original_responses[model_id]
                else:
                    # 如果护栏阻断，使用建议回答或拒答消息
                    suggest_answer = guardrail_dict.get('suggest_answer', '')
                    if suggest_answer:
                        model_results[model_id] = ModelResponse(content=suggest_answer)
                    else:
                        model_results[model_id] = ModelResponse(content="抱歉，我无法回答这个问题，因为它可能违反了安全准则。")
        
        return OnlineTestResponse(
            guardrail=guardrail_dict,
            models=model_results,
            original_responses=original_responses
        )
        
    except HTTPException:
        # 重新抛出HTTPException（包括429限速错误），不要转换为500错误
        raise
    except Exception as e:
        import traceback
        error_msg = f"Online test error: {e}\nTraceback: {traceback.format_exc()}"
        logger.error(error_msg)
        
        # 改进超时错误处理
        error_str = str(e).lower()
        if "timeout" in error_str or "timed out" in error_str:
            raise HTTPException(
                status_code=408, 
                detail="测试执行超时，这可能是由于模型响应时间过长导致的。请稍后重试，或联系管理员检查模型配置。"
            )
        else:
            raise HTTPException(status_code=500, detail=f"测试执行失败: {str(e)}")

async def call_guardrail_api(api_key: str, messages: List[Dict[str, Any]], user_uuid: uuid.UUID, db: Session, has_images: bool = False) -> Dict[str, Any]:
    """调用护栏API"""
    try:
        # 构建护栏API的URL - 根据配置自动适配环境
        guardrail_url = f"http://{settings.detection_host}:{settings.detection_port}/v1/guardrails"
        
        # 根据是否有图片选择合适的模型
        model_name = "Xiangxin-Guardrails-VL" if has_images else "Xiangxin-Guardrails-Text"
        
        async with httpx.AsyncClient(timeout=180.0) as client:  # 增加护栏API超时到3分钟
            response = await client.post(
                guardrail_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": model_name,
                    "messages": messages
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "compliance": {
                        "risk_level": result.get('result', {}).get('compliance', {}).get('risk_level', '无风险'),
                        "categories": result.get('result', {}).get('compliance', {}).get('categories', [])
                    },
                    "security": {
                        "risk_level": result.get('result', {}).get('security', {}).get('risk_level', '无风险'),
                        "categories": result.get('result', {}).get('security', {}).get('categories', [])
                    },
                    "data": {
                        "risk_level": result.get('result', {}).get('data', {}).get('risk_level', '无风险'),
                        "categories": result.get('result', {}).get('data', {}).get('categories', [])
                    },
                    "overall_risk_level": result.get('overall_risk_level', '无风险'),
                    "suggest_action": result.get('suggest_action', '通过'),
                    "suggest_answer": result.get('suggest_answer', '')
                }
            elif response.status_code == 429:
                # 处理限速错误，获取用户限速配置
                try:
                    from services.rate_limiter import RateLimitService
                    rate_limit_service = RateLimitService(db)
                    rate_limit_config = rate_limit_service.get_user_rate_limit(str(user_uuid))
                    rate_limit = rate_limit_config.requests_per_second if rate_limit_config and rate_limit_config.is_active else 1
                    
                    rate_limit_text = "无限制" if rate_limit == 0 else f"{rate_limit} 请求/秒"
                    
                    raise HTTPException(
                        status_code=429, 
                        detail=f"API调用频率超过限制，请稍后再试。当前限速：{rate_limit_text}。如需调整请联系管理员 {settings.support_email}"
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"获取用户限速配置失败: {e}")
                    raise HTTPException(
                        status_code=429, 
                        detail="API调用频率超过限制，请稍后再试。请检查您的API速度限制设置。"
                    )
            else:
                raise Exception(f"护栏API调用失败: HTTP {response.status_code}")
                
    except HTTPException:
        # 重新抛出HTTPException，不要捕获
        raise
    except Exception as e:
        logger.error(f"Guardrail API call failed: {e}")
        # 检查是否是限速相关的错误
        error_str = str(e).lower()
        if "rate limit" in error_str or "429" in error_str or "too many requests" in error_str:
            try:
                from services.rate_limiter import RateLimitService
                rate_limit_service = RateLimitService(db)
                rate_limit_config = rate_limit_service.get_user_rate_limit(str(user_uuid))
                rate_limit = rate_limit_config.requests_per_second if rate_limit_config and rate_limit_config.is_active else 1
                
                rate_limit_text = "无限制" if rate_limit == 0 else f"{rate_limit} 请求/秒"
                
                raise HTTPException(
                    status_code=429, 
                    detail=f"API调用频率超过限制，请稍后再试。当前限速：{rate_limit_text}。如需调整请联系管理员 {settings.support_email}"
                )
            except HTTPException:
                raise
            except Exception as ex:
                logger.error(f"获取用户限速配置失败: {ex}")
                raise HTTPException(
                    status_code=429, 
                    detail="API调用频率超过限制，请稍后再试。请检查您的API速度限制设置。"
                )
        
        return {
            "compliance": {
                "risk_level": "检测失败",
                "categories": ["系统错误"]
            },
            "security": {
                "risk_level": "检测失败",
                "categories": ["系统错误"]
            },
            "data": {
                "risk_level": "无风险",
                "categories": []
            },
            "overall_risk_level": "检测失败",
            "suggest_action": "系统错误",
            "suggest_answer": f"护栏检测系统出现错误: {str(e)}"
        }

async def test_model_api(model: ModelConfig, messages: List[Dict[str, Any]]) -> ModelResponse:
    """使用OpenAI SDK测试单个模型API"""
    try:
        # 创建OpenAI客户端，使用更长的超时时间以支持代理模型
        client = AsyncOpenAI(
            api_key=model.api_key,
            base_url=model.base_url.rstrip('/'),
            timeout=600.0  # 10分钟超时
        )
        
        # 调用模型API
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=messages,
            temperature=0.0
        )
        
        # 提取响应内容
        # 如果有reasoning_content,则返回reasoning_content
        reasoning_content = None
        if response.choices[0].message.reasoning_content:
            reasoning_content = response.choices[0].message.reasoning_content
        
        answer_content = response.choices[0].message.content if response.choices else '无响应'
        if reasoning_content:
            content = f"<think>\n{reasoning_content}\n</think>\n\n{answer_content}"
        else:
            content = answer_content
        
        return ModelResponse(content=content)
        
    except Exception as e:
        error_message = str(e)
        if "401" in error_message or "Unauthorized" in error_message:
            error_message = "API Key无效或未授权"
        elif "404" in error_message or "Not Found" in error_message:
            error_message = "API端点未找到或模型不存在"
        elif "timeout" in error_message.lower() or "timed out" in error_message.lower():
            error_message = "请求超时，模型响应时间过长，请稍后重试或联系管理员"
        elif "rate limit" in error_message.lower():
            error_message = "API调用频率限制"
        else:
            error_message = f"请求失败: {error_message}"
            
        logger.error(f"Model API call failed for {model.name}: {error_message}")
        return ModelResponse(
            content=None,
            error=error_message
        )