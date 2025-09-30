#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加敏感度阈值字段到 risk_type_config 表
为 risk_type_config 表添加敏感度阈值相关字段：
- high_sensitivity_threshold: 高敏感度阈值 (默认0.40)
- medium_sensitivity_threshold: 中敏感度阈值 (默认0.60)
- low_sensitivity_threshold: 低敏感度阈值 (默认0.95)
- sensitivity_trigger_level: 触发检测命中的最低敏感度等级 (默认"medium")
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

def migrate():
    """执行数据库迁移"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.database_url)

        logger.info("开始数据库迁移：添加敏感度阈值字段到 risk_type_config 表...")

        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()

            try:
                # 检查哪些字段已存在
                logger.info("检查现有字段...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'risk_type_config' 
                    AND column_name IN ('high_sensitivity_threshold', 'medium_sensitivity_threshold', 'low_sensitivity_threshold', 'sensitivity_trigger_level')
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                logger.info(f"现有敏感度字段: {existing_columns}")

                # 1. 添加高敏感度阈值字段
                if 'high_sensitivity_threshold' not in existing_columns:
                    logger.info("添加 high_sensitivity_threshold 字段...")
                    conn.execute(text("""
                        ALTER TABLE risk_type_config
                        ADD COLUMN high_sensitivity_threshold FLOAT DEFAULT 0.40
                    """))
                else:
                    logger.info("high_sensitivity_threshold 字段已存在，跳过")

                # 2. 添加中敏感度阈值字段
                if 'medium_sensitivity_threshold' not in existing_columns:
                    logger.info("添加 medium_sensitivity_threshold 字段...")
                    conn.execute(text("""
                        ALTER TABLE risk_type_config
                        ADD COLUMN medium_sensitivity_threshold FLOAT DEFAULT 0.60
                    """))
                else:
                    logger.info("medium_sensitivity_threshold 字段已存在，跳过")

                # 3. 添加低敏感度阈值字段
                if 'low_sensitivity_threshold' not in existing_columns:
                    logger.info("添加 low_sensitivity_threshold 字段...")
                    conn.execute(text("""
                        ALTER TABLE risk_type_config
                        ADD COLUMN low_sensitivity_threshold FLOAT DEFAULT 0.95
                    """))
                else:
                    logger.info("low_sensitivity_threshold 字段已存在，跳过")

                # 4. 添加敏感度触发等级字段
                if 'sensitivity_trigger_level' not in existing_columns:
                    logger.info("添加 sensitivity_trigger_level 字段...")
                    conn.execute(text("""
                        ALTER TABLE risk_type_config
                        ADD COLUMN sensitivity_trigger_level VARCHAR(10) DEFAULT 'medium'
                    """))
                else:
                    logger.info("sensitivity_trigger_level 字段已存在，跳过")

                # 5. 更新现有记录的默认值
                logger.info("更新现有记录的默认值...")
                conn.execute(text("""
                    UPDATE risk_type_config
                    SET 
                        high_sensitivity_threshold = COALESCE(high_sensitivity_threshold, 0.40),
                        medium_sensitivity_threshold = COALESCE(medium_sensitivity_threshold, 0.60),
                        low_sensitivity_threshold = COALESCE(low_sensitivity_threshold, 0.95),
                        sensitivity_trigger_level = COALESCE(sensitivity_trigger_level, 'medium')
                    WHERE high_sensitivity_threshold IS NULL 
                       OR medium_sensitivity_threshold IS NULL 
                       OR low_sensitivity_threshold IS NULL 
                       OR sensitivity_trigger_level IS NULL
                """))

                # 6. 验证迁移结果
                logger.info("验证迁移结果...")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'risk_type_config' 
                    AND column_name IN ('high_sensitivity_threshold', 'medium_sensitivity_threshold', 'low_sensitivity_threshold', 'sensitivity_trigger_level')
                    ORDER BY column_name
                """))
                
                migrated_columns = result.fetchall()
                logger.info("迁移后的敏感度字段:")
                for col in migrated_columns:
                    logger.info(f"  {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")

                # 检查现有记录数量
                result = conn.execute(text("SELECT COUNT(*) FROM risk_type_config"))
                record_count = result.scalar()
                logger.info(f"risk_type_config 表中共有 {record_count} 条记录")

                # 提交事务
                trans.commit()
                logger.info("✅ 数据库迁移完成！")

                # 显示最终表结构
                logger.info("最终表结构:")
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'risk_type_config' ORDER BY ordinal_position"))
                all_columns = [row[0] for row in result.fetchall()]
                for i, col in enumerate(all_columns, 1):
                    logger.info(f"  {i:2d}. {col}")

            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"❌ 迁移失败，已回滚: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ 数据库迁移错误: {e}")
        sys.exit(1)

def check_migration_needed():
    """检查是否需要迁移"""
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'risk_type_config' 
                AND column_name IN ('high_sensitivity_threshold', 'medium_sensitivity_threshold', 'low_sensitivity_threshold', 'sensitivity_trigger_level')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            required_columns = ['high_sensitivity_threshold', 'medium_sensitivity_threshold', 'low_sensitivity_threshold', 'sensitivity_trigger_level']
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                logger.info(f"需要迁移，缺失敏感度字段: {missing_columns}")
                return True
            else:
                logger.info("所有敏感度字段都已存在，无需迁移")
                return False
                
    except Exception as e:
        logger.error(f"检查迁移状态失败: {e}")
        return True  # 如果检查失败，假设需要迁移

if __name__ == "__main__":
    logger.info("象信AI安全护栏平台 - risk_type_config 敏感度字段迁移")
    logger.info("=" * 60)
    
    if check_migration_needed():
        migrate()
    else:
        logger.info("✅ 数据库已是最新版本，无需迁移")
