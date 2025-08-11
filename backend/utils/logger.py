import logging
import os
from datetime import datetime
from pathlib import Path
from config import settings

def setup_logger():
    """设置日志记录器"""
    # 获取或创建日志记录器
    logger = logging.getLogger("xiangxin_guardrails")
    
    # 如果已经配置过处理器，直接返回
    if logger.handlers:
        return logger
    
    # 创建日志目录
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建文件处理器
    log_file = log_dir / f"guardrails_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置日志记录器
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger