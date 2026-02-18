"""
Public landing endpoints (no auth). Safe for anonymous traffic.
Used by V1 landing page for Today's Top Picks.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.probability_engine import get_probability_engine

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache: (date_iso) -> { "as_of", "date", "picks" }; TTL 90s
_todays_picks_cache: Dict[str, Dict[str, Any]] = {}
_todays_picks_cache_ts: Dict[str, float] = {}
CACHE_TTL_SECONDS = 90
MAX_PICKS = 8
SPORTS_FOR_LANDING = ["NFL", "NBA", "NHL"]  # Order: try NFL first, then others for variety


class TodaysPickItem(BaseModel):
    """Single pick for public landing (no internal IDs in response)."""
    sport: str = Field(description="Sport code, e.g. NFL, NBA")
    event_id: str = Field(description="Game/event id for deep links")
    matchup: str = Field(description="e.g. Away @ Home")
    market: str = Field(description="moneyline|spread|total")
    selection: str = Field(description="Pick label, e.g. Chiefs, Over 47.5")
    odds: Optional[float] = Field(default=None, description="American odds if available")
    confidence: float = Field(description="0-100 confidence from model")
    start_time: Optional[str] = Field(default=None, description="ISO start time")
    analysis_url: str = Field(default="/app", description="Link to app/analysis")
    builder_url: str = Field(default="/app", description="Link to builder, optionally with prefill")


class TodaysTopPicksResponse(BaseModel):
    """Response for GET /api/public/todays-top-picks."""
    as_of: str = Field(description="ISO timestamp of response")
    date: str = Field(description="YYYY-MM-DD (today UTC)")
    picks: List[TodaysPickItem] = Field(default_factory=list)


def _market_display(market_type: str) -> str:
    m = (market_type or "").lower()
    if m == "h2h":
        return "moneyline"
    if m == "spreads":
        return "spread"
    if m == "totals":
        return "total"
    return market_type or "moneyline"


def _selection_display(outcome: str, market_type: str, home_team: Optional[str], away_team: Optional[str]) -> str:
    """Human-readable pick label."""
    if not outcome:
        return "—"
    o = (outcome or "").strip()
    m = (market_type or "").lower()
    if m == "h2h":
        if o.lower() == "home" and home_team:
            return home_team
        if o.lower() == "away" and away_team:
            return away_team
        return o
    if m in ("spreads", "totals"):
        return o  # e.g. "Over 47.5", "Chiefs -3.5"
    return o


def _parse_american_odds(price: Any) -> Optional[float]:
    """Parse price string to American odds number if possible."""
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


def _is_today_utc(start_time_iso: Optional[str]) -> bool:
    if not start_time_iso:
        return False
    try:
        s = str(start_time_iso).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.date() == datetime.now(timezone.utc).date()
    except Exception:
        return False


@router.get(
    "/public/todays-top-picks",
    response_model=TodaysTopPicksResponse,
    summary="Today's top picks for landing (public)",
)
async def get_todays_top_picks(db: AsyncSession = Depends(get_db)) -> TodaysTopPicksResponse:
    """
    Returns today's highest-confidence picks from the same pipeline used by the app.
    No auth required. Cached briefly for performance.
    If no picks are available for today (or DB/pipeline fails), returns empty list (no mock data).
    """
    now = datetime.now(timezone.utc)
    date_iso = now.strftime("%Y-%m-%d")
    cache_key = date_iso

    try:
        # Cache read
        if cache_key in _todays_picks_cache and cache_key in _todays_picks_cache_ts:
            age = now.timestamp() - _todays_picks_cache_ts[cache_key]
            if age < CACHE_TTL_SECONDS:
                return TodaysTopPicksResponse(**_todays_picks_cache[cache_key])

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
                today_only = [c for c in candidates if _is_today_utc(c.get("start_time"))]
                today_only.sort(key=lambda x: float(x.get("confidence_score") or 0), reverse=True)
                for c in today_only:
                    if len(picks) >= MAX_PICKS:
                        break
                    event_id = str(c.get("game_id") or "")
                    matchup = str(c.get("game") or "").strip() or "TBD"
                    market_type = (c.get("market_type") or "h2h").lower()
                    outcome = str(c.get("outcome") or "")
                    home_team = c.get("home_team")
                    away_team = c.get("away_team")
                    selection = _selection_display(outcome, market_type, home_team, away_team)
                    confidence = float(c.get("confidence_score") or 0)
                    start_time = c.get("start_time")
                    odds_val = _parse_american_odds(c.get("odds"))
                    builder_url = f"/app?prefill_game_id={event_id}" if event_id else "/app"
                    picks.append({
                        "sport": sport,
                        "event_id": event_id,
                        "matchup": matchup,
                        "market": _market_display(market_type),
                        "selection": selection,
                        "odds": odds_val,
                        "confidence": round(confidence, 1),
                        "start_time": start_time,
                        "analysis_url": "/app",
                        "builder_url": builder_url,
                    })
            except Exception as e:
                logger.warning("todays_top_picks sport=%s error=%s", sport, e, exc_info=True)
                continue

        as_of = now.isoformat()
        payload = {
            "as_of": as_of,
            "date": date_iso,
            "picks": picks,
        }
        _todays_picks_cache[cache_key] = payload
        _todays_picks_cache_ts[cache_key] = now.timestamp()

        return TodaysTopPicksResponse(**payload)
    except Exception as e:
        logger.warning("todays_top_picks failed (returning empty): %s", e, exc_info=True)
        return TodaysTopPicksResponse(
            as_of=now.isoformat(),
            date=date_iso,
            picks=[],
        )
