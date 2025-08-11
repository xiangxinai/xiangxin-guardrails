import re
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from database.models import Blacklist, Whitelist
from utils.logger import setup_logger

logger = setup_logger()

class KeywordService:
    """关键词匹配服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_blacklist(self, content: str) -> Tuple[bool, Optional[str], List[str]]:
        """检查黑名单
        
        Returns:
            (is_hit, list_name, matched_keywords)
        """
        try:
            # 获取启用的黑名单
            blacklists = self.db.query(Blacklist).filter_by(is_active=True).all()
            
            content_lower = content.lower()
            
            for blacklist in blacklists:
                keywords = blacklist.keywords if isinstance(blacklist.keywords, list) else []
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    logger.info(f"Blacklist hit: {blacklist.name}, keywords: {matched_keywords}")
                    return True, blacklist.name, matched_keywords
            
            return False, None, []
            
        except Exception as e:
            logger.error(f"Blacklist check error: {e}")
            return False, None, []
    
    def check_whitelist(self, content: str) -> Tuple[bool, Optional[str], List[str]]:
        """检查白名单
        
        Returns:
            (is_hit, list_name, matched_keywords)
        """
        try:
            # 获取启用的白名单
            whitelists = self.db.query(Whitelist).filter_by(is_active=True).all()
            
            content_lower = content.lower()
            
            for whitelist in whitelists:
                keywords = whitelist.keywords if isinstance(whitelist.keywords, list) else []
                matched_keywords = []
                
                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    logger.info(f"Whitelist hit: {whitelist.name}, keywords: {matched_keywords}")
                    return True, whitelist.name, matched_keywords
            
            return False, None, []
            
        except Exception as e:
            logger.error(f"Whitelist check error: {e}")
            return False, None, []
    
    def extract_sensitive_info(self, content: str) -> List[str]:
        """提取敏感信息（通过正则表达式）"""
        sensitive_patterns = [
            # 手机号
            (r'1[3-9]\d{9}', '手机号'),
            # 身份证号
            (r'\d{17}[\dX]|\d{15}', '身份证号'),
            # 邮箱
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '邮箱地址'),
            # IP地址
            (r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', 'IP地址'),
            # 银行卡号（简单匹配）
            (r'\b\d{16,19}\b', '银行卡号'),
        ]
        
        found_info = []
        
        for pattern, info_type in sensitive_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_info.extend([f"{info_type}: {match}" for match in matches])
        
        return found_info