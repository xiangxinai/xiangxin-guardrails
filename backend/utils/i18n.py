"""
国际化工具模块
提供多语言支持功能
"""
from typing import Dict, Any, Optional

# 翻译字典
TRANSLATIONS = {
    'zh': {
        'ban_reason_template': '在 {time_window} 分钟内触发 {trigger_count} 次{risk_level}风险',
        'risk_levels': {
            'low_risk': '低',
            'medium_risk': '中',
            'high_risk': '高'
        }
    },
    'en': {
        'ban_reason_template': 'Triggered {trigger_count} {risk_level} risk(s) within {time_window} minutes',
        'risk_levels': {
            'low_risk': 'low',
            'medium_risk': 'medium', 
            'high_risk': 'high'
        }
    }
}

def get_language_from_request(request=None, tenant_id: Optional[str] = None) -> str:
    """
    从请求中获取语言设置
    
    Args:
        request: FastAPI Request对象
        tenant_id: 租户ID（可用于获取租户语言偏好）
        
    Returns:
        语言代码，默认为'zh'
    """
    # 优先级：
    # 1. 请求头中的Accept-Language
    # 2. 租户设置（如果有的话）
    # 3. 默认中文
    
    if request:
        # 检查Accept-Language头
        accept_language = request.headers.get('accept-language', '')
        if 'en' in accept_language.lower():
            return 'en'
    
    # 默认返回中文
    return 'zh'

def translate(key: str, language: str = 'zh', **kwargs) -> str:
    """
    翻译指定的键值
    
    Args:
        key: 翻译键
        language: 语言代码
        **kwargs: 模板参数
        
    Returns:
        翻译后的文本
    """
    # 获取对应语言的翻译
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS['zh'])
    
    # 获取翻译文本
    text = lang_dict.get(key, key)
    
    # 如果有参数，进行格式化
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            # 如果格式化失败，返回原文本
            return text
    
    return text

def get_risk_level_text(risk_level: str, language: str = 'zh') -> str:
    """
    获取风险等级的本地化文本
    
    Args:
        risk_level: 风险等级（如 'high_risk'）
        language: 语言代码
        
    Returns:
        本地化的风险等级文本
    """
    lang_dict = TRANSLATIONS.get(language, TRANSLATIONS['zh'])
    risk_levels = lang_dict.get('risk_levels', {})
    return risk_levels.get(risk_level, risk_level)

def format_ban_reason(time_window: int, trigger_count: int, risk_level: str, language: str = 'zh') -> str:
    """
    格式化封禁原因
    
    Args:
        time_window: 时间窗口（分钟）
        trigger_count: 触发次数
        risk_level: 风险等级
        language: 语言代码
        
    Returns:
        格式化后的封禁原因
    """
    # 获取风险等级的本地化文本
    risk_level_text = get_risk_level_text(risk_level, language)
    
    # 格式化封禁原因
    return translate(
        'ban_reason_template',
        language=language,
        time_window=time_window,
        trigger_count=trigger_count,
        risk_level=risk_level_text
    )
