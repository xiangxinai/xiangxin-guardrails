#!/usr/bin/env python3
"""
运行用户重命名为租户的数据库迁移脚本
"""
import sys
import os
from pathlib import Path

# 添加backend路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import psycopg2
from config import settings
import urllib.parse

def run_migration():
    """执行迁移"""
    print("开始执行迁移：用户重命名为租户...")
    
    try:
        # 解析数据库URL
        url = urllib.parse.urlparse(settings.database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password
        )
        
        cur = conn.cursor()
        
        # 检查当前数据库状态
        print("📝 检查当前数据库状态...")
        
        # 检查是否存在users表
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('users', 'tenants');
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        print(f"现有表: {existing_tables}")
        
        # 检查response_templates表的列
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'response_templates' 
            AND column_name IN ('user_id', 'tenant_id');
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"response_templates表的列: {existing_columns}")
        
        # 如果tenants表已存在且response_templates已有tenant_id列，说明迁移已完成
        if 'tenants' in existing_tables and 'tenant_id' in existing_columns:
            print("✅ 迁移已完成，跳过")
            cur.close()
            conn.close()
            return True
        
        # 如果users表不存在但tenants表存在，检查是否需要重命名列
        if 'tenants' in existing_tables and 'user_id' in existing_columns:
            print("📝 需要重命名列: user_id -> tenant_id")
            # 读取迁移SQL文件
            migration_file = backend_path / "database" / "migrations" / "rename_users_to_tenants.sql"
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print("🚀 执行迁移...")
            # 分割SQL语句并逐个执行
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for statement in statements:
                if statement and not statement.startswith('DO $$'):
                    print(f"执行: {statement[:50]}...")
                    try:
                        cur.execute(statement)
                    except psycopg2.Error as e:
                        if "does not exist" in str(e) or "already exists" in str(e):
                            print(f"  跳过 (已存在或不存在): {e}")
                            continue
                        else:
                            raise
            
            conn.commit()
            print("✅ 迁移完成")
            
        elif 'users' in existing_tables:
            print("📝 需要完整迁移: users -> tenants")
            # 读取迁移SQL文件
            migration_file = backend_path / "database" / "migrations" / "rename_users_to_tenants.sql"
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print("🚀 执行迁移...")
            # 分割SQL语句并逐个执行
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for statement in statements:
                if statement and not statement.startswith('DO $$'):
                    print(f"执行: {statement[:50]}...")
                    try:
                        cur.execute(statement)
                    except psycopg2.Error as e:
                        if "does not exist" in str(e) or "already exists" in str(e):
                            print(f"  跳过 (已存在或不存在): {e}")
                            continue
                        else:
                            raise
            
            conn.commit()
            print("✅ 迁移完成")
        else:
            print("❌ 未找到users表或tenants表，请检查数据库状态")
            return False
        
        # 验证迁移结果
        print("🔍 验证迁移结果...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'response_templates' 
            AND column_name = 'tenant_id';
        """)
        if cur.fetchone():
            print("✅ response_templates.tenant_id 列存在")
        else:
            print("❌ response_templates.tenant_id 列不存在")
            return False
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 迁移成功完成！")
        sys.exit(0)
    else:
        print("💥 迁移失败！")
        sys.exit(1)
