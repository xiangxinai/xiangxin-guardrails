import asyncio
from typing import Dict, Optional
from utils.logger import setup_logger
import time

logger = setup_logger()

class RiskConfigCache:
    """风险配置缓存 - 内存缓存用户风险类型配置"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, bool]] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 300  # 5分钟缓存
        self._lock = asyncio.Lock()
    
    async def get_user_risk_config(self, user_id: str) -> Dict[str, bool]:
        """获取用户风险配置（带缓存）"""
        if not user_id:
            # 无用户ID时返回默认全部启用
            return self._get_default_config()
        
        async with self._lock:
            # 检查缓存是否有效
            current_time = time.time()
            if (user_id in self._cache and 
                user_id in self._cache_timestamps and
                current_time - self._cache_timestamps[user_id] < self._cache_ttl):
                return self._cache[user_id]
            
            # 缓存失效或不存在，从数据库获取
            try:
                config = await self._load_from_db(user_id)
                self._cache[user_id] = config
                self._cache_timestamps[user_id] = current_time
                return config
            except Exception as e:
                logger.error(f"Failed to load risk config for user {user_id}: {e}")
                # 数据库失败时返回默认配置
                default_config = self._get_default_config()
                self._cache[user_id] = default_config
                self._cache_timestamps[user_id] = current_time
                return default_config
    
    async def _load_from_db(self, user_id: str) -> Dict[str, bool]:
        """从数据库加载风险配置"""
        from database.connection import get_db
        from database.models import RiskTypeConfig
        from sqlalchemy.orm import Session
        
        # 使用同步数据库连接
        db: Session = next(get_db())
        try:
            config = db.query(RiskTypeConfig).filter(
                RiskTypeConfig.user_id == user_id
            ).first()
            
            if config:
                return {
                    'S1': config.s1_enabled, 'S2': config.s2_enabled, 'S3': config.s3_enabled, 'S4': config.s4_enabled,
                    'S5': config.s5_enabled, 'S6': config.s6_enabled, 'S7': config.s7_enabled, 'S8': config.s8_enabled,
                    'S9': config.s9_enabled, 'S10': config.s10_enabled, 'S11': config.s11_enabled, 'S12': config.s12_enabled
                }
            else:
                # 用户没有配置，返回默认启用
                return self._get_default_config()
        finally:
            db.close()
    
    def _get_default_config(self) -> Dict[str, bool]:
        """获取默认配置（全部启用）"""
        return {
            'S1': True, 'S2': True, 'S3': True, 'S4': True,
            'S5': True, 'S6': True, 'S7': True, 'S8': True,
            'S9': True, 'S10': True, 'S11': True, 'S12': True
        }
    
    async def is_risk_type_enabled(self, user_id: str, risk_type: str) -> bool:
        """检查指定风险类型是否启用"""
        config = await self.get_user_risk_config(user_id)
        return config.get(risk_type, True)  # 默认启用
    
    async def invalidate_user_cache(self, user_id: str):
        """使指定用户的缓存失效"""
        async with self._lock:
            if user_id in self._cache:
                del self._cache[user_id]
            if user_id in self._cache_timestamps:
                del self._cache_timestamps[user_id]
            logger.info(f"Invalidated risk config cache for user {user_id}")
    
    async def clear_cache(self):
        """清空所有缓存"""
        async with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("Cleared all risk config cache")

# 全局实例
risk_config_cache = RiskConfigCache()