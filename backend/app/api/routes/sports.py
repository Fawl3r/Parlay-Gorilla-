"""Sports metadata endpoints (includes in-season status)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.game import Game
from app.services.sports_availability_service import SportsAvailabilityService
from app.services.sports_config import list_supported_sports
from app.services.sports_ui_policy import SportsUiPolicy
from app.services.the_odds_api_client import OddsApiKeys, TheOddsApiClient

router = APIRouter()


_FINISHED_STATUSES = ("finished", "closed", "complete", "Final")


@router.get("/sports", summary="List supported sports (with season status)")
async def list_sports(db: AsyncSession = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Return metadata for supported sports plus a computed `in_season` flag.

    `in_season` is primarily driven by The Odds API `/sports` `active` flag. If the
    external call fails, we fall back to local DB activity (recent or upcoming games).
    """
    configs = list_supported_sports()
    now = datetime.utcnow()
    ui_policy = SportsUiPolicy.default()

    api = TheOddsApiClient(
        api_keys=OddsApiKeys(
            primary=settings.the_odds_api_key,
            fallback=getattr(settings, "the_odds_api_fallback_key", None),
        )
    )
    availability = SportsAvailabilityService(api=api)
    active_by_odds_key = await availability.get_active_by_odds_key()

    items: List[Dict[str, Any]] = []
    for cfg in configs:
        if ui_policy.should_hide(cfg.slug):
            continue
        odds_active: Optional[bool] = active_by_odds_key.get(cfg.odds_key)
        upcoming_count = await _count_upcoming_games(db=db, sport_code=cfg.code, now=now, lookahead_days=cfg.lookahead_days)
        recent_count = await _count_recent_games(db=db, sport_code=cfg.code, now=now, lookback_days=30)

        if odds_active is True:
            in_season = True
        elif odds_active is False:
            in_season = False
        else:
            # Fallback when Odds API `/sports` is unavailable.
            in_season = bool(upcoming_count > 0 or recent_count > 0)

        status_label = "Not in season" if not in_season else "In season"
        item = ui_policy.apply_overrides(
            {
                "slug": cfg.slug,
                "code": cfg.code,
                "odds_key": cfg.odds_key,
                "display_name": cfg.display_name,
                "default_markets": cfg.default_markets,
                "supported_markets": cfg.supported_markets,
                "lookahead_days": cfg.lookahead_days,
                "in_season": in_season,
                "status_label": status_label,
                "odds_api_active": odds_active,
                "upcoming_games": int(upcoming_count),
            }
        )
        items.append(item)

    # Keep stable ordering (config file order) so UI doesn't jump.
    return items


async def _count_upcoming_games(
    *,
    db: AsyncSession,
    sport_code: str,
    now: datetime,
    lookahead_days: int,
) -> int:
    cutoff_time = now - timedelta(hours=24)
    future_cutoff = now + timedelta(days=int(lookahead_days or 0))
    result = await db.execute(
        select(func.count())
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time >= cutoff_time)
        .where(Game.start_time <= future_cutoff)
        .where((Game.status.is_(None)) | (Game.status.notin_(_FINISHED_STATUSES)))
    )
    return int(result.scalar_one() or 0)


async def _count_recent_games(*, db: AsyncSession, sport_code: str, now: datetime, lookback_days: int) -> int:
    cutoff = now - timedelta(days=int(lookback_days or 0))
    result = await db.execute(
        select(func.count())
        .select_from(Game)
        .where(Game.sport == sport_code)
        .where(Game.start_time.is_not(None))
        .where(Game.start_time >= cutoff)
    )
    return int(result.scalar_one() or 0)




