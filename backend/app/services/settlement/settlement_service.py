"""Settlement service for parlay legs and parlays."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.parlay import Parlay
from app.models.saved_parlay import SavedParlay
from app.models.parlay_leg import ParlayLeg
from app.services.settlement.leg_result_calculator import LegResultCalculator
from app.services.settlement.parlay_status_calculator import ParlayStatusCalculator
from app.services.settlement.feed_event_generator import FeedEventGenerator

logger = logging.getLogger(__name__)

# Settlement metrics (in-memory, could be moved to Redis for multi-instance)
_settlement_metrics = {
    "legs_settled_total": 0,
    "parlays_settled_total": 0,
    "parlays_won_total": 0,
    "parlays_lost_total": 0,
    "errors_total": 0,
    "last_settlement_time": None,
    "last_settlement_duration_ms": None,
}


def get_settlement_metrics() -> Dict:
    """Get current settlement metrics."""
    return _settlement_metrics.copy()


def reset_settlement_metrics():
    """Reset settlement metrics (for testing)."""
    global _settlement_metrics
    _settlement_metrics = {
        "legs_settled_total": 0,
        "parlays_settled_total": 0,
        "parlays_won_total": 0,
        "parlays_lost_total": 0,
        "errors_total": 0,
        "last_settlement_time": None,
        "last_settlement_duration_ms": None,
    }


class SettlementStats:
    """Settlement statistics."""
    def __init__(self):
        self.legs_settled = 0
        self.parlays_settled = 0
        self.parlays_won = 0
        self.parlays_lost = 0


class SettlementService:
    """Service for settling parlay legs and updating parlay status."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self._leg_calculator = LegResultCalculator()
        self._parlay_calculator = ParlayStatusCalculator()
        self._feed_generator = FeedEventGenerator(db)
    
    async def settle_parlay_legs_for_game(self, game_id: UUID) -> int:
        """Settle all parlay legs for a game that just went FINAL.
        
        Args:
            game_id: Game ID that went FINAL
            
        Returns:
            Number of legs settled (0 on error or if game not FINAL)
        """
        if not game_id:
            logger.warning("settle_parlay_legs_for_game: Missing game_id")
            return 0
        
        try:
            # Get the game
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            
            if not game:
                logger.warning(f"settle_parlay_legs_for_game: Game {game_id} not found")
                return 0
            
            if game.status != "FINAL":
                logger.debug(f"settle_parlay_legs_for_game: Game {game_id} status is {game.status}, not FINAL")
                return 0
            
            # Validate game has scores
            if game.home_score is None or game.away_score is None:
                logger.warning(
                    f"settle_parlay_legs_for_game: Game {game_id} is FINAL but missing scores "
                    f"(home_score={game.home_score}, away_score={game.away_score})"
                )
                # Still process legs - they'll be VOIDed by calculator
            
            # Find all pending/live legs for this game
            result = await self.db.execute(
                select(ParlayLeg).where(
                    and_(
                        ParlayLeg.game_id == game_id,
                        ParlayLeg.status.in_(["PENDING", "LIVE"]),
                    )
                )
            )
            legs = result.scalars().all()
            
            if not legs:
                logger.debug(f"settle_parlay_legs_for_game: No pending/live legs found for game {game_id}")
                return 0
            
            logger.info(f"settle_parlay_legs_for_game: Processing {len(legs)} legs for game {game_id}")
            settled_count = 0
            error_count = 0
            
            for leg in legs:
                try:
                    # Validate leg
                    if not leg.market_type:
                        logger.warning(f"settle_parlay_legs_for_game: Leg {leg.id} missing market_type")
                        leg.status = "VOID"
                        leg.settled_at = datetime.utcnow()
                        leg.result_reason = "Missing market_type"
                        await self.db.flush()
                        settled_count += 1
                        continue
                    
                    # Calculate leg result
                    if leg.market_type == "h2h":
                        result_status = self._leg_calculator.calculate_moneyline_result(leg, game)
                    elif leg.market_type == "spreads":
                        result_status = self._leg_calculator.calculate_spread_result(leg, game)
                    elif leg.market_type == "totals":
                        result_status = self._leg_calculator.calculate_total_result(leg, game)
                    else:
                        logger.warning(
                            f"settle_parlay_legs_for_game: Unknown market_type '{leg.market_type}' "
                            f"for leg {leg.id}, VOIDing"
                        )
                        result_status = "VOID"
                    
                    # Update leg
                    leg.status = result_status
                    leg.settled_at = datetime.utcnow()
                    home_score_str = str(game.home_score) if game.home_score is not None else "None"
                    away_score_str = str(game.away_score) if game.away_score is not None else "None"
                    leg.result_reason = f"Game {game.away_team} @ {game.home_team} final: {away_score_str}-{home_score_str}"
                    
                    await self.db.flush()
                    settled_count += 1
                    
                    # Create feed event for leg result (with error handling)
                    try:
                        if result_status == "WON":
                            await self._feed_generator.create_leg_won_event(leg)
                        elif result_status == "LOST":
                            await self._feed_generator.create_leg_lost_event(leg)
                    except Exception as feed_error:
                        # Don't fail settlement if feed event creation fails
                        logger.error(
                            f"settle_parlay_legs_for_game: Error creating feed event for leg {leg.id}: {feed_error}",
                            exc_info=True
                        )
                    
                    # Update parlay status (with error handling)
                    try:
                        await self._update_parlay_status(leg)
                    except Exception as parlay_error:
                        # Log but don't fail - leg is already settled
                        logger.error(
                            f"settle_parlay_legs_for_game: Error updating parlay status for leg {leg.id}: {parlay_error}",
                            exc_info=True
                        )
                
                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"settle_parlay_legs_for_game: Error settling leg {leg.id} for game {game_id}: {e}",
                        exc_info=True
                    )
                    # Continue processing other legs
                    continue
            
            if error_count > 0:
                logger.warning(
                    f"settle_parlay_legs_for_game: Settled {settled_count} legs with {error_count} errors "
                    f"for game {game_id}"
                )
                _settlement_metrics["errors_total"] += error_count
            else:
                logger.info(f"settle_parlay_legs_for_game: Successfully settled {settled_count} legs for game {game_id}")
            
            # Update metrics
            _settlement_metrics["legs_settled_total"] += settled_count
            
            # Commit all changes
            try:
                await self.db.commit()
            except Exception as commit_error:
                logger.error(
                    f"settle_parlay_legs_for_game: Error committing settlement for game {game_id}: {commit_error}",
                    exc_info=True
                )
                await self.db.rollback()
                _settlement_metrics["errors_total"] += 1
                return 0
            
            return settled_count
        
        except Exception as e:
            logger.error(
                f"settle_parlay_legs_for_game: Fatal error settling legs for game {game_id}: {e}",
                exc_info=True
            )
            try:
                await self.db.rollback()
            except Exception:
                pass
            return 0
    
    async def settle_all_pending_parlays(self) -> SettlementStats:
        """Settle all parlays that have all legs settled.
        
        Returns:
            SettlementStats with counts
        """
        stats = SettlementStats()
        
        try:
            # Get all parlays with pending/live status
            result = await self.db.execute(
                select(Parlay).where(Parlay.status.in_(["PENDING", "LIVE"]))
            )
            parlays = result.scalars().all()
            
            if not parlays:
                logger.debug("settle_all_pending_parlays: No pending/live parlays found")
                return stats
            
            logger.info(f"settle_all_pending_parlays: Processing {len(parlays)} parlays")
            error_count = 0
            
            for parlay in parlays:
                try:
                    # Validate parlay
                    if not parlay.id:
                        logger.warning("settle_all_pending_parlays: Parlay missing id, skipping")
                        continue
                    
                    # Get all legs for this parlay
                    result = await self.db.execute(
                        select(ParlayLeg).where(ParlayLeg.parlay_id == parlay.id)
                    )
                    legs = result.scalars().all()
                    
                    if not legs:
                        logger.debug(f"settle_all_pending_parlays: Parlay {parlay.id} has no legs, skipping")
                        continue
                    
                    # Calculate new status
                    new_status = self._parlay_calculator.calculate_status(legs)
                    
                    # Only update if status changed
                    if new_status != parlay.status:
                        old_status = parlay.status
                        parlay.status = new_status
                        
                        if new_status in ("WON", "LOST", "PUSH", "VOID"):
                            parlay.settled_at = datetime.utcnow()
                        
                        await self.db.flush()
                        stats.parlays_settled += 1
                        
                        logger.info(
                            f"settle_all_pending_parlays: Parlay {parlay.id} status changed "
                            f"from {old_status} to {new_status}"
                        )
                        
                        # Create feed events (with error handling)
                        try:
                            if new_status == "WON":
                                stats.parlays_won += 1
                                user_alias = getattr(parlay, 'public_alias', None) if getattr(parlay, 'is_public', False) else None
                                # Extract odds from legs if available
                                odds = None
                                if legs and legs[0].price:
                                    odds = legs[0].price
                                await self._feed_generator.create_parlay_won_event(
                                    parlay,
                                    user_alias=user_alias,
                                    legs_count=len(legs),
                                    odds=odds,
                                )
                            elif new_status == "LOST":
                                stats.parlays_lost += 1
                                # Find which leg busted
                                busted_leg = None
                                for idx, leg in enumerate(legs, 1):
                                    if leg.status == "LOST":
                                        busted_leg = idx
                                        break
                                
                                user_alias = getattr(parlay, 'public_alias', None) if getattr(parlay, 'is_public', False) else None
                                await self._feed_generator.create_parlay_lost_event(
                                    parlay,
                                    user_alias=user_alias,
                                    busted_leg=busted_leg,
                                )
                        except Exception as feed_error:
                            # Don't fail settlement if feed event creation fails
                            logger.error(
                                f"settle_all_pending_parlays: Error creating feed event for parlay {parlay.id}: {feed_error}",
                                exc_info=True
                            )
                
                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"settle_all_pending_parlays: Error settling parlay {parlay.id}: {e}",
                        exc_info=True
                    )
                    # Continue processing other parlays
                    continue
            
            # Also process saved_parlays (custom parlays)
            result = await self.db.execute(
                select(SavedParlay).where(SavedParlay.status.in_(["PENDING", "LIVE"]))
            )
            saved_parlays = result.scalars().all()
            
            if saved_parlays:
                logger.info(f"settle_all_pending_parlays: Processing {len(saved_parlays)} saved parlays")
            
            for saved_parlay in saved_parlays:
                try:
                    # Validate saved_parlay
                    if not saved_parlay.id:
                        logger.warning("settle_all_pending_parlays: SavedParlay missing id, skipping")
                        continue
                    
                    result = await self.db.execute(
                        select(ParlayLeg).where(ParlayLeg.saved_parlay_id == saved_parlay.id)
                    )
                    legs = result.scalars().all()
                    
                    if not legs:
                        logger.debug(f"settle_all_pending_parlays: SavedParlay {saved_parlay.id} has no legs, skipping")
                        continue
                    
                    new_status = self._parlay_calculator.calculate_status(legs)
                    
                    if new_status != saved_parlay.status:
                        old_status = saved_parlay.status
                        saved_parlay.status = new_status
                        
                        if new_status in ("WON", "LOST", "PUSH", "VOID"):
                            saved_parlay.settled_at = datetime.utcnow()
                        
                        await self.db.flush()
                        stats.parlays_settled += 1
                        
                        logger.info(
                            f"settle_all_pending_parlays: SavedParlay {saved_parlay.id} status changed "
                            f"from {old_status} to {new_status}"
                        )
                        
                        # Create feed events (with error handling)
                        try:
                            if new_status == "WON":
                                stats.parlays_won += 1
                                user_alias = getattr(saved_parlay, 'public_alias', None) if getattr(saved_parlay, 'is_public', False) else None
                                await self._feed_generator.create_parlay_won_event(
                                    saved_parlay,
                                    user_alias=user_alias,
                                    legs_count=len(legs),
                                )
                            elif new_status == "LOST":
                                stats.parlays_lost += 1
                                busted_leg = None
                                for idx, leg in enumerate(legs, 1):
                                    if leg.status == "LOST":
                                        busted_leg = idx
                                        break
                                
                                user_alias = getattr(saved_parlay, 'public_alias', None) if getattr(saved_parlay, 'is_public', False) else None
                                await self._feed_generator.create_parlay_lost_event(
                                    saved_parlay,
                                    user_alias=user_alias,
                                    busted_leg=busted_leg,
                                )
                        except Exception as feed_error:
                            # Don't fail settlement if feed event creation fails
                            logger.error(
                                f"settle_all_pending_parlays: Error creating feed event for saved_parlay {saved_parlay.id}: {feed_error}",
                                exc_info=True
                            )
                
                except Exception as e:
                    error_count += 1
                    logger.error(
                        f"settle_all_pending_parlays: Error settling saved_parlay {saved_parlay.id}: {e}",
                        exc_info=True
                    )
                    # Continue processing other saved parlays
                    continue
            
            # Commit all changes
            try:
                await self.db.commit()
            except Exception as commit_error:
                logger.error(
                    f"settle_all_pending_parlays: Error committing settlement: {commit_error}",
                    exc_info=True
                )
                await self.db.rollback()
                # Return stats with what we processed before the commit error
                return stats
            
            # Update metrics
            _settlement_metrics["parlays_settled_total"] += stats.parlays_settled
            _settlement_metrics["parlays_won_total"] += stats.parlays_won
            _settlement_metrics["parlays_lost_total"] += stats.parlays_lost
            _settlement_metrics["last_settlement_time"] = datetime.utcnow().isoformat()
            
            if error_count > 0:
                logger.warning(
                    f"settle_all_pending_parlays: Settled {stats.parlays_settled} parlays with {error_count} errors"
                )
                _settlement_metrics["errors_total"] += error_count
            else:
                logger.info(
                    f"settle_all_pending_parlays: Successfully settled {stats.parlays_settled} parlays "
                    f"({stats.parlays_won} won, {stats.parlays_lost} lost)"
                )
        
        except Exception as e:
            logger.error(
                f"settle_all_pending_parlays: Fatal error: {e}",
                exc_info=True
            )
            _settlement_metrics["errors_total"] += 1
            try:
                await self.db.rollback()
            except Exception:
                pass
        
        return stats
    
    async def _update_parlay_status(self, leg: ParlayLeg):
        """Update parlay status after a leg is settled.
        
        Args:
            leg: ParlayLeg that was just settled
        """
        if not leg:
            logger.warning("_update_parlay_status: Missing leg")
            return
        
        try:
            # Update AI parlay if exists
            if leg.parlay_id:
                try:
                    result = await self.db.execute(
                        select(Parlay).where(Parlay.id == leg.parlay_id)
                    )
                    parlay = result.scalar_one_or_none()
                    
                    if parlay:
                        # Get all legs
                        result = await self.db.execute(
                            select(ParlayLeg).where(ParlayLeg.parlay_id == parlay.id)
                        )
                        legs = result.scalars().all()
                        
                        if not legs:
                            logger.debug(f"_update_parlay_status: Parlay {parlay.id} has no legs")
                            return
                        
                        new_status = self._parlay_calculator.calculate_status(legs)
                        
                        if new_status != parlay.status:
                            old_status = parlay.status
                            parlay.status = new_status
                            if new_status in ("WON", "LOST", "PUSH", "VOID"):
                                parlay.settled_at = datetime.utcnow()
                            await self.db.flush()
                            logger.debug(
                                f"_update_parlay_status: Parlay {parlay.id} status updated "
                                f"from {old_status} to {new_status}"
                            )
                except Exception as parlay_error:
                    logger.error(
                        f"_update_parlay_status: Error updating parlay {leg.parlay_id}: {parlay_error}",
                        exc_info=True
                    )
            
            # Update saved parlay if exists
            if leg.saved_parlay_id:
                try:
                    result = await self.db.execute(
                        select(SavedParlay).where(SavedParlay.id == leg.saved_parlay_id)
                    )
                    saved_parlay = result.scalar_one_or_none()
                    
                    if saved_parlay:
                        result = await self.db.execute(
                            select(ParlayLeg).where(ParlayLeg.saved_parlay_id == saved_parlay.id)
                        )
                        legs = result.scalars().all()
                        
                        if not legs:
                            logger.debug(f"_update_parlay_status: SavedParlay {saved_parlay.id} has no legs")
                            return
                        
                        new_status = self._parlay_calculator.calculate_status(legs)
                        
                        if new_status != saved_parlay.status:
                            old_status = saved_parlay.status
                            saved_parlay.status = new_status
                            if new_status in ("WON", "LOST", "PUSH", "VOID"):
                                saved_parlay.settled_at = datetime.utcnow()
                            await self.db.flush()
                            logger.debug(
                                f"_update_parlay_status: SavedParlay {saved_parlay.id} status updated "
                                f"from {old_status} to {new_status}"
                            )
                except Exception as saved_parlay_error:
                    logger.error(
                        f"_update_parlay_status: Error updating saved_parlay {leg.saved_parlay_id}: {saved_parlay_error}",
                        exc_info=True
                    )
        
        except Exception as e:
            logger.error(
                f"_update_parlay_status: Fatal error updating parlay status for leg {leg.id}: {e}",
                exc_info=True
            )
