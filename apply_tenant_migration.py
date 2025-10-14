#!/usr/bin/env python3
"""
执行租户迁移脚本的Python工具
"""

import sys
import os
sys.path.append('backend')

from sqlalchemy import text
from database.connection import get_admin_db_session

def apply_migration():
    """执行迁移脚本"""
    try:
        print("开始执行租户迁移...")

        # 读入迁移脚本
        with open('backend/database/migrations/rename_users_to_tenants.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 连接数据库
        db = get_admin_db_session()

        # 先检查是否还有 users 表
        result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")).scalar()
        if result:
            print("发现 users 表，开始迁移...")

            # 执行迁移SQL
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            for stmt in statements:
                try:
                    if stmt and not stmt.startswith('--'):
                        print(f"执行: {stmt[:60]}...")
                        db.execute(text(stmt))
                        db.commit()
                except Exception as e:
                    print(f"警告: 可能的执行错误 {e}，继续执行...")

            print("迁移脚本执行完成")
        else:
            print("不需要执行迁移：users 表不存在")

        # 检查结果
        tenant_exists = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')")).scalar()
        user_exists = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")).scalar()

        if tenant_exists and not user_exists:
            print("✅ 迁移成功完成")
        elif user_exists:
            print("❌ 迁移未完成，users 表仍然存在")
        else:
            print("❌ 问题：两个表都不存在")

        # 检查 response_templates 表的列
        columns = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'response_templates'
            AND column_name = 'tenant_id'
        """)).fetchall()

        if columns:
            print("✅ response_templates.tenant_id 列存在")
        else:
            print("❌ response_templates.tenant_id 列不存在")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    apply_migration()