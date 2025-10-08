#!/usr/bin/env python3
"""
Run users to tenants database migration script
"""
import sys
import os
from pathlib import Path

# Add backend path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

import psycopg2
from config import settings
import urllib.parse

def run_migration():
    """Run users to tenants database migration"""
    print("Start execution: users renamed to tenants...")
    
    try:
        # Parse database URL
        url = urllib.parse.urlparse(settings.database_url)
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            database=url.path[1:],
            user=url.username,
            password=url.password
        )
        
        cur = conn.cursor()
        
        # Check current database status
        print("📝 Check current database status...")
        
        # Check if users table exists
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name IN ('users', 'tenants');
        """)
        existing_tables = [row[0] for row in cur.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Check response_templates table columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'response_templates' 
            AND column_name IN ('user_id', 'tenant_id');
        """)
        existing_columns = [row[0] for row in cur.fetchall()]
        print(f"response_templates table columns: {existing_columns}")
        
        # If tenants table exists and response_templates has tenant_id column, migration is complete
        if 'tenants' in existing_tables and 'tenant_id' in existing_columns:
            print("✅ Migration completed, skip")
            cur.close()
            conn.close()
            return True
        
        # If users table does not exist but tenants table exists, check if columns need to be renamed
        if 'tenants' in existing_tables and 'user_id' in existing_columns:
            print("📝 Need to rename columns: user_id -> tenant_id")
            # Read migration SQL file
            migration_file = backend_path / "database" / "migrations" / "rename_users_to_tenants.sql"
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print("🚀 Execute migration...")
            # Split SQL statements and execute them one by one
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for statement in statements:
                if statement and not statement.startswith('DO $$'):
                    print(f"Execute: {statement[:50]}...")
                    # Execute SQL statement
                    try:
                        cur.execute(statement)
                    except psycopg2.Error as e:
                        if "does not exist" in str(e) or "already exists" in str(e):
                            print(f"  Skip (already exists or does not exist): {e}")
                            # Skip if column already exists or does not exist
                            continue
                        else:
                            raise
            
            conn.commit()
            print("✅ Migration completed")
            
        elif 'users' in existing_tables:
            print("📝 Need to complete migration: users -> tenants")
            # Read migration SQL file
            migration_file = backend_path / "database" / "migrations" / "rename_users_to_tenants.sql"
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()
            
            print("🚀 Execute migration...")
            # Split SQL statements and execute them one by one
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
            
            for statement in statements:
                if statement and not statement.startswith('DO $$'):
                    print(f"Execute: {statement[:50]}...")
                    try:
                        cur.execute(statement)
                    except psycopg2.Error as e:
                        if "does not exist" in str(e) or "already exists" in str(e):
                            print(f"  Skip (already exists or does not exist): {e}")
                            continue
                        else:
                            raise
            
            conn.commit()
            print("✅ Migration completed")
        else:
            print("❌ No users table or tenants table found, please check database status")
            return False
        
        # Verify migration result
        print("🔍 Verify migration result...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'response_templates' 
            AND column_name = 'tenant_id';
        """)
        if cur.fetchone():
            print("✅ response_templates.tenant_id column exists")
        else:
            print("❌ response_templates.tenant_id column does not exist")
            return False
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("🎉 Migration successfully completed!")
        sys.exit(0)
    else:
        print("💥 Migration failed!")
        sys.exit(1)
