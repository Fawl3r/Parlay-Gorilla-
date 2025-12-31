"""Builds enriched snapshots for custom parlay legs.

We store a JSON `legs` snapshot on `saved_parlays` for provenance + hashing.
For custom parlays, we optionally enrich legs with:
- book (from Market)
- game_start_time_utc (from Game)

This logic lives in a service to keep API route modules smaller and focused.
"""

from __future__ import annotations

import uuid
from datetime import timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.models.market import Market


class CustomLegsSnapshotBuilder:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def build(self, legs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        game_ids: set[uuid.UUID] = set()
        market_ids: set[uuid.UUID] = set()

        for leg in legs:
            try:
                game_ids.add(uuid.UUID(str(leg["game_id"])))
            except Exception:
                continue

            market_id = leg.get("market_id")
            if market_id:
                try:
                    market_ids.add(uuid.UUID(str(market_id)))
                except Exception:
                    pass

        games_by_id: Dict[str, Game] = {}
        if game_ids:
            res = await self._db.execute(select(Game).where(Game.id.in_(list(game_ids))))
            games_by_id = {str(g.id): g for g in res.scalars().all()}

        markets_by_id: Dict[str, Market] = {}
        if market_ids:
            res = await self._db.execute(select(Market).where(Market.id.in_(list(market_ids))))
            markets_by_id = {str(m.id): m for m in res.scalars().all()}

        enriched: List[Dict[str, Any]] = []
        for leg in legs:
            out = dict(leg)

            game = games_by_id.get(str(leg.get("game_id")))
            if game and game.start_time:
                out["game_start_time_utc"] = game.start_time.astimezone(timezone.utc).isoformat()

            market = markets_by_id.get(str(leg.get("market_id")))
            if market:
                out["book"] = market.book

            enriched.append(out)

        return enriched


