from typing import List, Optional
import json
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from database.connection import get_db
from database.models import DetectionResult
from models.responses import DetectionResultResponse, PaginatedResponse
from utils.logger import setup_logger
from config import settings

logger = setup_logger()
router = APIRouter(tags=["Results"])

@router.get("/results")
async def get_detection_results(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    risk_level: Optional[str] = Query(None, description="整体风险等级过滤"),
    security_risk_level: Optional[str] = Query(None, description="提示词攻击风险等级过滤"),
    compliance_risk_level: Optional[str] = Query(None, description="内容合规风险等级过滤"),
    category: Optional[str] = Query(None, description="风险类别过滤"),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    content_search: Optional[str] = Query(None, description="检测内容搜索"),
    request_id_search: Optional[str] = Query(None, description="请求ID搜索")
):
    """获取检测结果"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context and auth_context.get('data'):
            user_id = auth_context['data'].get('user_id')
        
        # 构建查询条件
        filters = []
        
        # 添加用户过滤条件
        if user_id is not None:
            filters.append(DetectionResult.user_id == user_id)
        
        # 风险等级过滤 - 支持整体风险等级或具体类型风险等级
        if risk_level:
            # 整体风险等级过滤：查找任一类型匹配的记录
            filters.append(or_(
                DetectionResult.security_risk_level == risk_level,
                DetectionResult.compliance_risk_level == risk_level
            ))
        
        if security_risk_level:
            filters.append(DetectionResult.security_risk_level == security_risk_level)
        
        if compliance_risk_level:
            filters.append(DetectionResult.compliance_risk_level == compliance_risk_level)
        
        # 类别过滤 - 在security_categories或compliance_categories中查找
        if category:
            # 使用PostgreSQL的JSON数组函数进行搜索
            filters.append(or_(
                text(f"'{category}' = ANY(SELECT json_array_elements_text(security_categories))"),
                text(f"'{category}' = ANY(SELECT json_array_elements_text(compliance_categories))")
            ))
        
        if start_date:
            filters.append(DetectionResult.created_at >= start_date + ' 00:00:00')
        
        if end_date:
            filters.append(DetectionResult.created_at <= end_date + ' 23:59:59')
        
        if content_search:
            filters.append(DetectionResult.content.like(f'%{content_search}%'))
        
        if request_id_search:
            filters.append(DetectionResult.request_id.like(f'%{request_id_search}%'))
        
        # 构建基础查询
        base_query = db.query(DetectionResult)
        if filters:
            base_query = base_query.filter(and_(*filters))
        else:
            # 如果无过滤条件也必须限定用户
            if user_id is not None:
                base_query = base_query.filter(DetectionResult.user_id == user_id)
        
        # 获取总数
        total = base_query.count()
        
        # 分页查询
        offset = (page - 1) * per_page
        results = base_query.order_by(
            DetectionResult.created_at.desc()
        ).offset(offset).limit(per_page).all()
        
        # 转换为响应模型
        items = []
        for result in results:
            items.append(DetectionResultResponse(
                id=result.id,
                request_id=result.request_id,
                content=result.content[:200] + "..." if len(result.content) > 200 else result.content,
                suggest_action=result.suggest_action,
                suggest_answer=result.suggest_answer,
                hit_keywords=result.hit_keywords,
                created_at=result.created_at,
                ip_address=result.ip_address,
                security_risk_level=result.security_risk_level,
                security_categories=result.security_categories,
                compliance_risk_level=result.compliance_risk_level,
                compliance_categories=result.compliance_categories
            ))
        
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )
        
    except Exception as e:
        logger.error(f"Get detection results error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detection results")

@router.get("/results/{result_id}", response_model=DetectionResultResponse)
async def get_detection_result(result_id: int, request: Request, db: Session = Depends(get_db)):
    """获取单个检测结果详情（确保当前用户只能查看自己的结果）"""
    try:
        # 获取用户上下文
        auth_context = getattr(request.state, 'auth_context', None)
        user_id = None
        if auth_context and auth_context.get('data'):
            user_id = auth_context['data'].get('user_id')
        
        result = db.query(DetectionResult).filter_by(id=result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Detection result not found")
        
        # 权限校验：只能查看自己的记录
        if user_id is not None and result.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        
        return DetectionResultResponse(
            id=result.id,
            request_id=result.request_id,
            content=result.content,
            suggest_action=result.suggest_action,
            suggest_answer=result.suggest_answer,
            hit_keywords=result.hit_keywords,
            created_at=result.created_at,
            ip_address=result.ip_address,
            security_risk_level=result.security_risk_level,
            security_categories=result.security_categories,
            compliance_risk_level=result.compliance_risk_level,
            compliance_categories=result.compliance_categories
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get detection result error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get detection result")