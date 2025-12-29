"""Service for tracking parlay results and performance.

Notes:
- We store AI-generated parlays in `parlays` (generation history).
- Outcomes are stored in `parlay_results` with per-leg status in `leg_results`.
- A background job periodically attempts to resolve outcomes from `game_results`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.market import Market
from app.models.parlay import Parlay
from app.models.parlay_results import ParlayResult
from app.services.parlay_grading import AiLegInputParser, GameResultLookupService, ParlayLegGrader, ParlayLegStatus
from app.services.parlay_grading.parlay_outcome_calculator import ParlayOutcomeCalculator


class ParlayTrackerService:
    """Service for tracking parlay outcomes and calculating performance metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._grader = ParlayLegGrader()
        self._ai_parser = AiLegInputParser()
        self._outcomes = ParlayOutcomeCalculator()
    
    async def resolve_parlay_result(
        self,
        parlay_id: str,
        leg_results: List[Dict]
    ) -> ParlayResult:
        """
        Resolve a parlay result based on actual game outcomes
        
        Args:
            parlay_id: ID of the parlay to resolve
            leg_results: List of dicts with leg outcomes
                Format: [{"leg_id": "...", "hit": True/False, ...}]
        
        Returns:
            Updated ParlayResult
        """
        # Get parlay
        result = await self.db.execute(
            select(Parlay).where(Parlay.id == parlay_id)
        )
        parlay = result.scalar_one_or_none()
        
        if not parlay:
            raise ValueError(f"Parlay {parlay_id} not found")
        
        # Get or create parlay result
        result = await self.db.execute(
            select(ParlayResult).where(ParlayResult.parlay_id == parlay_id)
        )
        parlay_result = result.scalar_one_or_none()
        
        if not parlay_result:
            parlay_result = ParlayResult(
                parlay_id=parlay_id,
                num_legs=parlay.num_legs,
                risk_profile=parlay.risk_profile,
                predicted_probability=float(parlay.parlay_hit_prob),
                predicted_confidence=0.0,  # Will calculate from legs
            )
            self.db.add(parlay_result)
        
        computed = self._compute_parlay_outcome(
            leg_results=leg_results,
            predicted_probability=float(parlay_result.predicted_probability or 0.0),
        )
        
        # Update parlay result
        parlay_result.hit = computed["hit"]
        parlay_result.legs_hit = computed["legs_hit"]
        parlay_result.legs_missed = computed["legs_missed"]
        parlay_result.leg_results = leg_results
        parlay_result.resolved_at = computed["resolved_at"]
        
        parlay_result.actual_probability = computed["actual_probability"]
        parlay_result.calibration_error = computed["calibration_error"]
        
        await self.db.commit()
        await self.db.refresh(parlay_result)
        
        return parlay_result
    
    async def get_parlay_performance_stats(
        self,
        risk_profile: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        Get performance statistics for resolved parlays
        
        Args:
            risk_profile: Filter by risk profile (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            user_id: Filter by user ID (optional, but required for authenticated endpoints)
        
        Returns:
            Dictionary with performance metrics
        """
        # Join ParlayResult with Parlay to filter by user_id
        query = (
            select(ParlayResult)
            .join(Parlay, ParlayResult.parlay_id == Parlay.id)
            .where(ParlayResult.hit.isnot(None))
        )
        
        if user_id:
            query = query.where(Parlay.user_id == user_id)
        if risk_profile:
            query = query.where(ParlayResult.risk_profile == risk_profile)
        if start_date:
            query = query.where(ParlayResult.created_at >= start_date)
        if end_date:
            query = query.where(ParlayResult.created_at <= end_date)
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return {
                "total_parlays": 0,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "avg_predicted_prob": 0.0,
                "avg_actual_prob": 0.0,
                "avg_calibration_error": 0.0,
            }
        
        total = len(results)
        hits = sum(1 for r in results if r.hit)
        misses = total - hits
        
        avg_predicted = sum(r.predicted_probability for r in results) / total
        avg_actual = sum(r.actual_probability or 0.0 for r in results) / total
        avg_calibration = sum(r.calibration_error or 0.0 for r in results) / total
        
        return {
            "total_parlays": total,
            "hits": hits,
            "misses": misses,
            "hit_rate": hits / total if total > 0 else 0.0,
            "avg_predicted_prob": avg_predicted,
            "avg_actual_prob": avg_actual,
            "avg_calibration_error": avg_calibration,
        }
    
    async def get_user_parlay_history(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Parlay]:
        """Get a user's parlay history"""
        result = await self.db.execute(
            select(Parlay)
            .where(Parlay.user_id == user_id)
            .order_by(Parlay.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def resolve_parlay_if_needed(self, *, parlay: Parlay) -> Optional[ParlayResult]:
        """
        Best-effort on-demand resolution for a single parlay.

        Useful for UI pages so users don't need to wait for the background job cadence.
        """
        res = await self.db.execute(
            select(ParlayResult).where(ParlayResult.parlay_id == parlay.id).limit(1)
        )
        existing = res.scalar_one_or_none()
        if existing and self._is_final_result(existing):
            return existing

        lookup = GameResultLookupService(self.db)
        await self._resolve_single_parlay(parlay=parlay, existing=existing, lookup=lookup)

        res = await self.db.execute(
            select(ParlayResult).where(ParlayResult.parlay_id == parlay.id).limit(1)
        )
        return res.scalar_one_or_none()
    
    async def auto_resolve_parlays(self):
        """
        Automatically resolve parlays based on game results
        This should be called periodically via background job
        """
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=4)

        result = await self.db.execute(
            select(Parlay)
            .where(Parlay.created_at.isnot(None))
            .where(Parlay.created_at < cutoff)
            .order_by(Parlay.created_at.desc())
            .limit(100)
        )
        parlays = list(result.scalars().all())
        if not parlays:
            return 0

        parlay_ids = [p.id for p in parlays if getattr(p, "id", None)]
        existing_results: Dict[str, ParlayResult] = {}
        if parlay_ids:
            res = await self.db.execute(select(ParlayResult).where(ParlayResult.parlay_id.in_(parlay_ids)))
            existing_results = {str(r.parlay_id): r for r in res.scalars().all()}

        lookup = GameResultLookupService(self.db)

        resolved_count = 0
        for parlay in parlays:
            parlay_id = str(parlay.id)
            parlay_result = existing_results.get(parlay_id)
            if parlay_result and self._is_final_result(parlay_result):
                continue

            updated = await self._resolve_single_parlay(parlay=parlay, existing=parlay_result, lookup=lookup)
            if updated:
                resolved_count += 1

        return resolved_count

    async def _resolve_single_parlay(
        self,
        *,
        parlay: Parlay,
        existing: Optional[ParlayResult],
        lookup: GameResultLookupService,
    ) -> bool:
        legs = list(getattr(parlay, "legs", []) or [])
        if not legs:
            return False

        # Batch load markets (to obtain the canonical Game rows for lookup).
        market_ids: List[uuid.UUID] = []
        for leg in legs:
            try:
                market_ids.append(uuid.UUID(str(leg.get("market_id"))))
            except Exception:
                continue

        markets_by_id: Dict[str, Market] = {}
        if market_ids:
            res = await self.db.execute(
                select(Market).where(Market.id.in_(market_ids)).options(selectinload(Market.game))
            )
            markets_by_id = {str(m.id): m for m in res.scalars().all()}

        leg_results: List[Dict[str, Any]] = []
        for leg in legs:
            market_id = str(leg.get("market_id") or "")
            market = markets_by_id.get(market_id)
            game = getattr(market, "game", None) if market else None

            game_result = None
            if game:
                game_result = await lookup.find_best(
                    sport=str(getattr(game, "sport", "") or ""),
                    home_team=str(getattr(game, "home_team", "") or ""),
                    away_team=str(getattr(game, "away_team", "") or ""),
                    start_time=getattr(game, "start_time", None),
                )

            parsed_or_err = self._ai_parser.parse(
                leg,
                home_team=str(getattr(game, "home_team", leg.get("home_team") or "") or ""),
                away_team=str(getattr(game, "away_team", leg.get("away_team") or "") or ""),
            )

            if parsed_or_err.parsed is None:
                graded = {
                    "status": ParlayLegStatus.pending.value,
                    "hit": None,
                    "notes": parsed_or_err.error or "parse_failed",
                }
            else:
                graded = self._grader.grade(parsed_leg=parsed_or_err.parsed, game_result=game_result).as_dict()

            leg_results.append(
                {
                    "market_id": market_id,
                    "market_type": leg.get("market_type"),
                    "outcome": leg.get("outcome"),
                    "game": leg.get("game"),
                    "home_team": getattr(game, "home_team", leg.get("home_team")),
                    "away_team": getattr(game, "away_team", leg.get("away_team")),
                    "sport": getattr(game, "sport", leg.get("sport")),
                    "odds": leg.get("odds"),
                    "probability": leg.get("probability"),
                    "confidence": leg.get("confidence"),
                    "game_id": str(getattr(game, "id", "")) if game else None,
                    **graded,
                }
            )

        # Upsert ParlayResult
        parlay_result = existing
        if parlay_result is None:
            parlay_result = ParlayResult(
                parlay_id=parlay.id,
                num_legs=int(getattr(parlay, "num_legs", len(legs)) or len(legs)),
                risk_profile=str(getattr(parlay, "risk_profile", "") or ""),
                predicted_probability=float(getattr(parlay, "parlay_hit_prob", 0.0) or 0.0),
                predicted_confidence=float(self._avg_confidence(legs)),
            )
            self.db.add(parlay_result)

        # Always refresh core metadata and leg results.
        parlay_result.num_legs = int(getattr(parlay, "num_legs", len(legs)) or len(legs))
        parlay_result.risk_profile = str(getattr(parlay, "risk_profile", "") or "")
        parlay_result.predicted_probability = float(getattr(parlay, "parlay_hit_prob", 0.0) or 0.0)
        parlay_result.predicted_confidence = float(self._avg_confidence(legs))
        parlay_result.leg_results = leg_results

        computed = self._compute_parlay_outcome(leg_results=leg_results, predicted_probability=parlay_result.predicted_probability)
        parlay_result.hit = computed["hit"]
        parlay_result.legs_hit = computed["legs_hit"]
        parlay_result.legs_missed = computed["legs_missed"]
        parlay_result.actual_probability = computed["actual_probability"]
        parlay_result.calibration_error = computed["calibration_error"]
        parlay_result.resolved_at = computed["resolved_at"]

        try:
            await self.db.commit()
            await self.db.refresh(parlay_result)
        except Exception:
            await self.db.rollback()
            return False

        # Count as "resolved attempt" only when we produced any non-pending status.
        return any(lr.get("status") != ParlayLegStatus.pending.value for lr in leg_results)

    @staticmethod
    def _avg_confidence(legs: List[Dict[str, Any]]) -> float:
        scores: List[float] = []
        for leg in legs:
            try:
                scores.append(float(leg.get("confidence", 0.0) or 0.0))
            except Exception:
                continue
        return sum(scores) / len(scores) if scores else 0.0

    @staticmethod
    def _is_final_result(result: ParlayResult) -> bool:
        """
        A result is considered final if we have per-leg status for all legs and none are pending.
        """
        leg_results = getattr(result, "leg_results", None)
        if not isinstance(leg_results, list) or not leg_results:
            return False
        for lr in leg_results:
            status = str((lr or {}).get("status") or "").lower().strip()
            if status != ParlayLegStatus.hit.value and status != ParlayLegStatus.missed.value and status != ParlayLegStatus.push.value:
                return False
        return True

    def _compute_parlay_outcome(
        self,
        *,
        leg_results: List[Dict[str, Any]],
        predicted_probability: Optional[float] = None,
    ) -> Dict[str, Any]:
        outcome = self._outcomes.compute(leg_results=leg_results, predicted_probability=predicted_probability)
        return {
            "hit": outcome.hit,
            "legs_hit": outcome.legs_hit,
            "legs_missed": outcome.legs_missed,
            "resolved_at": outcome.resolved_at,
            "actual_probability": outcome.actual_probability,
            "calibration_error": outcome.calibration_error,
            "status": outcome.status,
        }

