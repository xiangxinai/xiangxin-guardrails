"""
封禁策略 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from services.ban_policy_service import BanPolicyService
import logging

def get_current_tenant_id(request: Request) -> str:
    """从请求上下文获取当前租户ID"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    tenant_id = str(auth_context['data'].get('tenant_id'))
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID not found in auth context")

    return tenant_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ban-policy", tags=["ban-policy"])


class BanPolicyUpdate(BaseModel):
    """封禁策略更新模型"""
    enabled: bool = Field(False, description="是否启用封禁策略")
    risk_level: str = Field("高风险", description="触发封禁的最低风险等级", pattern="^(高风险|中风险|低风险)$")
    trigger_count: int = Field(3, ge=1, le=100, description="触发次数阈值")
    time_window_minutes: int = Field(10, ge=1, le=1440, description="时间窗口（分钟）")
    ban_duration_minutes: int = Field(60, ge=1, le=10080, description="封禁时长（分钟）")


class UnbanUserRequest(BaseModel):
    """解封用户请求模型"""
    user_id: str = Field(..., description="要解封的用户ID")


@router.get("")
async def get_ban_policy(tenant_id: str = Depends(get_current_tenant_id)):
    """获取当前租户的封禁策略配置"""
    try:
        policy = await BanPolicyService.get_ban_policy(tenant_id)

        if not policy:
            # 如果没有策略，返回默认值
            return {
                "enabled": False,
                "risk_level": "高风险",
                "trigger_count": 3,
                "time_window_minutes": 10,
                "ban_duration_minutes": 60
            }

        return policy

    except Exception as e:
        logger.error(f"Failed to get ban policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取封禁策略失败: {str(e)}")


@router.put("")
async def update_ban_policy(
    policy_data: BanPolicyUpdate,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """更新封禁策略配置"""
    try:
        policy = await BanPolicyService.update_ban_policy(
            tenant_id,
            policy_data.dict()
        )

        return {
            "success": True,
            "message": "封禁策略已更新",
            "policy": policy
        }

    except Exception as e:
        logger.error(f"Failed to update ban policy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新封禁策略失败: {str(e)}")


@router.get("/templates")
async def get_ban_policy_templates():
    """获取封禁策略预设模板"""
    return {
        "templates": [
            {
                "name": "严格模式",
                "description": "适用于高安全要求场景",
                "enabled": True,
                "risk_level": "高风险",
                "trigger_count": 3,
                "time_window_minutes": 10,
                "ban_duration_minutes": 60
            },
            {
                "name": "标准模式",
                "description": "平衡安全性和用户体验",
                "enabled": True,
                "risk_level": "高风险",
                "trigger_count": 5,
                "time_window_minutes": 30,
                "ban_duration_minutes": 30
            },
            {
                "name": "宽松模式",
                "description": "适用于测试或低风险场景",
                "enabled": True,
                "risk_level": "高风险",
                "trigger_count": 10,
                "time_window_minutes": 60,
                "ban_duration_minutes": 15
            },
            {
                "name": "关闭",
                "description": "不启用封禁策略",
                "enabled": False,
                "risk_level": "高风险",
                "trigger_count": 3,
                "time_window_minutes": 10,
                "ban_duration_minutes": 60
            }
        ]
    }


@router.get("/banned-users")
async def get_banned_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回的最大记录数"),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """获取被封禁的用户列表"""
    try:
        users = await BanPolicyService.get_banned_users(
            tenant_id,
            skip=skip,
            limit=limit
        )

        return {"users": users}

    except Exception as e:
        logger.error(f"Failed to get banned users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取封禁用户列表失败: {str(e)}")


@router.post("/unban")
async def unban_user(
    request: UnbanUserRequest,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """手动解除用户封禁"""
    try:
        success = await BanPolicyService.unban_user(tenant_id, request.user_id)

        if success:
            return {
                "success": True,
                "message": f"用户 {request.user_id} 已解除封禁"
            }
        else:
            return {
                "success": False,
                "message": f"用户 {request.user_id} 未被封禁或已解封"
            }

    except Exception as e:
        logger.error(f"Failed to unban user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"解除封禁失败: {str(e)}")


@router.get("/user-history/{user_id}")
async def get_user_risk_history(
    user_id: str,
    days: int = Query(7, ge=1, le=30, description="查询最近多少天的历史"),
    tenant_id: str = Depends(get_current_tenant_id)
):
    """获取用户的风险触发历史"""
    try:
        history = await BanPolicyService.get_user_risk_history(
            tenant_id,
            user_id,
            days=days
        )

        return {
            "user_id": user_id,
            "days": days,
            "total": len(history),
            "history": history
        }

    except Exception as e:
        logger.error(f"Failed to get user risk history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取用户风险历史失败: {str(e)}")


@router.get("/check-status/{user_id}")
async def check_user_ban_status(
    user_id: str,
    tenant_id: str = Depends(get_current_tenant_id)
):
    """检查用户的封禁状态"""
    try:
        ban_record = await BanPolicyService.check_user_banned(tenant_id, user_id)

        if ban_record:
            return {
                "is_banned": True,
                "ban_record": ban_record
            }
        else:
            return {
                "is_banned": False,
                "ban_record": None
            }

    except Exception as e:
        logger.error(f"Failed to check user ban status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检查封禁状态失败: {str(e)}")
