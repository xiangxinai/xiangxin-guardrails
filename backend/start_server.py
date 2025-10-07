#!/usr/bin/env python3
"""
Start server script
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
        workers=settings.uvicorn_workers if not settings.debug else 1
    )