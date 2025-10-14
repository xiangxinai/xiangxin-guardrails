#!/usr/bin/env python3
"""
数据库迁移执行脚本
用于新用户首次启动时执行所有必要的数据库迁移
"""

import asyncio
import asyncpg
import os
import sys
from pathlib import Path
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

# 数据库迁移文件按执行顺序排序
MIGRATION_FILES = [
    # 基础表结构（早期的迁移）
    "rename_users_to_tenants.sql",
    "add_confidence_thresholds.sql",
    "add_confidence_to_detection_results.sql",
    "add_confidence_trigger_level.sql",
    "add_confidence_trigger_level_proxy.sql",
    "add_stream_chunk_size.sql",
    "add_stream_chunk_size_to_proxy.sql",
    "add_is_global_to_knowledge_bases.sql",
    "simplify_proxy_models.sql",

    # 数据安全相关
    "add_data_security_fields.sql",
    "add_data_security_tables.sql",

    # 多模态相关
    "add_multimodal_fields.sql",

    # 封禁策略相关
    "add_ban_policy_tables.sql",

    # 字段长度优化
    "update_field_lengths.sql",

    # 清理和国际化
    "cleanup_old_tables.sql",
    "migrate_to_english_fields.sql",
]

async def execute_migration_file(connection, migration_file):
    """执行单个迁移文件"""
    migration_path = Path(__file__).parent / "migrations" / migration_file

    if not migration_path.exists():
        logger.warning(f"Migration file not found: {migration_file}")
        return False

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 分割SQL语句（简单的以分号分割，可能需要更复杂的解析器）
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

        for statement in statements:
            if statement:
                await connection.execute(statement)

        logger.info(f"Executed migration: {migration_file}")
        return True

    except Exception as e:
        logger.error(f"Failed to execute migration {migration_file}: {e}")
        return False

async def create_migration_tracking_table(connection):
    """创建迁移跟踪表"""
    try:
        await connection.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                migration_name VARCHAR(255) UNIQUE NOT NULL,
                executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                execution_time_ms INTEGER
            )
        """)
        logger.info("Migration tracking table created/verified")
    except Exception as e:
        logger.error(f"Failed to create migration tracking table: {e}")
        raise

async def is_migration_executed(connection, migration_name):
    """检查迁移是否已执行"""
    try:
        result = await connection.fetchval(
            "SELECT 1 FROM migration_history WHERE migration_name = $1",
            migration_name
        )
        return result is not None
    except Exception as e:
        logger.warning(f"Failed to check migration status for {migration_name}: {e}")
        return False

async def mark_migration_executed(connection, migration_name, execution_time_ms):
    """标记迁移为已执行"""
    try:
        await connection.execute(
            "INSERT INTO migration_history (migration_name, execution_time_ms) VALUES ($1, $2)",
            migration_name, execution_time_ms
        )
    except Exception as e:
        logger.warning(f"Failed to mark migration {migration_name} as executed: {e}")

async def reset_database_if_needed(connection):
    """如果需要，重置数据库"""
    if not settings.reset_database_on_startup:
        return

    try:
        logger.info("Resetting database (DROP ALL TABLES)...")

        # 获取所有表名并删除
        tables = await connection.fetch("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename != 'migration_history'
        """)

        for table in tables:
            await connection.execute(f'DROP TABLE IF EXISTS "{table["tablename"]}" CASCADE')

        logger.info("Database reset completed")

    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise

async def run_migrations():
    """运行所有迁移"""
    # 解析数据库连接信息
    db_url = settings.database_url.replace("postgresql://", "")
    user_pass, host_db = db_url.split("@")
    user, password = user_pass.split(":")
    host_port, db_name = host_db.split("/")
    host, port = host_port.split(":")

    try:
        # 连接到数据库
        connection = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=db_name
        )

        logger.info(f"Connected to database: {db_name}")

        # 重置数据库（如果需要）
        await reset_database_if_needed(connection)

        # 创建迁移跟踪表
        await create_migration_tracking_table(connection)

        # 执行迁移
        executed_count = 0
        for migration_file in MIGRATION_FILES:
            if not await is_migration_executed(connection, migration_file):
                import time
                start_time = time.time()

                success = await execute_migration_file(connection, migration_file)

                execution_time = int((time.time() - start_time) * 1000)

                if success:
                    await mark_migration_executed(connection, migration_file, execution_time)
                    executed_count += 1
                else:
                    logger.error(f"Migration failed: {migration_file}")
                    break
            else:
                logger.debug(f"Migration already executed: {migration_file}")

        logger.info(f"Migration process completed. Executed {executed_count} new migrations.")

        await connection.close()

    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        sys.exit(1)

async def main():
    """主函数"""
    logger.info("Starting database migration process...")

    try:
        await run_migrations()
        logger.info("Database migration process completed successfully!")
    except Exception as e:
        logger.error(f"Migration process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())