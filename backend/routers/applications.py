"""
Application Management API Routes

Provides endpoints for managing applications and their API keys.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from routers.auth import get_current_admin
from services.application_service import ApplicationService, APIKeyService
from models.requests import CreateApplicationRequest, UpdateApplicationRequest, CreateAPIKeyRequest, UpdateAPIKeyRequest
from models.responses import (
    ApplicationResponse, ApplicationDetailResponse,
    APIKeyResponse, APIKeyCreateResponse, ApiResponse
)
from typing import List
from datetime import datetime

router = APIRouter(tags=["Applications"])

# ==================== Application Management ====================

@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all applications for the current tenant

    Returns:
        List of applications
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')
    apps = ApplicationService.get_applications_by_tenant(db, tenant_id)

    return [
        ApplicationResponse(
            id=str(app.id),
            tenant_id=str(app.tenant_id),
            name=app.name,
            description=app.description,
            is_active=app.is_active,
            created_at=app.created_at,
            updated_at=app.updated_at
        )
        for app in apps
    ]

@router.post("", response_model=dict)
async def create_application(
    request: CreateApplicationRequest,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new application

    Args:
        request: Create application request

    Returns:
        Created application details and first API key
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    # Verify source application ownership if copying
    if request.copy_from_application_id:
        source_app = ApplicationService.get_application_by_id(
            db, request.copy_from_application_id, tenant_id
        )
        if not source_app:
            raise HTTPException(status_code=404, detail="Source application not found")

    # Create application
    app, api_key = ApplicationService.create_application(
        db=db,
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        copy_from_application_id=request.copy_from_application_id
    )

    return {
        "application": ApplicationResponse(
            id=str(app.id),
            tenant_id=str(app.tenant_id),
            name=app.name,
            description=app.description,
            is_active=app.is_active,
            created_at=app.created_at,
            updated_at=app.updated_at
        ),
        "first_api_key": api_key,
        "message": "Application created successfully. Please save the API key as it won't be shown again."
    }

@router.get("/{application_id}", response_model=ApplicationDetailResponse)
async def get_application(
    application_id: str,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get application details

    Args:
        application_id: Application ID

    Returns:
        Application details
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')
    app = ApplicationService.get_application_by_id(db, application_id, tenant_id)

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    api_key_count = ApplicationService.get_api_key_count(db, application_id)

    return ApplicationDetailResponse(
        id=str(app.id),
        tenant_id=str(app.tenant_id),
        name=app.name,
        description=app.description,
        is_active=app.is_active,
        api_key_count=api_key_count,
        created_at=app.created_at,
        updated_at=app.updated_at
    )

@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: str,
    request: UpdateApplicationRequest,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update an application

    Args:
        application_id: Application ID
        request: Update application request

    Returns:
        Updated application
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    app = ApplicationService.update_application(
        db=db,
        application_id=application_id,
        tenant_id=tenant_id,
        name=request.name,
        description=request.description,
        is_active=request.is_active
    )

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    return ApplicationResponse(
        id=str(app.id),
        tenant_id=str(app.tenant_id),
        name=app.name,
        description=app.description,
        is_active=app.is_active,
        created_at=app.created_at,
        updated_at=app.updated_at
    )

@router.delete("/{application_id}", response_model=ApiResponse)
async def delete_application(
    application_id: str,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an application

    Args:
        application_id: Application ID

    Returns:
        Success response
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    success = ApplicationService.delete_application(db, application_id, tenant_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete application. It might be the last application or not found."
        )

    return ApiResponse(
        success=True,
        message="Application deleted successfully"
    )

# ==================== API Key Management ====================

@router.get("/{application_id}/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    application_id: str,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all API keys for an application

    Args:
        application_id: Application ID

    Returns:
        List of API keys
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    # Verify application ownership
    app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    keys = APIKeyService.get_api_keys_by_application(db, application_id)

    return [
        APIKeyResponse(
            id=str(key.id),
            application_id=str(key.application_id),
            name=key.name,
            key_prefix=key.key_prefix,
            is_active=key.is_active,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            created_at=key.created_at,
            updated_at=key.updated_at
        )
        for key in keys
    ]

@router.post("/{application_id}/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    application_id: str,
    request: CreateAPIKeyRequest,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new API key for an application

    Args:
        application_id: Application ID
        request: Create API key request

    Returns:
        Created API key (with full key string, only shown once)
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    # Verify application ownership
    app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Parse expires_at if provided
    expires_at = None
    if request.expires_at:
        try:
            expires_at = datetime.fromisoformat(request.expires_at.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expires_at format. Use ISO format.")

    # Create API key
    key, api_key_str = APIKeyService.create_api_key(
        db=db,
        application_id=application_id,
        tenant_id=tenant_id,
        name=request.name,
        expires_at=expires_at
    )

    return APIKeyCreateResponse(
        id=str(key.id),
        application_id=str(key.application_id),
        name=key.name,
        api_key=api_key_str,  # Full key, only shown once
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        expires_at=key.expires_at,
        created_at=key.created_at
    )

@router.patch("/{application_id}/api-keys/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    application_id: str,
    key_id: str,
    request: UpdateAPIKeyRequest,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Update an API key

    Args:
        application_id: Application ID
        key_id: API key ID
        request: Update API key request

    Returns:
        Updated API key
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    # Verify application ownership
    app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update key
    key = APIKeyService.update_api_key(
        db=db,
        api_key_id=key_id,
        application_id=application_id,
        name=request.name,
        is_active=request.is_active
    )

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    return APIKeyResponse(
        id=str(key.id),
        application_id=str(key.application_id),
        name=key.name,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        expires_at=key.expires_at,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
        updated_at=key.updated_at
    )

@router.delete("/{application_id}/api-keys/{key_id}", response_model=ApiResponse)
async def delete_api_key(
    application_id: str,
    key_id: str,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an API key

    Args:
        application_id: Application ID
        key_id: API key ID

    Returns:
        Success response
    """
    tenant_id = current_user.get('tenant_id') or current_user.get('sub')

    # Verify application ownership
    app = ApplicationService.get_application_by_id(db, application_id, tenant_id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Delete key
    success = APIKeyService.delete_api_key(db, key_id, application_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete API key. It might be the last active key or not found."
        )

    return ApiResponse(
        success=True,
        message="API key deleted successfully"
    )
