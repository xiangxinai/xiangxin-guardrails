from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator

class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="消息角色: user, system, assistant")
    content: str = Field(..., description="消息内容")
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'system', 'assistant']:
            raise ValueError('role must be one of: user, system, assistant')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('content cannot be empty')
        if len(v) > 10000:
            raise ValueError('content too long (max 10000 characters)')
        return v.strip()

class GuardrailRequest(BaseModel):
    """护栏检测请求模型"""
    model: str = Field(..., description="模型名称")
    messages: List[Message] = Field(..., description="消息列表")
    max_tokens: Optional[int] = Field(None, description="最大令牌数")
    
    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('messages cannot be empty')
        return v

class BlacklistRequest(BaseModel):
    """黑名单请求模型"""
    name: str = Field(..., description="黑名单库名称")
    keywords: List[str] = Field(..., description="关键词列表")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not v:
            raise ValueError('keywords cannot be empty')
        return [kw.strip() for kw in v if kw.strip()]

class WhitelistRequest(BaseModel):
    """白名单请求模型"""
    name: str = Field(..., description="白名单库名称")
    keywords: List[str] = Field(..., description="关键词列表")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not v:
            raise ValueError('keywords cannot be empty')
        return [kw.strip() for kw in v if kw.strip()]

class ResponseTemplateRequest(BaseModel):
    """代答模板请求模型"""
    category: str = Field(..., description="风险类别")
    risk_level: str = Field(..., description="风险等级")
    template_content: str = Field(..., description="代答内容")
    is_default: bool = Field(False, description="是否为默认模板")
    is_active: bool = Field(True, description="是否启用")
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12', 'default']
        if v not in valid_categories:
            raise ValueError(f'category must be one of: {valid_categories}')
        return v
    
    @validator('risk_level')
    def validate_risk_level(cls, v):
        if v not in ['无风险', '低风险', '中风险', '高风险']:
            raise ValueError('risk_level must be one of: 无风险, 低风险, 中风险, 高风险')
        return v