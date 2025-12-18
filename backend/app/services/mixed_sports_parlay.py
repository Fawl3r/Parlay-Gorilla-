"""Mixed sports parlay builder service

This service handles building parlays that mix legs from multiple sports,
which helps reduce correlation and maximize edge discovery.

Uses model probabilities:
- Filters legs where model_prob > implied_prob (positive edge)
- Calculates parlay probability from model probabilities
- Ranks by confidence score
"""

from typing import List, Dict, Optional
from decimal import Decimal
from itertools import cycle
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.probability_engine import get_probability_engine, BaseProbabilityEngine


class MixedSportsParlayBuilder:
    """
    Service for building parlays that mix legs from multiple sports.
    
    Mixing sports in a parlay reduces correlation between legs since
    outcomes in different leagues are typically independent.
    
    Key features:
    - Filters for positive edge legs (model_prob > implied_prob)
    - Uses model probabilities for parlay calculations
    - Balances legs across sports for diversification
    """
    
    SUPPORTED_SPORTS = ["NFL", "NBA", "NHL", "MLB"]
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._engines: Dict[str, BaseProbabilityEngine] = {}
    
    def _get_engine(self, sport: str) -> BaseProbabilityEngine:
        """Get or create a probability engine for the specified sport."""
        sport_upper = sport.upper()
        if sport_upper not in self._engines:
            self._engines[sport_upper] = get_probability_engine(self.db, sport_upper)
        return self._engines[sport_upper]
    
    async def get_multi_sport_candidates(
        self,
        sports: List[str],
        min_confidence: float = 50.0,
        max_legs_per_sport: int = 50,
        week: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch candidate legs from multiple sports.
        
        Args:
            sports: List of sports to fetch legs from (e.g., ["NFL", "NBA", "NHL"])
            min_confidence: Minimum confidence score for candidate legs
            max_legs_per_sport: Maximum legs to fetch per sport
            week: NFL week to filter by (only applies to NFL legs)
            
        Returns:
            Combined list of candidate legs from all sports, sorted by confidence
        """
        all_candidates = []
        
        for sport in sports:
            sport_upper = sport.upper()
            if sport_upper not in self.SUPPORTED_SPORTS:
                print(f"Warning: Unsupported sport '{sport}', skipping")
                continue
            
            try:
                engine = self._get_engine(sport_upper)
                # Only pass week filter for NFL
                week_filter = week if sport_upper == "NFL" else None
                candidates = await engine.get_candidate_legs(
                    sport=sport_upper,
                    min_confidence=min_confidence,
                    max_legs=max_legs_per_sport,
                    week=week_filter
                )
                
                # Add sport identifier to each candidate
                for candidate in candidates:
                    candidate["sport"] = sport_upper
                
                all_candidates.extend(candidates)
                print(f"Found {len(candidates)} candidates from {sport_upper}")
                
            except Exception as e:
                print(f"Error fetching candidates from {sport_upper}: {e}")
                continue
        
        # Sort by confidence score
        all_candidates.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        return all_candidates
    
    async def build_mixed_parlay(
        self,
        num_legs: int,
        sports: List[str],
        risk_profile: str = "balanced",
        balance_sports: bool = True,
        week: Optional[int] = None
    ) -> Dict:
        """
        Build a parlay mixing legs from multiple sports.
        
        Args:
            num_legs: Number of legs for the parlay (1-20)
            sports: List of sports to include
            risk_profile: conservative, balanced, or degen
            balance_sports: If True, try to evenly distribute legs across sports
            week: NFL week number to build from (only applies to NFL legs)
            
        Returns:
            Dictionary with parlay details including mixed sport legs
        """
        # Validate inputs
        num_legs = max(1, min(20, num_legs))
        risk_profile = risk_profile.lower()
        if risk_profile not in ["conservative", "balanced", "degen"]:
            risk_profile = "balanced"
        
        # Filter to valid sports only
        valid_sports = [s.upper() for s in sports if s.upper() in self.SUPPORTED_SPORTS]
        if not valid_sports:
            valid_sports = ["NFL"]  # Default fallback
        
        # Get minimum confidence based on risk profile
        min_confidence = self._get_min_confidence(risk_profile)
        
        # Fetch candidates from all sports
        candidates = await self.get_multi_sport_candidates(
            sports=valid_sports,
            min_confidence=min_confidence,
            max_legs_per_sport=100,
            week=week
        )
        
        print(f"Total candidates from {len(valid_sports)} sports: {len(candidates)}")
        
        # Filter for positive edge legs first
        positive_edge_candidates = self._filter_positive_edge_legs(candidates, risk_profile)
        print(f"[Mixed Parlay] {len(positive_edge_candidates)} candidates with positive edge")
        
        # Use positive edge candidates if we have enough
        if len(positive_edge_candidates) >= num_legs:
            candidates = positive_edge_candidates
        else:
            print(f"[Mixed Parlay] Not enough positive edge legs, using all candidates")
        
        # Lower threshold if not enough candidates
        if len(candidates) < num_legs:
            for lower_threshold in [min_confidence * 0.8, min_confidence * 0.6, 30.0, 20.0, 0.0]:
                candidates = await self.get_multi_sport_candidates(
                    sports=valid_sports,
                    min_confidence=lower_threshold,
                    max_legs_per_sport=150,
                    week=week
                )
                print(f"With threshold {lower_threshold}: {len(candidates)} candidates")
                if len(candidates) >= num_legs:
                    break
        
        if len(candidates) < num_legs:
            print(f"Warning: Only {len(candidates)} candidates available, need {num_legs}")
        
        # Select legs with sport balancing
        if balance_sports and len(valid_sports) > 1:
            selected_legs = self._select_balanced_legs(candidates, num_legs, valid_sports, risk_profile)
        else:
            selected_legs = self._select_best_legs(candidates, num_legs, risk_profile)
        
        # Build leg data
        legs_data = self._build_legs_data(selected_legs)
        
        # Calculate parlay probability
        leg_probs = [leg.get("probability", 0.5) for leg in legs_data]
        parlay_prob = self._calculate_parlay_probability(leg_probs)
        
        # Calculate confidence scores
        actual_num_legs = len(legs_data)
        confidence_scores = [float(leg.get("confidence", 50.0)) for leg in legs_data]
        overall_confidence = sum(confidence_scores) / actual_num_legs if actual_num_legs > 0 else 0.0
        
        # Calculate model confidence (normalized 0-1)
        model_confidence = min(1.0, overall_confidence / 100.0) if overall_confidence > 0 else 0.5
        
        # Count upsets (plus-money underdogs)
        upset_count = 0
        for leg in legs_data:
            try:
                odds_str = str(leg.get("odds", "0"))
                # Parse American odds
                if odds_str.startswith("+"):
                    upset_count += 1
                elif odds_str.lstrip("-").isdigit():
                    odds_val = int(odds_str)
                    if odds_val > 0:
                        upset_count += 1
            except (ValueError, TypeError):
                pass
        
        # Calculate parlay EV (expected value)
        parlay_ev = self._calculate_parlay_ev(legs_data, parlay_prob)
        
        # Import model version
        from app.core.model_config import MODEL_VERSION
        
        # Count sports used
        sports_used = list(set(leg.get("sport", "NFL") for leg in legs_data))
        
        return {
            "legs": legs_data,
            "num_legs": int(actual_num_legs),
            "parlay_hit_prob": float(parlay_prob),
            "risk_profile": str(risk_profile),
            "confidence_scores": confidence_scores,
            "overall_confidence": float(overall_confidence),
            "sports_mixed": sports_used,
            "is_mixed_sports": len(sports_used) > 1,
            # Model metrics for UI
            "parlay_ev": float(parlay_ev),
            "model_confidence": float(model_confidence),
            "upset_count": int(upset_count),
            "model_version": MODEL_VERSION,
        }
    
    def _get_min_confidence(self, risk_profile: str) -> float:
        """Get minimum confidence threshold based on risk profile."""
        thresholds = {
            "conservative": 70.0,
            "balanced": 55.0,
            "degen": 40.0,
        }
        return thresholds.get(risk_profile, 55.0)
    
    def _filter_positive_edge_legs(
        self,
        candidates: List[Dict],
        risk_profile: str,
    ) -> List[Dict]:
        """
        Filter legs where model probability > implied probability (positive edge).
        
        This is a core requirement: only select legs where our model believes
        the true probability is higher than what the market implies.
        """
        # Minimum edge thresholds by risk profile
        min_edge_thresholds = {
            "conservative": 0.02,   # 2% edge
            "balanced": 0.01,       # 1% edge
            "degen": 0.0,           # Any positive edge
        }
        min_edge = min_edge_thresholds.get(risk_profile, 0.01)
        
        positive_edge_legs = []
        
        for leg in candidates:
            model_prob = leg.get("adjusted_prob", 0)
            implied_prob = leg.get("implied_prob", 0)
            edge = leg.get("edge", model_prob - implied_prob if implied_prob > 0 else 0)
            
            if edge >= min_edge:
                leg["model_edge"] = edge
                positive_edge_legs.append(leg)
        
        positive_edge_legs.sort(key=lambda x: x.get("model_edge", 0), reverse=True)
        
        return positive_edge_legs
    
    def _select_balanced_legs(
        self,
        candidates: List[Dict],
        num_legs: int,
        sports: List[str],
        risk_profile: str
    ) -> List[Dict]:
        """
        Select legs with balanced distribution across sports.
        
        Distributes legs evenly across available sports while still
        prioritizing high-confidence picks.
        """
        # Group candidates by sport
        by_sport = {sport: [] for sport in sports}
        for candidate in candidates:
            sport = candidate.get("sport", "NFL")
            if sport in by_sport:
                by_sport[sport].append(candidate)
        
        # Calculate how many legs per sport (round-robin style)
        legs_per_sport = {sport: 0 for sport in sports}
        sports_cycle = cycle(sports)
        for _ in range(num_legs):
            sport = next(sports_cycle)
            while not by_sport[sport] and any(by_sport.values()):
                sport = next(sports_cycle)
            if by_sport[sport]:
                legs_per_sport[sport] += 1
        
        # Select legs from each sport
        selected = []
        selected_keys = set()
        
        for sport, count in legs_per_sport.items():
            sport_candidates = by_sport[sport]
            # Sort by EV/confidence
            sport_candidates.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
            
            added = 0
            for candidate in sport_candidates:
                if added >= count:
                    break
                key = (candidate.get("game_id"), candidate.get("market_type"), candidate.get("outcome"))
                if key not in selected_keys:
                    selected.append(candidate)
                    selected_keys.add(key)
                    added += 1
        
        # Fill remaining slots with best remaining candidates
        if len(selected) < num_legs:
            remaining = [c for c in candidates if c not in selected]
            remaining.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
            
            for candidate in remaining:
                if len(selected) >= num_legs:
                    break
                key = (candidate.get("game_id"), candidate.get("market_type"), candidate.get("outcome"))
                if key not in selected_keys:
                    # Check for conflicts before adding
                    if not self._conflicts_with_selected(candidate, selected):
                        selected.append(candidate)
                        selected_keys.add(key)
        
        # Remove any conflicting legs that may have been added
        selected = self._remove_conflicting_legs(selected)
        
        return selected[:num_legs]
    
    def _select_best_legs(
        self,
        candidates: List[Dict],
        num_legs: int,
        risk_profile: str
    ) -> List[Dict]:
        """Select best legs without sport balancing - pure confidence/EV based."""
        # Deduplicate by (game_id, market_type, outcome)
        unique_legs = {}
        for leg in candidates:
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            if key not in unique_legs or leg.get("confidence_score", 0) > unique_legs[key].get("confidence_score", 0):
                unique_legs[key] = leg
        
        # Sort by confidence and take top N, filtering conflicts
        sorted_legs = sorted(unique_legs.values(), key=lambda x: x.get("confidence_score", 0), reverse=True)
        selected = []
        for leg in sorted_legs:
            if len(selected) >= num_legs:
                break
            if not self._conflicts_with_selected(leg, selected):
                selected.append(leg)
        
        return selected[:num_legs]
    
    def _conflicts_with_selected(self, leg: Dict, selected: List[Dict]) -> bool:
        """
        Check if a leg logically conflicts with any selected leg.
        
        Conflicts occur when:
        1. Same game, same market_type, opposite outcomes (e.g., Home win vs Away win)
        2. Same game, totals market, Over vs Under
        3. Same player, same prop, Over vs Under
        4. Same team covering spread and not covering spread
        """
        leg_game_id = leg.get("game_id")
        leg_market_type = leg.get("market_type", "").lower()
        leg_outcome = str(leg.get("outcome", "")).lower()
        leg_home_team = leg.get("home_team", "").lower()
        leg_away_team = leg.get("away_team", "").lower()
        
        for selected_leg in selected:
            # Must be same game to conflict
            if selected_leg.get("game_id") != leg_game_id:
                continue
            
            selected_market_type = selected_leg.get("market_type", "").lower()
            selected_outcome = str(selected_leg.get("outcome", "")).lower()
            selected_home_team = selected_leg.get("home_team", "").lower()
            selected_away_team = selected_leg.get("away_team", "").lower()
            
            # Check for moneyline conflicts (same game, opposite teams)
            if leg_market_type == "h2h" and selected_market_type == "h2h":
                # Check if outcomes are opposite (home vs away)
                if ("home" in leg_outcome and "away" in selected_outcome) or \
                   ("away" in leg_outcome and "home" in selected_outcome):
                    # Verify it's the same teams
                    if leg_home_team == selected_home_team and leg_away_team == selected_away_team:
                        print(f"[MixedParlay] Conflict detected: {leg_outcome} vs {selected_outcome} (moneyline)")
                        return True
            
            # Check for totals conflicts (Over vs Under)
            if leg_market_type in ["total", "totals", "over_under"] and \
               selected_market_type in ["total", "totals", "over_under"]:
                # Check if one is over and one is under
                leg_is_over = "over" in leg_outcome
                selected_is_over = "over" in selected_outcome
                if leg_is_over != selected_is_over:
                    # Check if it's the same total line (approximate match)
                    leg_numbers = re.findall(r'\d+\.?\d*', leg_outcome)
                    selected_numbers = re.findall(r'\d+\.?\d*', selected_outcome)
                    if leg_numbers and selected_numbers:
                        leg_total = float(leg_numbers[0])
                        selected_total = float(selected_numbers[0])
                        # Allow small difference for different books (e.g., 44.5 vs 45)
                        if abs(leg_total - selected_total) <= 1.0:
                            print(f"[MixedParlay] Conflict detected: {leg_outcome} vs {selected_outcome} (totals)")
                            return True
            
            # Check for spread conflicts (same team covering vs not covering)
            if leg_market_type in ["spread", "spreads"] and \
               selected_market_type in ["spread", "spreads"]:
                # Check if same team but opposite outcomes
                leg_team_match = re.search(r'(\w+)\s*([+-]?\d+\.?\d*)', leg_outcome)
                selected_team_match = re.search(r'(\w+)\s*([+-]?\d+\.?\d*)', selected_outcome)
                
                if leg_team_match and selected_team_match:
                    leg_team = leg_team_match.group(1).lower()
                    leg_spread = float(leg_team_match.group(2))
                    selected_team = selected_team_match.group(1).lower()
                    selected_spread = float(selected_team_match.group(2))
                    
                    # Same team, opposite spread directions (one positive, one negative)
                    if leg_team == selected_team and leg_spread * selected_spread < 0:
                        print(f"[MixedParlay] Conflict detected: {leg_outcome} vs {selected_outcome} (spread)")
                        return True
            
            # Check for player prop conflicts (same player, same prop, Over vs Under)
            if leg_market_type in ["player_prop", "player_props"] and \
               selected_market_type in ["player_prop", "player_props"]:
                # Extract player name and prop type
                leg_parts = leg_outcome.split()
                selected_parts = selected_outcome.split()
                
                # Check if same player (first few words) and opposite over/under
                if len(leg_parts) >= 2 and len(selected_parts) >= 2:
                    # Player name is usually first 2-3 words
                    leg_player = " ".join(leg_parts[:2]).lower()
                    selected_player = " ".join(selected_parts[:2]).lower()
                    
                    if leg_player == selected_player:
                        leg_is_over = "over" in leg_outcome
                        selected_is_over = "over" in selected_outcome
                        if leg_is_over != selected_is_over:
                            # Check if same prop type (points, rebounds, etc.)
                            leg_prop_type = [w for w in leg_parts if w.lower() in ["points", "rebounds", "assists", "goals", "yards", "tds"]]
                            selected_prop_type = [w for w in selected_parts if w.lower() in ["points", "rebounds", "assists", "goals", "yards", "tds"]]
                            if leg_prop_type and selected_prop_type and leg_prop_type[0].lower() == selected_prop_type[0].lower():
                                # Extract the line number
                                leg_numbers = re.findall(r'\d+\.?\d*', leg_outcome)
                                selected_numbers = re.findall(r'\d+\.?\d*', selected_outcome)
                                if leg_numbers and selected_numbers:
                                    leg_line = float(leg_numbers[-1])  # Last number is usually the line
                                    selected_line = float(selected_numbers[-1])
                                    if abs(leg_line - selected_line) <= 1.0:
                                        print(f"[MixedParlay] Conflict detected: {leg_outcome} vs {selected_outcome} (player prop)")
                                        return True
        
        return False
    
    def _remove_conflicting_legs(self, selected: List[Dict]) -> List[Dict]:
        """
        Remove logically conflicting legs, keeping the ones with higher confidence.
        
        This ensures we don't have impossible combinations like:
        - Same team winning and losing
        - Over and Under on the same total
        - Same player Over and Under on the same prop
        """
        if len(selected) <= 1:
            return selected
        
        # Sort by confidence (keep best legs)
        sorted_legs = sorted(selected, key=lambda x: x.get("confidence_score", 0), reverse=True)
        
        filtered = []
        for leg in sorted_legs:
            if not self._conflicts_with_selected(leg, filtered):
                filtered.append(leg)
        
        return filtered
    
    def _build_legs_data(self, selected_legs: List[Dict]) -> List[Dict]:
        """Convert selected leg candidates to response format."""
        legs_data = []
        
        for leg in selected_legs:
            # Build game string if not present
            game_str = leg.get("game", "")
            if not game_str:
                home_team = leg.get("home_team", "")
                away_team = leg.get("away_team", "")
                if home_team and away_team:
                    game_str = f"{away_team} @ {home_team}"
                else:
                    game_str = f"Game {str(leg.get('game_id', ''))[:8]}"
            
            leg_data = {
                "market_id": str(leg.get("market_id", "")),
                "outcome": str(leg.get("outcome", "")),
                "game": str(game_str),
                "home_team": str(leg.get("home_team", "")),
                "away_team": str(leg.get("away_team", "")),
                "market_type": str(leg.get("market_type", "")),
                "odds": str(leg.get("odds", "")),
                "probability": float(leg.get("adjusted_prob", 0.0)),
                "confidence": float(leg.get("confidence_score", 0.0)),
                "sport": str(leg.get("sport", "NFL")),
            }
            
            # Skip legs with missing required fields
            if not leg_data["market_id"] or not leg_data["outcome"]:
                continue
            
            legs_data.append(leg_data)
        
        return legs_data
    
    def _calculate_parlay_probability(self, leg_probabilities: List[float]) -> float:
        """Calculate overall parlay hit probability."""
        if not leg_probabilities:
            return 0.0
        
        parlay_prob = 1.0
        for prob in leg_probabilities:
            parlay_prob *= prob
        
        return parlay_prob
    
    def _calculate_parlay_ev(self, legs_data: List[Dict], parlay_prob: float) -> float:
        """
        Calculate expected value for the parlay.
        
        EV = (model_prob * decimal_payout) - 1
        
        Args:
            legs_data: List of leg dictionaries with odds
            parlay_prob: Combined model probability for the parlay
        
        Returns:
            Expected value as a decimal (0.1 = +10% EV)
        """
        if not legs_data or parlay_prob <= 0:
            return 0.0
        
        # Calculate combined decimal odds from each leg
        combined_decimal_odds = 1.0
        
        for leg in legs_data:
            try:
                odds_str = str(leg.get("odds", "-110"))
                
                # Parse American odds to decimal
                if odds_str.startswith("+"):
                    american_odds = int(odds_str[1:])
                    decimal_odds = (american_odds / 100) + 1
                elif odds_str.startswith("-"):
                    american_odds = abs(int(odds_str))
                    decimal_odds = (100 / american_odds) + 1
                else:
                    # Try parsing as number
                    american_odds = int(odds_str)
                    if american_odds > 0:
                        decimal_odds = (american_odds / 100) + 1
                    else:
                        decimal_odds = (100 / abs(american_odds)) + 1
                
                combined_decimal_odds *= decimal_odds
            except (ValueError, TypeError, ZeroDivisionError):
                # Default to -110 odds (1.909 decimal)
                combined_decimal_odds *= 1.909
        
        # EV = (prob * payout) - stake
        # For $1 stake: EV = (prob * decimal_odds) - 1
        ev = (parlay_prob * combined_decimal_odds) - 1
        
        return round(ev, 4)


async def build_mixed_sports_parlay(
    db: AsyncSession,
    num_legs: int,
    sports: List[str],
    risk_profile: str = "balanced",
    balance_sports: bool = True,
    week: Optional[int] = None
) -> Dict:
    """
    Convenience function for building mixed sports parlays.
    
    Args:
        db: Database session
        num_legs: Number of legs
        sports: List of sports to mix
        risk_profile: Risk profile (conservative/balanced/degen)
        balance_sports: Whether to evenly distribute legs across sports
        week: NFL week number to build from (only applies to NFL legs)
        
    Returns:
        Parlay data dictionary
    """
    builder = MixedSportsParlayBuilder(db)
    return await builder.build_mixed_parlay(
        num_legs=num_legs,
        sports=sports,
        risk_profile=risk_profile,
        balance_sports=balance_sports,
        week=week
    )

