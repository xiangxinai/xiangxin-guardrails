import time
import asyncio
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text, select, update
from database.models import TenantRateLimit, TenantRateLimitCounter, Tenant
from utils.logger import setup_logger

logger = setup_logger()

class PostgreSQLRateLimiter:
    """基于PostgreSQL的跨进程限速器"""

    def __init__(self):
        # 本地缓存租户限速配置 {tenant_id: requests_per_second}
        self._rate_limits: Dict[str, int] = {}
        # 本地缓存租户当前计数（用于快速预检查）{tenant_id: (count, window_start_time)}
        self._local_cache: Dict[str, tuple] = {}
        # 配置缓存更新时间
        self._cache_update_time = 0
        self._cache_ttl = 30  # 30秒缓存配置
        self._local_cache_ttl = 0.5  # 本地计数缓存500ms，减少DB查询
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, tenant_id: str, db: Session) -> bool:
        """检查租户是否允许请求（跨进程安全）

        注意：为保持向后兼容，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            # 更新配置缓存
            await self._update_config_cache_if_needed(db)

            # 获取租户限速配置
            rate_limit = self._rate_limits.get(tenant_id, 1)  # 默认每秒1个请求

            # 0表示无限制
            if rate_limit == 0:
                return True

            # 先检查本地缓存，快速判断是否明显超限
            if await self._quick_local_check(tenant_id, rate_limit):
                # 本地缓存显示可能超限，需要精确的数据库检查
                return await self._db_rate_limit_check(tenant_id, rate_limit, db)
            else:
                # 本地缓存显示安全范围内，直接进行数据库原子操作
                return await self._db_rate_limit_check(tenant_id, rate_limit, db)

        except Exception as e:
            logger.error(f"Rate limit check failed for tenant {tenant_id}: {e}")
            # 发生错误时允许通过，避免影响服务
            return True
    
    async def _quick_local_check(self, tenant_id: str, rate_limit: int) -> bool:
        """快速本地缓存检查（不准确但高效）"""
        current_time = time.time()
        cache_entry = self._local_cache.get(tenant_id)

        if not cache_entry:
            return False  # 没有缓存，需要DB检查

        count, window_start = cache_entry

        # 检查缓存是否过期
        if current_time - window_start > self._local_cache_ttl:
            return False  # 缓存过期，需要DB检查

        # 如果本地计数接近限制，返回True表示需要精确检查
        return count >= rate_limit * 0.8  # 达到80%时触发精确检查
    
    async def _db_rate_limit_check(self, tenant_id: str, rate_limit: int, db: Session) -> bool:
        """数据库原子限速检查和更新"""
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)
            current_time = datetime.now()

            # 使用数据库原子操作进行限速检查和更新
            result = db.execute(text("""
                INSERT INTO tenant_rate_limit_counters (tenant_id, current_count, window_start, last_updated)
                VALUES (:tenant_id, 1, :current_time, :current_time)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    current_count = CASE
                        WHEN tenant_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                        THEN 1
                        ELSE tenant_rate_limit_counters.current_count + 1
                    END,
                    window_start = CASE
                        WHEN tenant_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                        THEN :current_time
                        ELSE tenant_rate_limit_counters.window_start
                    END,
                    last_updated = :current_time
                WHERE tenant_rate_limit_counters.current_count < :rate_limit
                   OR tenant_rate_limit_counters.window_start < :current_time - INTERVAL '1 second'
                RETURNING current_count, window_start
            """), {
                "tenant_id": tenant_uuid,
                "current_time": current_time,
                "rate_limit": rate_limit
            })

            row = result.fetchone()

            if row:
                # 请求被允许，更新本地缓存
                self._local_cache[tenant_id] = (row[0], time.time())
                logger.debug(f"Rate limit allowed for tenant {tenant_id}: {row[0]}/{rate_limit}")
                db.commit()
                return True
            else:
                # 请求被限制
                # 获取当前计数用于日志记录
                counter_result = db.execute(text("""
                    SELECT current_count FROM tenant_rate_limit_counters WHERE tenant_id = :tenant_id
                """), {"tenant_id": tenant_uuid})
                counter_row = counter_result.fetchone()
                current_count = counter_row[0] if counter_row else 0

                logger.warning(f"Rate limit exceeded for tenant {tenant_id}: {current_count}/{rate_limit}")
                db.rollback()
                return False

        except Exception as e:
            logger.error(f"Database rate limit check failed for tenant {tenant_id}: {e}")
            db.rollback()
            # 数据库错误时允许通过
            return True
    
    async def _update_config_cache_if_needed(self, db: Session):
        """根据需要更新配置缓存"""
        current_time = time.time()
        if current_time - self._cache_update_time > self._cache_ttl:
            try:
                # 查询所有启用的租户限速配置
                rate_limits = db.query(TenantRateLimit).filter(TenantRateLimit.is_active == True).all()

                # 更新缓存
                new_limits = {}
                for limit in rate_limits:
                    new_limits[str(limit.tenant_id)] = limit.requests_per_second

                self._rate_limits = new_limits
                self._cache_update_time = current_time

                logger.debug(f"Rate limit config cache updated with {len(new_limits)} entries")

            except Exception as e:
                logger.error(f"Failed to update rate limit config cache: {e}")
    
    def clear_user_cache(self, tenant_id: str):
        """清除指定租户的缓存

        注意：为保持向后兼容，函数名保持为 clear_user_cache，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        # 清除本地缓存
        if tenant_id in self._local_cache:
            del self._local_cache[tenant_id]

        # 强制下次更新配置缓存
        self._cache_update_time = 0

# 全局限速器实例
rate_limiter = PostgreSQLRateLimiter()

class RateLimitService:
    """限速服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_rate_limit(self, tenant_id: str) -> Optional[TenantRateLimit]:
        """获取租户限速配置

        注意：为保持向后兼容，函数名保持为 get_user_rate_limit，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)
            return self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()
        except Exception as e:
            logger.error(f"Failed to get tenant rate limit for {tenant_id}: {e}")
            return None
    
    def set_user_rate_limit(self, tenant_id: str, requests_per_second: int) -> TenantRateLimit:
        """设置租户限速

        注意：为保持向后兼容，函数名保持为 set_user_rate_limit，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)

            # 检查租户是否存在
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            # 查找现有配置
            rate_limit_config = self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()

            if rate_limit_config:
                # 更新现有配置
                rate_limit_config.requests_per_second = requests_per_second
                rate_limit_config.is_active = True
                rate_limit_config.updated_at = datetime.now()
            else:
                # 创建新配置
                rate_limit_config = TenantRateLimit(
                    tenant_id=tenant_uuid,
                    requests_per_second=requests_per_second,
                    is_active=True
                )
                self.db.add(rate_limit_config)

            self.db.commit()

            # 清除租户缓存，强制重新加载
            rate_limiter.clear_user_cache(tenant_id)

            logger.info(f"Set rate limit for tenant {tenant_id}: {requests_per_second} rps")
            return rate_limit_config

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set tenant rate limit for {tenant_id}: {e}")
            raise
    
    def disable_user_rate_limit(self, tenant_id: str):
        """禁用租户限速

        注意：为保持向后兼容，函数名保持为 disable_user_rate_limit，参数名保持为 tenant_id，但实际处理的是 tenant_id
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)

            rate_limit_config = self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()
            if rate_limit_config:
                rate_limit_config.is_active = False
                rate_limit_config.updated_at = datetime.now()
                self.db.commit()

                # 清除租户缓存
                rate_limiter.clear_user_cache(tenant_id)

                logger.info(f"Disabled rate limit for tenant {tenant_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to disable tenant rate limit for {tenant_id}: {e}")
            raise
    
    def list_user_rate_limits(self, skip: int = 0, limit: int = 100):
        """列出所有租户限速配置

        注意：为保持向后兼容，函数名保持为 list_user_rate_limits
        """
        return (
            self.db.query(TenantRateLimit)
            .join(Tenant, TenantRateLimit.tenant_id == Tenant.id)
            .filter(TenantRateLimit.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )