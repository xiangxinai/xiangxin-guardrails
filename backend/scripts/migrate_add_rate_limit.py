#!/usr/bin/env python3
"""
数据库迁移脚本：添加用户限速表
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import engine, SessionLocal
from database.models import Base, TenantRateLimit, Tenant
from sqlalchemy import text
from utils.logger import setup_logger

logger = setup_logger()

def migrate_add_rate_limit_table():
    """添加租户限速表"""
    try:
        # 检查表是否已存在
        with engine.connect() as conn:
            result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenant_rate_limits')"))
            table_exists = result.scalar()

            if table_exists:
                logger.info("tenant_rate_limits table already exists, skipping migration")
                return True

        # 创建新表
        logger.info("Creating tenant_rate_limits table...")
        TenantRateLimit.__table__.create(engine)

        logger.info("tenant_rate_limits table created successfully")

        # 为现有租户创建默认限速配置（每秒1个请求）
        db = SessionLocal()
        try:
            tenants = db.query(Tenant).all()
            logger.info(f"Setting default rate limits for {len(tenants)} tenants...")

            for tenant in tenants:
                # 检查是否已有限速配置
                existing_limit = db.query(TenantRateLimit).filter(TenantRateLimit.tenant_id == tenant.id).first()
                if not existing_limit:
                    rate_limit = TenantRateLimit(
                        tenant_id=tenant.id,
                        requests_per_second=1,  # 默认每秒1个请求
                        is_active=True
                    )
                    db.add(rate_limit)
            
            db.commit()
            logger.info("Default rate limits created successfully")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create default rate limits: {e}")
            raise
        finally:
            db.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting rate limit table migration...")
    success = migrate_add_rate_limit_table()
    
    if success:
        logger.info("Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("Migration failed")
        sys.exit(1)