"""Feed event generator for parlay wins/losses."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parlay import Parlay
from app.models.saved_parlay import SavedParlay
from app.models.parlay_leg import ParlayLeg
from app.models.parlay_feed_event import ParlayFeedEvent


class FeedEventGenerator:
    """Generate feed events for parlay settlement."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_parlay_won_event(
        self,
        parlay: Parlay | SavedParlay,
        user_alias: str | None = None,
        legs_count: int | None = None,
        odds: str | None = None,
    ) -> ParlayFeedEvent:
        """Create PARLAY_WON feed event."""
        parlay_type = "AI" if isinstance(parlay, Parlay) else "CUSTOM"
        legs = legs_count or (parlay.num_legs if isinstance(parlay, Parlay) else len(parlay.legs) if isinstance(parlay, SavedParlay) else 0)
        odds_str = odds or "+0"
        
        summary = f"✅ {parlay_type} PARLAY HIT — {legs}-Leg {odds_str}"
        if user_alias:
            summary += f" ({user_alias})"
        
        event = ParlayFeedEvent(
            event_type="PARLAY_WON",
            sport=None,  # Could extract from legs if needed
            parlay_id=parlay.id if isinstance(parlay, Parlay) else None,
            saved_parlay_id=parlay.id if isinstance(parlay, SavedParlay) else None,
            user_alias=user_alias,
            summary=summary,
            metadata={
                "parlay_type": parlay_type,
                "legs_count": legs,
                "odds": odds_str,
            },
        )
        self.db.add(event)
        await self.db.flush()
        return event
    
    async def create_parlay_lost_event(
        self,
        parlay: Parlay | SavedParlay,
        user_alias: str | None = None,
        busted_leg: int | None = None,
    ) -> ParlayFeedEvent:
        """Create PARLAY_LOST feed event."""
        parlay_type = "AI" if isinstance(parlay, Parlay) else "CUSTOM"
        
        summary = f"❌ {parlay_type} PARLAY LOST"
        if busted_leg:
            summary += f" — busted on Leg {busted_leg}"
        if user_alias:
            summary += f" ({user_alias})"
        
        event = ParlayFeedEvent(
            event_type="PARLAY_LOST",
            sport=None,
            parlay_id=parlay.id if isinstance(parlay, Parlay) else None,
            saved_parlay_id=parlay.id if isinstance(parlay, SavedParlay) else None,
            user_alias=user_alias,
            summary=summary,
            metadata={
                "parlay_type": parlay_type,
                "busted_leg": busted_leg,
            },
        )
        self.db.add(event)
        await self.db.flush()
        return event
    
    async def create_leg_won_event(
        self,
        leg: ParlayLeg,
        parlay: Parlay | SavedParlay | None = None,
    ) -> ParlayFeedEvent:
        """Create LEG_WON feed event."""
        summary = f"✅ Leg WON: {leg.selection}"
        
        event = ParlayFeedEvent(
            event_type="LEG_WON",
            sport=None,
            parlay_id=parlay.id if isinstance(parlay, Parlay) else None,
            saved_parlay_id=parlay.id if isinstance(parlay, SavedParlay) else None,
            summary=summary,
            metadata={
                "leg_id": str(leg.id),
                "game_id": str(leg.game_id),
                "market_type": leg.market_type,
                "selection": leg.selection,
            },
        )
        self.db.add(event)
        await self.db.flush()
        return event
    
    async def create_leg_lost_event(
        self,
        leg: ParlayLeg,
        parlay: Parlay | SavedParlay | None = None,
    ) -> ParlayFeedEvent:
        """Create LEG_LOST feed event."""
        summary = f"❌ Leg LOST: {leg.selection}"
        
        event = ParlayFeedEvent(
            event_type="LEG_LOST",
            sport=None,
            parlay_id=parlay.id if isinstance(parlay, Parlay) else None,
            saved_parlay_id=parlay.id if isinstance(parlay, SavedParlay) else None,
            summary=summary,
            metadata={
                "leg_id": str(leg.id),
                "game_id": str(leg.game_id),
                "market_type": leg.market_type,
                "selection": leg.selection,
            },
        )
        self.db.add(event)
        await self.db.flush()
        return event
