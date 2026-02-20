"""
Prediction Tracker Service

Tracks model predictions vs actual outcomes for:
- Accuracy metrics
- Calibration analysis
- Per-team bias learning
- Model version comparison

This is the core of the "learning from misses" system.
"""

from typing import Dict, Optional, List, Any, Tuple

# Type alias to avoid complex bracket nesting in signature
StrategyContributionsList = List[Tuple[str, float, float]]
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, case
from sqlalchemy.orm import selectinload
import hashlib
import logging
import uuid

from app.models.model_prediction import ModelPrediction
from app.models.prediction_outcome import PredictionOutcome, TeamCalibration
from app.models.strategy_contribution import StrategyContribution
from app.models.game import Game
from app.models.game_results import GameResult
from app.core.model_config import MODEL_VERSION, CALIBRATION_CONFIG

logger = logging.getLogger(__name__)

# Minimum resolved count before reporting real metrics
MIN_RESOLVED_FOR_METRICS = 30
# Ignore games older than this for resolution
RESOLUTION_MAX_AGE_DAYS = 7


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
        strategy_components: Optional[Dict[str, float]] = None,
        strategy_contributions: Optional[StrategyContributionsList] = None,
        market_regime: Optional[str] = None,
        correlation_id: Optional[str] = None,
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
            Created or existing ModelPrediction record (idempotent by idempotency_key).
        """
        # Idempotency key: same key => return existing row (prevents double logging on retries)
        event_id = str(game_id) if game_id else ""
        sel = (team_side or "").lower()
        mv = model_version or MODEL_VERSION
        if game_time is not None:
            try:
                day_bucket = game_time.date().isoformat() if hasattr(game_time, "date") else str(game_time)[:10]
            except Exception:
                day_bucket = datetime.now(timezone.utc).date().isoformat()
        else:
            day_bucket = datetime.now(timezone.utc).date().isoformat()
        raw = f"{sport.upper()}|{event_id}|{(market_type or '').lower()}|{sel}|{mv}|{day_bucket}"
        idempotency_key = hashlib.sha256(raw.encode()).hexdigest()

        existing = await self.db.execute(
            select(ModelPrediction).where(ModelPrediction.idempotency_key == idempotency_key).limit(1)
        )
        existing_row = existing.scalar_one_or_none()
        if existing_row is not None:
            await self.db.refresh(existing_row)
            logger.debug(
                "[PredictionTracker] Idempotent skip: existing prediction for key prefix %s",
                idempotency_key[:12],
            )
            return existing_row

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
            model_version=mv,
            calculation_method=calculation_method,
            confidence_score=confidence_score,
            feature_snapshot=features,
            is_resolved="false",
            strategy_components=strategy_components,
            market_regime=market_regime,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
        )

        self.db.add(prediction)
        await self.db.commit()
        await self.db.refresh(prediction)

        if strategy_contributions and prediction.id:
            for strategy_name, weight, contribution_value in strategy_contributions:
                self.db.add(StrategyContribution(
                    prediction_id=prediction.id,
                    strategy_name=strategy_name,
                    weight=weight,
                    contribution_value=contribution_value,
                ))
            await self.db.commit()
        
        logger.info(
            "prediction_recorded",
            extra={
                "prediction_id": str(prediction.id),
                "event_id": str(game_id) if game_id else None,
                "sport": sport,
                "market_type": market_type,
                "correlation_id": correlation_id,
            },
        )
        return prediction

    async def record_prediction(self, prediction_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        """
        Record a single prediction with validation and duplicate protection.
        Call immediately after AI prediction generation.
        """
        try:
            prob = prediction_data.get("predicted_probability") or prediction_data.get("predicted_prob")
            if prob is None:
                logger.warning("[PredictionTracker] record_prediction skipped: missing probability")
                return None
            prob = float(prob)
            if not (0 <= prob <= 1):
                logger.warning(
                    "[PredictionTracker] record_prediction skipped: probability out of range",
                    extra={"prob": prob},
                )
                return None
            game_id = prediction_data.get("game_id") or prediction_data.get("event_id")
            sport = (prediction_data.get("sport") or "").upper()
            market_type = (prediction_data.get("market_type") or "moneyline").lower()
            team_side = (prediction_data.get("team_side") or prediction_data.get("selection") or "").lower()
            if not game_id:
                logger.warning("[PredictionTracker] record_prediction skipped: missing event_id/game_id")
                return None
            if not team_side or not sport:
                logger.warning("[PredictionTracker] record_prediction skipped: missing sport or team_side")
                return None
            # Duplicate prevention: save_prediction uses idempotency_key (sha256 of sport|event_id|market|side|version|day)
            implied_prob = prediction_data.get("implied_prob") or prediction_data.get("implied_prob_market")
            if implied_prob is not None:
                implied_prob = float(implied_prob)
                if not (0 < implied_prob <= 1):
                    implied_prob = None
            odds_decimal = prediction_data.get("odds_decimal")
            if implied_prob is None and odds_decimal is not None and float(odds_decimal) > 0:
                implied_prob = 1.0 / float(odds_decimal)
                if not (0 < implied_prob <= 1):
                    implied_prob = None
            confidence_score = prediction_data.get("confidence_score")
            if confidence_score is None and prob is not None:
                confidence_score = prob * 100.0 if prob <= 1 else prob
            pred = await self.save_prediction(
                game_id=game_id,
                sport=sport,
                home_team=prediction_data.get("home_team", ""),
                away_team=prediction_data.get("away_team", ""),
                market_type=market_type,
                team_side=team_side,
                predicted_prob=prob,
                implied_prob=implied_prob,
                model_version=prediction_data.get("model_version"),
                calculation_method=prediction_data.get("calculation_method"),
                confidence_score=confidence_score,
                features=prediction_data.get("features"),
                game_time=prediction_data.get("game_time"),
                strategy_components=prediction_data.get("strategy_components"),
                strategy_contributions=prediction_data.get("strategy_contributions"),
                market_regime=prediction_data.get("market_regime"),
                correlation_id=prediction_data.get("correlation_id"),
            )
            if pred and (prediction_data.get("expected_value") is not None or prediction_data.get("implied_odds") is not None):
                pred.expected_value = prediction_data.get("expected_value")
                pred.implied_odds = prediction_data.get("implied_odds")
                await self.db.commit()
                await self.db.refresh(pred)
            return pred
        except Exception as e:
            logger.exception("[PredictionTracker] record_prediction failed: %s", e)
            try:
                await self.db.rollback()
            except Exception:
                pass
            return None

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
            
            # Mark prediction as resolved on the prediction row
            now_utc = datetime.now(timezone.utc)
            prediction.is_resolved = "true"
            prediction.resolved_at = now_utc
            prediction.result = was_correct
            if actual_score_home is not None and actual_score_away is not None and actual_score_home == actual_score_away:
                prediction.result_enum = "PUSH"
            else:
                prediction.result_enum = "WIN" if was_correct else "LOSS"

            outcomes.append(outcome)
            
            logger.info(
                "prediction_resolved",
                extra={
                    "prediction_id": str(prediction.id),
                    "event_id": str(game_id),
                    "result_enum": prediction.result_enum,
                    "was_correct": was_correct,
                },
            )
        
        await self.db.commit()

        correlation_id = predictions[0].correlation_id if predictions else None
        try:
            from app.services.institutional.rl_weight_optimizer import RLWeightOptimizer
            rl = RLWeightOptimizer(self.db)
            await rl.run_update_if_due(correlation_id=correlation_id)
        except Exception as e:
            logger.warning("[PredictionTracker] RL update after resolve failed (non-fatal): %s", e)
        try:
            from app.services.institutional.model_health_service import ModelHealthService
            health_svc = ModelHealthService(self.db)
            await health_svc.evaluate_and_update()
        except Exception as e:
            logger.warning("[PredictionTracker] Model health update after resolve failed (non-fatal): %s", e)

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
        
        _total_q = select(func.count(ModelPrediction.id)).where(ModelPrediction.created_at >= cutoff_date)
        if sport:
            _total_q = _total_q.where(ModelPrediction.sport == sport.upper())
        if market_type:
            _total_q = _total_q.where(ModelPrediction.market_type == market_type.lower())
        if model_version:
            _total_q = _total_q.where(ModelPrediction.model_version == model_version)
        total_pred_result = await self.db.execute(_total_q)
        total_predictions_all = total_pred_result.scalar() or 0

        result = await self.db.execute(query)
        rows = result.all()
        
        if not rows:
            return {
                "total_predictions": total_predictions_all,
                "resolved_predictions": 0,
                "correct_predictions": 0,
                "correct": 0,
                "accuracy": None,
                "brier_score": None,
                "calibration_error": None,
                "avg_edge": None,
                "avg_ev": None,
                "positive_edge_accuracy": None,
                "ev_accuracy": None,
                "positive_edge_count": 0,
                "status": "Insufficient Data",
            }

        # Metrics computed ONLY from resolved predictions (rows are joined with PredictionOutcome)
        total = len(rows)
        correct = sum(1 for _, outcome in rows if outcome.was_correct)
        if total < MIN_RESOLVED_FOR_METRICS:
            return {
                "total_predictions": total_predictions_all,
                "resolved_predictions": total,
                "correct_predictions": correct,
                "correct": correct,
                "accuracy": None,
                "brier_score": None,
                "calibration_error": None,
                "avg_edge": None,
                "avg_ev": None,
                "positive_edge_accuracy": None,
                "ev_accuracy": None,
                "positive_edge_count": 0,
                "status": "Insufficient Data",
            }

        # Exclude PUSH from Brier: use y=1 for WIN, y=0 for LOSS; PUSH excluded (or y=0.5 per spec - we exclude for simplicity)
        non_push = [(pred, outcome) for pred, outcome in rows if outcome.was_correct is not None]
        brier_denom = len(non_push) if non_push else 0
        brier_score = (
            sum(outcome.error_magnitude ** 2 for _, outcome in non_push) / brier_denom
            if brier_denom else None
        )
        accuracy = correct / total
        calibration_error = abs(sum(o.signed_error for _, o in rows) / total)

        edges = [(pred.edge, outcome.was_correct) for pred, outcome in rows if pred.edge is not None]
        avg_edge = sum(e[0] for e in edges) / len(edges) if edges else None
        evs = [pred.expected_value for pred, _ in rows if pred.expected_value is not None]
        avg_ev = sum(evs) / len(evs) if evs else None

        positive_edge_bets = [e for e in edges if e[0] > 0]
        pos_edge_accuracy = (
            sum(1 for e in positive_edge_bets if e[1]) / len(positive_edge_bets)
            if positive_edge_bets else None
        )
        ev_accuracy = pos_edge_accuracy

        return {
            "total_predictions": total_predictions_all,
            "resolved_predictions": total,
            "correct_predictions": correct,
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "brier_score": round(brier_score, 4) if brier_score is not None else None,
            "calibration_error": round(calibration_error, 4),
            "avg_edge": round(avg_edge, 4) if avg_edge is not None else None,
            "avg_ev": round(avg_ev, 4) if avg_ev is not None else None,
            "positive_edge_accuracy": round(pos_edge_accuracy, 4) if pos_edge_accuracy is not None else None,
            "ev_accuracy": ev_accuracy,
            "positive_edge_count": len(positive_edge_bets),
            "status": "Ok",
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

