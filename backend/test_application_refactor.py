#!/usr/bin/env python3
"""
Test script for application-level configuration refactor

This script tests the core functionality of the new application model.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.connection import get_admin_db_session
from database.models import Tenant, Application, APIKey
from services.application_service import ApplicationService, APIKeyService
from utils.api_key import verify_api_key, hash_api_key
from utils.logger import setup_logger

logger = setup_logger()

def test_application_service():
    """Test ApplicationService"""
    print("\n" + "="*60)
    print("Testing Application Service")
    print("="*60)

    db = get_admin_db_session()
    try:
        # Find a test tenant
        tenant = db.query(Tenant).first()
        if not tenant:
            print("❌ No tenant found. Please create a tenant first.")
            return False

        print(f"✓ Using tenant: {tenant.email}")

        # Test 1: List applications
        print("\n[Test 1] Listing applications...")
        apps = ApplicationService.get_applications_by_tenant(db, str(tenant.id))
        print(f"  Found {len(apps)} application(s)")
        for app in apps:
            print(f"    - {app.name} (ID: {app.id}, Active: {app.is_active})")

        # Test 2: Get application details
        if apps:
            print(f"\n[Test 2] Getting application details...")
            app = apps[0]
            detail = ApplicationService.get_application_by_id(db, str(app.id), str(tenant.id))
            if detail:
                print(f"  ✓ Application: {detail.name}")
                key_count = ApplicationService.get_api_key_count(db, str(app.id))
                print(f"  ✓ API Keys: {key_count}")
            else:
                print("  ❌ Failed to get application details")
                return False

        # Test 3: Create new application
        print(f"\n[Test 3] Creating new application...")
        new_app, first_key = ApplicationService.create_application(
            db=db,
            tenant_id=str(tenant.id),
            name="Test Application",
            description="Created by test script"
        )
        print(f"  ✓ Created: {new_app.name} (ID: {new_app.id})")
        print(f"  ✓ First API Key: {first_key[:20]}...")

        # Test 4: Update application
        print(f"\n[Test 4] Updating application...")
        updated = ApplicationService.update_application(
            db=db,
            application_id=str(new_app.id),
            tenant_id=str(tenant.id),
            description="Updated by test script"
        )
        if updated:
            print(f"  ✓ Updated: {updated.name}")
            print(f"  ✓ New description: {updated.description}")
        else:
            print("  ❌ Failed to update application")
            return False

        # Don't delete the test application yet - we'll use it for API key tests
        test_app_id = str(new_app.id)

        print("\n✅ All Application Service tests passed!")
        return test_app_id

    finally:
        db.close()

def test_api_key_service(app_id: str):
    """Test APIKeyService"""
    print("\n" + "="*60)
    print("Testing API Key Service")
    print("="*60)

    db = get_admin_db_session()
    try:
        # Find the application
        app = db.query(Application).filter(Application.id == app_id).first()
        if not app:
            print(f"❌ Application {app_id} not found")
            return False

        print(f"✓ Using application: {app.name}")

        # Test 1: List API keys
        print("\n[Test 1] Listing API keys...")
        keys = APIKeyService.get_api_keys_by_application(db, app_id)
        print(f"  Found {len(keys)} API key(s)")
        for key in keys:
            print(f"    - {key.name or 'Unnamed'} ({key.key_prefix}..., Active: {key.is_active})")

        # Test 2: Create new API key
        print(f"\n[Test 2] Creating new API key...")
        new_key, key_string = APIKeyService.create_api_key(
            db=db,
            application_id=app_id,
            tenant_id=str(app.tenant_id),
            name="Test API Key"
        )
        print(f"  ✓ Created: {new_key.name}")
        print(f"  ✓ Key: {key_string[:20]}...")
        print(f"  ✓ Prefix: {new_key.key_prefix}")

        # Test 3: Verify API key
        print(f"\n[Test 3] Verifying API key...")
        auth_context = verify_api_key(db, key_string)
        if auth_context:
            print(f"  ✓ Verified!")
            print(f"  ✓ Tenant ID: {auth_context['tenant_id']}")
            print(f"  ✓ Application ID: {auth_context['application_id']}")
            print(f"  ✓ API Key ID: {auth_context['api_key_id']}")
        else:
            print("  ❌ Failed to verify API key")
            return False

        # Test 4: Update API key
        print(f"\n[Test 4] Updating API key...")
        updated = APIKeyService.update_api_key(
            db=db,
            api_key_id=str(new_key.id),
            application_id=app_id,
            name="Updated Test Key"
        )
        if updated:
            print(f"  ✓ Updated: {updated.name}")
        else:
            print("  ❌ Failed to update API key")
            return False

        # Test 5: Disable API key
        print(f"\n[Test 5] Disabling API key...")
        disabled = APIKeyService.update_api_key(
            db=db,
            api_key_id=str(new_key.id),
            application_id=app_id,
            is_active=False
        )
        if disabled and not disabled.is_active:
            print(f"  ✓ Disabled: {disabled.name}")

            # Verify disabled key doesn't work
            auth_context = verify_api_key(db, key_string)
            if not auth_context:
                print(f"  ✓ Disabled key correctly rejected")
            else:
                print(f"  ❌ Disabled key still works (should be rejected)")
                return False
        else:
            print("  ❌ Failed to disable API key")
            return False

        print("\n✅ All API Key Service tests passed!")
        return True

    finally:
        db.close()

def test_data_model():
    """Test data model relationships"""
    print("\n" + "="*60)
    print("Testing Data Model Relationships")
    print("="*60)

    db = get_admin_db_session()
    try:
        # Test tenant -> applications relationship
        print("\n[Test 1] Tenant -> Applications relationship...")
        tenant = db.query(Tenant).first()
        if not tenant:
            print("❌ No tenant found")
            return False

        print(f"  Tenant: {tenant.email}")
        print(f"  Applications: {len(tenant.applications)}")
        for app in tenant.applications:
            print(f"    - {app.name} ({len(app.api_keys)} keys)")

        # Test application -> API keys relationship
        if tenant.applications:
            print("\n[Test 2] Application -> API Keys relationship...")
            app = tenant.applications[0]
            print(f"  Application: {app.name}")
            print(f"  API Keys: {len(app.api_keys)}")
            for key in app.api_keys:
                print(f"    - {key.name or 'Unnamed'} (Active: {key.is_active})")

        # Test application -> configurations relationship
        print("\n[Test 3] Application -> Configurations relationship...")
        if tenant.applications:
            app = tenant.applications[0]
            print(f"  Application: {app.name}")

            # Check blacklists
            from database.models import Blacklist
            blacklists = db.query(Blacklist).filter(
                Blacklist.application_id == app.id
            ).all()
            print(f"  Blacklists: {len(blacklists)}")

            # Check whitelists
            from database.models import Whitelist
            whitelists = db.query(Whitelist).filter(
                Whitelist.application_id == app.id
            ).all()
            print(f"  Whitelists: {len(whitelists)}")

            # Check risk config
            from database.models import RiskTypeConfig
            risk_config = db.query(RiskTypeConfig).filter(
                RiskTypeConfig.application_id == app.id
            ).first()
            print(f"  Risk Config: {'✓' if risk_config else '✗'}")

        print("\n✅ All Data Model tests passed!")
        return True

    finally:
        db.close()

def cleanup_test_data():
    """Clean up test data created during testing"""
    print("\n" + "="*60)
    print("Cleaning Up Test Data")
    print("="*60)

    db = get_admin_db_session()
    try:
        # Find and delete test applications
        from database.models import Application
        test_apps = db.query(Application).filter(
            Application.name == "Test Application"
        ).all()

        for app in test_apps:
            print(f"  Deleting: {app.name} (ID: {app.id})")
            db.delete(app)

        db.commit()
        print(f"✓ Cleaned up {len(test_apps)} test application(s)")

    finally:
        db.close()

def main():
    """Main test runner"""
    print("\n" + "="*70)
    print(" 🧪 Application-Level Configuration Refactor Test Suite")
    print("="*70)

    try:
        # Test 1: Data Model
        if not test_data_model():
            print("\n❌ Data model tests failed!")
            return 1

        # Test 2: Application Service
        test_app_id = test_application_service()
        if not test_app_id:
            print("\n❌ Application service tests failed!")
            return 1

        # Test 3: API Key Service
        if not test_api_key_service(test_app_id):
            print("\n❌ API key service tests failed!")
            return 1

        print("\n" + "="*70)
        print(" ✅ All Tests Passed!")
        print("="*70)

        # Cleanup
        response = input("\nDo you want to clean up test data? (yes/no): ")
        if response.lower() == 'yes':
            cleanup_test_data()

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
