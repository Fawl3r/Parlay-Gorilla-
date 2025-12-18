from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExtractedOddsLines:
    """Compact representation of key betting lines for analysis/selection."""

    book: str
    home_team: str
    away_team: str

    home_ml: Optional[str]
    away_ml: Optional[str]
    home_implied_prob: Optional[float]
    away_implied_prob: Optional[float]

    home_spread_point: Optional[float]
    away_spread_point: Optional[float]
    home_spread_price: Optional[str]
    away_spread_price: Optional[str]

    total_line: Optional[float]
    total_over_price: Optional[str]
    total_under_price: Optional[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "book": self.book,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "home_ml": self.home_ml,
            "away_ml": self.away_ml,
            "home_implied_prob": self.home_implied_prob,
            "away_implied_prob": self.away_implied_prob,
            "home_spread_point": self.home_spread_point,
            "away_spread_point": self.away_spread_point,
            "home_spread_price": self.home_spread_price,
            "away_spread_price": self.away_spread_price,
            "total_line": self.total_line,
            "total_over_price": self.total_over_price,
            "total_under_price": self.total_under_price,
        }


class OddsLineExtractor:
    """Extract key lines from The Odds API event payload."""

    _PREFERRED_BOOKS = ["draftkings", "fanduel", "betmgm", "caesars", "pointsbet", "betrivers"]

    def extract(self, *, event: Dict[str, Any]) -> Optional[ExtractedOddsLines]:
        home_team = str(event.get("home_team") or "").strip()
        away_team = str(event.get("away_team") or "").strip()
        if not home_team or not away_team:
            return None

        bookmaker = self._pick_bookmaker(event.get("bookmakers") or [])
        if not bookmaker:
            return None

        book_key = str(bookmaker.get("key") or bookmaker.get("title") or "").lower().strip() or "unknown"
        markets = bookmaker.get("markets") or []

        h2h = self._find_market(markets, "h2h")
        spreads = self._find_market(markets, "spreads")
        totals = self._find_market(markets, "totals")

        home_ml, away_ml, home_prob, away_prob = self._extract_h2h(h2h, home_team, away_team)
        h_sp, a_sp, h_sp_price, a_sp_price = self._extract_spreads(spreads, home_team, away_team)
        total_line, over_price, under_price = self._extract_totals(totals)

        return ExtractedOddsLines(
            book=book_key,
            home_team=home_team,
            away_team=away_team,
            home_ml=home_ml,
            away_ml=away_ml,
            home_implied_prob=home_prob,
            away_implied_prob=away_prob,
            home_spread_point=h_sp,
            away_spread_point=a_sp,
            home_spread_price=h_sp_price,
            away_spread_price=a_sp_price,
            total_line=total_line,
            total_over_price=over_price,
            total_under_price=under_price,
        )

    def _pick_bookmaker(self, bookmakers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not bookmakers:
            return None

        def rank(b: Dict[str, Any]) -> int:
            key = str(b.get("key") or "").lower().strip()
            try:
                return self._PREFERRED_BOOKS.index(key)
            except ValueError:
                return len(self._PREFERRED_BOOKS)

        return sorted(bookmakers, key=rank)[0]

    @staticmethod
    def _find_market(markets: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
        key_lower = str(key).lower().strip()
        for m in markets:
            if str(m.get("key") or "").lower().strip() == key_lower:
                return m
        return None

    def _extract_h2h(
        self, market: Optional[Dict[str, Any]], home_team: str, away_team: str
    ) -> tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
        if not market:
            return None, None, None, None
        home_ml = away_ml = None
        home_prob = away_prob = None
        for o in market.get("outcomes") or []:
            name = str(o.get("name") or "")
            price = o.get("price")
            if price is None:
                continue
            price_str, implied = self._normalize_price_and_implied(price)
            if name == home_team:
                home_ml, home_prob = price_str, implied
            elif name == away_team:
                away_ml, away_prob = price_str, implied
        return home_ml, away_ml, home_prob, away_prob

    def _extract_spreads(
        self, market: Optional[Dict[str, Any]], home_team: str, away_team: str
    ) -> tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        if not market:
            return None, None, None, None

        home_point = away_point = None
        home_price = away_price = None
        for o in market.get("outcomes") or []:
            name = str(o.get("name") or "")
            point = o.get("point")
            price = o.get("price")
            if point is None or price is None:
                continue
            price_str, _ = self._normalize_price_and_implied(price)
            if name == home_team:
                home_point = float(point)
                home_price = price_str
            elif name == away_team:
                away_point = float(point)
                away_price = price_str
        return home_point, away_point, home_price, away_price

    def _extract_totals(self, market: Optional[Dict[str, Any]]) -> tuple[Optional[float], Optional[str], Optional[str]]:
        if not market:
            return None, None, None

        total_line = None
        over_price = under_price = None
        for o in market.get("outcomes") or []:
            name = str(o.get("name") or "")
            point = o.get("point")
            price = o.get("price")
            if point is None or price is None:
                continue
            if total_line is None:
                try:
                    total_line = float(point)
                except Exception:
                    total_line = None
            price_str, _ = self._normalize_price_and_implied(price)
            if name.lower() == "over":
                over_price = price_str
            elif name.lower() == "under":
                under_price = price_str
        return total_line, over_price, under_price

    @staticmethod
    def _normalize_price_and_implied(price: Any) -> tuple[str, Optional[float]]:
        """
        Normalize The Odds API "price" into the same string format we store in DB:
        - American: +150, -110
        - Decimal: "2.50" etc (we still return a string)
        """
        try:
            # American odds are ints like -110, +150.
            if isinstance(price, (int, float)) and abs(float(price)) >= 100 and float(price) != 0:
                american = int(price)
                decimal = (american / 100.0 + 1.0) if american > 0 else (100.0 / abs(american) + 1.0)
                implied = 1.0 / decimal if decimal > 0 else None
                price_str = f"+{american}" if american > 0 else str(american)
                return price_str, implied

            # Otherwise treat as decimal odds.
            dec = float(price)
            implied = 1.0 / dec if dec > 0 else None
            return f"{dec:.2f}", implied
        except Exception:
            return str(price), None




