import time
import hashlib
from typing import Dict, Optional, Any
from utils.logger import setup_logger

logger = setup_logger()

class AuthCache:
    """认证缓存 - 高性能内存缓存"""
    
    def __init__(self, ttl: int = 300):  # 5分钟缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl
    
    def _make_key(self, token: str) -> str:
        """生成缓存键"""
        return hashlib.md5(token.encode()).hexdigest()
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """获取缓存的认证信息"""
        key = self._make_key(token)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry['timestamp'] < self._ttl:
                return entry['data']
            else:
                # 过期，删除
                del self._cache[key]
        return None
    
    def set(self, token: str, auth_data: Dict[str, Any]):
        """设置缓存"""
        key = self._make_key(token)
        self._cache[key] = {
            'data': auth_data,
            'timestamp': time.time()
        }
    
    def invalidate(self, token: str):
        """使缓存失效"""
        key = self._make_key(token)
        if key in self._cache:
            del self._cache[key]
    
    def clear_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self._cache.items():
            if current_time - entry['timestamp'] >= self._ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleared {len(expired_keys)} expired auth cache entries")
    
    def size(self) -> int:
        """获取缓存大小"""
        return len(self._cache)

# 全局认证缓存实例
auth_cache = AuthCache(ttl=300)  # 5分钟缓存