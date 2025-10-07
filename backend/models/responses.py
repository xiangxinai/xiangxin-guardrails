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

class DataSecurityResult(BaseModel):
    """数据安全检测结果"""
    risk_level: str
    categories: List[str]

class GuardrailResult(BaseModel):
    """护栏检测结果"""
    compliance: ComplianceResult
    security: SecurityResult
    data: DataSecurityResult

class GuardrailResponse(BaseModel):
    """护栏API响应模型"""
    id: str
    result: GuardrailResult
    overall_risk_level: str  # 综合风险等级：无风险/低风险/中风险/高风险
    suggest_action: str  # 通过，拒答，代答
    suggest_answer: Optional[str] = None
    score: Optional[float] = None  # 检测概率分数 (0.0-1.0)

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
    security_risk_level: str = "no_risk"
    security_categories: List[str] = []
    compliance_risk_level: str = "no_risk"
    compliance_categories: List[str] = []
    # 数据安全检测结果
    data_risk_level: str = "no_risk"
    data_categories: List[str] = []
    # 检测结果相关字段
    score: Optional[float] = None  # 检测概率分数 (0.0-1.0)
    # 多模态相关字段
    has_image: bool = False
    image_count: int = 0
    image_paths: List[str] = []
    image_urls: List[str] = []  # 带签名的图片访问URLs

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

class SensitivityThresholdResponse(BaseModel):
    """敏感度阈值配置响应模型"""
    high_sensitivity_threshold: float      # 高敏感度阈值
    medium_sensitivity_threshold: float    # 中敏感度阈值
    low_sensitivity_threshold: float       # 低敏感度阈值
    sensitivity_trigger_level: str         # 触发检测命中的最低敏感度等级

class DashboardStats(BaseModel):
    """仪表板统计数据"""
    total_requests: int
    security_risks: int
    compliance_risks: int
    data_leaks: int
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

class ProxyCompletionResponse(BaseModel):
    """代理完成响应模型"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, int]] = None

class ProxyModelListResponse(BaseModel):
    """代理模型列表响应"""
    object: str = "list"
    data: List[Dict[str, Any]]

class KnowledgeBaseResponse(BaseModel):
    """知识库响应模型"""
    id: int
    category: str
    name: str
    description: Optional[str]
    file_path: str
    vector_file_path: Optional[str]
    total_qa_pairs: int
    is_active: bool
    is_global: bool
    created_at: datetime
    updated_at: datetime

class KnowledgeBaseFileInfo(BaseModel):
    """知识库文件信息"""
    original_file_exists: bool
    vector_file_exists: bool
    original_file_size: int
    vector_file_size: int
    total_qa_pairs: int

class SimilarQuestionResult(BaseModel):
    """相似问题搜索结果"""
    questionid: str
    question: str
    answer: str
    similarity_score: float
    rank: int

class DataSecurityEntityTypeResponse(BaseModel):
    """数据安全实体类型响应模型"""
    id: str
    entity_type: str
    display_name: str
    risk_level: str  # 低、中、高
    pattern: str
    anonymization_method: str
    anonymization_config: Dict[str, Any]
    check_input: bool
    check_output: bool
    is_active: bool
    is_global: bool
    created_at: datetime
    updated_at: datetime