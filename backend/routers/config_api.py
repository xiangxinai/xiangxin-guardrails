from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Blacklist, Whitelist, ResponseTemplate, KnowledgeBase, User
from models.requests import BlacklistRequest, WhitelistRequest, ResponseTemplateRequest, KnowledgeBaseRequest
from models.responses import (
    BlacklistResponse, WhitelistResponse, ResponseTemplateResponse, ApiResponse,
    KnowledgeBaseResponse, KnowledgeBaseFileInfo, SimilarQuestionResult
)
from utils.logger import setup_logger
from utils.auth import verify_token
from config import settings
from services.keyword_cache import keyword_cache
from services.template_cache import template_cache
from services.enhanced_template_service import enhanced_template_service
from services.admin_service import admin_service
from services.knowledge_base_service import knowledge_base_service

logger = setup_logger()
router = APIRouter(tags=["Configuration"])
security = HTTPBearer()

def get_current_user_from_request(request: Request, db: Session) -> User:
    """从请求获取当前用户（更健壮，兼容admin token与无切换状态）。"""
    # 1) 优先检查是否有用户切换会话
    switch_token = request.headers.get('x-switch-session')
    if switch_token:
        switched_user = admin_service.get_switched_user(db, switch_token)
        if switched_user:
            return switched_user

    # 2) 从认证上下文获取用户
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context or 'data' not in auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    data = auth_context['data']
    user_id_value = data.get('user_id')
    user_email_value = data.get('email')

    # 2a) 尝试通过 user_id 解析为 UUID 并查询
    if user_id_value:
        try:
            user_uuid = uuid.UUID(str(user_id_value))
            user = db.query(User).filter(User.id == user_uuid).first()
            if user:
                return user
        except ValueError:
            # 继续尝试通过邮箱查找
            pass

    # 2b) 退化为使用 email 查找（兼容 admin token 或回退上下文）
    if user_email_value:
        user = db.query(User).filter(User.email == user_email_value).first()
        if user:
            return user

    # 2c) 最后手段：解析 Authorization 头部的JWT，再次尝试
    auth_header = request.headers.get('authorization') or request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = verify_token(token)
            raw_user_id = payload.get('user_id') or payload.get('sub')
            if raw_user_id:
                try:
                    user_uuid = uuid.UUID(str(raw_user_id))
                    user = db.query(User).filter(User.id == user_uuid).first()
                    if user:
                        return user
                except ValueError:
                    pass
            email_claim = payload.get('email') or payload.get('username')
            if email_claim:
                user = db.query(User).filter(User.email == email_claim).first()
                if user:
                    return user
        except Exception:
            pass

    # 无法定位到有效用户
    raise HTTPException(status_code=401, detail="User not found or invalid context")

# 黑名单管理
@router.get("/config/blacklist", response_model=List[BlacklistResponse])
async def get_blacklist(request: Request, db: Session = Depends(get_db)):
    """获取黑名单配置"""
    try:
        current_user = get_current_user_from_request(request, db)
        blacklists = db.query(Blacklist).filter(Blacklist.user_id == current_user.id).order_by(Blacklist.created_at.desc()).all()
        return [BlacklistResponse(
            id=bl.id,
            name=bl.name,
            keywords=bl.keywords or [],
            description=bl.description,
            is_active=bl.is_active,
            created_at=bl.created_at,
            updated_at=bl.updated_at
        ) for bl in blacklists]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get blacklist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get blacklist")

@router.post("/config/blacklist", response_model=ApiResponse)
async def create_blacklist(blacklist_request: BlacklistRequest, request: Request, db: Session = Depends(get_db)):
    """创建黑名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        blacklist = Blacklist(
            user_id=current_user.id,
            name=blacklist_request.name,
            keywords=blacklist_request.keywords,
            description=blacklist_request.description,
            is_active=blacklist_request.is_active
        )
        db.add(blacklist)
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Blacklist created: {blacklist_request.name} for user: {current_user.email}")
        return ApiResponse(success=True, message="Blacklist created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create blacklist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create blacklist")

@router.put("/config/blacklist/{blacklist_id}", response_model=ApiResponse)
async def update_blacklist(blacklist_id: int, blacklist_request: BlacklistRequest, request: Request, db: Session = Depends(get_db)):
    """更新黑名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        blacklist = db.query(Blacklist).filter_by(id=blacklist_id, user_id=current_user.id).first()
        if not blacklist:
            raise HTTPException(status_code=404, detail="Blacklist not found")
        
        blacklist.name = blacklist_request.name
        blacklist.keywords = blacklist_request.keywords
        blacklist.description = blacklist_request.description
        blacklist.is_active = blacklist_request.is_active
        
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Blacklist updated: {blacklist_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Blacklist updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update blacklist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update blacklist")

@router.delete("/config/blacklist/{blacklist_id}", response_model=ApiResponse)
async def delete_blacklist(blacklist_id: int, request: Request, db: Session = Depends(get_db)):
    """删除黑名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        blacklist = db.query(Blacklist).filter_by(id=blacklist_id, user_id=current_user.id).first()
        if not blacklist:
            raise HTTPException(status_code=404, detail="Blacklist not found")
        
        db.delete(blacklist)
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Blacklist deleted: {blacklist_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Blacklist deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete blacklist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete blacklist")

# 白名单管理
@router.get("/config/whitelist", response_model=List[WhitelistResponse])
async def get_whitelist(request: Request, db: Session = Depends(get_db)):
    """获取白名单配置"""
    try:
        current_user = get_current_user_from_request(request, db)
        # 若列缺失（升级前数据库），尝试无 user_id 过滤，回退支持
        try:
            whitelists = db.query(Whitelist).filter(Whitelist.user_id == current_user.id).order_by(Whitelist.created_at.desc()).all()
        except Exception as e:
            logger.warning(f"Whitelist query failed with user_id filter, falling back: {e}")
            whitelists = db.query(Whitelist).order_by(Whitelist.created_at.desc()).all()
        return [WhitelistResponse(
            id=wl.id,
            name=wl.name,
            keywords=wl.keywords or [],
            description=wl.description,
            is_active=wl.is_active,
            created_at=wl.created_at,
            updated_at=wl.updated_at
        ) for wl in whitelists]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get whitelist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get whitelist")

@router.post("/config/whitelist", response_model=ApiResponse)
async def create_whitelist(whitelist_request: WhitelistRequest, request: Request, db: Session = Depends(get_db)):
    """创建白名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        whitelist = Whitelist(
            user_id=current_user.id,
            name=whitelist_request.name,
            keywords=whitelist_request.keywords,
            description=whitelist_request.description,
            is_active=whitelist_request.is_active
        )
        db.add(whitelist)
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Whitelist created: {whitelist_request.name} for user: {current_user.email}")
        return ApiResponse(success=True, message="Whitelist created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create whitelist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create whitelist")

@router.put("/config/whitelist/{whitelist_id}", response_model=ApiResponse)
async def update_whitelist(whitelist_id: int, whitelist_request: WhitelistRequest, request: Request, db: Session = Depends(get_db)):
    """更新白名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        whitelist = db.query(Whitelist).filter_by(id=whitelist_id, user_id=current_user.id).first()
        if not whitelist:
            raise HTTPException(status_code=404, detail="Whitelist not found")
        
        whitelist.name = whitelist_request.name
        whitelist.keywords = whitelist_request.keywords
        whitelist.description = whitelist_request.description
        whitelist.is_active = whitelist_request.is_active
        
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Whitelist updated: {whitelist_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Whitelist updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update whitelist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update whitelist")

@router.delete("/config/whitelist/{whitelist_id}", response_model=ApiResponse)
async def delete_whitelist(whitelist_id: int, request: Request, db: Session = Depends(get_db)):
    """删除白名单"""
    try:
        current_user = get_current_user_from_request(request, db)
        whitelist = db.query(Whitelist).filter_by(id=whitelist_id, user_id=current_user.id).first()
        if not whitelist:
            raise HTTPException(status_code=404, detail="Whitelist not found")
        
        db.delete(whitelist)
        db.commit()
        
        # 立即失效关键词缓存
        await keyword_cache.invalidate_cache()
        
        logger.info(f"Whitelist deleted: {whitelist_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Whitelist deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete whitelist error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete whitelist")

# 代答模板管理
@router.get("/config/responses", response_model=List[ResponseTemplateResponse])
async def get_response_templates(request: Request, db: Session = Depends(get_db)):
    """获取代答模板配置"""
    try:
        current_user = get_current_user_from_request(request, db)
        # 若列缺失（升级前数据库），尝试全局模板回退
        try:
            templates = db.query(ResponseTemplate).filter(ResponseTemplate.user_id == current_user.id).order_by(ResponseTemplate.created_at.desc()).all()
        except Exception as e:
            logger.warning(f"ResponseTemplate query failed with user_id filter, falling back: {e}")
            templates = db.query(ResponseTemplate).order_by(ResponseTemplate.created_at.desc()).all()
        return [ResponseTemplateResponse(
            id=rt.id,
            category=rt.category,
            risk_level=rt.risk_level,
            template_content=rt.template_content,
            is_default=rt.is_default,
            is_active=rt.is_active,
            created_at=rt.created_at,
            updated_at=rt.updated_at
        ) for rt in templates]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get response templates error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get response templates")

@router.post("/config/responses", response_model=ApiResponse)
async def create_response_template(template_request: ResponseTemplateRequest, request: Request, db: Session = Depends(get_db)):
    """创建代答模板"""
    try:
        current_user = get_current_user_from_request(request, db)
        template = ResponseTemplate(
            user_id=current_user.id,
            category=template_request.category,
            risk_level=template_request.risk_level,
            template_content=template_request.template_content,
            is_default=template_request.is_default,
            is_active=template_request.is_active
        )
        db.add(template)
        db.commit()
        
        # 立即失效模板缓存
        await template_cache.invalidate_cache()
        await enhanced_template_service.invalidate_cache()
        
        logger.info(f"Response template created: {template_request.category} for user: {current_user.email}")
        return ApiResponse(success=True, message="Response template created successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create response template error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create response template")

@router.put("/config/responses/{template_id}", response_model=ApiResponse)
async def update_response_template(template_id: int, template_request: ResponseTemplateRequest, request: Request, db: Session = Depends(get_db)):
    """更新代答模板"""
    try:
        current_user = get_current_user_from_request(request, db)
        template = db.query(ResponseTemplate).filter_by(id=template_id, user_id=current_user.id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Response template not found")
        
        template.category = template_request.category
        template.risk_level = template_request.risk_level
        template.template_content = template_request.template_content
        template.is_default = template_request.is_default
        template.is_active = template_request.is_active
        
        db.commit()
        
        # 立即失效模板缓存
        await template_cache.invalidate_cache()
        await enhanced_template_service.invalidate_cache()
        
        logger.info(f"Response template updated: {template_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Response template updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update response template error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update response template")

@router.delete("/config/responses/{template_id}", response_model=ApiResponse)
async def delete_response_template(template_id: int, request: Request, db: Session = Depends(get_db)):
    """删除代答模板"""
    try:
        current_user = get_current_user_from_request(request, db)
        template = db.query(ResponseTemplate).filter_by(id=template_id, user_id=current_user.id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Response template not found")
        
        db.delete(template)
        db.commit()
        
        # 立即失效模板缓存
        await template_cache.invalidate_cache()
        await enhanced_template_service.invalidate_cache()
        
        logger.info(f"Response template deleted: {template_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Response template deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete response template error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete response template")

# 系统信息
@router.get("/config/system-info")
async def get_system_info():
    """获取系统信息"""
    try:
        return {
            "support_email": settings.support_email if settings.support_email else None,
            "app_name": settings.app_name,
            "app_version": settings.app_version
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system info")

# 缓存管理
@router.get("/config/cache-info")
async def get_cache_info():
    """获取缓存信息"""
    try:
        keyword_cache_info = keyword_cache.get_cache_info()
        template_cache_info = template_cache.get_cache_info()
        enhanced_template_cache_info = enhanced_template_service.get_cache_info()
        return {
            "status": "success",
            "data": {
                "keyword_cache": keyword_cache_info,
                "template_cache": template_cache_info,
                "enhanced_template_cache": enhanced_template_cache_info
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get cache info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache info")

@router.post("/config/cache/refresh")
async def refresh_cache():
    """手动刷新缓存"""
    try:
        await keyword_cache.invalidate_cache()
        await template_cache.invalidate_cache()
        await enhanced_template_service.invalidate_cache()
        return {
            "status": "success",
            "message": "All caches refreshed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh cache error: {e}")
        raise HTTPException(status_code=500, detail="Failed to refresh cache")

# 知识库管理
@router.get("/config/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases(
    category: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """获取知识库列表"""
    try:
        current_user = get_current_user_from_request(request, db)

        # 查询用户自己的知识库 + 全局知识库
        query = db.query(KnowledgeBase).filter(
            (KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.is_global == True)
        )

        if category:
            query = query.filter(KnowledgeBase.category == category)

        knowledge_bases = query.order_by(KnowledgeBase.created_at.desc()).all()

        return [KnowledgeBaseResponse(
            id=kb.id,
            category=kb.category,
            name=kb.name,
            description=kb.description,
            file_path=kb.file_path,
            vector_file_path=kb.vector_file_path,
            total_qa_pairs=kb.total_qa_pairs,
            is_active=kb.is_active,
            is_global=kb.is_global,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ) for kb in knowledge_bases]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get knowledge bases error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge bases")

@router.post("/config/knowledge-bases", response_model=ApiResponse)
async def create_knowledge_base(
    file: UploadFile = File(...),
    category: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    is_active: bool = Form(True),
    is_global: bool = Form(False),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """创建知识库"""
    try:
        current_user = get_current_user_from_request(request, db)

        # 调试信息
        logger.info(f"Create knowledge base - category: {category}, name: {name}, description: {description}, is_active: {is_active}, is_global: {is_global}")
        logger.info(f"File info - filename: {file.filename}, content_type: {file.content_type}")

        # 验证参数
        if not category or not name:
            logger.error(f"Missing required parameters - category: {category}, name: {name}")
            raise HTTPException(status_code=400, detail="Category and name are required")

        # 检查全局权限（仅管理员可设置全局知识库）
        if is_global and not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="Only administrators can create global knowledge bases")

        if category not in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12']:
            raise HTTPException(status_code=400, detail="Invalid category")

        # 验证文件类型（不再严格依赖文件扩展名，改为依赖内容验证）
        # if not file.filename.endswith('.jsonl'):
        #     raise HTTPException(status_code=400, detail="File must be a JSONL file")

        # 检查是否已存在同名知识库
        existing = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == current_user.id,
            KnowledgeBase.category == category,
            KnowledgeBase.name == name
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Knowledge base with this name already exists for this category")

        # 读取文件内容
        file_content = await file.read()

        # 解析JSONL文件
        qa_pairs = knowledge_base_service.parse_jsonl_file(file_content)

        # 创建数据库记录
        knowledge_base = KnowledgeBase(
            user_id=current_user.id,
            category=category,
            name=name,
            description=description,
            file_path="",  # 将在下面设置
            total_qa_pairs=len(qa_pairs),
            is_active=is_active,
            is_global=is_global
        )

        db.add(knowledge_base)
        db.flush()  # 获取 ID

        # 保存原始文件
        file_path = knowledge_base_service.save_original_file(file_content, knowledge_base.id, file.filename)
        knowledge_base.file_path = file_path

        # 创建向量索引
        vector_file_path = knowledge_base_service.create_vector_index(qa_pairs, knowledge_base.id)
        knowledge_base.vector_file_path = vector_file_path

        db.commit()

        # 立即失效增强模板缓存
        await enhanced_template_service.invalidate_cache()

        logger.info(f"Knowledge base created: {name} for category {category}, user: {current_user.email}")
        return ApiResponse(success=True, message="Knowledge base created successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Create knowledge base error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create knowledge base: {str(e)}")

@router.put("/config/knowledge-bases/{kb_id}", response_model=ApiResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_request: KnowledgeBaseRequest,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """更新知识库（仅基本信息，不包括文件）"""
    try:
        current_user = get_current_user_from_request(request, db)

        # 查找知识库（用户自己的或者全局的）
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id
        ).first()

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # 权限检查：只能编辑自己的知识库，或者管理员可以编辑全局知识库
        if knowledge_base.user_id != current_user.id and not (current_user.is_super_admin and knowledge_base.is_global):
            raise HTTPException(status_code=403, detail="Permission denied")

        # 检查全局权限（仅管理员可设置全局知识库）
        if kb_request.is_global and not current_user.is_super_admin:
            raise HTTPException(status_code=403, detail="Only administrators can set knowledge bases as global")

        # 检查是否与其他知识库重名
        existing = db.query(KnowledgeBase).filter(
            KnowledgeBase.user_id == current_user.id,
            KnowledgeBase.category == kb_request.category,
            KnowledgeBase.name == kb_request.name,
            KnowledgeBase.id != kb_id
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Knowledge base with this name already exists for this category")

        knowledge_base.category = kb_request.category
        knowledge_base.name = kb_request.name
        knowledge_base.description = kb_request.description
        knowledge_base.is_active = kb_request.is_active
        knowledge_base.is_global = kb_request.is_global

        db.commit()

        # 立即失效增强模板缓存
        await enhanced_template_service.invalidate_cache()

        logger.info(f"Knowledge base updated: {kb_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Knowledge base updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update knowledge base error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update knowledge base")

@router.delete("/config/knowledge-bases/{kb_id}", response_model=ApiResponse)
async def delete_knowledge_base(
    kb_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """删除知识库"""
    try:
        current_user = get_current_user_from_request(request, db)

        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # 删除相关文件
        knowledge_base_service.delete_knowledge_base_files(kb_id)

        # 删除数据库记录
        db.delete(knowledge_base)
        db.commit()

        # 立即失效增强模板缓存
        await enhanced_template_service.invalidate_cache()

        logger.info(f"Knowledge base deleted: {kb_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Knowledge base deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Delete knowledge base error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")

@router.post("/config/knowledge-bases/{kb_id}/replace-file", response_model=ApiResponse)
async def replace_knowledge_base_file(
    kb_id: int,
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """替换知识库文件"""
    try:
        current_user = get_current_user_from_request(request, db)

        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        # 验证文件类型（不再严格依赖文件扩展名，改为依赖内容验证）
        # if not file.filename.endswith('.jsonl'):
        #     raise HTTPException(status_code=400, detail="File must be a JSONL file")

        # 读取文件内容
        file_content = await file.read()

        # 解析JSONL文件
        qa_pairs = knowledge_base_service.parse_jsonl_file(file_content)

        # 删除旧文件
        knowledge_base_service.delete_knowledge_base_files(kb_id)

        # 保存新的原始文件
        file_path = knowledge_base_service.save_original_file(file_content, kb_id, file.filename)

        # 创建新的向量索引
        vector_file_path = knowledge_base_service.create_vector_index(qa_pairs, kb_id)

        # 更新数据库记录
        knowledge_base.file_path = file_path
        knowledge_base.vector_file_path = vector_file_path
        knowledge_base.total_qa_pairs = len(qa_pairs)

        db.commit()

        # 立即失效增强模板缓存
        await enhanced_template_service.invalidate_cache()

        logger.info(f"Knowledge base file replaced: {kb_id} for user: {current_user.email}")
        return ApiResponse(success=True, message="Knowledge base file replaced successfully")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Replace knowledge base file error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to replace knowledge base file: {str(e)}")

@router.get("/config/knowledge-bases/{kb_id}/info", response_model=KnowledgeBaseFileInfo)
async def get_knowledge_base_info(
    kb_id: int,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """获取知识库文件信息"""
    try:
        current_user = get_current_user_from_request(request, db)

        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        ).first()

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found")

        file_info = knowledge_base_service.get_file_info(kb_id)

        return KnowledgeBaseFileInfo(**file_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get knowledge base info error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge base info")

@router.post("/config/knowledge-bases/{kb_id}/search", response_model=List[SimilarQuestionResult])
async def search_similar_questions(
    kb_id: int,
    query: str,
    top_k: Optional[int] = 5,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """搜索相似问题"""
    try:
        current_user = get_current_user_from_request(request, db)

        # 查找知识库（用户自己的或者全局的）
        knowledge_base = db.query(KnowledgeBase).filter(
            KnowledgeBase.id == kb_id,
            ((KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.is_global == True)),
            KnowledgeBase.is_active == True
        ).first()

        if not knowledge_base:
            raise HTTPException(status_code=404, detail="Knowledge base not found or not active")

        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        results = knowledge_base_service.search_similar_questions(query.strip(), kb_id, top_k)

        return [SimilarQuestionResult(**result) for result in results]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search similar questions error: {e}")
        raise HTTPException(status_code=500, detail="Failed to search similar questions")

@router.get("/config/categories/{category}/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases_by_category(
    category: str,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """获取指定类别的知识库列表"""
    try:
        current_user = get_current_user_from_request(request, db)

        if category not in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12']:
            raise HTTPException(status_code=400, detail="Invalid category")

        # 查询用户自己的知识库 + 全局知识库
        knowledge_bases = db.query(KnowledgeBase).filter(
            ((KnowledgeBase.user_id == current_user.id) | (KnowledgeBase.is_global == True)),
            KnowledgeBase.category == category,
            KnowledgeBase.is_active == True
        ).order_by(KnowledgeBase.created_at.desc()).all()

        return [KnowledgeBaseResponse(
            id=kb.id,
            category=kb.category,
            name=kb.name,
            description=kb.description,
            file_path=kb.file_path,
            vector_file_path=kb.vector_file_path,
            total_qa_pairs=kb.total_qa_pairs,
            is_active=kb.is_active,
            is_global=kb.is_global,
            created_at=kb.created_at,
            updated_at=kb.updated_at
        ) for kb in knowledge_bases]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get knowledge bases by category error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge bases by category")