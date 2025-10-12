#!/usr/bin/env python3
"""
Create default risk configs for existing tenants that don't have any

This script ensures all tenants have at least one default config set,
which is required for the new config-set-centric architecture.
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database.models import Tenant, RiskTypeConfig
from services.risk_config_service import create_user_default_risk_config


def main():
    """Create default risk configs for tenants that don't have any"""
    db = next(get_db())

    try:
        # Get all active and verified tenants
        tenants = db.query(Tenant).filter(
            Tenant.is_active == True,
            Tenant.is_verified == True
        ).all()

        print(f"Found {len(tenants)} active tenants")

        created_count = 0
        skipped_count = 0

        for tenant in tenants:
            # Check if tenant already has risk configs
            existing_configs = db.query(RiskTypeConfig).filter(
                RiskTypeConfig.tenant_id == tenant.id
            ).count()

            if existing_configs > 0:
                print(f"✓ Tenant {tenant.email} already has {existing_configs} config(s), skipping")
                skipped_count += 1
                continue

            # Create default config
            try:
                count = create_user_default_risk_config(db, str(tenant.id))
                print(f"✓ Created {count} default config for tenant {tenant.email}")
                created_count += 1
            except Exception as e:
                print(f"✗ Failed to create config for tenant {tenant.email}: {e}")

        print(f"\nSummary:")
        print(f"  Created: {created_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Total:   {len(tenants)}")

    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
