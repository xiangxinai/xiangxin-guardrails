#!/usr/bin/env python3
"""
数据库迁移脚本 - v2.3.0 完整迁移
为 detection_results 表添加版本2.1.0、2.2.0、2.3.0中新增的所有字段：
- sensitivity_level: 敏感度等级
- sensitivity_score: 敏感度分数
- has_image: 是否包含图片
- image_count: 图片数量
- image_paths: 图片路径列表
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

        logger.info("开始数据库迁移：v2.3.0 完整迁移...")

        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()

            try:
                # 检查哪些字段已存在
                logger.info("检查现有字段...")
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'detection_results' 
                    AND column_name IN ('sensitivity_level', 'sensitivity_score', 'has_image', 'image_count', 'image_paths')
                """))
                existing_columns = [row[0] for row in result.fetchall()]
                logger.info(f"现有字段: {existing_columns}")

                # 1. 添加敏感度相关字段 (v2.1.0)
                if 'sensitivity_level' not in existing_columns:
                    logger.info("添加 sensitivity_level 字段...")
                    conn.execute(text("""
                        ALTER TABLE detection_results
                        ADD COLUMN sensitivity_level VARCHAR(10)
                    """))
                else:
                    logger.info("sensitivity_level 字段已存在，跳过")

                if 'sensitivity_score' not in existing_columns:
                    logger.info("添加 sensitivity_score 字段...")
                    conn.execute(text("""
                        ALTER TABLE detection_results
                        ADD COLUMN sensitivity_score FLOAT
                    """))
                else:
                    logger.info("sensitivity_score 字段已存在，跳过")

                # 2. 添加多模态相关字段 (v2.3.0)
                if 'has_image' not in existing_columns:
                    logger.info("添加 has_image 字段...")
                    conn.execute(text("""
                        ALTER TABLE detection_results
                        ADD COLUMN has_image BOOLEAN DEFAULT FALSE
                    """))

                    # 添加索引
                    logger.info("为 has_image 添加索引...")
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_detection_results_has_image
                        ON detection_results(has_image)
                    """))
                else:
                    logger.info("has_image 字段已存在，跳过")

                if 'image_count' not in existing_columns:
                    logger.info("添加 image_count 字段...")
                    conn.execute(text("""
                        ALTER TABLE detection_results
                        ADD COLUMN image_count INTEGER DEFAULT 0
                    """))
                else:
                    logger.info("image_count 字段已存在，跳过")

                if 'image_paths' not in existing_columns:
                    logger.info("添加 image_paths 字段...")
                    conn.execute(text("""
                        ALTER TABLE detection_results
                        ADD COLUMN image_paths JSON
                    """))
                else:
                    logger.info("image_paths 字段已存在，跳过")

                # 3. 更新现有记录的默认值
                logger.info("更新现有记录的默认值...")
                
                # 更新多模态字段默认值
                conn.execute(text("""
                    UPDATE detection_results
                    SET has_image = FALSE, image_count = 0, image_paths = '[]'::json
                    WHERE has_image IS NULL OR image_count IS NULL OR image_paths IS NULL
                """))

                # 4. 验证迁移结果
                logger.info("验证迁移结果...")
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'detection_results' 
                    AND column_name IN ('sensitivity_level', 'sensitivity_score', 'has_image', 'image_count', 'image_paths')
                    ORDER BY column_name
                """))
                
                migrated_columns = result.fetchall()
                logger.info("迁移后的字段:")
                for col in migrated_columns:
                    logger.info(f"  {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")

                # 提交事务
                trans.commit()
                logger.info("✅ 数据库迁移完成！")

                # 显示最终表结构
                logger.info("最终表结构:")
                result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'detection_results' ORDER BY ordinal_position"))
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
                WHERE table_name = 'detection_results' 
                AND column_name IN ('sensitivity_level', 'sensitivity_score', 'has_image', 'image_count', 'image_paths')
            """))
            existing_columns = [row[0] for row in result.fetchall()]
            
            required_columns = ['sensitivity_level', 'sensitivity_score', 'has_image', 'image_count', 'image_paths']
            missing_columns = [col for col in required_columns if col not in existing_columns]
            
            if missing_columns:
                logger.info(f"需要迁移，缺失字段: {missing_columns}")
                return True
            else:
                logger.info("所有字段都已存在，无需迁移")
                return False
                
    except Exception as e:
        logger.error(f"检查迁移状态失败: {e}")
        return True  # 如果检查失败，假设需要迁移

if __name__ == "__main__":
    logger.info("象信AI安全护栏平台 - 数据库迁移 v2.3.0")
    logger.info("=" * 50)
    
    if check_migration_needed():
        migrate()
    else:
        logger.info("✅ 数据库已是最新版本，无需迁移")
