"""Probability calculation engine for parlay building"""

from decimal import Decimal
from typing import Dict, List, Optional, Type
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.market import Market
from app.models.odds import Odds
from app.services.data_fetchers.nfl_stats import NFLStatsFetcher
from app.services.data_fetchers.nba_stats import NBAStatsFetcher
from app.services.data_fetchers.nhl_stats import NHLStatsFetcher
from app.services.data_fetchers.weather import WeatherFetcher
from app.services.data_fetchers.injuries import InjuryFetcher


class BaseProbabilityEngine:
    """Engine for calculating win probabilities and edges."""

    sport_code = "GENERIC"

    def __init__(
        self,
        db: AsyncSession,
        stats_fetcher=None,
        weather_fetcher=None,
        injury_fetcher=None,
    ):
        self.db = db
        self.stats_fetcher = stats_fetcher
        self.weather_fetcher = weather_fetcher
        self.injury_fetcher = injury_fetcher

        # Cache for performance (avoid repeated API calls)
        self._team_stats_cache = {}
        self._weather_cache = {}
        self._injury_cache = {}
        self._team_strength_cache = {}
    
    async def calculate_leg_probability_from_odds(
        self,
        odds_obj: Odds,
        market_id,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None
    ) -> Dict:
        """
        Calculate the win probability for a specific leg using an existing odds object
        
        Args:
            odds_obj: Odds object
            market_id: Market ID
            outcome: Outcome (home/away, spread, total)
            home_team: Home team name
            away_team: Away team name
            game_start_time: Optional game start time for weather/context
            market_type: Optional market type (h2h, spreads, totals)
        
        Returns:
            dict with probability, edge, confidence_score
        """
        # Base probability is the implied probability from odds
        implied_prob = float(odds_obj.implied_prob)
        
        # Apply enhanced heuristic adjustments
        adjusted_prob = await self._apply_heuristics(
            implied_prob,
            market_id,
            outcome,
            home_team,
            away_team,
            game_start_time,
            market_type
        )
        
        # Calculate edge (how much better is our probability vs implied)
        edge = adjusted_prob - implied_prob
        
        # Calculate value score
        value_score = self._calculate_value_score(adjusted_prob, implied_prob, float(odds_obj.decimal_price))
        
        # Confidence score (0-100) based on edge, probability, and value
        confidence = self._calculate_confidence(adjusted_prob, edge, value_score)
        
        return {
            "market_id": str(market_id),
            "outcome": outcome,
            "implied_prob": implied_prob,
            "adjusted_prob": adjusted_prob,
            "edge": edge,
            "value_score": value_score,
            "confidence_score": confidence,
            "odds": odds_obj.price,
            "decimal_odds": float(odds_obj.decimal_price),
        }
    
    async def calculate_leg_probability(
        self,
        market_id,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None
    ) -> Dict:
        """
        Calculate the win probability for a specific leg (legacy method for backward compatibility)
        
        Returns:
            dict with probability, edge, confidence_score
        """
        # Get the odds for this market and outcome
        result = await self.db.execute(
            select(Odds)
            .join(Market)
            .where(Market.id == market_id)
            .where(Odds.outcome == outcome)
            .order_by(Odds.implied_prob.desc())  # Get best odds
            .limit(1)
        )
        odds_obj = result.scalar_one_or_none()
        
        if not odds_obj:
            return None
        
        return await self.calculate_leg_probability_from_odds(
            odds_obj, market_id, outcome, home_team, away_team, game_start_time, market_type
        )
    
    async def _apply_heuristics(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        game_start_time: Optional[datetime] = None,
        market_type: Optional[str] = None
    ) -> float:
        """
        Apply enhanced heuristic adjustments to implied probability
        
        Uses:
        - Team performance factors (recent form, strength)
        - Situational factors (rest days, travel, divisional games)
        - Weather impact
        - Injury impact
        - Market efficiency analysis
        """
        adjusted = implied_prob
        
        # Determine which team the outcome favors
        is_home_outcome = "home" in outcome.lower() or outcome.lower() == home_team.lower()
        favored_team = home_team if is_home_outcome else away_team
        opponent_team = away_team if is_home_outcome else home_team
        
        # 1. Team Performance Factors
        team_strength = await self._calculate_team_strength(favored_team, opponent_team)
        if team_strength:
            strength_diff = team_strength.get("strength_diff", 0)
            # Adjust probability based on team strength difference
            adjusted += strength_diff * 0.05  # Scale strength diff to probability adjustment
        
        # 2. Situational Adjustments
        situational_adj = await self._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )
        adjusted += situational_adj
        
        # 3. Weather Impact (for outdoor games)
        if game_start_time:
            weather_adj = await self._apply_weather_adjustment(
                home_team, game_start_time, is_home_outcome, market_type
            )
            adjusted += weather_adj
        
        # 4. Injury Impact
        injury_adj = await self._apply_injury_adjustment(favored_team, opponent_team, is_home_outcome)
        adjusted += injury_adj
        
        # 5. Sport-specific tweaks (overridable)
        sport_adj = await self._apply_sport_specific_adjustments(
            implied_prob,
            market_id,
            outcome,
            home_team,
            away_team,
            market_type,
        )
        adjusted += sport_adj

        # 6. Market Efficiency (detect value)
        market_adj = self._detect_market_inefficiencies(implied_prob)
        adjusted += market_adj
        
        # 7. Extreme odds adjustment (keep existing logic)
        if implied_prob > 0.85:
            adjusted = adjusted * 0.98  # Slight reduction for heavy favorites
        elif implied_prob < 0.15:
            adjusted = adjusted * 1.02  # Slight increase for heavy underdogs
        
        # Ensure probability stays in valid range
        adjusted = max(0.01, min(0.99, adjusted))
        
        return adjusted
    
    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        """Hook for sport-specific tuning in derived classes."""
        return 0.0

    async def _calculate_team_strength(self, team1: str, team2: str) -> Optional[Dict]:
        """
        Calculate team strength metrics and comparison (with caching)
        
        Returns:
            Dictionary with strength metrics and difference
        """
        # Check cache first
        cache_key = (team1.lower(), team2.lower())
        if cache_key in self._team_strength_cache:
            return self._team_strength_cache[cache_key]
        
        if not self.stats_fetcher:
            return None
        try:
            # Check individual team caches
            if team1.lower() not in self._team_stats_cache:
                self._team_stats_cache[team1.lower()] = await self.stats_fetcher.get_team_stats(team1)
            if team2.lower() not in self._team_stats_cache:
                self._team_stats_cache[team2.lower()] = await self.stats_fetcher.get_team_stats(team2)
            
            team1_stats = self._team_stats_cache[team1.lower()]
            team2_stats = self._team_stats_cache[team2.lower()]
            
            if not team1_stats or not team2_stats:
                return None
            
            # Calculate win percentage
            team1_wins = team1_stats.get("wins", 0)
            team1_losses = team1_stats.get("losses", 0)
            team1_games = team1_wins + team1_losses
            team1_win_pct = team1_wins / team1_games if team1_games > 0 else 0.5
            
            team2_wins = team2_stats.get("wins", 0)
            team2_losses = team2_stats.get("losses", 0)
            team2_games = team2_wins + team2_losses
            team2_win_pct = team2_wins / team2_games if team2_games > 0 else 0.5
            
            # Get recent form (cache key includes team name)
            form_key1 = f"{team1.lower()}_form"
            form_key2 = f"{team2.lower()}_form"
            
            if form_key1 not in self._team_stats_cache:
                self._team_stats_cache[form_key1] = await self.stats_fetcher.get_recent_form(team1, games=5)
            if form_key2 not in self._team_stats_cache:
                self._team_stats_cache[form_key2] = await self.stats_fetcher.get_recent_form(team2, games=5)
            
            team1_form = self._team_stats_cache[form_key1]
            team2_form = self._team_stats_cache[form_key2]
            
            # Calculate recent form (wins in last 5)
            team1_recent_wins = 0
            for g in team1_form:
                if g.get("completed"):
                    home_team_name = g.get("home_team", "").lower()
                    away_team_name = g.get("away_team", "").lower()
                    team1_lower = team1.lower()
                    if team1_lower in home_team_name:
                        if g.get("home_score", 0) > g.get("away_score", 0):
                            team1_recent_wins += 1
                    elif team1_lower in away_team_name:
                        if g.get("away_score", 0) > g.get("home_score", 0):
                            team1_recent_wins += 1
            
            team2_recent_wins = 0
            for g in team2_form:
                if g.get("completed"):
                    home_team_name = g.get("home_team", "").lower()
                    away_team_name = g.get("away_team", "").lower()
                    team2_lower = team2.lower()
                    if team2_lower in home_team_name:
                        if g.get("home_score", 0) > g.get("away_score", 0):
                            team2_recent_wins += 1
                    elif team2_lower in away_team_name:
                        if g.get("away_score", 0) > g.get("home_score", 0):
                            team2_recent_wins += 1
            
            # Strength difference (-1 to 1, where positive favors team1)
            strength_diff = (team1_win_pct - team2_win_pct) + ((team1_recent_wins - team2_recent_wins) * 0.1)
            
            result = {
                "team1_win_pct": team1_win_pct,
                "team2_win_pct": team2_win_pct,
                "team1_recent_form": team1_recent_wins / 5.0 if team1_form else 0.5,
                "team2_recent_form": team2_recent_wins / 5.0 if team2_form else 0.5,
                "strength_diff": strength_diff,
            }
            
            # Cache the result
            self._team_strength_cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"Error calculating team strength: {e}")
            return None
    
    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime]
    ) -> float:
        """
        Apply situational adjustments (rest days, travel, divisional games)
        
        Returns:
            Probability adjustment (-0.1 to 0.1)
        """
        adjustment = 0.0
        
        if not game_start_time:
            return adjustment
        
        # Rest days calculation (simplified - would need actual last game dates)
        # For now, use day of week as proxy
        day_of_week = game_start_time.weekday()
        
        # Divisional games tend to be closer (reduce favorite advantage slightly)
        # This is a simplified check - would need actual division data
        if is_home_outcome:
            # Home team advantage already accounted for, but divisional games reduce it
            adjustment += 0.01  # Small home boost
        
        # Travel distance (simplified - would need actual distances)
        # West coast teams traveling east have disadvantage
        # For now, use time zone as proxy
        adjustment += 0.0  # Placeholder for travel adjustments
        
        return adjustment
    
    async def _apply_weather_adjustment(
        self,
        home_team: str,
        game_start_time: datetime,
        is_home_outcome: bool,
        market_type: Optional[str]
    ) -> float:
        """
        Apply weather-based adjustments (with caching)
        
        Returns:
            Probability adjustment based on weather impact
        """
        # Cache key: team + date (same weather for all legs of same game)
        cache_key = (home_team.lower(), game_start_time.date() if game_start_time else None)
        
        if not self.weather_fetcher:
            return 0.0
        try:
            if cache_key not in self._weather_cache:
                self._weather_cache[cache_key] = await self.weather_fetcher.get_game_weather(
                    home_team, game_start_time
                )
            
            weather = self._weather_cache[cache_key]
            
            if not weather or not weather.get("affects_game"):
                return 0.0
            
            # Weather typically favors the home team (they're more used to conditions)
            if is_home_outcome:
                # Home team advantage in bad weather
                return 0.02
            else:
                # Away team disadvantage in bad weather
                return -0.02
                
        except Exception as e:
            print(f"Error applying weather adjustment: {e}")
            return 0.0
    
    async def _apply_injury_adjustment(
        self,
        favored_team: str,
        opponent_team: str,
        is_home_outcome: bool
    ) -> float:
        """
        Apply injury-based adjustments (with caching)
        
        Returns:
            Probability adjustment based on key player injuries
        """
        if not self.injury_fetcher:
            return 0.0
        try:
            # Check cache first
            if favored_team.lower() not in self._injury_cache:
                self._injury_cache[favored_team.lower()] = await self.injury_fetcher.get_key_player_status(favored_team)
            if opponent_team.lower() not in self._injury_cache:
                self._injury_cache[opponent_team.lower()] = await self.injury_fetcher.get_key_player_status(opponent_team)
            
            favored_injuries = self._injury_cache[favored_team.lower()]
            opponent_injuries = self._injury_cache[opponent_team.lower()]
            
            adjustment = 0.0
            
            # Check for high-impact injuries on favored team
            for player, status in favored_injuries.items():
                impact = status.get("impact", "none")
                if impact == "high":
                    adjustment -= 0.03  # Reduce probability if key player out
                elif impact == "medium":
                    adjustment -= 0.015
            
            # Check for high-impact injuries on opponent (helps favored team)
            for player, status in opponent_injuries.items():
                impact = status.get("impact", "none")
                if impact == "high":
                    adjustment += 0.03  # Increase probability if opponent key player out
                elif impact == "medium":
                    adjustment += 0.015
            
            return adjustment
            
        except Exception as e:
            print(f"Error applying injury adjustment: {e}")
            return 0.0
    
    def _detect_market_inefficiencies(self, implied_prob: float) -> float:
        """
        Detect market inefficiencies and value opportunities
        
        Returns:
            Small adjustment if value detected
        """
        # Simple heuristic: if implied prob is in "sweet spot" (40-60%), 
        # markets are often less efficient
        if 0.40 <= implied_prob <= 0.60:
            # Slight positive adjustment for middle-range probabilities
            # (markets often misprice these)
            return 0.01
        
        # Extreme probabilities are usually well-priced
        return 0.0
    
    def _calculate_value_score(self, adjusted_prob: float, implied_prob: float, decimal_odds: float) -> float:
        """
        Calculate expected value score
        
        Returns:
            Value score (positive = value bet, negative = bad value)
        """
        # Expected value = (adjusted_prob * decimal_odds) - 1
        expected_value = (adjusted_prob * decimal_odds) - 1.0
        
        # Normalize to -1 to 1 scale
        return max(-1.0, min(1.0, expected_value))
    
    def _calculate_confidence(self, probability: float, edge: float, value_score: float = 0.0) -> float:
        """
        Calculate confidence score (0-100) based on probability, edge, and value
        
        Higher probability + positive edge + positive value = higher confidence
        """
        # Base confidence from probability (50-100 scale)
        prob_score = 50 + (probability * 50)
        
        # Edge bonus (0-20 points)
        edge_bonus = min(20, max(0, edge * 200))  # Scale edge to 0-20
        
        # Value bonus (0-10 points)
        value_bonus = min(10, max(0, value_score * 10))  # Scale value to 0-10
        
        # Combine scores
        confidence = prob_score + edge_bonus + value_bonus
        
        # Normalize to 0-100
        return max(0, min(100, confidence))
    
    async def get_candidate_legs(
        self,
        sport: Optional[str] = None,
        min_confidence: float = 50.0,
        max_legs: int = 50
    ) -> List[Dict]:
        """
        Get candidate legs for parlay building
        
        Returns legs sorted by confidence score
        """
        # Get recent games
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=48)
        
        target_sport = (sport or self.sport_code or "NFL").upper()
        candidate_legs = []
        
        # Optimize: Load all relationships at once
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(Game)
            .where(Game.sport == target_sport)
            .where(Game.start_time >= cutoff_time)
            .where(Game.status == "scheduled")
            .options(selectinload(Game.markets).selectinload(Market.odds))
        )
        games = result.scalars().all()
        
        print(f"Found {len(games)} {target_sport} games with relationships loaded")
        
        # Pre-fetch and cache data for all games to avoid repeated API calls
        print("Pre-fetching auxiliary data for all games...")
        for game in games:
            # Cache team stats (only fetch once per team)
            if self.stats_fetcher:
                if game.home_team.lower() not in self._team_stats_cache:
                    self._team_stats_cache[game.home_team.lower()] = await self.stats_fetcher.get_team_stats(game.home_team)
                if game.away_team.lower() not in self._team_stats_cache:
                    self._team_stats_cache[game.away_team.lower()] = await self.stats_fetcher.get_team_stats(game.away_team)
            
            # Cache weather (once per game)
            if self.weather_fetcher and game.start_time:
                weather_key = (game.home_team.lower(), game.start_time.date())
                if weather_key not in self._weather_cache:
                    self._weather_cache[weather_key] = await self.weather_fetcher.get_game_weather(
                        game.home_team, game.start_time
                    )
            
            # Cache injuries (once per team)
            if self.injury_fetcher:
                if game.home_team.lower() not in self._injury_cache:
                    self._injury_cache[game.home_team.lower()] = await self.injury_fetcher.get_key_player_status(game.home_team)
                if game.away_team.lower() not in self._injury_cache:
                    self._injury_cache[game.away_team.lower()] = await self.injury_fetcher.get_key_player_status(game.away_team)
        
        print(f"Pre-fetching complete. Processing {len(games)} games...")
        
        processed_count = 0
        for game in games:
            for market in game.markets:
                if market.market_type not in ["h2h", "spreads", "totals"]:
                    continue
                    
                for odds in market.odds:
                    processed_count += 1
                    if processed_count % 100 == 0:
                        print(f"Processed {processed_count} odds, found {len(candidate_legs)} candidates so far...")
                    
                    try:
                        # Use the optimized method that doesn't query the database again
                        # Data is now cached, so this will be fast
                        leg_prob = await self.calculate_leg_probability_from_odds(
                            odds,
                            market.id,
                            odds.outcome,
                            game.home_team,
                            game.away_team,
                            game.start_time,
                            market.market_type
                        )
                        
                        if leg_prob and leg_prob["confidence_score"] >= min_confidence:
                            leg_prob.update({
                                "game_id": str(game.id),
                                "game": f"{game.away_team} @ {game.home_team}",
                                "home_team": game.home_team,
                                "away_team": game.away_team,
                                "market_type": market.market_type,
                                "book": market.book,
                                "start_time": game.start_time.isoformat(),
                            })
                            candidate_legs.append(leg_prob)
                    except Exception as e:
                        print(f"Error calculating leg probability for market {market.id}, outcome {odds.outcome}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
        
        print(f"Finished processing. Found {len(candidate_legs)} candidate legs")
        
        # Sort by confidence score (descending)
        candidate_legs.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        print(f"Returning top {min(max_legs, len(candidate_legs))} candidate legs")
        return candidate_legs[:max_legs]
    
    def calculate_parlay_probability(self, leg_probabilities: List[float]) -> float:
        """
        Calculate overall parlay hit probability
        
        For independent events: P(parlay) = P(leg1) * P(leg2) * ... * P(legN)
        """
        if not leg_probabilities:
            return 0.0
        
        parlay_prob = 1.0
        for prob in leg_probabilities:
            parlay_prob *= prob
        
        return parlay_prob


class GenericProbabilityEngine(BaseProbabilityEngine):
    """Fallback probability engine for sports without dedicated models."""

    sport_code = "GENERIC"

    def __init__(self, db: AsyncSession):
        super().__init__(db, injury_fetcher=InjuryFetcher())


class NFLProbabilityEngine(BaseProbabilityEngine):
    """NFL-specific probability engine (default)."""

    sport_code = "NFL"

    def __init__(self, db: AsyncSession):
        super().__init__(
            db,
            stats_fetcher=NFLStatsFetcher(),
            weather_fetcher=WeatherFetcher(),
            injury_fetcher=InjuryFetcher(),
        )


class NBAProbabilityEngine(BaseProbabilityEngine):
    """NBA probability engine with pace/offensive rating heuristics."""

    sport_code = "NBA"

    def __init__(self, db: AsyncSession):
        super().__init__(db, stats_fetcher=NBAStatsFetcher(), injury_fetcher=InjuryFetcher())

    async def _apply_situational_adjustments(
        self,
        home_team: str,
        away_team: str,
        is_home_outcome: bool,
        game_start_time: Optional[datetime],
    ) -> float:
        base = await super()._apply_situational_adjustments(
            home_team, away_team, is_home_outcome, game_start_time
        )
        if is_home_outcome:
            base += 0.02  # NBA home-court edge
        if game_start_time:
            # Mild fatigue penalty for early weekday games (travel heavy)
            if game_start_time.weekday() in (0, 1):  # Monday/Tuesday
                base -= 0.01
        return base

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        if not self.stats_fetcher:
            return 0.0
        adjustment = 0.0
        favored_team = home_team if "home" in outcome.lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        team_stats = await self.stats_fetcher.get_team_stats(favored_team)
        opponent_stats = await self.stats_fetcher.get_team_stats(opponent_team)
        if not team_stats or not opponent_stats:
            return 0.0

        offensive_edge = (
            team_stats.get("offensive_rating", 110) - opponent_stats.get("defensive_rating", 110)
        ) / 100.0
        adjustment += offensive_edge * 0.1

        if market_type == "totals":
            pace_avg = (team_stats.get("pace", 99) + opponent_stats.get("pace", 99)) / 2
            adjustment += (pace_avg - 100) * 0.003

        rebound_edge = (team_stats.get("rebound_rate", 50) - opponent_stats.get("rebound_rate", 50)) / 100.0
        adjustment += rebound_edge * 0.05

        return adjustment


class NHLProbabilityEngine(BaseProbabilityEngine):
    """NHL probability engine using goal differential & special teams heuristics."""

    sport_code = "NHL"

    def __init__(self, db: AsyncSession):
        super().__init__(db, stats_fetcher=NHLStatsFetcher(), injury_fetcher=InjuryFetcher())

    async def _apply_sport_specific_adjustments(
        self,
        implied_prob: float,
        market_id: str,
        outcome: str,
        home_team: str,
        away_team: str,
        market_type: Optional[str] = None,
    ) -> float:
        if not self.stats_fetcher:
            return 0.0
        adjustment = 0.0
        favored_team = home_team if "home" in outcome.lower() else away_team
        opponent_team = away_team if favored_team == home_team else home_team

        team_stats = await self.stats_fetcher.get_team_stats(favored_team)
        opponent_stats = await self.stats_fetcher.get_team_stats(opponent_team)
        if not team_stats or not opponent_stats:
            return 0.0

        goal_edge = (team_stats.get("goals_for", 3.0) - opponent_stats.get("goals_against", 2.8)) * 0.05
        adjustment += goal_edge

        special_teams_edge = (
            (team_stats.get("power_play_pct", 20) - opponent_stats.get("penalty_kill_pct", 80)) / 100.0
        )
        adjustment += special_teams_edge * 0.05

        recent_form = await self.stats_fetcher.get_recent_form(favored_team)
        if recent_form:
            wins = sum(1 for game in recent_form if game.get("is_win"))
            adjustment += (wins / len(recent_form) - 0.5) * 0.05

        return adjustment


ENGINE_CLASS_MAP: Dict[str, Type[BaseProbabilityEngine]] = {
    "nfl": NFLProbabilityEngine,
    "americanfootball_nfl": NFLProbabilityEngine,
    "nba": NBAProbabilityEngine,
    "basketball_nba": NBAProbabilityEngine,
    "nhl": NHLProbabilityEngine,
    "icehockey_nhl": NHLProbabilityEngine,
    "mlb": GenericProbabilityEngine,
    "baseball_mlb": GenericProbabilityEngine,
    "soccer": GenericProbabilityEngine,
    "soccer_epl": GenericProbabilityEngine,
    "ufc": GenericProbabilityEngine,
    "mma": GenericProbabilityEngine,
    "mma_mixed_martial_arts": GenericProbabilityEngine,
    "boxing": GenericProbabilityEngine,
    "boxing_boxing": GenericProbabilityEngine,
}


def get_probability_engine(db: AsyncSession, sport: Optional[str] = None) -> BaseProbabilityEngine:
    """Factory returning an engine tuned for the requested sport."""
    key = (sport or "nfl").lower()
    engine_cls = ENGINE_CLASS_MAP.get(key, NFLProbabilityEngine)
    return engine_cls(db)


# Backwards compatibility (legacy imports expect ProbabilityEngine to be NFL)
ProbabilityEngine = NFLProbabilityEngine

