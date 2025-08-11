from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Dict, Any, Optional
import asyncio
import uuid
import httpx
from sqlalchemy.orm import Session
from database.connection import get_db
from services.guardrail_service import GuardrailService
from models.requests import GuardrailRequest, Message
from utils.logger import setup_logger
from openai import AsyncOpenAI
from config import settings

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

class ModelResponse(BaseModel):
    content: Optional[str] = None
    error: Optional[str] = None

class OnlineTestResponse(BaseModel):
    guardrail: Dict[str, Any]
    models: Dict[str, ModelResponse] = {}

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
        guardrail_dict = await call_guardrail_api(user_api_key, messages)
        
        # 如果是问题类型且配置了模型，从数据库获取完整配置并调用模型API
        model_results = {}
        if request_data.input_type == 'question' and request_data.models:
            enabled_model_ids = [m.id for m in request_data.models if m.enabled]
            logger.info(f"Testing {len(enabled_model_ids)} enabled models: {enabled_model_ids}")
            
            # 从数据库获取完整的模型配置（包括API key）
            from database.models import TestModelConfig
            db_models = db.query(TestModelConfig).filter(
                TestModelConfig.id.in_(enabled_model_ids),
                TestModelConfig.user_id == user_uuid,
                TestModelConfig.enabled == True
            ).all()
            
            logger.info(f"Found {len(db_models)} models in database")
            
            # 并行调用所有启用的模型
            tasks = []
            for db_model in db_models:
                # 创建ModelConfig对象
                model_config = ModelConfig(
                    id=str(db_model.id),
                    name=db_model.name,
                    base_url=db_model.base_url,
                    api_key=db_model.api_key,
                    model_name=db_model.model_name,
                    enabled=db_model.enabled
                )
                task = test_model_api(model_config, messages)
                tasks.append((str(db_model.id), task))
            
            # 等待所有模型响应
            if tasks:
                results = await asyncio.gather(
                    *[task for _, task in tasks], 
                    return_exceptions=True
                )
                
                for i, (model_id, _) in enumerate(tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        model_results[model_id] = ModelResponse(
                            content=None,
                            error=f"请求失败: {str(result)}"
                        )
                    else:
                        model_results[model_id] = result
        
        return OnlineTestResponse(
            guardrail=guardrail_dict,
            models=model_results
        )
        
    except Exception as e:
        import traceback
        error_msg = f"Online test error: {e}\nTraceback: {traceback.format_exc()}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=f"测试执行失败: {str(e)}")

async def call_guardrail_api(api_key: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """调用护栏API"""
    try:
        # 构建护栏API的URL
        guardrail_url = f"http://{settings.host}:{settings.port}/v1/guardrails"
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                guardrail_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": "Xiangxin-Guardrails-Text",
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
                    "overall_risk_level": result.get('overall_risk_level', '无风险'),
                    "suggest_action": result.get('suggest_action', '通过'),
                    "suggest_answer": result.get('suggest_answer', '')
                }
            else:
                raise Exception(f"护栏API调用失败: HTTP {response.status_code}")
                
    except Exception as e:
        logger.error(f"Guardrail API call failed: {e}")
        # 返回默认的安全结果
        return {
            "compliance": {
                "risk_level": "无风险",
                "categories": []
            },
            "security": {
                "risk_level": "无风险", 
                "categories": []
            },
            "overall_risk_level": "无风险",
            "suggest_action": "通过",
            "suggest_answer": ""
        }

async def test_model_api(model: ModelConfig, messages: List[Dict[str, str]]) -> ModelResponse:
    """使用OpenAI SDK测试单个模型API"""
    try:
        # 创建OpenAI客户端
        client = AsyncOpenAI(
            api_key=model.api_key,
            base_url=model.base_url.rstrip('/'),
            timeout=30.0
        )
        
        # 调用模型API
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=messages,
            temperature=0.0
        )
        
        # 提取响应内容
        content = response.choices[0].message.content if response.choices else '无响应'
        return ModelResponse(content=content)
        
    except Exception as e:
        error_message = str(e)
        if "401" in error_message or "Unauthorized" in error_message:
            error_message = "API Key无效或未授权"
        elif "404" in error_message or "Not Found" in error_message:
            error_message = "API端点未找到或模型不存在"
        elif "timeout" in error_message.lower():
            error_message = "请求超时"
        elif "rate limit" in error_message.lower():
            error_message = "API调用频率限制"
        else:
            error_message = f"请求失败: {error_message}"
            
        logger.error(f"Model API call failed for {model.name}: {error_message}")
        return ModelResponse(
            content=None,
            error=error_message
        )