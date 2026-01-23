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
            Number of legs settled
        """
        try:
            # Get the game
            result = await self.db.execute(select(Game).where(Game.id == game_id))
            game = result.scalar_one_or_none()
            
            if not game or game.status != "FINAL":
                return 0
            
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
            
            settled_count = 0
            
            for leg in legs:
                try:
                    # Calculate leg result
                    if leg.market_type == "h2h":
                        result_status = self._leg_calculator.calculate_moneyline_result(leg, game)
                    elif leg.market_type == "spreads":
                        result_status = self._leg_calculator.calculate_spread_result(leg, game)
                    elif leg.market_type == "totals":
                        result_status = self._leg_calculator.calculate_total_result(leg, game)
                    else:
                        result_status = "VOID"
                    
                    # Update leg
                    leg.status = result_status
                    leg.settled_at = datetime.utcnow()
                    leg.result_reason = f"Game {game.away_team} @ {game.home_team} final: {game.away_score}-{game.home_score}"
                    
                    await self.db.flush()
                    settled_count += 1
                    
                    # Create feed event for leg result
                    if result_status == "WON":
                        await self._feed_generator.create_leg_won_event(leg)
                    elif result_status == "LOST":
                        await self._feed_generator.create_leg_lost_event(leg)
                    
                    # Update parlay status
                    await self._update_parlay_status(leg)
                
                except Exception as e:
                    logger.error(f"Error settling leg {leg.id}: {e}")
                    continue
            
            return settled_count
        
        except Exception as e:
            logger.error(f"Error settling legs for game {game_id}: {e}")
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
            
            for parlay in parlays:
                try:
                    # Get all legs for this parlay
                    result = await self.db.execute(
                        select(ParlayLeg).where(ParlayLeg.parlay_id == parlay.id)
                    )
                    legs = result.scalars().all()
                    
                    if not legs:
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
                        
                        # Create feed events
                        if new_status == "WON":
                            stats.parlays_won += 1
                            user_alias = parlay.public_alias if parlay.is_public else None
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
                            
                            user_alias = parlay.public_alias if parlay.is_public else None
                            await self._feed_generator.create_parlay_lost_event(
                                parlay,
                                user_alias=user_alias,
                                busted_leg=busted_leg,
                            )
                
                except Exception as e:
                    logger.error(f"Error settling parlay {parlay.id}: {e}")
                    continue
            
            # Also process saved_parlays (custom parlays)
            result = await self.db.execute(
                select(SavedParlay).where(SavedParlay.status.in_(["PENDING", "LIVE"]))
            )
            saved_parlays = result.scalars().all()
            
            for saved_parlay in saved_parlays:
                try:
                    result = await self.db.execute(
                        select(ParlayLeg).where(ParlayLeg.saved_parlay_id == saved_parlay.id)
                    )
                    legs = result.scalars().all()
                    
                    if not legs:
                        continue
                    
                    new_status = self._parlay_calculator.calculate_status(legs)
                    
                    if new_status != saved_parlay.status:
                        saved_parlay.status = new_status
                        
                        if new_status in ("WON", "LOST", "PUSH", "VOID"):
                            saved_parlay.settled_at = datetime.utcnow()
                        
                        await self.db.flush()
                        stats.parlays_settled += 1
                        
                        if new_status == "WON":
                            stats.parlays_won += 1
                            user_alias = saved_parlay.public_alias if saved_parlay.is_public else None
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
                            
                            user_alias = saved_parlay.public_alias if saved_parlay.is_public else None
                            await self._feed_generator.create_parlay_lost_event(
                                saved_parlay,
                                user_alias=user_alias,
                                busted_leg=busted_leg,
                            )
                
                except Exception as e:
                    logger.error(f"Error settling saved_parlay {saved_parlay.id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error in settle_all_pending_parlays: {e}")
        
        return stats
    
    async def _update_parlay_status(self, leg: ParlayLeg):
        """Update parlay status after a leg is settled."""
        try:
            # Update AI parlay if exists
            if leg.parlay_id:
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
                    
                    new_status = self._parlay_calculator.calculate_status(legs)
                    
                    if new_status != parlay.status:
                        parlay.status = new_status
                        if new_status in ("WON", "LOST", "PUSH", "VOID"):
                            parlay.settled_at = datetime.utcnow()
                        await self.db.flush()
            
            # Update saved parlay if exists
            if leg.saved_parlay_id:
                result = await self.db.execute(
                    select(SavedParlay).where(SavedParlay.id == leg.saved_parlay_id)
                )
                saved_parlay = result.scalar_one_or_none()
                
                if saved_parlay:
                    result = await self.db.execute(
                        select(ParlayLeg).where(ParlayLeg.saved_parlay_id == saved_parlay.id)
                    )
                    legs = result.scalars().all()
                    
                    new_status = self._parlay_calculator.calculate_status(legs)
                    
                    if new_status != saved_parlay.status:
                        saved_parlay.status = new_status
                        if new_status in ("WON", "LOST", "PUSH", "VOID"):
                            saved_parlay.settled_at = datetime.utcnow()
                        await self.db.flush()
        
        except Exception as e:
            logger.error(f"Error updating parlay status: {e}")
