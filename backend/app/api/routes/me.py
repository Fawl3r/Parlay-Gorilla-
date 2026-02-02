"""Me API: GET /api/me/entitlements (single source of truth for UI)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_optional_user
from app.models.user import User
from app.schemas.entitlements import EntitlementsResponse
from app.services.entitlements import EntitlementService

router = APIRouter()


@router.get("/entitlements", response_model=EntitlementsResponse)
async def get_entitlements(
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Get current user entitlements (plan, credits, features).

    Returns 200 for both anonymous and authenticated users.
    Anonymous: is_authenticated=False, plan=anon.
    """
    service = EntitlementService(db)
    return await service.get_entitlements_for_user(current_user)
