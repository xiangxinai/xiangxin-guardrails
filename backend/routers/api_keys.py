"""
API Key Management Routes

Provides REST API endpoints for tenant API key management
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from database.connection import get_db
from services.api_key_service import ApiKeyService
from utils.logger import setup_logger

logger = setup_logger()
router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


def get_current_tenant_id(request: Request) -> str:
    """Get current tenant ID from request context"""
    auth_context = getattr(request.state, 'auth_context', None)
    if not auth_context:
        raise HTTPException(status_code=401, detail="Not authenticated")

    tenant_id = str(auth_context['data'].get('tenant_id'))
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID not found in auth context")

    return tenant_id


# Request/Response Models
class CreateApiKeyRequest(BaseModel):
    """Request model for creating an API key"""
    name: str = Field(..., min_length=1, max_length=100, description="API key name/description")
    template_id: Optional[int] = Field(None, description="Protection config template ID to associate")
    is_default: bool = Field(False, description="Whether this is the default key")


class UpdateApiKeyRequest(BaseModel):
    """Request model for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New API key name")
    template_id: Optional[int] = Field(None, description="New protection config template ID")
    is_active: Optional[bool] = Field(None, description="Whether the key is active")
    is_default: Optional[bool] = Field(None, description="Whether this is the default key")


class AssociateBlacklistRequest(BaseModel):
    """Request model for associating a blacklist with an API key"""
    blacklist_id: int = Field(..., description="Blacklist ID to associate")


class ApiKeyResponse(BaseModel):
    """Response model for API key details"""
    id: str
    name: str
    api_key: str
    is_active: bool
    is_default: bool
    template_id: Optional[int]
    template_name: Optional[str]
    blacklist_ids: List[int]
    last_used_at: Optional[str]
    created_at: str
    updated_at: str


class ApiKeyListResponse(BaseModel):
    """Response model for API key list"""
    total: int
    api_keys: List[ApiKeyResponse]


# Endpoints
@router.post("", response_model=ApiKeyResponse, status_code=201)
async def create_api_key(
    request: CreateApiKeyRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Create a new API key for the current tenant

    Args:
        request: API key creation parameters
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        Created API key details

    Raises:
        400: If name already exists or invalid parameters
        500: If creation fails
    """
    try:
        api_key = ApiKeyService.create_api_key(
            db=db,
            tenant_id=tenant_id,
            name=request.name,
            template_id=request.template_id,
            is_default=request.is_default
        )

        # Get full details
        keys = ApiKeyService.list_api_keys(db, tenant_id)
        created_key = next((k for k in keys if k["id"] == str(api_key.id)), None)

        if not created_key:
            raise HTTPException(status_code=500, detail="Failed to retrieve created API key")

        return ApiKeyResponse(**created_key)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """List all API keys for the current tenant

    Args:
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        List of API keys with metadata
    """
    try:
        api_keys = ApiKeyService.list_api_keys(db, tenant_id)
        return ApiKeyListResponse(
            total=len(api_keys),
            api_keys=[ApiKeyResponse(**key) for key in api_keys]
        )
    except Exception as e:
        logger.error(f"Error listing API keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Get details of a specific API key

    Args:
        api_key_id: API key UUID
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        API key details

    Raises:
        404: If API key not found
    """
    try:
        keys = ApiKeyService.list_api_keys(db, tenant_id)
        api_key = next((k for k in keys if k["id"] == api_key_id), None)

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        return ApiKeyResponse(**api_key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get API key")


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    api_key_id: str,
    request: UpdateApiKeyRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Update an API key

    Args:
        api_key_id: API key UUID
        request: Update parameters
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        Updated API key details

    Raises:
        400: If invalid parameters or name conflict
        404: If API key not found
        500: If update fails
    """
    try:
        api_key = ApiKeyService.update_api_key(
            db=db,
            api_key_id=api_key_id,
            tenant_id=tenant_id,
            name=request.name,
            template_id=request.template_id,
            is_active=request.is_active,
            is_default=request.is_default
        )

        # Get full details
        keys = ApiKeyService.list_api_keys(db, tenant_id)
        updated_key = next((k for k in keys if k["id"] == api_key_id), None)

        if not updated_key:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated API key")

        return ApiKeyResponse(**updated_key)

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update API key")


@router.delete("/{api_key_id}", status_code=204)
async def delete_api_key(
    api_key_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Delete an API key

    Args:
        api_key_id: API key UUID
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Raises:
        400: If trying to delete the only key or default key
        404: If API key not found
        500: If deletion fails
    """
    try:
        result = ApiKeyService.delete_api_key(db, api_key_id, tenant_id)

        if not result:
            raise HTTPException(status_code=404, detail="API key not found")

        return None

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete API key")


@router.post("/{api_key_id}/regenerate")
async def regenerate_api_key(
    api_key_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Regenerate the API key string (creates a new key value)

    Args:
        api_key_id: API key UUID
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        New API key string

    Raises:
        404: If API key not found
        500: If regeneration fails
    """
    try:
        new_api_key = ApiKeyService.regenerate_api_key(db, api_key_id, tenant_id)

        return {
            "api_key": new_api_key,
            "message": "API key regenerated successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error regenerating API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate API key")


@router.post("/{api_key_id}/blacklists")
async def associate_blacklist(
    api_key_id: str,
    request: AssociateBlacklistRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Associate a blacklist with an API key

    Args:
        api_key_id: API key UUID
        request: Association parameters
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Returns:
        Success message

    Raises:
        400: If blacklist or key invalid, or already associated
        404: If API key or blacklist not found
        500: If association fails
    """
    try:
        result = ApiKeyService.associate_blacklist(
            db=db,
            api_key_id=api_key_id,
            blacklist_id=request.blacklist_id,
            tenant_id=tenant_id
        )

        if not result:
            raise HTTPException(status_code=400, detail="Blacklist already associated with this API key")

        return {
            "message": "Blacklist associated successfully",
            "api_key_id": api_key_id,
            "blacklist_id": request.blacklist_id
        }

    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error associating blacklist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to associate blacklist")


@router.delete("/{api_key_id}/blacklists/{blacklist_id}", status_code=204)
async def disassociate_blacklist(
    api_key_id: str,
    blacklist_id: int,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """Remove blacklist association from an API key

    Args:
        api_key_id: API key UUID
        blacklist_id: Blacklist ID
        tenant_id: Current tenant ID (from auth)
        db: Database session

    Raises:
        404: If association not found
        500: If disassociation fails
    """
    try:
        result = ApiKeyService.disassociate_blacklist(
            db=db,
            api_key_id=api_key_id,
            blacklist_id=blacklist_id,
            tenant_id=tenant_id
        )

        if not result:
            raise HTTPException(status_code=404, detail="Blacklist association not found")

        return None

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disassociating blacklist: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to disassociate blacklist")
