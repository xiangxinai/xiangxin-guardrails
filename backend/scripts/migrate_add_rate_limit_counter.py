#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加用户实时限速计数器表
"""
import sys
import os

# 添加项目根路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from database.connection import get_db_session, engine
from database.models import UserRateLimitCounter
from utils.logger import setup_logger

logger = setup_logger()

def create_rate_limit_counter_table():
    """创建用户实时限速计数器表"""
    try:
        # 创建表
        UserRateLimitCounter.__table__.create(engine, checkfirst=True)
        logger.info("Successfully created user_rate_limit_counters table")
        
        # 创建索引（确保性能）
        with engine.connect() as conn:
            # 创建复合索引用于快速查询和更新
            try:
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_rate_counter_user_window 
                    ON tenant_rate_limit_counters(tenant_id, window_start);
                """))
                logger.info("Successfully created index idx_rate_counter_user_window")
            except Exception as e:
                logger.warning(f"Index creation might have failed (could be normal): {e}")
            
            conn.commit()
        
        logger.info("Rate limit counter table migration completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to create rate limit counter table: {e}")
        raise

def main():
    """执行迁移"""
    logger.info("Starting rate limit counter table migration...")
    
    try:
        create_rate_limit_counter_table()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()