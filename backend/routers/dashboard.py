from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from database.connection import get_db
from services.stats_service import StatsService
from models.responses import DashboardStats
from utils.logger import setup_logger
from config import settings
from typing import Optional

logger = setup_logger()
router = APIRouter(tags=["Dashboard"])

def get_current_user_id(request: Request) -> str:
    """从请求上下文获取当前用户ID"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = str(auth_context['data'].get('user_id'))
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in auth context")
    
    return user_id

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(request: Request, db: Session = Depends(get_db)):
    """获取仪表板统计数据"""
    try:
        current_user_id = get_current_user_id(request)
        
        stats_service = StatsService(db)
        stats = stats_service.get_dashboard_stats(user_id=current_user_id)
        
        logger.info(f"Dashboard stats retrieved successfully for user {current_user_id}")
        return DashboardStats(**stats)
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@router.get("/dashboard/category-distribution")
async def get_category_distribution(
    request: Request,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """获取风险类别分布统计"""
    try:
        current_user_id = get_current_user_id(request)
        
        stats_service = StatsService(db) 
        category_data = stats_service.get_category_distribution(start_date, end_date, user_id=current_user_id)
        
        logger.info(f"Category distribution retrieved successfully for user {current_user_id}")
        return {"categories": category_data}
        
    except Exception as e:
        logger.error(f"Category distribution error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get category distribution")