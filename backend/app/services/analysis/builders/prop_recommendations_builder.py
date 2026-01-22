"""Prop recommendations builder - deterministic prop betting recommendations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PropRecommendationsBuilder:
    """Build prop recommendations based on line value and implied probability."""

    @staticmethod
    def build(
        *,
        props_snapshot: Dict[str, Any],
        game: Any,  # Game model
    ) -> Optional[Dict[str, Any]]:
        """
        Build prop recommendations deterministically.
        
        Args:
            props_snapshot: Props data from OddsSnapshotBuilder.build_props_snapshot()
            game: Game model (for sport context)
            
        Returns:
            Dict with top_props list and notes, or None if no props available
        """
        props_list = props_snapshot.get("props", [])
        if not props_list:
            return None
        
        top_props: List[Dict[str, Any]] = []
        
        for prop in props_list[:10]:  # Limit to top 10 props
            market_key = prop.get("market_key")
            player_name = prop.get("player_name")
            line = prop.get("line")
            over_price = prop.get("over_price")
            under_price = prop.get("under_price")
            best_book_over = prop.get("best_book_over")
            best_book_under = prop.get("best_book_under")
            
            if not market_key or not player_name or line is None:
                continue
            
            # Calculate recommendation based on line shopping and implied probability edge
            recommendation = PropRecommendationsBuilder._calculate_recommendation(
                prop=prop,
                market_key=market_key,
                player_name=player_name,
                line=line,
            )
            
            if recommendation:
                top_props.append(recommendation)
        
        # Sort by confidence (highest first)
        top_props.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        # Return top 5
        return {
            "top_props": top_props[:5],
            "notes": "Props are volatile; reduce stake size.",
        }
    
    @staticmethod
    def _calculate_recommendation(
        *,
        prop: Dict[str, Any],
        market_key: str,
        player_name: str,
        line: float,
    ) -> Optional[Dict[str, Any]]:
        """Calculate a single prop recommendation."""
        over_price = prop.get("over_price")
        under_price = prop.get("under_price")
        best_book_over = prop.get("best_book_over")
        best_book_under = prop.get("best_book_under")
        
        # Need at least one side to make a recommendation
        if not over_price and not under_price:
            return None
        
        # Convert American odds to implied probability
        def american_to_prob(price_str: str) -> Optional[float]:
            try:
                price = int(price_str.replace("+", ""))
                if price > 0:
                    return 100.0 / (price + 100.0)
                else:
                    return abs(price) / (abs(price) + 100.0)
            except (ValueError, TypeError):
                return None
        
        over_prob = american_to_prob(over_price) if over_price else None
        under_prob = american_to_prob(under_price) if under_price else None
        
        # If both sides available, look for value (line shopping edge)
        if over_prob and under_prob:
            # Calculate vig
            total_prob = over_prob + under_prob
            vig = total_prob - 1.0
            
            # Remove vig to get fair probabilities
            fair_over = over_prob / total_prob
            fair_under = under_prob / total_prob
            
            # Look for edge (prefer side with better price relative to fair)
            over_edge = fair_over - over_prob
            under_edge = fair_under - under_prob
            
            # Calculate EV (Expected Value)
            def calculate_ev(win_prob: float, price_str: str) -> float:
                """Calculate expected value from win probability and American odds."""
                try:
                    price = int(price_str.replace("+", ""))
                    if price > 0:
                        payout = price / 100.0
                    else:
                        payout = 100.0 / abs(price)
                    ev = (win_prob * payout) - (1.0 - win_prob)
                    return ev
                except (ValueError, TypeError):
                    return 0.0
            
            over_ev = calculate_ev(fair_over, over_price) if over_price else 0.0
            under_ev = calculate_ev(fair_under, under_price) if under_price else 0.0
            
            if over_edge > under_edge and over_edge > 0.02:  # 2% edge threshold
                pick = f"Over {line:.1f}"
                confidence = min(95, 50 + int(over_edge * 1000))
                ev_score = round(over_ev * 100, 1)  # Convert to percentage
                why = f"Over priced at {over_price} implies {over_prob:.1%} probability, but fair value suggests {fair_over:.1%}. Line shopping edge of {over_edge:.1%}."
                best_odds = {"book": best_book_over or "unknown", "price": over_price}
            elif under_edge > over_edge and under_edge > 0.02:
                pick = f"Under {line:.1f}"
                confidence = min(95, 50 + int(under_edge * 1000))
                ev_score = round(under_ev * 100, 1)  # Convert to percentage
                why = f"Under priced at {under_price} implies {under_prob:.1%} probability, but fair value suggests {fair_under:.1%}. Line shopping edge of {under_edge:.1%}."
                best_odds = {"book": best_book_under or "unknown", "price": under_price}
            else:
                # No clear edge, use EV to determine
                if over_ev > under_ev:
                    pick = f"Over {line:.1f}"
                    confidence = 55
                    ev_score = round(over_ev * 100, 1)
                    why = f"Over side offers slightly better value at {over_price} vs {under_price}."
                    best_odds = {"book": best_book_over or "unknown", "price": over_price}
                else:
                    pick = f"Under {line:.1f}"
                    confidence = 55
                    ev_score = round(under_ev * 100, 1)
                    why = f"Under side offers slightly better value at {under_price} vs {over_price}."
                    best_odds = {"book": best_book_under or "unknown", "price": under_price}
            else:
                # No clear edge, but still provide recommendation based on best odds
                if over_prob < under_prob:
                    pick = f"Over {line:.1f}"
                    confidence = 55
                    why = f"Over side offers slightly better value at {over_price} vs {under_price}."
                    best_odds = {"book": best_book_over or "unknown", "price": over_price}
                else:
                    pick = f"Under {line:.1f}"
                    confidence = 55
                    why = f"Under side offers slightly better value at {under_price} vs {over_price}."
                    best_odds = {"book": best_book_under or "unknown", "price": under_price}
        elif over_price:
            # Only over available
            pick = f"Over {line:.1f}"
            confidence = 50
            why = f"Over available at {over_price}. Line shopping recommended to compare across books."
            best_odds = {"book": best_book_over or "unknown", "price": over_price}
        elif under_price:
            # Only under available
            pick = f"Under {line:.1f}"
            confidence = 50
            why = f"Under available at {under_price}. Line shopping recommended to compare across books."
            best_odds = {"book": best_book_under or "unknown", "price": under_price}
        else:
            return None
        
        # Calculate EV for the selected pick
        ev_score = 0.0
        if over_price and pick.startswith("Over"):
            ev_score = calculate_ev(fair_over if 'fair_over' in locals() else 0.5, over_price)
        elif under_price and pick.startswith("Under"):
            ev_score = calculate_ev(fair_under if 'fair_under' in locals() else 0.5, under_price)
        
        return {
            "market": market_key,
            "player": player_name,
            "pick": pick,
            "confidence": confidence,
            "why": why,
            "best_odds": best_odds,
            "ev_score": round(ev_score * 100, 1),  # EV as percentage
        }
