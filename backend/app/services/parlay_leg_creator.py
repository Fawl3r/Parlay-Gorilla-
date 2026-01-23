"""Service for creating parlay_legs records from JSON legs."""

from __future__ import annotations

import logging
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parlay_leg import ParlayLeg
from app.models.game import Game
from app.models.market import Market

logger = logging.getLogger(__name__)


class ParlayLegCreator:
    """Create parlay_legs records from JSON leg data."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_legs_from_json(
        self,
        legs_json: List[Dict[str, Any]],
        parlay_id: UUID | None = None,
        saved_parlay_id: UUID | None = None,
    ) -> List[ParlayLeg]:
        """Create parlay_legs records from JSON legs.
        
        Args:
            legs_json: List of leg dictionaries from parlay.legs JSON
            parlay_id: ID of AI parlay (if applicable)
            saved_parlay_id: ID of saved parlay (if applicable)
            
        Returns:
            List of created ParlayLeg objects
        """
        created_legs = []
        
        for leg_data in legs_json:
            try:
                # Extract game_id from market_id or game lookup
                game_id = await self._resolve_game_id(leg_data)
                
                if not game_id:
                    logger.warning(f"Could not resolve game_id for leg: {leg_data}")
                    continue
                
                # Extract market type
                market_type = str(leg_data.get("market_type", "h2h")).lower()
                
                # Extract selection (outcome)
                selection = str(leg_data.get("outcome", ""))
                
                # Extract line (for spreads/totals)
                line = None
                if market_type in ("spreads", "totals"):
                    # Try to extract from outcome string or line field
                    line_str = leg_data.get("line") or leg_data.get("point")
                    if line_str:
                        try:
                            line = float(line_str)
                        except (ValueError, TypeError):
                            pass
                
                # Extract price (odds)
                price = str(leg_data.get("odds", ""))
                
                # Create leg
                leg = ParlayLeg(
                    parlay_id=parlay_id,
                    saved_parlay_id=saved_parlay_id,
                    game_id=game_id,
                    market_type=market_type,
                    selection=selection,
                    line=line,
                    price=price,
                    status="PENDING",
                )
                
                self.db.add(leg)
                created_legs.append(leg)
            
            except Exception as e:
                logger.error(f"Error creating leg from JSON: {e}")
                continue
        
        await self.db.flush()
        return created_legs
    
    async def _resolve_game_id(self, leg_data: Dict[str, Any]) -> UUID | None:
        """Resolve game_id from leg data.
        
        Tries:
        1. Direct game_id field
        2. market_id -> Market -> game_id
        3. game string lookup (home_team/away_team)
        """
        # Method 1: Direct game_id
        if "game_id" in leg_data:
            try:
                return UUID(leg_data["game_id"])
            except (ValueError, TypeError):
                pass
        
        # Method 2: market_id -> Market -> game_id
        market_id = leg_data.get("market_id")
        if market_id:
            try:
                result = await self.db.execute(
                    select(Market).where(Market.id == UUID(market_id))
                )
                market = result.scalar_one_or_none()
                if market:
                    return market.game_id
            except Exception as e:
                logger.debug(f"Error resolving game_id from market_id: {e}")
        
        # Method 3: Game lookup by teams (less reliable)
        home_team = leg_data.get("home_team")
        away_team = leg_data.get("away_team")
        sport = leg_data.get("sport")
        
        if home_team and away_team and sport:
            # Try to find game by team names (recent games only)
            from datetime import datetime, timedelta
            from sqlalchemy import and_
            
            cutoff = datetime.utcnow() - timedelta(days=7)
            result = await self.db.execute(
                select(Game).where(
                    and_(
                        Game.sport == sport.upper(),
                        Game.home_team == home_team,
                        Game.away_team == away_team,
                        Game.start_time >= cutoff,
                    )
                ).limit(1)
            )
            game = result.scalar_one_or_none()
            if game:
                return game.id
        
        return None
