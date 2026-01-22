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
        
        # Add last_updated timestamp from most recent market/odds
        last_updated = None
        for market in markets:
            if market.odds:
                for odd in market.odds:
                    if hasattr(odd, "created_at") and odd.created_at:
                        if last_updated is None or odd.created_at > last_updated:
                            last_updated = odd.created_at
        if last_updated:
            snapshot["last_updated"] = last_updated.isoformat() if hasattr(last_updated, "isoformat") else str(last_updated)

        return snapshot

    def build_props_snapshot(self, *, game: Game, markets: List[Market]) -> Dict[str, Any]:
        """
        Build props snapshot from player_props markets.
        
        Returns normalized props data across books (FanDuel, DraftKings preferred).
        """
        preferred_books = ["fanduel", "draftkings"]
        
        def book_rank(book: str) -> int:
            try:
                return preferred_books.index((book or "").lower())
            except ValueError:
                return len(preferred_books)
        
        # Filter player_props markets
        props_markets = [m for m in markets if (m.market_type or "").lower() == "player_props"]
        if not props_markets:
            return {}
        
        # Group by book and sort by preference
        props_by_book: Dict[str, Market] = {}
        for market in props_markets:
            book = (market.book or "").lower()
            if book not in props_by_book or book_rank(book) < book_rank(props_by_book[book].book or ""):
                props_by_book[book] = market
        
        props_list: List[Dict[str, Any]] = []
        
        for book, market in props_by_book.items():
            for odd in (market.odds or []):
                outcome = str(odd.outcome or "")
                
                # Parse player prop from outcome
                # Format: "Player Name Prop Type Over 27.5" or "Player Name Prop Type Under 27.5"
                # Or: "Player Name Prop Type 27.5" (with over/under in name)
                prop_data = self._parse_prop_outcome(outcome)
                if not prop_data:
                    continue
                
                player_name = prop_data["player_name"]
                market_key = prop_data["market_key"]
                line = prop_data["line"]
                direction = prop_data["direction"]  # "over" or "under"
                
                # Find or create prop entry
                prop_entry = None
                for p in props_list:
                    if p["player_name"] == player_name and p["market_key"] == market_key and p["line"] == line:
                        prop_entry = p
                        break
                
                if not prop_entry:
                    prop_entry = {
                        "market_key": market_key,
                        "player_name": player_name,
                        "line": line,
                        "over_price": None,
                        "under_price": None,
                        "best_book_over": None,
                        "best_book_under": None,
                        "last_updated": None,
                    }
                    props_list.append(prop_entry)
                
                # Update price and book for direction
                if direction == "over":
                    if prop_entry["over_price"] is None or book_rank(book) < book_rank(prop_entry["best_book_over"] or ""):
                        prop_entry["over_price"] = odd.price
                        prop_entry["best_book_over"] = book
                elif direction == "under":
                    if prop_entry["under_price"] is None or book_rank(book) < book_rank(prop_entry["best_book_under"] or ""):
                        prop_entry["under_price"] = odd.price
                        prop_entry["best_book_under"] = book
                
                # Update last_updated from market/odds timestamp
                if hasattr(odd, "created_at") and odd.created_at:
                    prop_entry["last_updated"] = odd.created_at.isoformat()
        
        return {"props": props_list}
    
    def _parse_prop_outcome(self, outcome: str) -> Optional[Dict[str, Any]]:
        """
        Parse player prop outcome string.
        
        Examples from The Odds API:
        - "LeBron James Points Over 27.5"
        - "Patrick Mahomes Passing Yards Under 300.5"
        - "Player Name Prop Type 24.5" (with over/under in name)
        
        The Odds API stores as: "{outcome_name} {point:.1f}" where outcome_name
        includes player name + prop description + Over/Under.
        """
        import re
        
        # Try to extract line number (at end of string)
        line_match = re.search(r"(\d+\.?\d*)\s*$", outcome)
        if not line_match:
            return None
        
        line = float(line_match.group(1))
        
        # Extract direction (over/under) - check before removing line
        outcome_lower = outcome.lower()
        if "over" in outcome_lower:
            direction = "over"
        elif "under" in outcome_lower:
            direction = "under"
        else:
            # Default to over if not specified
            direction = "over"
        
        # Extract player name and prop type
        # Remove direction, line, and clean up
        cleaned = re.sub(r"\s*(over|under)\s*", " ", outcome_lower, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*\d+\.?\d*\s*$", "", cleaned).strip()
        
        # Map common prop types (sport-specific)
        market_key_map = {
            # NBA
            "points": "player_points",
            "rebounds": "player_rebounds",
            "assists": "player_assists",
            "threes": "player_threes",
            "three pointers": "player_threes",
            "3-pointers": "player_threes",
            # NFL
            "passing yards": "player_pass_yards",
            "rushing yards": "player_rush_yards",
            "receiving yards": "player_rec_yards",
            "touchdowns": "player_touchdowns",
            "tds": "player_touchdowns",
            # NHL
            "shots on goal": "player_shots_on_goal",
            "shots": "player_shots_on_goal",
        }
        
        market_key = "player_points"  # Default
        player_name = cleaned
        
        # Find matching prop type
        for prop_text, key in market_key_map.items():
            if prop_text in cleaned:
                market_key = key
                # Remove prop type from player name
                player_name = cleaned.replace(prop_text, "").strip()
                # Also remove common words that might be left
                player_name = re.sub(r"\s+(made|total|scored|thrown|caught|rushed)\s*$", "", player_name, flags=re.IGNORECASE)
                break
        
        # Clean up player name (remove extra spaces, capitalize)
        player_name = " ".join(player_name.split()).title()
        
        if not player_name:
            return None
        
        return {
            "player_name": player_name,
            "market_key": market_key,
            "line": line,
            "direction": direction,
        }

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



