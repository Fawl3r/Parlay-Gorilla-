"""Service for tracking outcomes of user-saved parlays (`saved_parlays`).

This service grades saved parlays (custom + AI-saved) against `game_results`.
It is designed to be safe to call either from a background job or on-demand
from API routes.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.game import Game
from app.models.market import Market
from app.models.saved_parlay import SavedParlay, SavedParlayType
from app.models.saved_parlay_results import SavedParlayResult
from app.services.parlay_grading import (
    AiLegInputParser,
    CustomLegInputParser,
    GameResultLookupService,
    ParlayLegGrader,
    ParlayLegStatus,
)
from app.services.parlay_grading.parlay_outcome_calculator import ParlayOutcomeCalculator


class SavedParlayTrackerService:
    """Tracks and resolves outcomes for `SavedParlay` rows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._grader = ParlayLegGrader()
        self._ai_parser = AiLegInputParser()
        self._custom_parser = CustomLegInputParser()
        self._outcomes = ParlayOutcomeCalculator()

    async def auto_resolve_saved_parlays(self, *, limit: int = 100) -> int:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=4)

        res = await self.db.execute(
            select(SavedParlay)
            .where(SavedParlay.created_at.isnot(None))
            .where(SavedParlay.created_at < cutoff)
            .order_by(SavedParlay.created_at.desc())
            .limit(int(limit))
        )
        saved = list(res.scalars().all())
        if not saved:
            return 0

        saved_ids = [s.id for s in saved if getattr(s, "id", None)]
        existing_by_saved: Dict[str, SavedParlayResult] = {}
        if saved_ids:
            res = await self.db.execute(
                select(SavedParlayResult).where(SavedParlayResult.saved_parlay_id.in_(saved_ids))
            )
            existing_by_saved = {str(r.saved_parlay_id): r for r in res.scalars().all()}

        lookup = GameResultLookupService(self.db)

        resolved_count = 0
        for sp in saved:
            sp_id = str(sp.id)
            existing = existing_by_saved.get(sp_id)
            if existing and self._is_final(existing):
                continue

            updated = await self._resolve_single(saved_parlay=sp, existing=existing, lookup=lookup)
            if updated:
                resolved_count += 1

        return resolved_count

    async def resolve_saved_parlay_if_needed(self, *, saved_parlay: SavedParlay) -> Optional[SavedParlayResult]:
        """
        Resolve one saved parlay on-demand (best-effort).

        Returns the SavedParlayResult after attempting to resolve.
        """
        res = await self.db.execute(
            select(SavedParlayResult).where(SavedParlayResult.saved_parlay_id == saved_parlay.id).limit(1)
        )
        existing = res.scalar_one_or_none()
        if existing and self._is_final(existing):
            return existing

        lookup = GameResultLookupService(self.db)
        await self._resolve_single(saved_parlay=saved_parlay, existing=existing, lookup=lookup)

        res = await self.db.execute(
            select(SavedParlayResult).where(SavedParlayResult.saved_parlay_id == saved_parlay.id).limit(1)
        )
        return res.scalar_one_or_none()

    async def _resolve_single(
        self,
        *,
        saved_parlay: SavedParlay,
        existing: Optional[SavedParlayResult],
        lookup: GameResultLookupService,
    ) -> bool:
        legs = list(getattr(saved_parlay, "legs", []) or [])
        if not legs:
            return False

        parlay_type = str(getattr(saved_parlay, "parlay_type", "") or "")
        if parlay_type == SavedParlayType.ai_generated.value:
            leg_results = await self._grade_ai_saved_legs(legs=legs, lookup=lookup)
        else:
            leg_results = await self._grade_custom_saved_legs(legs=legs, lookup=lookup)

        outcome = self._outcomes.compute(leg_results=leg_results, predicted_probability=None)

        record = existing
        if record is None:
            record = SavedParlayResult(
                saved_parlay_id=saved_parlay.id,
                user_id=saved_parlay.user_id,
                parlay_type=parlay_type,
                num_legs=len(legs),
                hit=outcome.hit,
                legs_hit=outcome.legs_hit,
                legs_missed=outcome.legs_missed,
                leg_results=leg_results,
                resolved_at=outcome.resolved_at,
            )
            self.db.add(record)
        else:
            record.parlay_type = parlay_type
            record.num_legs = len(legs)
            record.hit = outcome.hit
            record.legs_hit = outcome.legs_hit
            record.legs_missed = outcome.legs_missed
            record.leg_results = leg_results
            record.resolved_at = outcome.resolved_at

        try:
            await self.db.commit()
            await self.db.refresh(record)
        except Exception:
            await self.db.rollback()
            return False

        return any(lr.get("status") != ParlayLegStatus.pending.value for lr in leg_results)

    async def _grade_ai_saved_legs(self, *, legs: List[Dict[str, Any]], lookup: GameResultLookupService) -> List[Dict[str, Any]]:
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

        results: List[Dict[str, Any]] = []
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
                graded = {"status": ParlayLegStatus.pending.value, "hit": None, "notes": parsed_or_err.error or "parse_failed"}
            else:
                graded = self._grader.grade(parsed_leg=parsed_or_err.parsed, game_result=game_result).as_dict()

            results.append(
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

        return results

    async def _grade_custom_saved_legs(
        self,
        *,
        legs: List[Dict[str, Any]],
        lookup: GameResultLookupService,
    ) -> List[Dict[str, Any]]:
        game_ids: List[uuid.UUID] = []
        for leg in legs:
            try:
                game_ids.append(uuid.UUID(str(leg.get("game_id"))))
            except Exception:
                continue

        games_by_id: Dict[str, Game] = {}
        if game_ids:
            res = await self.db.execute(select(Game).where(Game.id.in_(game_ids)))
            games_by_id = {str(g.id): g for g in res.scalars().all()}

        results: List[Dict[str, Any]] = []
        for leg in legs:
            game_id = str(leg.get("game_id") or "")
            game = games_by_id.get(game_id)

            game_result = None
            if game:
                game_result = await lookup.find_best(
                    sport=str(getattr(game, "sport", "") or ""),
                    home_team=str(getattr(game, "home_team", "") or ""),
                    away_team=str(getattr(game, "away_team", "") or ""),
                    start_time=getattr(game, "start_time", None),
                )

            parsed_or_err = self._custom_parser.parse(
                leg,
                home_team=str(getattr(game, "home_team", "") or ""),
                away_team=str(getattr(game, "away_team", "") or ""),
            )

            if parsed_or_err.parsed is None:
                graded = {"status": ParlayLegStatus.pending.value, "hit": None, "notes": parsed_or_err.error or "parse_failed"}
            else:
                graded = self._grader.grade(parsed_leg=parsed_or_err.parsed, game_result=game_result).as_dict()

            results.append(
                {
                    "game_id": game_id,
                    "market_id": leg.get("market_id"),
                    "market_type": leg.get("market_type"),
                    "pick": leg.get("pick"),
                    "point": leg.get("point"),
                    "odds": leg.get("odds"),
                    "home_team": getattr(game, "home_team", None),
                    "away_team": getattr(game, "away_team", None),
                    "sport": getattr(game, "sport", None),
                    **graded,
                }
            )

        return results

    @staticmethod
    def _is_final(result: SavedParlayResult) -> bool:
        leg_results = getattr(result, "leg_results", None)
        if not isinstance(leg_results, list) or not leg_results:
            return False
        for lr in leg_results:
            status = str((lr or {}).get("status") or "").lower().strip()
            if status not in {ParlayLegStatus.hit.value, ParlayLegStatus.missed.value, ParlayLegStatus.push.value}:
                return False
        return True


