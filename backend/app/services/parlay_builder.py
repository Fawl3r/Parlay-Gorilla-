"""Parlay builder service"""

from typing import List, Dict, Optional
from decimal import Decimal
from itertools import cycle
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.probability_engine import get_probability_engine
from app.models.parlay import Parlay


class ParlayBuilderService:
    """Service for building parlay suggestions"""
    
    def __init__(self, db: AsyncSession, sport: str = "NFL"):
        self.db = db
        self.sport = sport
        self.prob_engine = get_probability_engine(db, sport)
    
    async def build_parlay(
        self,
        num_legs: int,
        risk_profile: str = "balanced",
        sport: Optional[str] = None,
    ) -> Dict:
        """
        Build a parlay suggestion based on parameters
        
        Args:
            num_legs: Number of legs (1-20)
            risk_profile: conservative, balanced, or degen
            
        Returns:
            Dictionary with parlay details
        """
        # Validate inputs
        num_legs = max(1, min(20, num_legs))
        risk_profile = risk_profile.lower()
        if risk_profile not in ["conservative", "balanced", "degen"]:
            risk_profile = "balanced"
        
        # Get candidate legs based on risk profile
        min_confidence = self._get_min_confidence(risk_profile)
        print(f"Getting candidate legs with min_confidence={min_confidence}")
        
        # Start with requested confidence, but be flexible
        active_sport = sport or self.sport
        candidates = await self.prob_engine.get_candidate_legs(
            sport=active_sport,
            min_confidence=min_confidence,
            max_legs=200  # Get more candidates to work with
        )
        
        print(f"Found {len(candidates)} candidate legs with min_confidence={min_confidence}")
        
        # If not enough, lower confidence threshold progressively
        if len(candidates) < num_legs:
            print(f"Not enough candidates with {min_confidence} confidence. Lowering threshold...")
            for lower_threshold in [min_confidence * 0.9, min_confidence * 0.8, min_confidence * 0.7, 30.0, 20.0]:
                candidates = await self.prob_engine.get_candidate_legs(
                    sport=active_sport,
                    min_confidence=lower_threshold,
                    max_legs=200
                )
                print(f"Found {len(candidates)} candidates with min_confidence={lower_threshold}")
                if len(candidates) >= num_legs:
                    break
        
        if len(candidates) < num_legs:
            # Last resort: get all legs regardless of confidence
            print("Getting all available legs regardless of confidence...")
            candidates = await self.prob_engine.get_candidate_legs(
                sport=active_sport,
                min_confidence=0.0,
                max_legs=200
            )
            print(f"Found {len(candidates)} total candidate legs")
        
        # If still not enough, we'll work with what we have
        if len(candidates) < num_legs:
            print(f"Warning: Only {len(candidates)} candidates available, requested {num_legs}. Will use available legs.")
        
        # Select legs based on risk profile strategy with enhanced optimization
        selected_legs = await self._select_legs_optimized(candidates, num_legs, risk_profile)
        
        # Calculate parlay probability
        leg_probs = [leg["adjusted_prob"] for leg in selected_legs]
        parlay_prob = self.prob_engine.calculate_parlay_probability(leg_probs)
        
        # Prepare legs data for storage
        legs_data = []
        for leg in selected_legs:
            # Debug: print leg keys to see what's available
            if not leg.get("game"):
                print(f"Leg missing 'game' field. Available keys: {list(leg.keys())}")
            
            # Ensure all required fields are present
            # Build game string if not present
            game_str = leg.get("game", "")
            if not game_str:
                # Try to reconstruct from available data
                # Check if we have home_team/away_team in the leg
                home_team = leg.get("home_team", "")
                away_team = leg.get("away_team", "")
                if home_team and away_team:
                    game_str = f"{away_team} @ {home_team}"
                else:
                    # Last resort: use game_id
                    game_id = leg.get("game_id", "")
                    game_str = f"Game {str(game_id)[:8]}" if game_id else "Unknown Game"
            
            # Build leg_data dictionary (always defined, regardless of game_str path)
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
            }
            
            # Validate required fields (be more lenient - only skip if truly missing)
            if not leg_data["market_id"] or leg_data["market_id"] == "unknown":
                print(f"Warning: Leg missing market_id. Leg keys: {list(leg.keys())}")
                # Use game_id as fallback if available
                if leg.get("game_id"):
                    leg_data["market_id"] = str(leg.get("game_id"))
                else:
                    print(f"Skipping leg with no market_id: {leg}")
                    continue
            
            if not leg_data["outcome"]:
                print(f"Skipping leg with no outcome: {leg}")
                continue
                
            legs_data.append(leg_data)
        
        # If we still don't have enough, try to get more from candidates
        if len(legs_data) < num_legs:
            print(f"Only got {len(legs_data)} valid legs, need {num_legs}. Trying to get more...")
            
            # Get all candidates again with lower threshold
            all_candidates = await self.prob_engine.get_candidate_legs(
                min_confidence=0.0,  # No minimum
                max_legs=500
            )
            
            # Add more legs that weren't already selected
            selected_game_keys = {(leg.get("game_id"), leg.get("market_type"), leg.get("outcome")) 
                                 for leg in selected_legs}
            
            for candidate in all_candidates:
                if len(legs_data) >= num_legs:
                    break
                
                key = (candidate.get("game_id"), candidate.get("market_type"), candidate.get("outcome"))
                if key not in selected_game_keys:
                    # Build leg data
                    game_str = candidate.get("game", "")
                    if not game_str:
                        home_team = candidate.get("home_team", "")
                        away_team = candidate.get("away_team", "")
                        if home_team and away_team:
                            game_str = f"{away_team} @ {home_team}"
                    
                    leg_data = {
                        "market_id": str(candidate.get("market_id", "")),
                        "outcome": str(candidate.get("outcome", "")),
                        "game": str(game_str or "Unknown Game"),
                        "home_team": str(candidate.get("home_team", "")),
                        "away_team": str(candidate.get("away_team", "")),
                        "market_type": str(candidate.get("market_type", "")),
                        "odds": str(candidate.get("odds", "")),
                        "probability": float(candidate.get("adjusted_prob", 0.0)),
                        "confidence": float(candidate.get("confidence_score", 0.0)),
                    }
                    
                    if leg_data["market_id"] and leg_data["outcome"]:
                        legs_data.append(leg_data)
                        selected_game_keys.add(key)
            
            print(f"After adding more candidates: {len(legs_data)} legs")
        
        # Final check - use what we have
        if len(legs_data) < num_legs:
            print(f"Final: Got {len(legs_data)} valid legs, requested {num_legs}. Using available legs.")
        
        # Use actual number of valid legs
        actual_num_legs = len(legs_data)
        
        # Recalculate parlay probability from actual legs_data (in case some legs were skipped or added)
        leg_probs_final = [leg.get("probability", 0.0) for leg in legs_data]
        parlay_prob_final = self.prob_engine.calculate_parlay_probability(leg_probs_final)
        
        # Calculate confidence scores from legs_data (not selected_legs, since some may have been skipped)
        confidence_scores = [float(leg.get("confidence", 0.0)) for leg in legs_data]
        overall_confidence = float(sum(leg.get("confidence", 0.0) for leg in legs_data) / actual_num_legs if actual_num_legs > 0 else 0.0)
        
        return {
            "legs": legs_data,
            "num_legs": int(actual_num_legs),  # Use actual count, not requested
            "parlay_hit_prob": float(parlay_prob_final),
            "risk_profile": str(risk_profile),
            "confidence_scores": confidence_scores,
            "overall_confidence": overall_confidence,
        }

    async def build_triple_parlay(
        self,
        sports: Optional[List[str]] = None,
        leg_overrides: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Dict]:
        """
        Build triple parlays (Safe/Balanced/Degen) with tailored configurations.
        """
        leg_overrides = leg_overrides or {}
        available_sports = [s for s in (sports or [self.sport]) if s]
        if not available_sports:
            raise ValueError("At least one sport must be provided to build triple parlays")

        profile_configs = {
            "safe": {
                "risk_profile": "conservative",
                "default_legs": 4,
                "min_legs": 3,
                "max_legs": 6,
                "confidence_floor": 70,
            },
            "balanced": {
                "risk_profile": "balanced",
                "default_legs": 8,
                "min_legs": 7,
                "max_legs": 12,
                "confidence_floor": 55,
            },
            "degen": {
                "risk_profile": "degen",
                "default_legs": 14,
                "min_legs": 13,
                "max_legs": 20,
                "confidence_floor": 40,
            },
        }

        sport_cycle = cycle(available_sports)
        results: Dict[str, Dict] = {}

        for profile_name, config in profile_configs.items():
            requested_legs = leg_overrides.get(profile_name)
            num_legs = config["default_legs"]
            if requested_legs is not None:
                num_legs = max(config["min_legs"], min(config["max_legs"], int(requested_legs)))

            target_sport = next(sport_cycle)
            builder = ParlayBuilderService(self.db, target_sport)
            parlay_data = await builder.build_parlay(
                num_legs=num_legs,
                risk_profile=config["risk_profile"],
                sport=target_sport,
            )

            results[profile_name] = {
                "parlay": parlay_data,
                "config": {
                    "num_legs": parlay_data.get("num_legs", num_legs),
                    "risk_profile": config["risk_profile"],
                    "sport": target_sport,
                    "confidence_floor": config["confidence_floor"],
                    "leg_range": (config["min_legs"], config["max_legs"]),
                },
            }

        return results
    
    def _get_min_confidence(self, risk_profile: str) -> float:
        """Get minimum confidence threshold based on risk profile"""
        thresholds = {
            "conservative": 70.0,  # Only high-confidence picks
            "balanced": 55.0,      # Mix of medium-high confidence
            "degen": 40.0,         # Lower threshold, more risk
        }
        return thresholds.get(risk_profile, 55.0)
    
    def _select_legs(
        self,
        candidates: List[Dict],
        num_legs: int,
        risk_profile: str
    ) -> List[Dict]:
        """
        Select legs based on risk profile strategy
        
        - Conservative: Top N highest confidence
        - Balanced: Mix of high and medium confidence
        - Degen: More variety, include some lower confidence with higher edge
        
        Ensures each leg is unique by (game_id, market_type, outcome) combination
        """
        # First, deduplicate candidates by (game_id, market_type, outcome)
        # Keep the one with highest confidence for each unique combination
        unique_legs = {}
        for leg in candidates:
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            if key not in unique_legs or leg["confidence_score"] > unique_legs[key]["confidence_score"]:
                unique_legs[key] = leg
        
        # Convert back to list and sort by confidence
        deduplicated = list(unique_legs.values())
        deduplicated.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        if len(deduplicated) < num_legs:
            raise ValueError(f"Not enough unique candidate legs available. Found {len(deduplicated)} unique legs, need {num_legs}")
        
        if risk_profile == "conservative":
            # Simply take top N highest confidence
            return deduplicated[:num_legs]
        
        elif risk_profile == "balanced":
            # Take mix: 60% top confidence, 40% high edge
            top_count = int(num_legs * 0.6)
            edge_sorted = sorted(deduplicated, key=lambda x: x["edge"], reverse=True)
            
            selected = deduplicated[:top_count]
            selected_keys = {(leg.get("game_id"), leg.get("market_type"), leg.get("outcome")) for leg in selected}
            
            # Add high-edge picks that aren't already selected
            for leg in edge_sorted:
                if len(selected) >= num_legs:
                    break
                key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
                if key not in selected_keys:
                    selected.append(leg)
                    selected_keys.add(key)
            
            return selected[:num_legs]
        
        else:  # degen
            # More variety: mix of confidence and edge
            selected = []
            selected_keys = set()
            
            top_third = deduplicated[:len(deduplicated)//3]
            middle_third = deduplicated[len(deduplicated)//3:2*len(deduplicated)//3]
            bottom_third = deduplicated[2*len(deduplicated)//3:]
            
            # Mix: 40% top, 40% middle, 20% bottom (for variety)
            top_count = int(num_legs * 0.4)
            middle_count = int(num_legs * 0.4)
            bottom_count = num_legs - top_count - middle_count
            
            # Helper to add unique legs
            def add_unique_legs(leg_list, count):
                for leg in leg_list:
                    if len(selected) >= num_legs:
                        break
                    key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
                    if key not in selected_keys:
                        selected.append(leg)
                        selected_keys.add(key)
            
            add_unique_legs(top_third, top_count)
            add_unique_legs(middle_third, middle_count)
            add_unique_legs(bottom_third, bottom_count)
            
            # Fill remaining slots with any unique legs
            if len(selected) < num_legs:
                for leg in deduplicated:
                    if len(selected) >= num_legs:
                        break
                    key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
                    if key not in selected_keys:
                        selected.append(leg)
                        selected_keys.add(key)
            
            return selected[:num_legs]
    
    async def _select_legs_optimized(
        self,
        candidates: List[Dict],
        num_legs: int,
        risk_profile: str
    ) -> List[Dict]:
        """
        Enhanced leg selection with correlation analysis, diversification, and EV optimization
        """
        # First, deduplicate candidates by (game_id, market_type, outcome)
        # Keep the one with highest confidence for each unique combination
        unique_legs = {}
        for leg in candidates:
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            if key not in unique_legs or leg.get("confidence_score", 0) > unique_legs[key].get("confidence_score", 0):
                unique_legs[key] = leg
        
        deduplicated = list(unique_legs.values())
        
        # If we don't have enough unique legs, try to get more by allowing different market types from same game
        if len(deduplicated) < num_legs:
            print(f"Only found {len(deduplicated)} unique legs, need {num_legs}. Trying to expand...")
            
            # Allow multiple market types from same game (e.g., h2h + spread from same game)
            expanded_legs = {}
            for leg in candidates:
                # Use (game_id, outcome) as key instead of (game_id, market_type, outcome)
                # This allows same outcome across different market types
                key = (leg.get("game_id"), leg.get("outcome"))
                if key not in expanded_legs or leg.get("confidence_score", 0) > expanded_legs[key].get("confidence_score", 0):
                    expanded_legs[key] = leg
            
            if len(expanded_legs) >= num_legs:
                print(f"Expanded to {len(expanded_legs)} legs by allowing different market types")
                deduplicated = list(expanded_legs.values())
            else:
                # Still not enough - use original candidates but deduplicate less strictly
                # Allow same game + outcome but different books
                final_legs = {}
                for leg in candidates:
                    # Only deduplicate by game_id + outcome (allow different books/markets)
                    key = (leg.get("game_id"), leg.get("outcome"))
                    if key not in final_legs or leg.get("confidence_score", 0) > final_legs[key].get("confidence_score", 0):
                        final_legs[key] = leg
                
                if len(final_legs) >= num_legs:
                    print(f"Using {len(final_legs)} legs with relaxed deduplication")
                    deduplicated = list(final_legs.values())
                else:
                    # Last resort: use all candidates, just remove exact duplicates
                    seen = set()
                    final_candidates = []
                    for leg in candidates:
                        key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"), leg.get("odds"))
                        if key not in seen:
                            seen.add(key)
                            final_candidates.append(leg)
                    
                    if len(final_candidates) < num_legs:
                        raise ValueError(
                            f"Not enough candidate legs available. Found {len(final_candidates)} unique legs, need {num_legs}. "
                            f"Try reducing the number of legs or changing the risk profile."
                        )
                    deduplicated = final_candidates
        
        # Calculate EV scores for all candidates
        for leg in deduplicated:
            leg["ev_score"] = self._calculate_leg_ev(leg)
        
        # Select legs using optimization strategy
        if risk_profile == "conservative":
            selected = self._optimize_for_ev(deduplicated, num_legs, min_confidence=70.0)
        elif risk_profile == "balanced":
            selected = self._optimize_for_ev(deduplicated, num_legs, min_confidence=55.0)
        else:  # degen
            selected = self._optimize_for_ev(deduplicated, num_legs, min_confidence=40.0, allow_lower_confidence=True)
        
        # Ensure diversification
        selected = self._ensure_diversification(selected, num_legs)
        
        # Remove highly correlated legs
        selected = self._remove_correlated_legs(selected)
        
        # If we removed legs, fill back up
        if len(selected) < num_legs:
            remaining = [leg for leg in deduplicated if leg not in selected]
            remaining.sort(key=lambda x: x.get("ev_score", 0), reverse=True)
            for leg in remaining:
                if len(selected) >= num_legs:
                    break
                if not self._is_correlated_with_selected(leg, selected):
                    selected.append(leg)
        
        return selected[:num_legs]
    
    def _calculate_leg_ev(self, leg: Dict) -> float:
        """
        Calculate expected value score for a leg
        
        EV = (probability * decimal_odds) - 1
        Higher EV = better value
        """
        prob = leg.get("adjusted_prob", 0)
        decimal_odds = leg.get("decimal_odds", 1.0)
        ev = (prob * decimal_odds) - 1.0
        
        # Also factor in confidence and edge
        confidence = leg.get("confidence_score", 0) / 100.0
        edge = leg.get("edge", 0)
        
        # Combined score: EV weighted by confidence
        ev_score = ev * (0.7 + 0.3 * confidence) + edge * 0.5
        
        return ev_score
    
    def _optimize_for_ev(
        self,
        candidates: List[Dict],
        num_legs: int,
        min_confidence: float = 50.0,
        allow_lower_confidence: bool = False
    ) -> List[Dict]:
        """
        Select legs that maximize expected value
        
        Uses a greedy algorithm: select legs with highest EV that meet criteria
        """
        # Filter by confidence
        filtered = [leg for leg in candidates if leg.get("confidence_score", 0) >= min_confidence]
        
        if not allow_lower_confidence and len(filtered) < num_legs:
            # If not enough high-confidence legs, lower threshold slightly
            filtered = [leg for leg in candidates if leg.get("confidence_score", 0) >= min_confidence * 0.8]
        
        # Sort by EV score
        filtered.sort(key=lambda x: x.get("ev_score", -999), reverse=True)
        
        selected = []
        selected_keys = set()
        
        # Greedy selection: pick highest EV legs
        for leg in filtered:
            if len(selected) >= num_legs:
                break
            key = (leg.get("game_id"), leg.get("market_type"), leg.get("outcome"))
            if key not in selected_keys:
                selected.append(leg)
                selected_keys.add(key)
        
        return selected
    
    def _ensure_diversification(self, selected: List[Dict], num_legs: int) -> List[Dict]:
        """
        Ensure legs are diversified across games while allowing best-value market types
        
        Allows unlimited legs per market type (e.g. all totals if they are best value),
        but still limits legs per game to prevent over-concentration and correlation issues.
        """
        if len(selected) <= 1:
            return selected
        
        diversified = []
        game_counts = {}
        market_type_counts = {}
        
        # Sort by EV to prioritize best legs
        sorted_selected = sorted(selected, key=lambda x: x.get("ev_score", -999), reverse=True)
        
        for leg in sorted_selected:
            game_id = leg.get("game_id")
            market_type = leg.get("market_type")
            
            # Check if adding this leg maintains diversification
            game_count = game_counts.get(game_id, 0)
            market_count = market_type_counts.get(market_type, 0)
            
            # Allow max 2 legs per game (prevents over-concentration and correlation)
            # Allow unlimited legs per market type (let best value drive selection)
            max_per_game = max(2, num_legs // 10)
            max_per_market = num_legs  # No limit on market type - pick best value regardless
            
            if game_count < max_per_game:
                # Only check game limit, not market type limit
                diversified.append(leg)
                game_counts[game_id] = game_count + 1
                market_type_counts[market_type] = market_count + 1
            
            if len(diversified) >= num_legs:
                break
        
        # Fill remaining slots if needed
        if len(diversified) < num_legs:
            for leg in sorted_selected:
                if leg not in diversified and len(diversified) < num_legs:
                    diversified.append(leg)
        
        return diversified
    
    def _calculate_leg_correlation(self, leg1: Dict, leg2: Dict) -> float:
        """
        Calculate correlation between two legs (0-1, where 1 = highly correlated)
        
        Legs are correlated if:
        - Same game
        - Related outcomes (e.g., home team win + home team spread)
        - Same market type for same game
        """
        correlation = 0.0
        
        # Same game = high correlation
        if leg1.get("game_id") == leg2.get("game_id"):
            correlation += 0.5
            
            # Same market type = even higher correlation
            if leg1.get("market_type") == leg2.get("market_type"):
                correlation += 0.3
            
            # Related outcomes (e.g., home win + home spread)
            outcome1 = leg1.get("outcome", "").lower()
            outcome2 = leg2.get("outcome", "").lower()
            
            if "home" in outcome1 and "home" in outcome2:
                correlation += 0.2
            elif "away" in outcome1 and "away" in outcome2:
                correlation += 0.2
        
        return min(1.0, correlation)
    
    def _is_correlated_with_selected(self, leg: Dict, selected: List[Dict], threshold: float = 0.6) -> bool:
        """
        Check if a leg is highly correlated with any selected leg
        """
        for selected_leg in selected:
            correlation = self._calculate_leg_correlation(leg, selected_leg)
            if correlation >= threshold:
                return True
        return False
    
    def _remove_correlated_legs(self, selected: List[Dict], max_correlation: float = 0.6) -> List[Dict]:
        """
        Remove highly correlated legs, keeping the ones with higher EV
        """
        if len(selected) <= 1:
            return selected
        
        # Sort by EV (keep best legs)
        sorted_legs = sorted(selected, key=lambda x: x.get("ev_score", -999), reverse=True)
        
        filtered = []
        for leg in sorted_legs:
            if not self._is_correlated_with_selected(leg, filtered, threshold=max_correlation):
                filtered.append(leg)
        
        return filtered

