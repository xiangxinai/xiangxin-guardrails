#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加图片检测相关字段
为 detection_results 表添加 has_image, image_count, image_paths 字段
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, Column, Boolean, Integer, JSON, text
from sqlalchemy.orm import sessionmaker
from config import settings
from utils.logger import setup_logger

logger = setup_logger()

def migrate():
    """执行数据库迁移"""
    try:
        # 创建数据库引擎
        engine = create_engine(settings.database_url)

        logger.info("开始数据库迁移：添加图片检测相关字段...")

        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()

            try:
                # 添加 has_image 字段
                logger.info("添加 has_image 字段...")
                conn.execute(text("""
                    ALTER TABLE detection_results
                    ADD COLUMN IF NOT EXISTS has_image BOOLEAN DEFAULT FALSE
                """))

                # 添加索引
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_detection_results_has_image
                    ON detection_results(has_image)
                """))

                # 添加 image_count 字段
                logger.info("添加 image_count 字段...")
                conn.execute(text("""
                    ALTER TABLE detection_results
                    ADD COLUMN IF NOT EXISTS image_count INTEGER DEFAULT 0
                """))

                # 添加 image_paths 字段
                logger.info("添加 image_paths 字段...")
                conn.execute(text("""
                    ALTER TABLE detection_results
                    ADD COLUMN IF NOT EXISTS image_paths JSON
                """))

                # 更新现有记录的默认值
                logger.info("更新现有记录...")
                conn.execute(text("""
                    UPDATE detection_results
                    SET has_image = FALSE, image_count = 0, image_paths = '[]'
                    WHERE has_image IS NULL
                """))

                # 提交事务
                trans.commit()
                logger.info("✅ 数据库迁移完成！")

            except Exception as e:
                # 回滚事务
                trans.rollback()
                logger.error(f"❌ 迁移失败，已回滚: {e}")
                raise

    except Exception as e:
        logger.error(f"❌ 数据库迁移错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()