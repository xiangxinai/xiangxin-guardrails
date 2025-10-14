"""
Migration script: Migrate from tenant-level to application-level configuration

This script:
1. Creates a default application for each tenant
2. Migrates API keys to the new APIKey table
3. Migrates all configurations to application-level
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.connection import get_admin_db_session
from database.models import (
    Tenant, Application, APIKey,
    RiskTypeConfig, Blacklist, Whitelist, ResponseTemplate,
    KnowledgeBase, DataSecurityEntityType,
    TestModelConfig, ProxyModelConfig
)
from utils.api_key import hash_api_key, get_api_key_prefix
from utils.logger import setup_logger
import uuid

logger = setup_logger()

def migrate_tenant_to_applications():
    """
    Migrate existing tenant-level configurations to application-level
    """
    db = get_admin_db_session()

    try:
        logger.info("Starting migration to application model...")

        # Get all tenants
        tenants = db.query(Tenant).all()
        logger.info(f"Found {len(tenants)} tenants to migrate")

        for tenant in tenants:
            logger.info(f"\nMigrating tenant: {tenant.email} ({tenant.id})")

            try:
                # 1. Create default application for this tenant
                default_app = Application(
                    id=uuid.uuid4(),
                    tenant_id=tenant.id,
                    name="Default Application",
                    description="Migrated from single configuration setup",
                    is_active=True
                )
                db.add(default_app)
                db.flush()  # Get the app ID
                logger.info(f"  ✓ Created default application: {default_app.id}")

                # 2. Migrate API Key
                if tenant.api_key:
                    logger.info(f"  → Migrating API key: {tenant.api_key[:20]}...")

                    # Hash the existing API key
                    key_hash = hash_api_key(tenant.api_key)
                    key_prefix = get_api_key_prefix(tenant.api_key)

                    api_key = APIKey(
                        id=uuid.uuid4(),
                        tenant_id=tenant.id,
                        application_id=default_app.id,
                        key_hash=key_hash,
                        key_prefix=key_prefix,
                        name="Migrated Key",
                        is_active=True
                    )
                    db.add(api_key)
                    logger.info(f"  ✓ Migrated API key")
                else:
                    logger.warning(f"  ⚠ No API key found for tenant {tenant.email}")

                # 3. Migrate RiskTypeConfig
                risk_config = db.query(RiskTypeConfig).filter(
                    RiskTypeConfig.tenant_id == tenant.id
                ).first()

                if risk_config:
                    risk_config.application_id = default_app.id
                    logger.info(f"  ✓ Migrated risk type config")
                else:
                    logger.info(f"  ℹ No risk type config found")

                # 4. Migrate Blacklists
                blacklists = db.query(Blacklist).filter(
                    Blacklist.tenant_id == tenant.id
                ).all()

                for bl in blacklists:
                    bl.application_id = default_app.id

                if blacklists:
                    logger.info(f"  ✓ Migrated {len(blacklists)} blacklists")

                # 5. Migrate Whitelists
                whitelists = db.query(Whitelist).filter(
                    Whitelist.tenant_id == tenant.id
                ).all()

                for wl in whitelists:
                    wl.application_id = default_app.id

                if whitelists:
                    logger.info(f"  ✓ Migrated {len(whitelists)} whitelists")

                # 6. Migrate ResponseTemplates (only tenant-owned, not global)
                templates = db.query(ResponseTemplate).filter(
                    ResponseTemplate.tenant_id == tenant.id,
                    ResponseTemplate.is_default == False  # Don't migrate system defaults
                ).all()

                for tmpl in templates:
                    tmpl.application_id = default_app.id

                if templates:
                    logger.info(f"  ✓ Migrated {len(templates)} response templates")

                # 7. Migrate KnowledgeBases
                knowledge_bases = db.query(KnowledgeBase).filter(
                    KnowledgeBase.tenant_id == tenant.id,
                    KnowledgeBase.is_global == False  # Don't migrate global knowledge bases
                ).all()

                for kb in knowledge_bases:
                    kb.application_id = default_app.id

                if knowledge_bases:
                    logger.info(f"  ✓ Migrated {len(knowledge_bases)} knowledge bases")

                # 8. Migrate DataSecurityEntityTypes
                entity_types = db.query(DataSecurityEntityType).filter(
                    DataSecurityEntityType.tenant_id == tenant.id,
                    DataSecurityEntityType.is_global == False  # Don't migrate global types
                ).all()

                for et in entity_types:
                    et.application_id = default_app.id

                if entity_types:
                    logger.info(f"  ✓ Migrated {len(entity_types)} data security entity types")

                # 9. Migrate TestModelConfigs
                test_models = db.query(TestModelConfig).filter(
                    TestModelConfig.tenant_id == tenant.id
                ).all()

                for tm in test_models:
                    tm.application_id = default_app.id

                if test_models:
                    logger.info(f"  ✓ Migrated {len(test_models)} test model configs")

                # 10. Migrate ProxyModelConfigs
                proxy_models = db.query(ProxyModelConfig).filter(
                    ProxyModelConfig.tenant_id == tenant.id
                ).all()

                for pm in proxy_models:
                    pm.application_id = default_app.id

                if proxy_models:
                    logger.info(f"  ✓ Migrated {len(proxy_models)} proxy model configs")

                logger.info(f"✅ Successfully migrated tenant: {tenant.email}")

            except Exception as e:
                logger.error(f"❌ Failed to migrate tenant {tenant.email}: {e}")
                raise

        # Commit all changes
        db.commit()
        logger.info("\n" + "="*60)
        logger.info("✅ Migration completed successfully!")
        logger.info(f"Total tenants migrated: {len(tenants)}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        db.rollback()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Starting Migration to Application Model")
    print("="*60 + "\n")

    print("⚠️  WARNING: This will migrate all tenant-level configurations")
    print("   to application-level. Make sure you have a database backup!\n")

    response = input("Do you want to continue? (yes/no): ")

    if response.lower() == 'yes':
        migrate_tenant_to_applications()
    else:
        print("\n❌ Migration cancelled by user")
        sys.exit(0)
