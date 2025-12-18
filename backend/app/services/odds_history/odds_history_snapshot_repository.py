from __future__ import annotations

from datetime import date
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.odds_history_snapshot import OddsHistorySnapshot


class OddsHistorySnapshotRepository:
    """DB access for historical odds snapshots."""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def has_sport_snapshot_for_date(self, *, sport_key: str, snapshot_kind: str, snapshot_date: date) -> bool:
        result = await self._db.execute(
            select(OddsHistorySnapshot.id)
            .where(OddsHistorySnapshot.sport_key == sport_key)
            .where(OddsHistorySnapshot.snapshot_kind == snapshot_kind)
            .where(OddsHistorySnapshot.snapshot_date == snapshot_date)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_latest_for_game(self, *, external_game_id: str, snapshot_kind: str) -> Optional[OddsHistorySnapshot]:
        result = await self._db.execute(
            select(OddsHistorySnapshot)
            .where(OddsHistorySnapshot.external_game_id == external_game_id)
            .where(OddsHistorySnapshot.snapshot_kind == snapshot_kind)
            .order_by(OddsHistorySnapshot.snapshot_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_data_for_games(
        self, *, external_game_ids: Iterable[str], snapshot_kind: str
    ) -> Dict[str, Dict[str, Any]]:
        ids = [str(x) for x in external_game_ids if x]
        if not ids:
            return {}

        # SQLite doesn't support DISTINCT ON; do a simple "latest per id" in Python.
        result = await self._db.execute(
            select(OddsHistorySnapshot)
            .where(OddsHistorySnapshot.external_game_id.in_(ids))
            .where(OddsHistorySnapshot.snapshot_kind == snapshot_kind)
            .order_by(OddsHistorySnapshot.external_game_id, OddsHistorySnapshot.snapshot_date.desc())
        )
        rows = result.scalars().all()
        latest: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            if row.external_game_id not in latest:
                latest[row.external_game_id] = dict(row.data or {})
        return latest

    async def upsert(
        self,
        *,
        external_game_id: str,
        sport_key: str,
        snapshot_kind: str,
        snapshot_date: date,
        requested_at,
        snapshot_time,
        data: Dict[str, Any],
    ) -> OddsHistorySnapshot:
        result = await self._db.execute(
            select(OddsHistorySnapshot)
            .where(OddsHistorySnapshot.external_game_id == external_game_id)
            .where(OddsHistorySnapshot.snapshot_kind == snapshot_kind)
            .where(OddsHistorySnapshot.snapshot_date == snapshot_date)
            .limit(1)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.requested_at = requested_at
            existing.snapshot_time = snapshot_time
            existing.data = data
            return existing

        row = OddsHistorySnapshot(
            external_game_id=external_game_id,
            sport_key=sport_key,
            snapshot_kind=snapshot_kind,
            snapshot_date=snapshot_date,
            requested_at=requested_at,
            snapshot_time=snapshot_time,
            data=data,
        )
        self._db.add(row)
        return row




