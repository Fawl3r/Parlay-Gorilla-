# backend/app/services/traffic_ranker.py
"""
Traffic ranker - determine which games get props based on page views and traffic signals.

This module provides both:
1. Database-backed traffic ranking (for props gating)
2. Smart traffic scoring (for prioritization/ranking)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import log
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_page_views import AnalysisPageViews


@dataclass(frozen=True)
class TrafficScore:
    """
    score: 0.0 - 1.0 (higher = should be prioritized / featured / generated first)
    debug: breakdown of signal contributions (for logging / tuning)
    """
    score: float
    debug: Dict[str, Any]


def _clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1.0 else x


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        # ensure tz-aware
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        # Accept ISO strings; safe fallback
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _log1p_norm(x: float, cap: float) -> float:
    """
    Compress large counts (page views) to 0..1 using log scale.
    cap: approximate "high" value where score nears 1.
    """
    if x <= 0:
        return 0.0
    # log(1+x) / log(1+cap)
    return _clamp01(log(1 + x) / log(1 + cap))


def _recency_norm(dt: Optional[datetime], half_life_hours: float) -> float:
    """
    Exponential decay based on age. Newer -> closer to 1.
    half_life_hours: after this many hours, signal halves.
    """
    if not dt:
        return 0.5  # unknown recency -> neutral-ish
    age = (_now_utc() - dt).total_seconds()
    if age < 0:
        age = 0
    half_life = half_life_hours * 3600.0
    if half_life <= 0:
        return 0.5
    # decay = 0.5^(age/half_life)
    decay = 0.5 ** (age / half_life)
    return _clamp01(decay)


def _sport_seasonality_boost(sport: Optional[str], when: Optional[datetime] = None) -> float:
    """
    Very lightweight seasonality without needing web calls.
    Returns 0..1 where higher = sport is 'hotter' right now.
    """
    sport = (sport or "").strip().lower()
    now = when or _now_utc()
    m = now.month

    # Simple seasonal peaks
    if sport in {"nfl", "american football"}:
        # NFL peak roughly Sep-Feb
        return 1.0 if m in {9, 10, 11, 12, 1, 2} else 0.35
    if sport in {"nba", "basketball"}:
        # Oct-Jun
        return 0.95 if m in {10, 11, 12, 1, 2, 3, 4, 5, 6} else 0.55
    if sport in {"nhl", "hockey"}:
        # Oct-Jun
        return 0.9 if m in {10, 11, 12, 1, 2, 3, 4, 5, 6} else 0.5
    if sport in {"mlb", "baseball"}:
        # Mar-Oct
        return 0.95 if m in {3, 4, 5, 6, 7, 8, 9, 10} else 0.45
    if sport in {"ncaaf", "college football"}:
        # Aug-Jan
        return 0.9 if m in {8, 9, 10, 11, 12, 1} else 0.35
    if sport in {"ncaab", "college basketball"}:
        # Nov-Apr (March Madness spike)
        if m == 3:
            return 1.0
        return 0.85 if m in {11, 12, 1, 2, 4} else 0.5

    return 0.6  # unknown sports stay neutral-ish


def _seo_slug_quality(slug: Optional[str]) -> float:
    """
    Quick SEO heuristic: short, readable, keyword-rich slugs tend to perform better.
    """
    if not slug:
        return 0.5
    s = slug.strip().lower()
    length = len(s)
    # penalize very long or very short
    if length < 8:
        base = 0.55
    elif length <= 60:
        base = 0.8
    else:
        base = 0.6

    # reward hyphenated, readable
    hyphens = s.count("-")
    if hyphens >= 2:
        base += 0.05
    if "vs" in s or "at" in s:
        base += 0.05

    return _clamp01(base)


def _odds_popularity_proxy(odds: Optional[Dict[str, Any]]) -> float:
    """
    Estimate 'public interest' from odds data without needing exact handle.
    Heuristics:
      - more bookmakers = more liquidity/interest
      - more markets (h2h/spread/totals) present = more interest
    """
    if not odds:
        return 0.5

    bookmakers = odds.get("bookmakers") or odds.get("sportsbooks") or []
    markets = odds.get("markets") or []

    # Some apps store odds in different shapes; handle both
    num_books = len(bookmakers) if isinstance(bookmakers, list) else 0
    num_markets = len(markets) if isinstance(markets, list) else 0

    # Normalize with mild caps
    books_score = _clamp01(num_books / 10.0)   # 10 books ~ max
    markets_score = _clamp01(num_markets / 6.0)  # 6 markets ~ max

    # If odds look richer (more outcomes/prices), bump slightly
    richness = 0.0
    try:
        if isinstance(bookmakers, list) and bookmakers:
            # count total market entries under first few books
            total_markets = 0
            for b in bookmakers[:3]:
                total_markets += len((b.get("markets") or []))
            richness = _clamp01(total_markets / 10.0)
    except Exception:
        richness = 0.0

    score = 0.45 * books_score + 0.35 * markets_score + 0.20 * richness
    return _clamp01(0.35 + 0.65 * score)  # keep it in a safe middle if sparse


class TrafficRanker:
    """
    Traffic ranker that supports both:
    1. Database-backed props gating (is_props_enabled_for_game)
    2. Smart traffic scoring for prioritization (score method)
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize with database session for props gating.
        
        Args:
            db: AsyncSession for querying analysis_page_views
        """
        self._db = db
        self._top_games_cache: Optional[Dict[str, Set[UUID]]] = None
        self._cache_expires_at: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # 5 minutes
        
        # Scoring weights (can be customized)
        self.weights = {
            "pageviews": 0.35,
            "recency": 0.20,
            "odds_popularity": 0.15,
            "seasonality": 0.15,
            "seo": 0.10,
            "trending": 0.05,
        }
        self.pageview_cap = 5000.0
        self.recency_half_life_hours = 24.0
    
    async def get_top_game_ids(
        self,
        league: str,
        window_days: int = 2,
        limit: int = 5,
    ) -> List[UUID]:
        """
        Get top game IDs by page views over last N days.
        
        Args:
            league: League code (NFL, NBA, etc.)
            window_days: Number of days to look back
            limit: Maximum number of games to return
            
        Returns:
            List of game IDs (UUIDs)
        """
        # Check cache
        if self._top_games_cache and self._cache_expires_at:
            if datetime.now(tz=timezone.utc) < self._cache_expires_at:
                return list(self._top_games_cache.get(league.upper(), set()))[:limit]
        
        # Query database
        cutoff_date = date.today() - timedelta(days=window_days)
        
        result = await self._db.execute(
            select(
                AnalysisPageViews.game_id,
                func.sum(AnalysisPageViews.views).label("total_views"),
            )
            .where(AnalysisPageViews.league == league.upper())
            .where(AnalysisPageViews.view_bucket_date >= cutoff_date)
            .group_by(AnalysisPageViews.game_id)
            .order_by(func.sum(AnalysisPageViews.views).desc())
            .limit(limit)
        )
        
        game_ids = [row.game_id for row in result.all()]
        
        # Update cache
        if self._top_games_cache is None:
            self._top_games_cache = {}
        self._top_games_cache[league.upper()] = set(game_ids)
        self._cache_expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=self._cache_ttl_seconds)
        
        return game_ids
    
    async def is_props_enabled_for_game(self, game_id: UUID, league: str) -> bool:
        """
        Check if props should be enabled for a game based on traffic rank.
        
        Args:
            game_id: Game UUID
            league: League code
            
        Returns:
            True if game is in top N by traffic, False otherwise
        """
        top_games = await self.get_top_game_ids(league=league, window_days=2, limit=5)
        return game_id in top_games

    def score(self, payload: Dict[str, Any]) -> TrafficScore:
        """
        Score a game/analysis for traffic prioritization.
        
        Expected payload (flexible):
          - page_views: int
          - views_24h: int (optional, better than lifetime)
          - created_at / updated_at / game_time / start_time: datetime or ISO str
          - sport: "NFL"/"NBA"/...
          - slug: "bears-vs-packers-week-..."
          - odds: dict (any shape; we only use proxies)
          - trending: float 0..1 (optional)
          
        Returns:
            TrafficScore with score (0.0-1.0) and debug breakdown
        """
        debug: Dict[str, Any] = {}

        # 1) Pageviews: prefer recent views if available
        views_24h = payload.get("views_24h")
        page_views = payload.get("page_views") if views_24h is None else views_24h
        try:
            pv = float(page_views or 0)
        except Exception:
            pv = 0.0
        pv_norm = _log1p_norm(pv, cap=self.pageview_cap)
        debug["pageviews_raw"] = pv
        debug["pageviews_norm"] = pv_norm

        # 2) Recency: pick best timestamp
        dt = (
            _parse_dt(payload.get("game_time"))
            or _parse_dt(payload.get("start_time"))
            or _parse_dt(payload.get("updated_at"))
            or _parse_dt(payload.get("created_at"))
        )
        recency = _recency_norm(dt, half_life_hours=self.recency_half_life_hours)
        debug["recency_dt"] = dt.isoformat() if dt else None
        debug["recency_norm"] = recency

        # 3) Odds popularity proxy
        odds = payload.get("odds")
        odds_pop = _odds_popularity_proxy(odds if isinstance(odds, dict) else None)
        debug["odds_popularity_norm"] = odds_pop

        # 4) Sport seasonality
        sport = payload.get("sport")
        season = _sport_seasonality_boost(sport, when=_now_utc())
        debug["sport"] = sport
        debug["seasonality_norm"] = season

        # 5) SEO slug heuristic
        slug = payload.get("slug") or payload.get("path") or payload.get("seo_slug")
        seo = _seo_slug_quality(slug)
        debug["slug"] = slug
        debug["seo_norm"] = seo

        # 6) Trending (optional): you can pipe in something like rolling velocity
        trending = payload.get("trending")
        try:
            tr = float(trending) if trending is not None else 0.5
        except Exception:
            tr = 0.5
        tr = _clamp01(tr)
        debug["trending_norm"] = tr

        w = self.weights
        score = (
            w["pageviews"] * pv_norm
            + w["recency"] * recency
            + w["odds_popularity"] * odds_pop
            + w["seasonality"] * season
            + w["seo"] * seo
            + w["trending"] * tr
        )

        debug["weights"] = dict(w)
        debug["score_raw"] = score
        return TrafficScore(score=_clamp01(score), debug=debug)

    def rank(self, items: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], TrafficScore]]:
        """
        Rank a list of items by traffic score.
        
        Args:
            items: List of payload dicts to score
            
        Returns:
            List of (item, TrafficScore) tuples, sorted by score descending
        """
        scored = []
        for it in items:
            try:
                ts = self.score(it)
            except Exception as e:
                ts = TrafficScore(score=0.5, debug={"error": str(e)})
            scored.append((it, ts))
        scored.sort(key=lambda x: x[1].score, reverse=True)
        return scored
