#!/usr/bin/env python3
"""
完整的租户迁移脚本 - 修复所有相关表的列名
"""

import sys
import os
sys.path.append('backend')

from sqlalchemy import text
from database.connection import get_admin_db_session

def complete_migration():
    """完成迁移，修复所有需要租户ID的表"""
    try:
        print("开始完成租户迁移...")

        # 连接数据库
        db = get_admin_db_session()

        # 需要重命名 user_id 为 tenant_id 的表
        tables_to_migrate = [
            'detection_results',
            'blacklist',
            'whitelist',
            'risk_type_config',
            'test_model_configs',
            'proxy_model_configs',
            'proxy_request_logs',
            'knowledge_bases',
            'data_security_entity_types'
        ]

        migrated_count = 0

        for table in tables_to_migrate:
            print(f"\n检查表 {table}...")

            # 检查当前列状态
            tenant_col = db.execute(text(f"""
                SELECT EXISTS (SELECT FROM information_schema.columns
                             WHERE table_name = '{table}' AND column_name = 'tenant_id')
            """)).scalar()
            user_col = db.execute(text(f"""
                SELECT EXISTS (SELECT FROM information_schema.columns
                             WHERE table_name = '{table}' AND column_name = 'user_id')
            """)).scalar()

            print(f"  - {table}: tenant_id={tenant_col}, user_id={user_col}")

            if user_col and not tenant_col:
                # 需要将 user_id 重命名为 tenant_id
                try:
                    db.execute(text(f"ALTER TABLE {table} RENAME COLUMN user_id TO tenant_id"))
                    db.commit()
                    print(f"  ✓ {table}.user_id 重命名为 tenant_id")
                    migrated_count += 1
                except Exception as e:
                    print(f"  ⚠ 重命名 {table} 列失败: {e}")
                    db.rollback()
            elif tenant_col:
                print(f"  ✓ {table} 已经有 tenant_id 列")
            else:
                print(f"  ⚠ {table} 既没有 user_id 也没有 tenant_id 列")

        # 检查索引是否需要重命名
        print(f"\n检查索引是否需要重命名...")
        indexes_to_check = [
            'idx_detection_results_user_id',
            'idx_blacklist_user_id',
            'idx_whitelist_user_id',
            'idx_response_templates_user_id'
        ]

        for idx_name in indexes_to_check:
            try:
                # 尝试重命名索引
                new_idx_name = idx_name.replace('user_id', 'tenant_id')
                db.execute(text(f"ALTER INDEX IF EXISTS {idx_name} RENAME TO {new_idx_name}"))
                db.commit()
                print(f"  ✓ 重命名索引 {idx_name} -> {new_idx_name}")
            except Exception as e:
                print(f"  ⚠ 重命名索引 {idx_name} 失败: {e}")
                db.rollback()

        # 验证最终结果
        print(f"\n最终验证:")
        verification_tables = ['detection_results', 'blacklist', 'whitelist', 'response_templates', 'risk_type_config']
        all_good = True

        for table in verification_tables:
            tenant_exists = db.execute(text(f"""
                SELECT EXISTS (SELECT FROM information_schema.columns
                             WHERE table_name = '{table}' AND column_name = 'tenant_id')
            """)).scalar()

            if tenant_exists:
                print(f"  ✅ {table} 有 tenant_id 列")
            else:
                print(f"  ❌ {table} 缺少 tenant_id 列")
                all_good = False

        if all_good:
            print(f"\n🎉 所有表迁移完成！总共迁移了 {migrated_count} 个表")
        else:
            print(f"\n⚠️  还有表需要手动处理")

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    complete_migration()