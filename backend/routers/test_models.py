from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from pydantic import ConfigDict
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import TestModelConfig, User
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(tags=["Test Models"])

class TestModelRequest(BaseModel):
    name: str
    base_url: str
    api_key: str
    model_name: str
    enabled: bool = True
    model_config = ConfigDict(protected_namespaces=())

class TestModelResponse(BaseModel):
    id: int
    name: str
    base_url: str
    model_name: str
    enabled: bool
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

@router.get("/test-models", response_model=List[TestModelResponse])
async def get_test_models(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取用户的被测模型配置"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = str(auth_context['data'].get('user_id'))
        user_uuid = uuid.UUID(user_id)
        
        # 查询用户的模型配置
        models = db.query(TestModelConfig).filter(
            TestModelConfig.user_id == user_uuid
        ).all()
        
        # 返回时不包含API Key（安全考虑）
        return [TestModelResponse(
            id=model.id,
            name=model.name,
            base_url=model.base_url,
            model_name=model.model_name,
            enabled=model.enabled
        ) for model in models]
        
    except Exception as e:
        logger.error(f"Get test models error: {e}")
        raise HTTPException(status_code=500, detail="获取模型配置失败")

@router.post("/test-models", response_model=TestModelResponse)
async def create_test_model(
    model_data: TestModelRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """创建被测模型配置"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = str(auth_context['data'].get('user_id'))
        user_uuid = uuid.UUID(user_id)
        
        # 创建新的模型配置
        new_model = TestModelConfig(
            user_id=user_uuid,
            name=model_data.name,
            base_url=model_data.base_url,
            api_key=model_data.api_key,
            model_name=model_data.model_name,
            enabled=model_data.enabled
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        return TestModelResponse(
            id=new_model.id,
            name=new_model.name,
            base_url=new_model.base_url,
            model_name=new_model.model_name,
            enabled=new_model.enabled
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Create test model error: {e}")
        raise HTTPException(status_code=500, detail="创建模型配置失败")

@router.put("/test-models/{model_id}", response_model=TestModelResponse)
async def update_test_model(
    model_id: int,
    model_data: TestModelRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """更新被测模型配置"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = str(auth_context['data'].get('user_id'))
        user_uuid = uuid.UUID(user_id)
        
        # 查询模型配置
        model = db.query(TestModelConfig).filter(
            TestModelConfig.id == model_id,
            TestModelConfig.user_id == user_uuid
        ).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        # 更新配置
        model.name = model_data.name
        model.base_url = model_data.base_url
        model.api_key = model_data.api_key
        model.model_name = model_data.model_name
        model.enabled = model_data.enabled
        
        db.commit()
        db.refresh(model)
        
        return TestModelResponse(
            id=model.id,
            name=model.name,
            base_url=model.base_url,
            model_name=model.model_name,
            enabled=model.enabled
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Update test model error: {e}")
        raise HTTPException(status_code=500, detail="更新模型配置失败")

@router.delete("/test-models/{model_id}")
async def delete_test_model(
    model_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """删除被测模型配置"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = str(auth_context['data'].get('user_id'))
        user_uuid = uuid.UUID(user_id)
        
        # 查询并删除模型配置
        model = db.query(TestModelConfig).filter(
            TestModelConfig.id == model_id,
            TestModelConfig.user_id == user_uuid
        ).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        db.delete(model)
        db.commit()
        
        return {"message": "模型配置已删除"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Delete test model error: {e}")
        raise HTTPException(status_code=500, detail="删除模型配置失败")

@router.patch("/test-models/{model_id}/toggle")
async def toggle_test_model(
    model_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """切换被测模型启用状态"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        if not auth_context:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        user_id = str(auth_context['data'].get('user_id'))
        user_uuid = uuid.UUID(user_id)
        
        # 查询模型配置
        model = db.query(TestModelConfig).filter(
            TestModelConfig.id == model_id,
            TestModelConfig.user_id == user_uuid
        ).first()
        
        if not model:
            raise HTTPException(status_code=404, detail="模型配置不存在")
        
        # 切换启用状态
        model.enabled = not model.enabled
        db.commit()
        
        return {"message": f"模型已{'启用' if model.enabled else '禁用'}"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Toggle test model error: {e}")
        raise HTTPException(status_code=500, detail="切换模型状态失败")