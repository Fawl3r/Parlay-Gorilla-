"""
Prediction Tracker Service

Tracks model predictions vs actual outcomes for:
- Accuracy metrics
- Calibration analysis
- Per-team bias learning
- Model version comparison

This is the core of the "learning from misses" system.
"""

from typing import Dict, Optional, List, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import selectinload
import logging
import uuid

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome, TeamCalibration
from app.models.game import Game
from app.models.game_results import GameResult
from app.core.model_config import MODEL_VERSION, CALIBRATION_CONFIG

logger = logging.getLogger(__name__)


class PredictionTrackerService:
    """
    Service for tracking predictions and learning from outcomes.
    
    Key functions:
    - save_prediction(): Store a prediction when analysis is generated
    - resolve_prediction(): Link prediction to actual outcome
    - get_accuracy_stats(): Calculate accuracy, Brier score, calibration
    - calculate_team_bias(): Compute per-team bias adjustments
    - update_team_calibrations(): Refresh calibration values
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._calibration_cache: Dict[str, float] = {}
        self._cache_timestamp: Optional[datetime] = None
    
    async def save_prediction(
        self,
        game_id: Optional[str],
        sport: str,
        home_team: str,
        away_team: str,
        market_type: str,
        team_side: str,
        predicted_prob: float,
        implied_prob: Optional[float] = None,
        model_version: Optional[str] = None,
        calculation_method: Optional[str] = None,
        confidence_score: Optional[float] = None,
        features: Optional[Dict] = None,
        game_time: Optional[datetime] = None,
    ) -> ModelPrediction:
        """
        Save a prediction for tracking.
        
        Args:
            game_id: UUID of the game
            sport: Sport code (NFL, NBA, etc.)
            home_team: Home team name
            away_team: Away team name
            market_type: moneyline, spread, or total
            team_side: home, away, over, or under
            predicted_prob: Model's predicted probability (0-1)
            implied_prob: Market-implied probability (0-1)
            model_version: Version string (defaults to current)
            calculation_method: How probability was calculated
            confidence_score: Model confidence (0-100)
            features: Feature vector snapshot for debugging
            game_time: Scheduled game time
        
        Returns:
            Created ModelPrediction record
        """
        # Calculate edge
        edge = None
        if implied_prob is not None and implied_prob > 0:
            edge = predicted_prob - implied_prob
        
        prediction = ModelPrediction(
            game_id=uuid.UUID(game_id) if game_id else None,
            sport=sport.upper(),
            home_team=home_team,
            away_team=away_team,
            game_time=game_time,
            market_type=market_type,
            team_side=team_side,
            predicted_prob=predicted_prob,
            implied_prob=implied_prob,
            edge=edge,
            model_version=model_version or MODEL_VERSION,
            calculation_method=calculation_method,
            confidence_score=confidence_score,
            feature_snapshot=features,
            is_resolved="false",
        )
        
        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)
        
        logger.info(
            f"[PredictionTracker] Saved prediction: {away_team} @ {home_team}, "
            f"{market_type}/{team_side}, prob={predicted_prob:.3f}, edge={edge:.3f if edge else 'N/A'}"
        )
        
        return prediction
    
    async def resolve_prediction(
        self,
        game_id: str,
        actual_winner_side: str,
        actual_score_home: Optional[float] = None,
        actual_score_away: Optional[float] = None,
    ) -> List[PredictionOutcome]:
        """
        Resolve all predictions for a completed game.
        
        Args:
            game_id: UUID of the game
            actual_winner_side: "home" or "away"
            actual_score_home: Final home score
            actual_score_away: Final away score
        
        Returns:
            List of created PredictionOutcome records
        """
        # Find unresolved predictions for this game
        result = await self.db.execute(
            select(ModelPrediction)
            .where(ModelPrediction.game_id == uuid.UUID(game_id))
            .where(ModelPrediction.is_resolved == "false")
        )
        predictions = result.scalars().all()
        
        if not predictions:
            logger.debug(f"[PredictionTracker] No unresolved predictions for game {game_id}")
            return []
        
        outcomes = []
        
        for prediction in predictions:
            # Determine if prediction was correct
            was_correct = self._check_prediction_correct(
                prediction, actual_winner_side, actual_score_home, actual_score_away
            )
            
            # Calculate error metrics
            actual_outcome = 1.0 if was_correct else 0.0
            error_magnitude = abs(prediction.predicted_prob - actual_outcome)
            signed_error = prediction.predicted_prob - actual_outcome
            
            # Create outcome record
            outcome = PredictionOutcome(
                prediction_id=prediction.id,
                was_correct=was_correct,
                error_magnitude=error_magnitude,
                signed_error=signed_error,
                actual_result=actual_winner_side,
                actual_score_home=actual_score_home,
                actual_score_away=actual_score_away,
            )
            
            self.db.add(outcome)
            
            # Mark prediction as resolved
            prediction.is_resolved = "true"
            
            outcomes.append(outcome)
            
            logger.info(
                f"[PredictionTracker] Resolved: {prediction.market_type}/{prediction.team_side}, "
                f"correct={was_correct}, error={error_magnitude:.3f}"
            )
        
        await self.db.commit()
        
        return outcomes
    
    def _check_prediction_correct(
        self,
        prediction: ModelPrediction,
        actual_winner_side: str,
        home_score: Optional[float],
        away_score: Optional[float],
    ) -> bool:
        """Determine if a prediction was correct"""
        market_type = prediction.market_type.lower()
        team_side = prediction.team_side.lower()
        
        if market_type in ["moneyline", "h2h"]:
            # Moneyline: did the predicted team win?
            return team_side == actual_winner_side.lower()
        
        elif market_type in ["spread", "spreads"]:
            # Spread: did the predicted team cover?
            # Would need the spread line from prediction features
            # For now, approximate with winner
            return team_side == actual_winner_side.lower()
        
        elif market_type in ["total", "totals"]:
            # Total: over or under?
            if home_score is not None and away_score is not None:
                total = home_score + away_score
                # Would need the total line from features
                # Assume 45 as average NFL total for now
                total_line = 45.0
                if prediction.feature_snapshot:
                    total_line = prediction.feature_snapshot.get("total_line", 45.0)
                
                if team_side == "over":
                    return total > total_line
                else:
                    return total < total_line
            return False
        
        return False
    
    async def get_accuracy_stats(
        self,
        sport: Optional[str] = None,
        market_type: Optional[str] = None,
        lookback_days: int = 30,
        model_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get accuracy statistics for predictions.
        
        Args:
            sport: Filter by sport
            market_type: Filter by market type
            lookback_days: How far back to look
            model_version: Filter by model version
        
        Returns:
            Dict with accuracy, Brier score, calibration stats
        """
        # Build query
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        
        query = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.created_at >= cutoff_date)
        )
        
        if sport:
            query = query.where(ModelPrediction.sport == sport.upper())
        if market_type:
            query = query.where(ModelPrediction.market_type == market_type.lower())
        if model_version:
            query = query.where(ModelPrediction.model_version == model_version)
        
        result = await self.db.execute(query)
        rows = result.all()
        
        if not rows:
            return {
                "total_predictions": 0,
                "correct_predictions": 0,
                "correct": 0,
                "accuracy": 0.0,
                "brier_score": 0.0,
                "calibration_error": 0.0,
                "avg_edge": 0.0,
                "positive_edge_accuracy": 0.0,
            }
        
        # Calculate metrics
        total = len(rows)
        correct = sum(1 for _, outcome in rows if outcome.was_correct)
        accuracy = correct / total
        
        # Brier score: mean squared error of probability predictions
        brier_score = sum(outcome.error_magnitude ** 2 for _, outcome in rows) / total
        
        # Calibration error: difference between predicted prob and actual outcomes
        calibration_error = abs(sum(outcome.signed_error for _, outcome in rows) / total)
        
        # Edge metrics
        edges = [(pred.edge, outcome.was_correct) for pred, outcome in rows if pred.edge is not None]
        avg_edge = sum(e[0] for e in edges) / len(edges) if edges else 0.0
        
        # Accuracy when we had positive edge
        positive_edge_bets = [e for e in edges if e[0] > 0]
        pos_edge_accuracy = (
            sum(1 for e in positive_edge_bets if e[1]) / len(positive_edge_bets)
            if positive_edge_bets else 0.0
        )
        
        return {
            "total_predictions": total,
            "correct_predictions": correct,
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "brier_score": round(brier_score, 4),
            "calibration_error": round(calibration_error, 4),
            "avg_edge": round(avg_edge, 4),
            "positive_edge_accuracy": round(pos_edge_accuracy, 4),
            "positive_edge_count": len(positive_edge_bets),
        }
    
    async def calculate_team_bias(
        self,
        team_name: str,
        sport: str,
        min_games: int = 10,
    ) -> Optional[Dict[str, float]]:
        """
        Calculate bias adjustment for a specific team.
        
        Positive bias = we consistently overrate this team
        Negative bias = we consistently underrate this team
        
        Args:
            team_name: Team name to calculate bias for
            sport: Sport code
            min_games: Minimum games for reliable calculation
        
        Returns:
            Dict with bias metrics or None if insufficient data
        """
        # Find predictions involving this team
        query = (
            select(ModelPrediction, PredictionOutcome)
            .join(PredictionOutcome, PredictionOutcome.prediction_id == ModelPrediction.id)
            .where(ModelPrediction.sport == sport.upper())
            .where(
                (ModelPrediction.home_team.ilike(f"%{team_name}%")) |
                (ModelPrediction.away_team.ilike(f"%{team_name}%"))
            )
            .order_by(ModelPrediction.created_at.desc())
            .limit(CALIBRATION_CONFIG["lookback_games"])
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        if len(rows) < min_games:
            return None
        
        # Calculate average signed error when predicting FOR this team
        errors_for = []
        errors_against = []
        
        for pred, outcome in rows:
            # Determine if prediction was for or against this team
            is_home = team_name.lower() in pred.home_team.lower()
            predicted_for_team = (
                (is_home and pred.team_side.lower() == "home") or
                (not is_home and pred.team_side.lower() == "away")
            )
            
            if predicted_for_team:
                errors_for.append(outcome.signed_error)
            else:
                errors_against.append(outcome.signed_error)
        
        # Calculate bias
        # Positive error = we predicted too high, team underperformed
        avg_error_for = sum(errors_for) / len(errors_for) if errors_for else 0.0
        avg_error_against = sum(errors_against) / len(errors_against) if errors_against else 0.0
        
        # Net bias (positive = we overrate this team)
        bias = avg_error_for
        
        return {
            "team_name": team_name,
            "sport": sport,
            "bias_adjustment": -bias,  # Negate to get correction
            "avg_signed_error": bias,
            "sample_size": len(rows),
            "accuracy_for": (
                sum(1 for p, o in rows if o.was_correct and 
                    ((team_name.lower() in p.home_team.lower() and p.team_side.lower() == "home") or
                     (team_name.lower() in p.away_team.lower() and p.team_side.lower() == "away")))
                / len(errors_for) if errors_for else 0.0
            ),
        }
    
    async def get_team_bias_adjustments(
        self,
        sport: str,
    ) -> Dict[str, float]:
        """
        Get all team bias adjustments for a sport.
        
        Returns cached values if fresh, otherwise recalculates.
        
        Args:
            sport: Sport code
        
        Returns:
            Dict mapping team_name -> bias_adjustment
        """
        # Check cache freshness
        cache_age = CALIBRATION_CONFIG["recalibration_frequency_days"]
        if self._cache_timestamp:
            age = datetime.now(timezone.utc) - self._cache_timestamp
            if age.days < cache_age:
                return {k: v for k, v in self._calibration_cache.items() if k.startswith(f"{sport}:")}
        
        # Fetch from database
        result = await self.db.execute(
            select(TeamCalibration)
            .where(TeamCalibration.sport == sport.upper())
        )
        calibrations = result.scalars().all()
        
        adjustments = {}
        for cal in calibrations:
            key = f"{sport}:{cal.team_name}"
            adjustments[cal.team_name] = cal.clamped_adjustment
            self._calibration_cache[key] = cal.clamped_adjustment
        
        self._cache_timestamp = datetime.now(timezone.utc)
        
        return adjustments
    
    async def update_team_calibrations(
        self,
        sport: str,
    ) -> int:
        """
        Recalculate and store team calibrations for a sport.
        
        Should be called periodically (e.g., weekly) by a background job.
        
        Args:
            sport: Sport code
        
        Returns:
            Number of teams updated
        """
        # Get all unique teams
        result = await self.db.execute(
            select(ModelPrediction.home_team, ModelPrediction.away_team)
            .where(ModelPrediction.sport == sport.upper())
            .where(ModelPrediction.is_resolved == "true")
            .distinct()
        )
        team_rows = result.all()
        
        teams = set()
        for row in team_rows:
            teams.add(row[0])
            teams.add(row[1])
        
        updated = 0
        
        for team_name in teams:
            bias_data = await self.calculate_team_bias(
                team_name, 
                sport,
                min_games=CALIBRATION_CONFIG["min_games_for_adjustment"]
            )
            
            if not bias_data:
                continue
            
            # Upsert calibration record
            result = await self.db.execute(
                select(TeamCalibration)
                .where(TeamCalibration.team_name == team_name)
                .where(TeamCalibration.sport == sport.upper())
            )
            calibration = result.scalar_one_or_none()
            
            if calibration:
                calibration.bias_adjustment = bias_data["bias_adjustment"]
                calibration.avg_signed_error = bias_data["avg_signed_error"]
                calibration.sample_size = bias_data["sample_size"]
                calibration.accuracy = bias_data.get("accuracy_for")
            else:
                calibration = TeamCalibration(
                    team_name=team_name,
                    sport=sport.upper(),
                    bias_adjustment=bias_data["bias_adjustment"],
                    avg_signed_error=bias_data["avg_signed_error"],
                    sample_size=bias_data["sample_size"],
                    accuracy=bias_data.get("accuracy_for"),
                )
                self.db.add(calibration)
            
            updated += 1
        
        await self.db.commit()
        
        # Clear cache
        self._cache_timestamp = None
        self._calibration_cache = {}
        
        logger.info(f"[PredictionTracker] Updated calibrations for {updated} teams in {sport}")
        
        return updated
    
    def get_cached_bias(self, team_name: str, sport: str) -> float:
        """Get cached bias adjustment for a team (fast, for real-time use)"""
        key = f"{sport.upper()}:{team_name}"
        return self._calibration_cache.get(key, 0.0)


async def get_prediction_tracker(db: AsyncSession) -> PredictionTrackerService:
    """Factory function for prediction tracker"""
    return PredictionTrackerService(db)

