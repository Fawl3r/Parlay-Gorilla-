"""
Ops debug: GET /ops/sport-state/{sport_code} for sport state decision trace.

Gated by OPS_DEBUG_ENABLED and optional X-Ops-Token. Read-only; no secrets.
"""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.services.game_listing_window_service import get_listing_window_for_sport_state
from app.services.sport_state_policy import SportStatePolicy, get_policy_for_sport
from app.services.sport_state_service import get_sport_state
from app.services.sports_config import get_sport_config
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _window_reason(
    sport_state: str,
    policy: SportStatePolicy,
    window_start_utc: datetime | None,
    window_end_utc: datetime | None,
) -> str:
    """Human-readable reason for listing window (e.g. OFFSEASON_NONE, IN_SEASON_10D)."""
    if sport_state == "OFFSEASON" or (window_start_utc is None and window_end_utc is None):
        return "OFFSEASON_NONE"
    if sport_state in ("IN_SEASON", "POSTSEASON"):
        days = policy.listing_in_season_days
        return f"IN_SEASON_{days}D" if policy.mode == "cadence" else f"EVENT_BASED_{days}D"
    if sport_state in ("PRESEASON", "IN_BREAK"):
        days = policy.listing_preseason_days
        return f"PRESEASON_{days}D" if policy.mode == "cadence" else f"EVENT_BASED_{days}D"
    return "UNKNOWN"


async def _require_ops_debug(x_ops_token: str | None = Header(None, alias="X-Ops-Token")) -> None:
    """Raise 404 if ops debug disabled; 403 if token required and missing/wrong."""
    settings = get_settings()
    if not settings.ops_debug_enabled:
        raise HTTPException(status_code=404, detail="Not Found")
    if settings.ops_debug_token is not None and (settings.ops_debug_token or "").strip():
        if (x_ops_token or "").strip() != (settings.ops_debug_token or "").strip():
            raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/sport-state/{sport_code}")
async def get_sport_state_debug(
    sport_code: str,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_ops_debug),
) -> Dict[str, Any]:
    """
    Debug endpoint: full decision trace for sport state and listing window.

    Returns policy, get_sport_state payload, decision inputs, and listing window.
    Requires OPS_DEBUG_ENABLED=true; optionally X-Ops-Token if OPS_DEBUG_TOKEN is set.
    """
    try:
        config = get_sport_config(sport_code)
        code = config.code
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown sport")

    now = datetime.now(timezone.utc)
    policy = get_policy_for_sport(code)
    state_result = await get_sport_state(db, code, now=now, policy=policy)
    sport_state_value = state_result.get("sport_state", "")

    window = get_listing_window_for_sport_state(
        sport_state_value,
        now=now,
        policy=policy,
    )
    if window:
        window_start_utc = window.start_utc.isoformat()
        window_end_utc = window.end_utc.isoformat()
        window_reason = _window_reason(
            sport_state_value,
            policy,
            window.start_utc,
            window.end_utc,
        )
    else:
        window_start_utc = None
        window_end_utc = None
        window_reason = _window_reason(sport_state_value, policy, None, None)

    decision_inputs = {
        "upcoming_soon_count": state_result.get("upcoming_soon_count", 0),
        "upcoming_preseason_count": 0,  # reserved for future use
        "upcoming_postseason_soon_count": state_result.get("upcoming_postseason_soon_count", 0),
        "recent_count": state_result.get("recent_count", 0),
        "days_to_next": state_result.get("days_to_next"),
        "next_game_at": state_result.get("next_game_at"),
        "last_game_at": state_result.get("last_game_at"),
    }

    return {
        "sport_code": code,
        "now_utc": now.isoformat(),
        "policy": dataclasses.asdict(policy),
        "sport_state": state_result,
        "decision_inputs": decision_inputs,
        "listing_window": {
            "window_start_utc": window_start_utc,
            "window_end_utc": window_end_utc,
            "window_reason": window_reason,
        },
    }
