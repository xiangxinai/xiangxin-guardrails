#!/usr/bin/env python3
"""
启动代理服务脚本
"""
import sys
from pathlib import Path

# 确保模块路径
sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"Starting {settings.app_name} Proxy Service...")
    print(f"Port: {settings.proxy_port}")
    print(f"Workers: {settings.proxy_uvicorn_workers}")
    print(f"Debug: {settings.debug}")
    
    uvicorn.run(
        "proxy_service:app",
        host=settings.host,
        port=settings.proxy_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        workers=settings.proxy_uvicorn_workers if not settings.debug else 1,
        access_log=True
    )