"""
并发限制中间件
基于asyncio.Semaphore实现服务级别的并发控制，防止资源耗尽
"""
import asyncio
import time
from typing import Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from utils.logger import setup_logger

logger = setup_logger()

class ConcurrentLimitMiddleware(BaseHTTPMiddleware):
    """并发限制中间件"""
    
    # 全局信号量字典，按服务类型存储
    _semaphores: Dict[str, asyncio.Semaphore] = {}
    _stats: Dict[str, Dict[str, int]] = {}
    
    def __init__(self, app, service_type: str, max_concurrent: int):
        """
        初始化并发限制中间件
        
        Args:
            app: FastAPI应用
            service_type: 服务类型 (admin/detection/proxy)
            max_concurrent: 最大并发请求数
        """
        super().__init__(app)
        self.service_type = service_type
        self.max_concurrent = max_concurrent
        
        # 创建服务级信号量
        if service_type not in self._semaphores:
            self._semaphores[service_type] = asyncio.Semaphore(max_concurrent)
            self._stats[service_type] = {
                'current_requests': 0,
                'total_requests': 0,
                'rejected_requests': 0,
                'max_concurrent_reached': 0
            }
            logger.info(f"Concurrent limit middleware initialized for {service_type}: max_concurrent={max_concurrent}")
    
    async def dispatch(self, request: Request, call_next):
        """处理请求的并发控制"""
        semaphore = self._semaphores[self.service_type]
        stats = self._stats[self.service_type]
        
        # 更新统计
        stats['total_requests'] += 1
        
        # 尝试获取信号量
        acquired = False
        try:
            # 非阻塞方式尝试获取信号量
            acquired = semaphore.locked() == False and await self._try_acquire(semaphore)
            
            if not acquired:
                # 并发数已达上限，返回429错误
                stats['rejected_requests'] += 1
                current_concurrent = self.max_concurrent - (semaphore._value if hasattr(semaphore, '_value') else 0)
                
                logger.warning(
                    f"Concurrent limit reached for {self.service_type} service. "
                    f"Current: {current_concurrent}/{self.max_concurrent}, "
                    f"Path: {request.url.path}"
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "message": f"Service temporarily overloaded. Maximum {self.max_concurrent} concurrent requests allowed.",
                            "type": "service_overloaded",
                            "code": 429,
                            "service": self.service_type,
                            "retry_after": 1
                        }
                    },
                    headers={"Retry-After": "1"}
                )
            
            # 更新并发统计
            stats['current_requests'] += 1
            current_concurrent = stats['current_requests']
            if current_concurrent > stats['max_concurrent_reached']:
                stats['max_concurrent_reached'] = current_concurrent
            
            # 处理请求
            start_time = time.time()
            response = await call_next(request)
            end_time = time.time()
            
            # 添加性能头信息
            response.headers["X-Service-Type"] = self.service_type
            response.headers["X-Concurrent-Limit"] = str(self.max_concurrent)
            response.headers["X-Current-Concurrent"] = str(current_concurrent)
            response.headers["X-Processing-Time"] = f"{(end_time - start_time) * 1000:.2f}ms"
            
            return response
            
        finally:
            if acquired:
                # 释放信号量
                semaphore.release()
                stats['current_requests'] -= 1
    
    async def _try_acquire(self, semaphore: asyncio.Semaphore, timeout: float = 0.001) -> bool:
        """
        非阻塞尝试获取信号量
        
        Args:
            semaphore: 异步信号量
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功获取
        """
        try:
            await asyncio.wait_for(semaphore.acquire(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    @classmethod
    def get_stats(cls, service_type: str) -> Optional[Dict[str, int]]:
        """获取服务并发统计信息"""
        return cls._stats.get(service_type)
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, int]]:
        """获取所有服务的并发统计信息"""
        return cls._stats.copy()
    
    @classmethod
    def reset_stats(cls, service_type: str = None):
        """重置统计信息"""
        if service_type:
            if service_type in cls._stats:
                stats = cls._stats[service_type]
                stats.update({
                    'total_requests': 0,
                    'rejected_requests': 0,
                    'max_concurrent_reached': 0
                })
                logger.info(f"Reset concurrent stats for {service_type}")
        else:
            for service in cls._stats:
                cls.reset_stats(service)
            logger.info("Reset concurrent stats for all services")