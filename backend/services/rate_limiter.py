import time
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, select, update
from database.models import UserRateLimit, UserRateLimitCounter, User
from utils.logger import setup_logger

logger = setup_logger()

class PostgreSQLRateLimiter:
    """基于PostgreSQL的跨进程限速器"""
    
    def __init__(self):
        # 本地缓存用户限速配置 {user_id: requests_per_second}
        self._rate_limits: Dict[str, int] = {}
        # 本地缓存用户当前计数（用于快速预检查）{user_id: (count, window_start_time)}
        self._local_cache: Dict[str, tuple] = {}
        # 配置缓存更新时间
        self._cache_update_time = 0
        self._cache_ttl = 30  # 30秒缓存配置
        self._local_cache_ttl = 0.5  # 本地计数缓存500ms，减少DB查询
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, user_id: str, db: Session) -> bool:
        """检查用户是否允许请求（跨进程安全）"""
        try:
            # 更新配置缓存
            await self._update_config_cache_if_needed(db)
            
            # 获取用户限速配置
            rate_limit = self._rate_limits.get(user_id, 1)  # 默认每秒1个请求
            
            # 0表示无限制
            if rate_limit == 0:
                return True
            
            # 先检查本地缓存，快速判断是否明显超限
            if await self._quick_local_check(user_id, rate_limit):
                # 本地缓存显示可能超限，需要精确的数据库检查
                return await self._db_rate_limit_check(user_id, rate_limit, db)
            else:
                # 本地缓存显示安全范围内，直接进行数据库原子操作
                return await self._db_rate_limit_check(user_id, rate_limit, db)
        
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {e}")
            # 发生错误时允许通过，避免影响服务
            return True
    
    async def _quick_local_check(self, user_id: str, rate_limit: int) -> bool:
        """快速本地缓存检查（不准确但高效）"""
        current_time = time.time()
        cache_entry = self._local_cache.get(user_id)
        
        if not cache_entry:
            return False  # 没有缓存，需要DB检查
        
        count, window_start = cache_entry
        
        # 检查缓存是否过期
        if current_time - window_start > self._local_cache_ttl:
            return False  # 缓存过期，需要DB检查
        
        # 如果本地计数接近限制，返回True表示需要精确检查
        return count >= rate_limit * 0.8  # 达到80%时触发精确检查
    
    async def _db_rate_limit_check(self, user_id: str, rate_limit: int, db: Session) -> bool:
        """数据库原子限速检查和更新"""
        try:
            from uuid import UUID
            user_uuid = UUID(user_id)
            current_time = datetime.now()
            
            # 使用数据库原子操作进行限速检查和更新
            result = db.execute(text("""
                INSERT INTO user_rate_limit_counters (user_id, current_count, window_start, last_updated)
                VALUES (:user_id, 1, :current_time, :current_time)
                ON CONFLICT (user_id) DO UPDATE SET
                    current_count = CASE 
                        WHEN user_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                        THEN 1
                        ELSE user_rate_limit_counters.current_count + 1
                    END,
                    window_start = CASE 
                        WHEN user_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                        THEN :current_time
                        ELSE user_rate_limit_counters.window_start
                    END,
                    last_updated = :current_time
                WHERE user_rate_limit_counters.current_count < :rate_limit 
                   OR user_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                RETURNING current_count, window_start
            """), {
                "user_id": user_uuid,
                "current_time": current_time,
                "rate_limit": rate_limit
            })
            
            row = result.fetchone()
            
            if row:
                # 请求被允许，更新本地缓存
                self._local_cache[user_id] = (row[0], time.time())
                logger.debug(f"Rate limit allowed for user {user_id}: {row[0]}/{rate_limit}")
                db.commit()
                return True
            else:
                # 请求被限制
                # 获取当前计数用于日志记录
                counter_result = db.execute(text("""
                    SELECT current_count FROM user_rate_limit_counters WHERE user_id = :user_id
                """), {"user_id": user_uuid})
                counter_row = counter_result.fetchone()
                current_count = counter_row[0] if counter_row else 0
                
                logger.warning(f"Rate limit exceeded for user {user_id}: {current_count}/{rate_limit}")
                db.rollback()
                return False
                
        except Exception as e:
            logger.error(f"Database rate limit check failed for user {user_id}: {e}")
            db.rollback()
            # 数据库错误时允许通过
            return True
    
    async def _update_config_cache_if_needed(self, db: Session):
        """根据需要更新配置缓存"""
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
                
                logger.debug(f"Rate limit config cache updated with {len(new_limits)} entries")
                
            except Exception as e:
                logger.error(f"Failed to update rate limit config cache: {e}")
    
    def clear_user_cache(self, user_id: str):
        """清除指定用户的缓存"""
        # 清除本地缓存
        if user_id in self._local_cache:
            del self._local_cache[user_id]
        
        # 强制下次更新配置缓存
        self._cache_update_time = 0

# 全局限速器实例
rate_limiter = PostgreSQLRateLimiter()

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