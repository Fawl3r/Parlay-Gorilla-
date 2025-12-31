"""Analysis route aggregation.

This module keeps the import path `app.api.routes.analysis` stable while
splitting endpoints into small, focused route modules:
- list + cache routes: `analysis_list_routes.py`
- generation routes: `analysis_generate_routes.py`
- detail (article) routes: `analysis_detail_routes.py`

It also re-exports `_generate_slug` for backward compatibility with existing
scripts and schedulers.
"""

from __future__ import annotations

from datetime import datetime
import re

from fastapi import APIRouter

from app.api.routes.analysis_detail_routes import router as detail_router
from app.api.routes.analysis_generate_routes import router as generate_router
from app.api.routes.analysis_list_routes import _analysis_list_cache, router as list_router
from app.utils.nfl_week import calculate_nfl_week

router = APIRouter()
router.include_router(list_router)
router.include_router(generate_router)
router.include_router(detail_router)


def _generate_slug(home_team: str, away_team: str, league: str, game_time: datetime) -> str:
    """Generate URL-friendly slug for analysis page (backward compatible)."""
    home_clean = re.sub(r"[^a-z0-9]+", "-", (home_team or "").lower()).strip("-")
    away_clean = re.sub(r"[^a-z0-9]+", "-", (away_team or "").lower()).strip("-")

    if (league or "").upper() == "NFL":
        week = calculate_nfl_week(game_time)
        # Fallback to date format if week is None (e.g., before season start or after week 18)
        if week is not None:
            return f"{league.lower()}/{away_clean}-vs-{home_clean}-week-{week}-{game_time.year}"

    date_str = game_time.strftime("%Y-%m-%d")
    return f"{league.lower()}/{away_clean}-vs-{home_clean}-{date_str}"


__all__ = ["router", "_generate_slug", "_analysis_list_cache"]


