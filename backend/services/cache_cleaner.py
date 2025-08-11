import asyncio
from datetime import datetime, timedelta
from utils.auth_cache import auth_cache
from services.rate_limiter import rate_limiter
from services.keyword_cache import keyword_cache
from utils.logger import setup_logger

logger = setup_logger()

class CacheCleaner:
    """缓存清理服务"""
    
    def __init__(self):
        self._cleanup_task = None
        self._running = False
    
    async def start(self):
        """启动缓存清理服务"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cache cleaner service started")
    
    async def stop(self):
        """停止缓存清理服务"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache cleaner service stopped")
    
    async def _cleanup_loop(self):
        """清理循环"""
        while self._running:
            try:
                # 清理过期的认证缓存
                auth_cache.clear_expired()
                
                # 清理过期的限速记录 (保留最近2分钟的记录)
                current_time = asyncio.get_event_loop().time()
                cutoff_time = current_time - 120  # 2分钟前
                
                # 清理过期的用户请求记录
                expired_users = []
                for user_id, request_deque in rate_limiter._user_requests.items():
                    # 清理过期记录
                    while request_deque and request_deque[0] < cutoff_time:
                        request_deque.popleft()
                    
                    # 如果队列为空且用户超过5分钟没有活动，删除该用户记录
                    if not request_deque:
                        expired_users.append(user_id)
                
                # 删除过期用户记录
                for user_id in expired_users:
                    if user_id in rate_limiter._user_requests:
                        del rate_limiter._user_requests[user_id]
                
                if expired_users:
                    logger.debug(f"Cleaned up {len(expired_users)} inactive user rate limit records")
                
                # 记录缓存统计信息
                auth_cache_size = auth_cache.size()
                rate_limit_users = len(rate_limiter._user_requests)
                keyword_cache_info = keyword_cache.get_cache_info()
                
                if auth_cache_size > 0 or rate_limit_users > 0 or keyword_cache_info['blacklist_keywords'] > 0:
                    logger.debug(f"Cache stats - Auth: {auth_cache_size}, Rate limit users: {rate_limit_users}, Keywords: B{keyword_cache_info['blacklist_keywords']}/W{keyword_cache_info['whitelist_keywords']}")
                
                # 每60秒清理一次
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(60)

# 全局缓存清理服务实例
cache_cleaner = CacheCleaner()