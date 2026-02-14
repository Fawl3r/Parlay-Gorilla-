"""Sports metadata endpoints (includes in-season status)."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.game import Game
from app.services.sport_state_service import get_sport_state
from app.services.sports_availability_service import SportsAvailabilityService
from app.services.sports_config import (
    apply_sport_visibility_overrides,
    is_sport_visible,
    list_supported_sports,
)
from app.services.the_odds_api_client import OddsApiKeys, TheOddsApiClient

router = APIRouter()
logger = logging.getLogger(__name__)


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

    api = TheOddsApiClient(
        api_keys=OddsApiKeys(
            primary=settings.the_odds_api_key,
            fallback=getattr(settings, "the_odds_api_fallback_key", None),
        )
    )
    availability = SportsAvailabilityService(api=api)
    try:
        active_by_odds_key = await availability.get_active_by_odds_key()
    except Exception:
        logger.exception("Error fetching Odds API /sports activity; using empty activity map")
        active_by_odds_key = {}

    items: List[Dict[str, Any]] = []
    for cfg in configs:
        if not is_sport_visible(cfg):
            continue
        odds_active: Optional[bool] = active_by_odds_key.get(cfg.odds_key)
        try:
            state_result = await get_sport_state(db=db, sport_code=cfg.code, now=now)
        except Exception:
            logger.exception("Error computing sport_state for %s; returning safe defaults", cfg.code)
            state_result = {
                "sport_state": "OFFSEASON",
                "next_game_at": None,
                "last_game_at": None,
                "state_reason": "state_compute_error",
                "is_enabled": False,
                "days_to_next": None,
                "preseason_enable_days": None,
                "upcoming_soon_count": 0,
                "recent_count": 0,
            }
        sport_state = state_result["sport_state"]
        next_game_at = state_result.get("next_game_at")
        last_game_at = state_result.get("last_game_at")
        state_reason = state_result.get("state_reason", "")
        is_enabled = state_result.get("is_enabled", False)
        days_to_next = state_result.get("days_to_next")
        preseason_enable_days = state_result.get("preseason_enable_days")
        upcoming_soon_count = state_result.get("upcoming_soon_count", 0)
        recent_count = state_result.get("recent_count", 0)

        if odds_active is True:
            in_season = sport_state not in ("OFFSEASON", "PRESEASON")
        elif odds_active is False:
            in_season = sport_state not in ("OFFSEASON", "PRESEASON")
        else:
            in_season = sport_state not in ("OFFSEASON", "PRESEASON")

        if sport_state == "IN_BREAK":
            status_label = "League break"
        elif sport_state == "OFFSEASON":
            status_label = "Offseason"
        elif sport_state == "PRESEASON":
            status_label = "Preseason"
        elif sport_state == "POSTSEASON":
            status_label = "Postseason"
        elif sport_state == "IN_SEASON":
            status_label = "In season"
        else:
            status_label = "Not in season"

        item = apply_sport_visibility_overrides(
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
                "upcoming_games": int(upcoming_soon_count),
                "sport_state": sport_state,
                "next_game_at": next_game_at,
                "last_game_at": last_game_at,
                "state_reason": state_reason,
                "is_enabled": is_enabled,
                "days_to_next": days_to_next,
                "preseason_enable_days": preseason_enable_days,
            },
            cfg.slug,
        )
        items.append(item)

    # Keep stable ordering (config file order) so UI doesn't jump.
    return items




