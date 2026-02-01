from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from app.services.team_name_normalizer import TeamNameNormalizer


MIN_MODEL_PROB = 0.43
MIN_IMPLIED_PROB = 0.05
MAX_IMPLIED_PROB = 0.90
MAX_EDGE_ABS = 0.25  # |model_prob - implied_prob| cap
MIN_BOOKS_GOOD = 3
MIN_BOOKS_THIN = 2
MAX_PRICE_SPREAD_SUSPECT = 80


def _parse_american_odds(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    s = str(value).strip().replace("+", "").replace("−", "-").replace("–", "-")
    s = "".join(c for c in s if c.isdigit() or c == "-")
    if not s or s == "-":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _implied_prob_from_american(american_odds: int) -> float:
    if american_odds > 0:
        return 100.0 / (american_odds + 100)
    return abs(american_odds) / (abs(american_odds) + 100.0)


@dataclass(frozen=True)
class UnderdogPriceStats:
    books_count: int
    best_underdog_ml: Optional[int]
    median_underdog_ml: Optional[int]
    price_spread: Optional[int]
    worst_underdog_ml: Optional[int]


@dataclass(frozen=True)
class CandidateQualityAssessment:
    ok: bool
    reject_reason: Optional[str] = None
    odds_quality: str = "bad"  # good | thin | bad
    flags: List[str] = field(default_factory=list)


class UnderdogH2HPriceExtractor:
    """Extract underdog H2H prices across books (home vs away only; ignores draw)."""

    def __init__(self, *, team_normalizer: Optional[TeamNameNormalizer] = None) -> None:
        self._team_normalizer = team_normalizer or TeamNameNormalizer()

    def extract_prices(self, *, home_team: str, away_team: str, markets: List[Any]) -> List[int]:
        home_norm = self._team_normalizer.normalize(home_team)
        away_norm = self._team_normalizer.normalize(away_team)

        # Deduplicate by book: one underdog price per book.
        by_book: Dict[str, int] = {}

        for market in markets or []:
            if str(getattr(market, "market_type", "") or "").lower() != "h2h":
                continue

            book = str(getattr(market, "book", "") or "").strip().lower() or "unknown"
            odds_rows = getattr(market, "odds", None) or []

            home_price = None
            away_price = None
            home_implied = None
            away_implied = None

            for odd in odds_rows:
                out_raw = str(getattr(odd, "outcome", "") or "")
                out_lower = out_raw.lower()
                out_norm = self._team_normalizer.normalize(out_raw)

                is_home = out_lower == "home" or (out_norm and out_norm == home_norm)
                is_away = out_lower == "away" or (out_norm and out_norm == away_norm)
                is_draw = out_lower in ("draw", "tie", "tied")
                if is_draw:
                    continue

                if is_home:
                    home_price = _parse_american_odds(getattr(odd, "price", None))
                    ip = getattr(odd, "implied_prob", None)
                    if ip is not None:
                        try:
                            home_implied = float(ip)
                        except (TypeError, ValueError):
                            home_implied = None
                    elif home_price is not None:
                        home_implied = _implied_prob_from_american(home_price)
                elif is_away:
                    away_price = _parse_american_odds(getattr(odd, "price", None))
                    ip = getattr(odd, "implied_prob", None)
                    if ip is not None:
                        try:
                            away_implied = float(ip)
                        except (TypeError, ValueError):
                            away_implied = None
                    elif away_price is not None:
                        away_implied = _implied_prob_from_american(away_price)

            if home_price is None or away_price is None:
                continue
            if home_implied is None or away_implied is None:
                continue

            # Underdog = lower implied probability (less likely).
            underdog_price = home_price if home_implied <= away_implied else away_price
            by_book[book] = underdog_price

        return list(by_book.values())


class UnderdogPriceStatsCalculator:
    def compute(self, prices: List[int]) -> UnderdogPriceStats:
        if not prices:
            return UnderdogPriceStats(books_count=0, best_underdog_ml=None, median_underdog_ml=None, price_spread=None, worst_underdog_ml=None)

        sorted_prices = sorted(prices)
        books_count = len(sorted_prices)
        best = max(sorted_prices)
        worst = min(sorted_prices)
        median = sorted_prices[(books_count - 1) // 2]  # lower-middle for even
        spread = (best - worst) if books_count >= 2 else None

        return UnderdogPriceStats(
            books_count=books_count,
            best_underdog_ml=best,
            median_underdog_ml=median,
            price_spread=spread,
            worst_underdog_ml=worst,
        )


class UpsetCandidateSanityChecker:
    """Applies conservative quality gates and flags (full mode only)."""

    def assess(
        self,
        *,
        model_prob: Optional[float],
        implied_prob: Optional[float],
        edge_abs: Optional[float],
        price_stats: UnderdogPriceStats,
    ) -> CandidateQualityAssessment:
        if model_prob is None or model_prob < MIN_MODEL_PROB:
            return CandidateQualityAssessment(ok=False, reject_reason="low_model_prob")
        if implied_prob is None or implied_prob < MIN_IMPLIED_PROB or implied_prob > MAX_IMPLIED_PROB:
            return CandidateQualityAssessment(ok=False, reject_reason="bad_implied_prob")
        if edge_abs is None or edge_abs > MAX_EDGE_ABS:
            return CandidateQualityAssessment(ok=False, reject_reason="edge_cap")
        if price_stats.books_count < MIN_BOOKS_THIN:
            return CandidateQualityAssessment(ok=False, reject_reason="too_few_books")

        flags: List[str] = []
        odds_quality = "good"

        if price_stats.books_count < MIN_BOOKS_GOOD:
            flags.append("low_books")
            odds_quality = "thin"

        if price_stats.price_spread is not None and price_stats.price_spread >= MAX_PRICE_SPREAD_SUSPECT:
            flags.append("stale_odds_suspected")
            odds_quality = "thin"

        return CandidateQualityAssessment(ok=True, odds_quality=odds_quality, flags=flags)

