from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.game import Game
from app.services.odds_history.odds_history_snapshot_repository import OddsHistorySnapshotRepository
from app.services.odds_history.odds_line_extractor import OddsLineExtractor
from app.services.sports_config import SportConfig
from app.services.the_odds_api_client import OddsApiKeys, TheOddsApiClient


class OddsHistorySyncService:
    """Sync a single lookback snapshot per sport per day (UTC) using Odds API historical endpoints."""

    SNAPSHOT_KIND_LOOKBACK_24H = "lookback_24h"

    def __init__(self, db: AsyncSession):
        self._db = db
        self._repo = OddsHistorySnapshotRepository(db)
        self._extractor = OddsLineExtractor()
        self._api = TheOddsApiClient(
            api_keys=OddsApiKeys(
                primary=settings.the_odds_api_key,
                fallback=getattr(settings, "the_odds_api_fallback_key", None),
            )
        )

    async def sync_daily_lookback_24h_for_sport(self, *, sport_config: SportConfig) -> int:
        today_utc = datetime.now(tz=timezone.utc).date()
        if await self._repo.has_sport_snapshot_for_date(
            sport_key=sport_config.odds_key, snapshot_kind=self.SNAPSHOT_KIND_LOOKBACK_24H, snapshot_date=today_utc
        ):
            return 0

        upcoming_ids = await self._get_upcoming_external_ids(sport_config=sport_config)
        if not upcoming_ids:
            return 0

        requested_at = datetime.now(tz=timezone.utc) - timedelta(hours=24)
        requested_at_iso = requested_at.isoformat(timespec="seconds").replace("+00:00", "Z")
        payload = await self._api.get_historical_odds(
            sport_key=sport_config.odds_key,
            date_iso=requested_at_iso,
            regions="us",
            markets="h2h,spreads,totals",
            odds_format="american",
            timeout_seconds=25.0,
        )

        snapshot_time = _parse_iso_datetime(payload.get("timestamp"))
        events = payload.get("data") or []
        if not isinstance(events, list):
            return 0

        stored = 0
        for event in events:
            if not isinstance(event, dict):
                continue
            external_id = str(event.get("id") or "").strip()
            if not external_id or external_id not in upcoming_ids:
                continue

            extracted = self._extractor.extract(event=event)
            if not extracted:
                continue

            await self._repo.upsert(
                external_game_id=external_id,
                sport_key=sport_config.odds_key,
                snapshot_kind=self.SNAPSHOT_KIND_LOOKBACK_24H,
                snapshot_date=today_utc,
                requested_at=requested_at,
                snapshot_time=snapshot_time,
                data=extracted.as_dict(),
            )
            stored += 1

        if stored > 0:
            await self._db.commit()

        return stored

    async def _get_upcoming_external_ids(self, *, sport_config: SportConfig) -> Set[str]:
        now = datetime.now(tz=timezone.utc)
        cutoff_time = now - timedelta(hours=24)
        future_cutoff = now + timedelta(days=sport_config.lookahead_days)

        result = await self._db.execute(
            select(Game.external_game_id)
            .where(Game.sport == sport_config.code)
            .where(Game.start_time >= cutoff_time)
            .where(Game.start_time <= future_cutoff)
        )
        ids = {str(x) for x in result.scalars().all() if x}
        # Only Odds API games have raw event ids; ESPN schedule fallback uses "espn:*".
        return {x for x in ids if not x.startswith("espn:")}


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


