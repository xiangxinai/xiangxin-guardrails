#!/usr/bin/env python3
"""
添加is_global列到knowledge_bases表的迁移脚本
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
    print("开始执行迁移：添加is_global列到knowledge_bases表...")
    
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
        
        # 检查列是否已存在
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'knowledge_bases' AND column_name = 'is_global';
        """)
        
        if cur.fetchone():
            print("✅ is_global列已存在，跳过迁移")
            cur.close()
            conn.close()
            return True
        
        print("📝 读取迁移SQL文件...")
        migration_file = backend_path / "database" / "migrations" / "add_is_global_to_knowledge_bases.sql"
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print("🚀 执行迁移...")
        # 分割SQL语句并逐个执行
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for statement in statements:
            if statement:
                print(f"执行: {statement[:50]}...")
                cur.execute(statement)
        
        conn.commit()
        
        # 验证迁移结果
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_bases' AND column_name = 'is_global';")
        if cur.fetchone():
            print("✅ 迁移成功！is_global列已添加到knowledge_bases表")
        else:
            print("❌ 迁移失败：is_global列未找到")
            return False
        
        # 显示当前表结构
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_bases' ORDER BY ordinal_position;")
        columns = [row[0] for row in cur.fetchall()]
        print("\n📋 更新后的knowledge_bases表结构：")
        for col in columns:
            print(f"  - {col}")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
