"""Upset finder API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.access_control import require_upset_finder_access
from app.core.dependencies import get_db
from app.middleware.rate_limiter import rate_limit
from app.models.user import User

router = APIRouter()


@router.get("/parlay/upsets/{sport}")
@rate_limit("20/hour")
async def find_upsets(
    request: Request,
    sport: str,
    min_edge: float = 0.03,
    max_results: int = 20,
    risk_tier: Optional[str] = None,
    week: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_upset_finder_access),
):
    """
    Find upset candidates with positive expected value.

    Premium-only feature.
    """
    _ = request, current_user
    from app.services.upset_finder import get_upset_finder

    try:
        finder = get_upset_finder(db, sport.upper())
        upsets = await finder.find_upsets(
            min_edge=min_edge,
            max_results=max_results,
            risk_tier=risk_tier,
            week=week,
        )
        return {
            "sport": sport.upper(),
            "count": len(upsets),
            "upsets": [u.to_dict() for u in upsets],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to find upsets: {str(exc)}") from exc


