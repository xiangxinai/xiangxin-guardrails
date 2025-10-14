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
    """Cross-process rate limiter based on PostgreSQL"""

    def __init__(self):
        # Local cache of tenant rate limits {tenant_id: requests_per_second}
        self._rate_limits: Dict[str, int] = {}
        # Local cache of tenant current count (for quick pre-check) {tenant_id: (count, window_start_time)}
        self._local_cache: Dict[str, tuple] = {}
        # Configuration cache update time
        self._cache_update_time = 0
        self._cache_ttl = 30  # 30 seconds cache configuration
        self._local_cache_ttl = 0.5  # Local count cache 500ms, reduce DB queries
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, tenant_id: str, db: Session) -> bool:
        """Check if tenant is allowed to request (cross-process safe)

        Note: For backward compatibility, parameter name remains tenant_id, but tenant_id is actually processed
        """
        tenant_id = tenant_id  # 为保持向后兼容，内部使用 tenant_id
        try:
            # Update configuration cache
            await self._update_config_cache_if_needed(db)

            # Get tenant rate limit configuration
            rate_limit = self._rate_limits.get(tenant_id, 1)  # 默认每秒1个请求

            # 0 means no limit
            if rate_limit == 0:
                return True

            # First check local cache, quickly determine if it is obviously over limit
            if await self._quick_local_check(tenant_id, rate_limit):
                # Local cache shows possible over limit, need precise database check
                return await self._db_rate_limit_check(tenant_id, rate_limit, db)
            else:
                # Local cache shows within safe range, directly perform database atomic operation
                return await self._db_rate_limit_check(tenant_id, rate_limit, db)

        except Exception as e:
            logger.error(f"Rate limit check failed for tenant {tenant_id}: {e}")
            # Allow through when error occurs, avoid affecting service
            return True
    
    async def _quick_local_check(self, tenant_id: str, rate_limit: int) -> bool:
        """Quick local cache check (not accurate but efficient)"""
        current_time = time.time()
        cache_entry = self._local_cache.get(tenant_id)

        if not cache_entry:
            return False  # No cache, need DB check

        count, window_start = cache_entry

        # Check if cache is expired
        if current_time - window_start > self._local_cache_ttl:
            return False  # Cache expired, need DB check

        # If local count is approaching limit, return True to trigger precise check
        return count >= rate_limit * 0.8  # Trigger precise check when reaching 80%
    
    async def _db_rate_limit_check(self, tenant_id: str, rate_limit: int, db: Session) -> bool:
        """Database atomic rate limit check and update"""
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)
            current_time = datetime.now()

            # Use database atomic operation for rate limit check and update
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
                # Request allowed, update local cache
                self._local_cache[tenant_id] = (row[0], time.time())
                logger.debug(f"Rate limit allowed for tenant {tenant_id}: {row[0]}/{rate_limit}")
                db.commit()
                return True
            else:
                # Request limited
                # Get current count for logging
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
            # Allow through when database error occurs
            return True
    
    async def _update_config_cache_if_needed(self, db: Session):
        """Update configuration cache if needed"""
        current_time = time.time()
        if current_time - self._cache_update_time > self._cache_ttl:
            try:
                # Query all enabled tenant rate limit configurations
                rate_limits = db.query(TenantRateLimit).filter(TenantRateLimit.is_active == True).all()

                # Update cache
                new_limits = {}
                for limit in rate_limits:
                    new_limits[str(limit.tenant_id)] = limit.requests_per_second

                self._rate_limits = new_limits
                self._cache_update_time = current_time

                logger.debug(f"Rate limit config cache updated with {len(new_limits)} entries")

            except Exception as e:
                logger.error(f"Failed to update rate limit config cache: {e}")
    
    def clear_user_cache(self, tenant_id: str):
        """Clear cache for specified tenant

        Note: For backward compatibility, function name remains clear_user_cache, parameter name remains tenant_id, but tenant_id is actually processed
        """
        tenant_id = tenant_id  # For backward compatibility, internally use tenant_id
        # Clear local cache
        if tenant_id in self._local_cache:
            del self._local_cache[tenant_id]

        # Force next update configuration cache
        self._cache_update_time = 0

# Global rate limiter instance
rate_limiter = PostgreSQLRateLimiter()

class RateLimitService:
    """Rate limit service"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_rate_limit(self, tenant_id: str) -> Optional[TenantRateLimit]:
        """Get tenant rate limit configuration

        Note: For backward compatibility, function name remains get_user_rate_limit, parameter name remains tenant_id, but tenant_id is actually processed
        """
        tenant_id = tenant_id  # For backward compatibility, internally use tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)
            return self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()
        except Exception as e:
            logger.error(f"Failed to get tenant rate limit for {tenant_id}: {e}")
            return None
    
    def set_user_rate_limit(self, tenant_id: str, requests_per_second: int) -> TenantRateLimit:
        """Set tenant rate limit

        Note: For backward compatibility, function name remains set_user_rate_limit, parameter name remains tenant_id, but tenant_id is actually processed
        """
        tenant_id = tenant_id  # For backward compatibility, internally use tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)

            # Check if tenant exists
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_uuid).first()
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            # Find existing configuration
            rate_limit_config = self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()

            if rate_limit_config:
            # Update existing configuration
                rate_limit_config.requests_per_second = requests_per_second
                rate_limit_config.is_active = True
                rate_limit_config.updated_at = datetime.now()
            else:
                # Create new configuration
                rate_limit_config = TenantRateLimit(
                    tenant_id=tenant_uuid,
                    requests_per_second=requests_per_second,
                    is_active=True
                )
                self.db.add(rate_limit_config)

            self.db.commit()

            # Clear tenant cache, force reload
            rate_limiter.clear_user_cache(tenant_id)

            logger.info(f"Set rate limit for tenant {tenant_id}: {requests_per_second} rps")
            return rate_limit_config

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to set tenant rate limit for {tenant_id}: {e}")
            raise
    
    def disable_user_rate_limit(self, tenant_id: str):
        """Disable tenant rate limit

        Note: For backward compatibility, function name remains disable_user_rate_limit, parameter name remains tenant_id, but tenant_id is actually processed
        """
        tenant_id = tenant_id  # For backward compatibility, internally use tenant_id
        try:
            from uuid import UUID
            tenant_uuid = UUID(tenant_id)

            rate_limit_config = self.db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant_uuid).first()
            if rate_limit_config:
                rate_limit_config.is_active = False
                rate_limit_config.updated_at = datetime.now()
                self.db.commit()

                # Clear tenant cache
                rate_limiter.clear_user_cache(tenant_id)

                logger.info(f"Disabled rate limit for tenant {tenant_id}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to disable tenant rate limit for {tenant_id}: {e}")
            raise
    
    def list_user_rate_limits(self, skip: int = 0, limit: int = 100, search: str = None):
        """List all tenant rate limit configurations

        Note: For backward compatibility, function name remains list_user_rate_limits
        Args:
            skip: Number of records to skip for pagination
            limit: Maximum number of records to return
            search: Search string to filter by tenant email
        """
        query = (
            self.db.query(TenantRateLimit)
            .join(Tenant, TenantRateLimit.tenant_id == Tenant.id)
            .filter(TenantRateLimit.is_active == True)
        )
        
        # Add search filter if provided
        if search:
            query = query.filter(Tenant.email.ilike(f'%{search}%'))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        results = query.offset(skip).limit(limit).all()
        
        return results, total