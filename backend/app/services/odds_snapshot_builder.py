from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.models.game import Game
from app.models.market import Market
from app.services.team_name_normalizer import TeamNameNormalizer


class OddsSnapshotBuilder:
    """Build a small canonical odds snapshot from stored Market/Odds rows."""

    def __init__(self, *, team_normalizer: TeamNameNormalizer | None = None):
        self._team_normalizer = team_normalizer or TeamNameNormalizer()

    def build(self, *, game: Game, markets: List[Market]) -> Dict[str, Any]:
        preferred_books = ["draftkings", "fanduel", "betmgm", "caesars", "pointsbet", "betrivers"]

        def book_rank(book: str) -> int:
            try:
                return preferred_books.index((book or "").lower())
            except ValueError:
                return len(preferred_books)

        def pick_market(mtype: str) -> Optional[Market]:
            candidates = [m for m in markets if (m.market_type or "").lower() == mtype]
            return sorted(candidates, key=lambda m: book_rank(m.book))[0] if candidates else None

        snapshot: Dict[str, Any] = {}

        h2h = pick_market("h2h")
        if h2h:
            snapshot["h2h_book"] = h2h.book
            home_norm = self._team_normalizer.normalize(game.home_team)
            away_norm = self._team_normalizer.normalize(game.away_team)
            for o in h2h.odds or []:
                out_raw = str(o.outcome or "")
                out_lower = out_raw.lower()
                out_norm = self._team_normalizer.normalize(out_raw)

                is_home = out_lower == "home" or (out_norm and out_norm == home_norm)
                is_away = out_lower == "away" or (out_norm and out_norm == away_norm)
                is_draw = out_lower in ("draw", "tie", "tied")

                if is_home:
                    snapshot["home_ml"] = o.price
                    snapshot["home_implied_prob"] = float(o.implied_prob) if o.implied_prob is not None else None
                elif is_away:
                    snapshot["away_ml"] = o.price
                    snapshot["away_implied_prob"] = float(o.implied_prob) if o.implied_prob is not None else None
                elif is_draw:
                    snapshot["draw_ml"] = o.price
                    snapshot["draw_implied_prob"] = float(o.implied_prob) if o.implied_prob is not None else None

        spreads = pick_market("spreads")
        if spreads:
            snapshot["spreads_book"] = spreads.book
            home_point, home_price = self._extract_team_point_and_price(team=game.home_team, odds=spreads.odds or [])
            away_point, away_price = self._extract_team_point_and_price(team=game.away_team, odds=spreads.odds or [])
            snapshot.update(
                {
                    "home_spread_point": home_point,
                    "away_spread_point": away_point,
                    "home_spread_price": home_price,
                    "away_spread_price": away_price,
                }
            )

        totals = pick_market("totals")
        if totals:
            snapshot["totals_book"] = totals.book
            total_line, over_price, under_price = self._extract_total_line_and_prices(totals.odds or [])
            snapshot.update(
                {
                    "total_line": total_line,
                    "total_over_price": over_price,
                    "total_under_price": under_price,
                }
            )

        return snapshot

    def _extract_team_point_and_price(self, *, team: str, odds: List[Any]) -> Tuple[Optional[float], Optional[str]]:
        team_norm = self._team_normalizer.normalize(team)
        for o in odds:
            outcome = str(getattr(o, "outcome", "") or "").strip()
            # We store spreads as "{team} {point:+.1f}" so parse the numeric token at the end.
            match = re.search(r"\s([+-]?\d+(?:\.\d+)?)\s*$", outcome)
            if not match:
                continue

            team_part = outcome[: match.start()].strip()
            if self._team_normalizer.normalize(team_part) != team_norm:
                continue

            try:
                return float(match.group(1)), str(getattr(o, "price", "") or "")
            except Exception:
                continue
        return None, None

    @staticmethod
    def _extract_total_line_and_prices(odds: List[Any]) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        total_line: Optional[float] = None
        over_price: Optional[str] = None
        under_price: Optional[str] = None
        for o in odds:
            outcome = str(getattr(o, "outcome", "") or "")
            match = re.search(r"(\d+\.?\d*)", outcome)
            if match and total_line is None:
                try:
                    total_line = float(match.group(1))
                except Exception:
                    pass
            if outcome.lower().startswith("over"):
                over_price = str(getattr(o, "price", "") or "")
            elif outcome.lower().startswith("under"):
                under_price = str(getattr(o, "price", "") or "")
        return total_line, over_price, under_price



