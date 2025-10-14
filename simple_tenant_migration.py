#!/usr/bin/env python3
"""
简化的租户迁移脚本 - 不使用PostgreSQL特有的DO块语法
"""

import sys
import os
sys.path.append('backend')

from sqlalchemy import text
from database.connection import get_admin_db_session

def apply_migration():
    """简化的迁移脚本，只执行核心的重命名操作"""
    try:
        print("开始执行简化的租户迁移...")

        # 连接数据库
        db = get_admin_db_session()

        # 检查当前状态
        users_exist = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")).scalar()
        tenants_exist = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tenants')")).scalar()
        response_templates_tenant_id = db.execute(text("""
            SELECT EXISTS (SELECT FROM information_schema.columns
                         WHERE table_name = 'response_templates' AND column_name = 'tenant_id')
        """)).scalar()

        print(f"当前状态:")
        print(f"  - users 表存在: {users_exist}")
        print(f"  - tenants 表存在: {tenants_exist}")
        print(f"  - response_templates.tenant_id 列存在: {response_templates_tenant_id}")

        if not users_exist and tenants_exist:
            print("✅ 迁移似乎已经完成，无需执行")
            return

        # 重命名主表
        if users_exist and not tenants_exist:
            print("重命名 users 表为 tenants...")
            try:
                db.execute(text("ALTER TABLE users RENAME TO tenants"))
                db.commit()
                print("✓ users 表重命名为 tenants")
            except Exception as e:
                print(f"⚠ 重命名主表出错: {e}")
                db.rollback()

        # 重命名 response_templates 表的列
        if users_exist:  # 如果还是使用 user 术语
            print("重命名 response_templates.user_id 为 tenant_id...")
            try:
                db.execute(text("ALTER TABLE response_templates RENAME COLUMN user_id TO tenant_id"))
                db.commit()
                print("✓ response_templates.user_id 重命名为 tenant_id")
            except Exception as e:
                print(f"⚠ 重命名 response_templates 列出错: {e}")
                db.rollback()
        elif tenants_exist and not response_templates_tenant_id:
            print("response_templates 表缺少 tenant_id 列，需要添加...")
            try:
                # 检查是否有 user_id 列
                user_id_exists = db.execute(text("""
                    SELECT EXISTS (SELECT FROM information_schema.columns
                                 WHERE table_name = 'response_templates' AND column_name = 'user_id')
                """)).scalar()

                if user_id_exists:
                    db.execute(text("ALTER TABLE response_templates RENAME COLUMN user_id TO tenant_id"))
                    print("✓ 将 response_templates.user_id 重命名为 tenant_id")
                else:
                    # 如果都没有，需要添加 tenant_id 列
                    db.execute(text("ALTER TABLE response_templates ADD COLUMN tenant_id UUID"))
                    db.execute(text("ALTER TABLE response_templates ADD FOREIGN KEY (tenant_id) REFERENCES tenants(id)"))
                    print("✓ 添加新的 tenant_id 列")

                db.commit()
            except Exception as e:
                print(f"⚠ 处理 response_templates 列出错: {e}")
                db.rollback()

        # 检查其他重要的表是否正确
        important_tables = ['detection_results', 'blacklist', 'whitelist', 'risk_type_config']
        for table in important_tables:
            tenant_col = db.execute(text(f"""
                SELECT EXISTS (SELECT FROM information_schema.columns
                             WHERE table_name = '{table}' AND column_name = 'tenant_id')
            """)).scalar()
            user_col = db.execute(text(f"""
                SELECT EXISTS (SELECT FROM information_schema.columns
                             WHERE table_name = '{table}' AND column_name = 'user_id')
            """)).scalar()

            print(f"  {table}: tenant_id={tenant_col}, user_id={user_col}")

        # 最终验证
        final_tenant_id = db.execute(text("""
            SELECT EXISTS (SELECT FROM information_schema.columns
                         WHERE table_name = 'response_templates' AND column_name = 'tenant_id')
        """)).scalar()

        if final_tenant_id:
            print("✅ 迁移完成！response_templates.tenant_id 列已存在")
        else:
            print("❌ 迁移未完成：response_templates 表仍然没有 tenant_id 列")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    apply_migration()