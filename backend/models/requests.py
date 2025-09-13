from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator, ConfigDict

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
        if len(v) > 1000000:
            raise ValueError('content too long (max 1000000 characters)')
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

class ProxyCompletionRequest(BaseModel):
    """代理完成请求模型"""
    model: str = Field(..., description="模型名称")
    messages: List[Message] = Field(..., description="消息列表")
    temperature: Optional[float] = Field(None, description="温度参数")
    top_p: Optional[float] = Field(None, description="Top-p参数")
    n: Optional[int] = Field(1, description="生成数量")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    stop: Optional[Union[str, List[str]]] = Field(None, description="停止词")
    max_tokens: Optional[int] = Field(None, description="最大token数")
    presence_penalty: Optional[float] = Field(None, description="存在惩罚")
    frequency_penalty: Optional[float] = Field(None, description="频率惩罚")
    user: Optional[str] = Field(None, description="用户标识")

class ProxyModelConfig(BaseModel):
    """代理模型配置模型"""
    config_name: str = Field(..., description="配置名称")
    api_base_url: str = Field(..., description="API基础URL")
    api_key: str = Field(..., description="API密钥")
    model_name: str = Field(..., description="模型名称")
    enabled: Optional[bool] = Field(True, description="是否启用")
    
    # 允许以 model_ 开头的字段名
    model_config = ConfigDict(protected_namespaces=())
    
    # 安全配置（极简设计）
    block_on_input_risk: Optional[bool] = Field(False, description="输入风险时是否阻断，默认不阻断")
    block_on_output_risk: Optional[bool] = Field(False, description="输出风险时是否阻断，默认不阻断") 
    enable_reasoning_detection: Optional[bool] = Field(True, description="是否检测reasoning内容，默认开启")
    stream_chunk_size: Optional[int] = Field(50, description="流式检测间隔，每N个chunk检测一次，默认50", ge=1, le=500)

class InputGuardrailRequest(BaseModel):
    """输入检测请求模型 - 适用于dify/coze等平台插件"""
    input: str = Field(..., description="用户输入文本")
    
    @validator('input')
    def validate_input(cls, v):
        if not v or not v.strip():
            raise ValueError('input cannot be empty')
        if len(v) > 1000000:
            raise ValueError('input too long (max 1000000 characters)')
        return v.strip()

class OutputGuardrailRequest(BaseModel):
    """输出检测请求模型 - 适用于dify/coze等平台插件"""
    input: str = Field(..., description="用户输入文本")
    output: str = Field(..., description="模型输出文本")
    
    @validator('input')
    def validate_input(cls, v):
        if not v or not v.strip():
            raise ValueError('input cannot be empty')
        if len(v) > 1000000:
            raise ValueError('input too long (max 1000000 characters)')
        return v.strip()
    
    @validator('output')
    def validate_output(cls, v):
        if not v or not v.strip():
            raise ValueError('output cannot be empty')
        if len(v) > 1000000:
            raise ValueError('output too long (max 1000000 characters)')
        return v.strip()