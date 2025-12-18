from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.game import Game
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository
from app.services.odds_history.odds_movement_service import OddsMovementService


class OddsHistoryProvider:
    """Provide a line-movement summary for a game using stored historical snapshots."""

    SNAPSHOT_KIND_LOOKBACK_24H = "lookback_24h"

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = OddsHistorySnapshotRepository(db)
        self._movement = OddsMovementService()

    async def get_line_movement(
        self, *, game: Game, current_snapshot: Dict[str, Any], snapshot_kind: str = SNAPSHOT_KIND_LOOKBACK_24H
    ) -> Optional[Dict[str, Any]]:
        external_id = str(getattr(game, "external_game_id", "") or "").strip()
        if not external_id or external_id.startswith("espn:"):
            return None

        hist = await self._repo.get_latest_for_game(external_game_id=external_id, snapshot_kind=snapshot_kind)
        if not hist or not isinstance(hist.data, dict):
            return None

        movement = self._movement.build(current=current_snapshot, historical=dict(hist.data))
        payload: Dict[str, Any] = movement.as_dict()
        payload["snapshot_kind"] = snapshot_kind
        payload["snapshot_date"] = hist.snapshot_date.isoformat() if getattr(hist, "snapshot_date", None) else None
        payload["snapshot_time"] = hist.snapshot_time.isoformat() if getattr(hist, "snapshot_time", None) else None
        payload["book"] = str((hist.data or {}).get("book") or "")
        return payload




