#!/usr/bin/env python3
"""
Run database migration to associate existing data with config sets

Usage:
    python backend/database/migrations/run_migration.py

Environment Variables:
    DATABASE_URL - PostgreSQL connection string (optional, defaults to config)
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from database.connection import get_db, engine
from utils.logger import setup_logger

logger = setup_logger()


def run_migration():
    """Execute the config set migration script"""

    migration_file = Path(__file__).parent / "migrate_to_config_sets.sql"

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    logger.info("=" * 80)
    logger.info("Starting Config Set Migration")
    logger.info("=" * 80)

    # Read migration SQL
    with open(migration_file, 'r') as f:
        sql_content = f.read()

    # Split by semicolons to execute statements individually
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

    # Filter out comment blocks and verification queries
    executable_statements = []
    for stmt in statements:
        # Skip verification queries (commented out in SQL file)
        if 'SELECT COUNT' in stmt or 'SELECT' in stmt and 'FROM tenants' in stmt:
            continue
        # Skip empty statements
        if not stmt or stmt.isspace():
            continue
        executable_statements.append(stmt)

    logger.info(f"Found {len(executable_statements)} SQL statements to execute")

    # Execute migration
    db = next(get_db())
    try:
        executed = 0
        for i, statement in enumerate(executable_statements, 1):
            try:
                # Show preview of statement
                preview = statement[:100].replace('\n', ' ')
                logger.info(f"[{i}/{len(executable_statements)}] Executing: {preview}...")

                result = db.execute(text(statement))
                db.commit()

                # Log affected rows if available
                if result.rowcount > 0:
                    logger.info(f"  ✓ Affected {result.rowcount} rows")
                else:
                    logger.info(f"  ✓ Completed (no rows affected)")

                executed += 1

            except Exception as e:
                logger.error(f"  ✗ Error executing statement: {e}")
                logger.error(f"  Statement: {statement[:200]}")
                db.rollback()
                raise

        logger.info("=" * 80)
        logger.info(f"Migration completed successfully! ({executed}/{len(executable_statements)} statements)")
        logger.info("=" * 80)

        # Run verification queries
        logger.info("\nRunning verification checks...")
        run_verification(db)

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def run_verification(db):
    """Run verification queries to check migration results"""

    verifications = [
        {
            "name": "Tenants with default config",
            "query": """
                SELECT COUNT(*) as count
                FROM risk_type_config
                WHERE is_default = true
            """,
            "expected": "Should equal number of tenants"
        },
        {
            "name": "API keys without template",
            "query": """
                SELECT COUNT(*) as count
                FROM tenant_api_keys
                WHERE template_id IS NULL
                AND is_active = true
            """,
            "expected": "Should be 0"
        },
        {
            "name": "Blacklists without template",
            "query": """
                SELECT COUNT(*) as count
                FROM blacklist
                WHERE template_id IS NULL
            """,
            "expected": "Should be 0"
        },
        {
            "name": "Whitelists without template",
            "query": """
                SELECT COUNT(*) as count
                FROM whitelist
                WHERE template_id IS NULL
            """,
            "expected": "Should be 0"
        }
    ]

    all_passed = True

    for check in verifications:
        try:
            result = db.execute(text(check["query"])).fetchone()
            count = result[0] if result else 0

            status = "✓" if count == 0 or "equal" in check["expected"] else "!"
            logger.info(f"{status} {check['name']}: {count} ({check['expected']})")

        except Exception as e:
            logger.error(f"✗ {check['name']}: Error - {e}")
            all_passed = False

    if all_passed:
        logger.info("\n✓ All verification checks passed!")
    else:
        logger.warning("\n! Some verification checks need attention")

    # Show summary
    try:
        summary = db.execute(text("""
            SELECT
                COUNT(DISTINCT tenant_id) as total_tenants,
                COUNT(*) as total_config_sets,
                SUM(CASE WHEN is_default THEN 1 ELSE 0 END) as default_configs
            FROM risk_type_config
        """)).fetchone()

        logger.info(f"\nSummary:")
        logger.info(f"  Total tenants with configs: {summary[0]}")
        logger.info(f"  Total config sets: {summary[1]}")
        logger.info(f"  Default configs: {summary[2]}")

    except Exception as e:
        logger.error(f"Error getting summary: {e}")


if __name__ == "__main__":
    logger.info("Config Set Migration Tool")
    logger.info(f"Database: {engine.url}")

    # Confirm before running
    response = input("\nThis will migrate existing data to use config sets. Continue? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        logger.info("Migration cancelled by user")
        sys.exit(0)

    success = run_migration()

    if success:
        logger.info("\n✓ Migration completed successfully!")
        logger.info("You can now use the config set features.")
        sys.exit(0)
    else:
        logger.error("\n✗ Migration failed!")
        logger.error("Please check the errors above and try again.")
        sys.exit(1)
