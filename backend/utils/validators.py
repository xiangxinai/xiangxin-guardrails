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

def clean_null_characters(text: str) -> str:
    """清理字符串中的NUL字符，防止数据库插入错误"""
    if not text:
        return text
    
    # 移除NUL字符（0x00）和其他控制字符
    # 保留常见的控制字符如换行符、制表符等
    import re
    # 移除NUL字符
    text = text.replace('\x00', '')
    # 移除其他可能导致问题的控制字符，但保留常见的如\n, \r, \t
    text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    return text

def clean_detection_data(data: dict) -> dict:
    """递归清理检测数据中的NUL字符"""
    if isinstance(data, dict):
        return {key: clean_detection_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [clean_detection_data(item) for item in data]
    elif isinstance(data, str):
        return clean_null_characters(data)
    else:
        return data

def extract_keywords(text: str) -> List[str]:
    """从文本中提取关键词"""
    # 简单的关键词提取，可以后续优化
    words = re.findall(r'\w+', text.lower())
    return [word for word in words if len(word) > 2]