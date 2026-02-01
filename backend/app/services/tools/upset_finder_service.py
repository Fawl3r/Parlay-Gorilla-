"""
Upset Finder (tools): next-X-days scan using usable H2H odds + model probs.
Returns ROI-ranked candidates and honest meta (games_scanned, games_with_odds, missing_odds).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.market import Market
from app.services.analysis.analysis_repository import AnalysisRepository
from app.services.model_win_probability import compute_game_win_probability
from app.services.odds_snapshot_builder import OddsSnapshotBuilder
from app.services.sports_config import get_sport_config, list_supported_sports
from app.services.games_deduplication_service import GamesDeduplicationService
from app.services.tools.upset_candidate_quality import (
    UnderdogH2HPriceExtractor,
    UnderdogPriceStatsCalculator,
    UpsetCandidateSanityChecker,
)

logger = logging.getLogger(__name__)

DEFAULT_DAYS = 7
DEFAULT_MIN_EDGE = 3.0
DEFAULT_MAX_RESULTS = 20
DEFAULT_MIN_UNDERDOG_ODDS = 110
# Hard cap to prevent worst-case load (e.g., large soccer slates)
MAX_GAMES_SCAN = 250


from app.services.tools.upset_candidate_quality import _parse_american_odds, _implied_prob_from_american


def _has_usable_h2h(game: Game) -> bool:
    """True if game has at least one h2h market with >=2 valid odds (price or implied_prob)."""
    markets = getattr(game, "markets", None) or []
    for market in markets:
        if str(getattr(market, "market_type", "") or "").lower() != "h2h":
            continue
        odds_rows = getattr(market, "odds", None) or []
        valid = 0
        for odd in odds_rows:
            if getattr(odd, "price", None) and str(odd.price).strip():
                valid += 1
            elif getattr(odd, "implied_prob", None) is not None:
                valid += 1
            if valid >= 2:
                return True
    return False


@dataclass
class UpsetCandidateItem:
    """One upset candidate for the API response."""

    game_id: str
    start_time: str
    league: str
    home_team: str
    away_team: str
    underdog_side: str  # "home" | "away"
    underdog_team: str
    underdog_ml: int
    implied_prob: float
    model_prob: float
    edge: float
    confidence: float
    books_count: int = 0
    best_underdog_ml: Optional[int] = None
    median_underdog_ml: Optional[int] = None
    price_spread: Optional[int] = None
    worst_underdog_ml: Optional[int] = None
    flags: List[str] = field(default_factory=list)
    odds_quality: str = "bad"
    market_disagreement: Optional[str] = None
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "start_time": self.start_time,
            "league": self.league,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "underdog_side": self.underdog_side,
            "underdog_team": self.underdog_team,
            "underdog_ml": self.underdog_ml,
            "implied_prob": round(self.implied_prob, 4),
            "model_prob": round(self.model_prob, 4),
            "edge": round(self.edge, 2),
            "confidence": round(self.confidence, 2),
            "books_count": self.books_count,
            "best_underdog_ml": self.best_underdog_ml,
            "median_underdog_ml": self.median_underdog_ml,
            "price_spread": self.price_spread,
            "worst_underdog_ml": self.worst_underdog_ml,
            "flags": self.flags,
            "odds_quality": self.odds_quality,
            "market_disagreement": self.market_disagreement,
            "reasons": self.reasons,
        }


@dataclass
class UpsetFinderToolsResult:
    """Full response for GET /api/tools/upsets."""

    sport: str
    window_days: int
    min_edge: float
    generated_at: str
    candidates: List[UpsetCandidateItem]
    meta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sport": self.sport,
            "window_days": self.window_days,
            "min_edge": self.min_edge,
            "generated_at": self.generated_at,
            "candidates": [c.to_dict() for c in self.candidates],
            "meta": self.meta,
        }


class UpsetFinderToolsService:
    """
    ROI-focused upset finder: next X days, usable H2H only, model probs from cache or compute.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._snapshot_builder = OddsSnapshotBuilder()
        self._analysis_repo = AnalysisRepository(db)
        self._deduper = GamesDeduplicationService()
        self._price_extractor = UnderdogH2HPriceExtractor()
        self._price_stats = UnderdogPriceStatsCalculator()
        self._sanity = UpsetCandidateSanityChecker()

    async def scan_meta(
        self,
        sport: str,
        days: int = DEFAULT_DAYS,
    ) -> Dict[str, Any]:
        """
        CHEAP meta-only scan.

        Non-negotiable:
        - Only runs `_fetch_games()` and `_has_usable_h2h()` to count coverage.
        - Does NOT compute implied probs, model probs, candidates, or edges.
        """
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=max(1, days))
        sport_codes = self._resolve_sport_codes(sport)

        games = await self._fetch_games(sport_codes, now, end)
        games = self._deduper.dedupe(games)
        games_scanned = len(games)
        games_with_odds = 0
        for game in games:
            if _has_usable_h2h(game):
                games_with_odds += 1

        missing_odds = max(0, games_scanned - games_with_odds)
        games_scanned_capped = games_scanned >= MAX_GAMES_SCAN

        return {
            "games_scanned": games_scanned,
            "games_with_odds": games_with_odds,
            "missing_odds": missing_odds,
            "games_scanned_capped": games_scanned_capped,
        }

    async def find_candidates(
        self,
        sport: str,
        days: int = DEFAULT_DAYS,
        min_edge: float = DEFAULT_MIN_EDGE,
        max_results: int = DEFAULT_MAX_RESULTS,
        min_underdog_odds: int = DEFAULT_MIN_UNDERDOG_ODDS,
    ) -> UpsetFinderToolsResult:
        """
        Scan upcoming games in [now, now+days], filter to usable H2H, compute edges, return candidates + meta.
        """
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=max(1, days))
        sport_codes = self._resolve_sport_codes(sport)
        generated_at = now.isoformat()

        games = await self._fetch_games(sport_codes, now, end)
        games = self._deduper.dedupe(games)
        games_scanned = len(games)
        games_scanned_capped = games_scanned >= MAX_GAMES_SCAN
        games_with_odds = 0
        missing_odds = 0
        candidates: List[UpsetCandidateItem] = []
        rejected_reason_counts: Dict[str, int] = {}

        for game in games:
            if not _has_usable_h2h(game):
                missing_odds += 1
                continue
            games_with_odds += 1

            markets = getattr(game, "markets", None) or []
            snapshot = self._snapshot_builder.build(game=game, markets=markets)
            home_implied = self._get_implied_prob(snapshot, "home")
            away_implied = self._get_implied_prob(snapshot, "away")
            if home_implied is None or away_implied is None:
                continue

            model_home, model_away, confidence = await self._get_model_probs(game, snapshot)
            if model_home is None or model_away is None:
                continue

            if home_implied <= away_implied:
                underdog_side = "home"
                underdog_team = game.home_team
                underdog_implied = home_implied
                underdog_model = model_home
                underdog_ml_raw = snapshot.get("home_ml")
            else:
                underdog_side = "away"
                underdog_team = game.away_team
                underdog_implied = away_implied
                underdog_model = model_away
                underdog_ml_raw = snapshot.get("away_ml")

            underdog_ml_int = _parse_american_odds(underdog_ml_raw)
            if underdog_ml_int is None or underdog_ml_int < min_underdog_odds:
                continue

            edge_frac = underdog_model - underdog_implied
            edge_abs = abs(edge_frac)
            edge_pct = edge_frac * 100.0
            if edge_pct < min_edge:
                continue

            # Book/price stats across all H2H markets (trust booster)
            prices = self._price_extractor.extract_prices(
                home_team=game.home_team or "",
                away_team=game.away_team or "",
                markets=markets,
            )
            price_stats = self._price_stats.compute(prices)

            quality = self._sanity.assess(
                model_prob=underdog_model,
                implied_prob=underdog_implied,
                edge_abs=edge_abs,
                price_stats=price_stats,
            )
            if not quality.ok:
                key = quality.reject_reason or "unknown"
                rejected_reason_counts[key] = rejected_reason_counts.get(key, 0) + 1
                continue

            start_time_str = (
                game.start_time.isoformat() if game.start_time else ""
            )
            conf_0_1 = min(1.0, max(0.0, confidence / 100.0)) if confidence is not None else 0.5

            reasons = self._build_reasons(edge_pct, underdog_model, underdog_implied, conf_0_1)

            candidates.append(
                UpsetCandidateItem(
                    game_id=str(game.id),
                    start_time=start_time_str,
                    league=game.sport or "",
                    home_team=game.home_team or "",
                    away_team=game.away_team or "",
                    underdog_side=underdog_side,
                    underdog_team=underdog_team,
                    underdog_ml=underdog_ml_int,
                    implied_prob=underdog_implied,
                    model_prob=underdog_model,
                    edge=edge_pct,
                    confidence=conf_0_1,
                    books_count=price_stats.books_count,
                    best_underdog_ml=price_stats.best_underdog_ml,
                    median_underdog_ml=price_stats.median_underdog_ml,
                    price_spread=price_stats.price_spread,
                    worst_underdog_ml=price_stats.worst_underdog_ml,
                    flags=quality.flags,
                    odds_quality=quality.odds_quality,
                    market_disagreement=None,
                    reasons=reasons,
                )
            )

        candidates.sort(
            key=lambda c: (-c.edge, -c.confidence, c.start_time)
        )
        candidates = candidates[:max_results]

        meta = {
            "games_scanned": games_scanned,
            "games_with_odds": games_with_odds,
            "missing_odds": missing_odds,
            "games_scanned_capped": games_scanned_capped,
            # extra meta for instrumentation (response_model will ignore unknown keys)
            "rejected_reason_counts": rejected_reason_counts,
        }

        return UpsetFinderToolsResult(
            sport=sport.lower() if sport.lower() != "all" else "all",
            window_days=days,
            min_edge=min_edge,
            generated_at=generated_at,
            candidates=candidates,
            meta=meta,
        )

    def _resolve_sport_codes(self, sport: str) -> List[str]:
        """Return list of sport codes to query (e.g. ['NBA'] or ['NFL','NBA',...] for 'all')."""
        s = (sport or "").strip().lower()
        if s == "all":
            return [c.code for c in list_supported_sports()]
        try:
            config = get_sport_config(sport)
            return [config.code]
        except ValueError:
            return []

    async def _fetch_games(
        self,
        sport_codes: List[str],
        start_utc: datetime,
        end_utc: datetime,
    ) -> List[Game]:
        """Load games in window for given sports, with markets and odds. Capped at MAX_GAMES_SCAN."""
        if not sport_codes:
            return []

        scheduled = ("scheduled", "status_scheduled")
        per_sport = max(50, MAX_GAMES_SCAN // len(sport_codes))
        all_games: List[Game] = []

        for code in sport_codes:
            result = await self._db.execute(
                select(Game)
                .where(Game.sport == code)
                .where(Game.start_time >= start_utc)
                .where(Game.start_time <= end_utc)
                .where(
                    or_(
                        Game.status.is_(None),
                        func.lower(Game.status).in_(scheduled),
                    )
                )
                .order_by(Game.start_time)
                .limit(per_sport)
                .options(selectinload(Game.markets).selectinload(Market.odds))
            )
            all_games.extend(result.scalars().all())
            if len(all_games) >= MAX_GAMES_SCAN:
                break

        all_games.sort(key=lambda g: g.start_time or datetime.max.replace(tzinfo=timezone.utc))
        return all_games[:MAX_GAMES_SCAN]

    def _get_implied_prob(self, snapshot: Dict[str, Any], side: str) -> Optional[float]:
        """Get implied prob for home or away from snapshot (0-1)."""
        key = "home_implied_prob" if side == "home" else "away_implied_prob"
        val = snapshot.get(key)
        if val is not None and isinstance(val, (int, float)):
            return float(val)
        ml_key = "home_ml" if side == "home" else "away_ml"
        ml = _parse_american_odds(snapshot.get(ml_key))
        if ml is not None:
            return _implied_prob_from_american(ml)
        return None

    async def _get_model_probs(
        self,
        game: Game,
        odds_snapshot: Dict[str, Any],
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Return (home_model_prob, away_model_prob, confidence_0_100).
        Prefer cached analysis; else compute via compute_game_win_probability.
        """
        cached = await self._analysis_repo.get_by_game_id(
            league=game.sport or "",
            game_id=game.id,
        )
        if cached and getattr(cached, "analysis_content", None):
            content = cached.analysis_content or {}
            mwp = content.get("model_win_probability") or {}
            if isinstance(mwp, dict):
                home_p = mwp.get("home_win_prob")
                away_p = mwp.get("away_win_prob")
                if home_p is not None and away_p is not None:
                    try:
                        h = float(home_p)
                        a = float(away_p)
                        conf = content.get("confidence") or content.get("ai_confidence")
                        c = float(conf) if conf is not None else 50.0
                        return (h, a, c)
                    except (TypeError, ValueError):
                        pass

        try:
            result = await compute_game_win_probability(
                self._db,
                home_team=game.home_team or "",
                away_team=game.away_team or "",
                sport=game.sport or "NFL",
                matchup_data={},
                odds_data=odds_snapshot,
            )
            home_p = result.get("home_model_prob")
            away_p = result.get("away_model_prob")
            conf = result.get("ai_confidence")
            if home_p is not None and away_p is not None:
                return (float(home_p), float(away_p), float(conf) if conf is not None else 50.0)
        except Exception as e:
            logger.debug("compute_game_win_probability failed for game %s: %s", game.id, e)
        return (None, None, None)

    def _build_reasons(
        self,
        edge_pct: float,
        model_prob: float,
        implied_prob: float,
        confidence: float,
    ) -> List[str]:
        """Short reason bullets for the candidate."""
        reasons = []
        reasons.append(f"Edge {edge_pct:.1f}% (model {model_prob:.0%} vs implied {implied_prob:.0%})")
        if confidence >= 0.6:
            reasons.append("Solid model confidence")
        return reasons
