"""
Public landing endpoints (no auth). Safe for anonymous traffic.
Used by V1 landing page for Top Picks section.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.probability_engine import get_probability_engine

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple in-memory cache (single slot, TTL-based)
_cache_payload: Optional[Dict[str, Any]] = None
_cache_ts: float = 0.0
CACHE_TTL_SECONDS = 90
MAX_PICKS = 8
# Sports tried in priority order; pipeline already filters by upcoming window
SPORTS_FOR_LANDING = ["NFL", "NBA", "NHL", "MLB"]


class TodaysPickItem(BaseModel):
    """Single pick card for the public landing page."""
    sport: str = Field(description="Sport code, e.g. NFL, NBA")
    event_id: str = Field(description="Game/event id for deep links")
    matchup: str = Field(description="e.g. Away @ Home")
    market: str = Field(description="moneyline | spread | total")
    selection: str = Field(description="Pick label, e.g. Chiefs, Over 47.5")
    odds: Optional[float] = Field(default=None, description="American odds if available")
    confidence: float = Field(description="0–100 confidence from model")
    start_time: Optional[str] = Field(default=None, description="ISO start time")
    analysis_url: str = Field(default="/app")
    builder_url: str = Field(default="/app")


class TodaysTopPicksResponse(BaseModel):
    """Response for GET /api/public/todays-top-picks."""
    as_of: str = Field(description="ISO timestamp of response")
    date: str = Field(description="YYYY-MM-DD (today UTC)")
    picks: List[TodaysPickItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _market_display(market_type: str) -> str:
    m = (market_type or "").lower()
    return {"h2h": "moneyline", "spreads": "spread", "totals": "total"}.get(m, market_type or "moneyline")


def _selection_display(
    outcome: str,
    market_type: str,
    home_team: Optional[str],
    away_team: Optional[str],
) -> str:
    if not outcome:
        return "—"
    o = outcome.strip()
    m = (market_type or "").lower()
    if m == "h2h":
        if o.lower() == "home" and home_team:
            return home_team
        if o.lower() == "away" and away_team:
            return away_team
    return o


def _parse_american_odds(price: Any) -> Optional[float]:
    if price is None:
        return None
    if isinstance(price, (int, float)) and price != 0:
        return float(price)
    s = str(price).strip().replace("+", "").replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get(
    "/public/todays-top-picks",
    response_model=TodaysTopPicksResponse,
    summary="Top picks for landing (public, no auth)",
)
async def get_todays_top_picks(db: AsyncSession = Depends(get_db)) -> TodaysTopPicksResponse:
    """
    Highest-confidence upcoming picks from the same pipeline used by the app.
    No auth required. Cached 90 s. Returns empty list (never 500) on failure.
    """
    global _cache_payload, _cache_ts

    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")

    try:
        # Serve from cache if fresh
        if _cache_payload is not None and (now.timestamp() - _cache_ts) < CACHE_TTL_SECONDS:
            return TodaysTopPicksResponse(**_cache_payload)

        picks: List[Dict[str, Any]] = []

        for sport in SPORTS_FOR_LANDING:
            if len(picks) >= MAX_PICKS:
                break
            try:
                engine = get_probability_engine(db, sport)
                candidates = await engine.get_candidate_legs(
                    sport=sport,
                    min_confidence=0.0,
                    max_legs=200,
                    week=None,
                    include_player_props=False,
                    now_utc=now,
                )
                if not candidates:
                    continue

                # Pipeline already restricts to upcoming window; use all candidates, sort by confidence
                sorted_candidates = sorted(
                    candidates,
                    key=lambda x: float(x.get("confidence_score") or 0),
                    reverse=True,
                )

                for c in sorted_candidates:
                    if len(picks) >= MAX_PICKS:
                        break
                    event_id = str(c.get("game_id") or "")
                    market_type = (c.get("market_type") or "h2h").lower()
                    outcome = str(c.get("outcome") or "")
                    pick_data = {
                        "sport": sport,
                        "event_id": event_id,
                        "matchup": str(c.get("game") or "").strip() or "TBD",
                        "market": _market_display(market_type),
                        "selection": _selection_display(
                            outcome, market_type,
                            c.get("home_team"), c.get("away_team"),
                        ),
                        "odds": _parse_american_odds(c.get("odds")),
                        "confidence": round(float(c.get("confidence_score") or 0), 1),
                        "start_time": c.get("start_time"),
                        "analysis_url": "/app",
                        "builder_url": f"/app?prefill_game_id={event_id}" if event_id else "/app",
                    }
                    picks.append(pick_data)

            except Exception as sport_err:
                logger.warning("top_picks sport=%s skipped: %s", sport, sport_err)
                continue

        payload = {"as_of": now.isoformat(), "date": date_iso, "picks": picks}
        _cache_payload = payload
        _cache_ts = now.timestamp()

        logger.info("top_picks built %d pick(s) as_of=%s", len(picks), date_iso)
        return TodaysTopPicksResponse(**payload)

    except Exception as e:
        logger.warning("top_picks failed (returning empty): %s", e, exc_info=True)
        return TodaysTopPicksResponse(as_of=now.isoformat(), date=date_iso, picks=[])
