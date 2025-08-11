import time
import asyncio
from typing import Dict, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import UserRateLimit, User
from utils.logger import setup_logger

logger = setup_logger()

class InMemoryRateLimiter:
    """高性能内存限速器"""
    
    def __init__(self):
        # 用户限速配置缓存 {user_id: requests_per_second}
        self._rate_limits: Dict[str, int] = {}
        # 用户请求记录 {user_id: deque([timestamp, timestamp, ...])}
        self._user_requests: Dict[str, deque] = defaultdict(lambda: deque())
        # 配置缓存更新时间
        self._cache_update_time = 0
        self._cache_ttl = 60  # 60秒缓存
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, user_id: str, db: Session) -> bool:
        """检查用户是否允许请求"""
        async with self._lock:
            # 更新缓存
            await self._update_cache_if_needed(db)
            
            # 获取用户限速配置
            rate_limit = self._rate_limits.get(user_id, 1)  # 默认每秒1个请求
            
            # 0表示无限制
            if rate_limit == 0:
                return True
                
            current_time = time.time()
            user_requests = self._user_requests[user_id]
            
            # 清理过期的请求记录（1秒前的记录）
            while user_requests and user_requests[0] < current_time - 1.0:
                user_requests.popleft()
            
            # 检查当前1秒内的请求数
            if len(user_requests) >= rate_limit:
                logger.warning(f"Rate limit exceeded for user {user_id}: {len(user_requests)}/{rate_limit}")
                return False
            
            # 记录当前请求
            user_requests.append(current_time)
            return True
    
    async def _update_cache_if_needed(self, db: Session):
        """根据需要更新缓存"""
        current_time = time.time()
        if current_time - self._cache_update_time > self._cache_ttl:
            try:
                # 查询所有启用的用户限速配置
                rate_limits = db.query(UserRateLimit).filter(UserRateLimit.is_active == True).all()
                
                # 更新缓存
                new_limits = {}
                for limit in rate_limits:
                    new_limits[str(limit.user_id)] = limit.requests_per_second
                
                self._rate_limits = new_limits
                self._cache_update_time = current_time
                
                logger.debug(f"Rate limit cache updated with {len(new_limits)} entries")
                
            except Exception as e:
                logger.error(f"Failed to update rate limit cache: {e}")
    
    def clear_user_cache(self, user_id: str):
        """清除指定用户的缓存"""
        if user_id in self._user_requests:
            del self._user_requests[user_id]
        
        # 强制下次更新配置缓存
        self._cache_update_time = 0

# 全局限速器实例
rate_limiter = InMemoryRateLimiter()

class RateLimitService:
    """限速服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_rate_limit(self, user_id: str) -> Optional[UserRateLimit]:
        """获取用户限速配置"""
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            return self.db.query(UserRateLimit).filter(UserRateLimit.user_id == user_uuid).first()
        except Exception as e:
            logger.error(f"Failed to get user rate limit for {user_id}: {e}")
            return None
    
    def set_user_rate_limit(self, user_id: str, requests_per_second: int) -> UserRateLimit:
        """设置用户限速"""
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            
            # 检查用户是否存在
            user = self.db.query(User).filter(User.id == user_uuid).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # 查找现有配置
            rate_limit_config = self.db.query(UserRateLimit).filter(UserRateLimit.user_id == user_uuid).first()
            
            if rate_limit_config:
                # 更新现有配置
                rate_limit_config.requests_per_second = requests_per_second
                rate_limit_config.is_active = True
                rate_limit_config.updated_at = datetime.now()
            else:
                # 创建新配置
                rate_limit_config = UserRateLimit(
                    user_id=user_uuid,
                    requests_per_second=requests_per_second,
                    is_active=True
                )
                self.db.add(rate_limit_config)
            
            self.db.commit()
            
            # 清除用户缓存，强制重新加载
            rate_limiter.clear_user_cache(user_id)
            
            logger.info(f"Set rate limit for user {user_id}: {requests_per_second} rps")
            return rate_limit_config
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set user rate limit for {user_id}: {e}")
            raise
    
    def disable_user_rate_limit(self, user_id: str):
        """禁用用户限速"""
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            
            rate_limit_config = self.db.query(UserRateLimit).filter(UserRateLimit.user_id == user_uuid).first()
            if rate_limit_config:
                rate_limit_config.is_active = False
                rate_limit_config.updated_at = datetime.now()
                self.db.commit()
                
                # 清除用户缓存
                rate_limiter.clear_user_cache(user_id)
                
                logger.info(f"Disabled rate limit for user {user_id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to disable user rate limit for {user_id}: {e}")
            raise
    
    def list_user_rate_limits(self, skip: int = 0, limit: int = 100):
        """列出所有用户限速配置"""
        return (
            self.db.query(UserRateLimit)
            .join(User, UserRateLimit.user_id == User.id)
            .filter(UserRateLimit.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )