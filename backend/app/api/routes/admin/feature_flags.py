"""
Admin feature flags API routes.

Provides feature flag management:
- List all flags
- Create/update/delete flags
- Toggle flags
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError, ProgrammingError
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.dependencies import get_db

logger = logging.getLogger(__name__)
from app.models.user import User
from app.services.feature_flag_service import FeatureFlagService
from .auth import require_admin

router = APIRouter()


class FeatureFlagResponse(BaseModel):
    """Feature flag response model."""
    id: str
    key: str
    name: Optional[str]
    description: Optional[str]
    enabled: bool
    category: Optional[str]
    targeting_rules: Optional[Dict[str, Any]]
    created_at: str
    updated_at: str


class FeatureFlagCreateRequest(BaseModel):
    """Request model for creating a feature flag."""
    key: str
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = False
    category: Optional[str] = None
    targeting_rules: Optional[Dict[str, Any]] = None


class FeatureFlagUpdateRequest(BaseModel):
    """Request model for updating a feature flag."""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    category: Optional[str] = None
    targeting_rules: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[FeatureFlagResponse])
async def list_feature_flags(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """List all feature flags. Returns [] on DB errors."""
    try:
        service = FeatureFlagService(db)
        flags = await service.get_all_flags()
        return [
            FeatureFlagResponse(
                id=str(f.id),
                key=f.key,
                name=f.name,
                description=f.description,
                enabled=f.enabled,
                category=f.category,
                targeting_rules=f.targeting_rules,
                created_at=f.created_at.isoformat() if f.created_at else "",
                updated_at=f.updated_at.isoformat() if f.updated_at else "",
            )
            for f in (flags or [])
        ]
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "feature_flags.list", "error": str(e)}, exc_info=True)
        return []


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Get a single feature flag by key. Returns minimal body on DB errors."""
    try:
        service = FeatureFlagService(db)
        flag = await service.get_flag(key)
        if not flag:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Feature flag '{key}' not found")
        return FeatureFlagResponse(
            id=str(flag.id),
            key=flag.key,
            name=flag.name,
            description=flag.description,
            enabled=flag.enabled,
            category=flag.category,
            targeting_rules=flag.targeting_rules,
            created_at=flag.created_at.isoformat() if flag.created_at else "",
            updated_at=flag.updated_at.isoformat() if flag.updated_at else "",
        )
    except HTTPException:
        raise
    except (OperationalError, ProgrammingError, Exception) as e:
        logger.warning("admin.endpoint.fallback", extra={"endpoint": "feature_flags.get", "error": str(e)}, exc_info=True)
        return FeatureFlagResponse(id="", key=key, name=None, description=None, enabled=False, category=None, targeting_rules=None, created_at="", updated_at="")


@router.post("", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(
    request: FeatureFlagCreateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Create a new feature flag.
    """
    service = FeatureFlagService(db)
    
    # Check if key already exists
    existing = await service.get_flag(request.key)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Feature flag with key '{request.key}' already exists"
        )
    
    flag = await service.create_flag(
        key=request.key,
        name=request.name,
        description=request.description,
        enabled=request.enabled,
        category=request.category,
        targeting_rules=request.targeting_rules,
    )
    
    return FeatureFlagResponse(
        id=str(flag.id),
        key=flag.key,
        name=flag.name,
        description=flag.description,
        enabled=flag.enabled,
        category=flag.category,
        targeting_rules=flag.targeting_rules,
        created_at=flag.created_at.isoformat() if flag.created_at else "",
        updated_at=flag.updated_at.isoformat() if flag.updated_at else "",
    )


@router.patch("/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    key: str,
    request: FeatureFlagUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Update a feature flag.
    """
    service = FeatureFlagService(db)
    
    flag = await service.update_flag(
        key=key,
        name=request.name,
        description=request.description,
        enabled=request.enabled,
        category=request.category,
        targeting_rules=request.targeting_rules,
    )
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found"
        )
    
    return FeatureFlagResponse(
        id=str(flag.id),
        key=flag.key,
        name=flag.name,
        description=flag.description,
        enabled=flag.enabled,
        category=flag.category,
        targeting_rules=flag.targeting_rules,
        created_at=flag.created_at.isoformat() if flag.created_at else "",
        updated_at=flag.updated_at.isoformat() if flag.updated_at else "",
    )


@router.post("/{key}/toggle", response_model=FeatureFlagResponse)
async def toggle_feature_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Toggle a feature flag on/off.
    """
    service = FeatureFlagService(db)
    flag = await service.toggle_flag(key)
    
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found"
        )
    
    return FeatureFlagResponse(
        id=str(flag.id),
        key=flag.key,
        name=flag.name,
        description=flag.description,
        enabled=flag.enabled,
        category=flag.category,
        targeting_rules=flag.targeting_rules,
        created_at=flag.created_at.isoformat() if flag.created_at else "",
        updated_at=flag.updated_at.isoformat() if flag.updated_at else "",
    )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(
    key: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """
    Delete a feature flag.
    """
    service = FeatureFlagService(db)
    deleted = await service.delete_flag(key)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found"
        )

