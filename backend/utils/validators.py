import re
from typing import List, Optional
from pydantic import BaseModel, validator

class MessageValidator(BaseModel):
    """消息验证器"""
    role: str
    content: str
    
    @validator('role')
    def validate_role(cls, v):
        if v not in ['user', 'system', 'assistant']:
            raise ValueError('role must be one of: user, system, assistant')
        return v
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('content cannot be empty')
        if len(v) > 10000:  # 限制内容长度
            raise ValueError('content too long (max 10000 characters)')
        return v.strip()

def validate_api_key(api_key: str) -> bool:
    """验证API密钥格式"""
    if not api_key:
        return False
    
    # 必须以 sk-xxai- 开头，且长度合理
    if not api_key.startswith('sk-xxai-'):
        return False
    if len(api_key) < 20 or len(api_key) > 128:
        return False
    
    return True

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def sanitize_input(text: str) -> str:
    """清理输入文本"""
    if not text:
        return ""
    
    # 移除潜在的恶意字符
    text = re.sub(r'[<>"\']', '', text)
    
    # 限制长度
    if len(text) > 10000:
        text = text[:10000]
    
    return text.strip()

def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 简单的关键词提取，可以后续优化
    words = re.findall(r'\w+', text.lower())
    return [word for word in words if len(word) > 2]