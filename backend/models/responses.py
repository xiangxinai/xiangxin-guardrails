from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ComplianceResult(BaseModel):
    """合规检测结果"""
    risk_level: str
    categories: List[str]

class SecurityResult(BaseModel):
    """安全检测结果"""
    risk_level: str
    categories: List[str]

class GuardrailResult(BaseModel):
    """护栏检测结果"""
    compliance: ComplianceResult
    security: SecurityResult

class GuardrailResponse(BaseModel):
    """护栏API响应模型"""
    id: str
    result: GuardrailResult
    overall_risk_level: str  # 综合风险等级：无风险/低风险/中风险/高风险
    suggest_action: str  # 通过，阻断，代答
    suggest_answer: Optional[str] = None

class DetectionResultResponse(BaseModel):
    """检测结果响应模型"""
    id: int
    request_id: str
    content: str
    suggest_action: Optional[str]
    suggest_answer: Optional[str]
    hit_keywords: Optional[str]
    created_at: datetime
    ip_address: Optional[str]
    # 分离的安全和合规检测结果
    security_risk_level: str = "无风险"
    security_categories: List[str] = []
    compliance_risk_level: str = "无风险"
    compliance_categories: List[str] = []

class BlacklistResponse(BaseModel):
    """黑名单响应模型"""
    id: int
    name: str
    keywords: List[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class WhitelistResponse(BaseModel):
    """白名单响应模型"""
    id: int
    name: str
    keywords: List[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ResponseTemplateResponse(BaseModel):
    """代答模板响应模型"""
    id: int
    category: str
    risk_level: str
    template_content: str
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

class DashboardStats(BaseModel):
    """仪表板统计数据"""
    total_requests: int
    security_risks: int
    compliance_risks: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    safe_count: int
    risk_distribution: Dict[str, int]
    daily_trends: List[Dict[str, Any]]

class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any]
    total: int
    page: int
    per_page: int
    pages: int

class ApiResponse(BaseModel):
    """通用API响应"""
    success: bool
    message: str
    data: Optional[Any] = None