from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from app.services.the_odds_api_client import TheOddsApiClient


@dataclass(frozen=True)
class SportsAvailabilitySnapshot:
    active_by_odds_key: Dict[str, bool]
    fetched_at: datetime
    expires_at: datetime


class SportsAvailabilityService:
    """Cache The Odds API `/sports` response to determine if a sport is active/in-season."""

    _cache_lock = asyncio.Lock()
    _cache: Optional[SportsAvailabilitySnapshot] = None

    def __init__(self, *, api: TheOddsApiClient, cache_ttl_hours: float = 6.0):
        self._api = api
        self._ttl = timedelta(hours=float(cache_ttl_hours))

    async def get_active_by_odds_key(self) -> Dict[str, bool]:
        now = datetime.now(tz=timezone.utc)
        cached = self.__class__._cache
        if cached and cached.expires_at > now:
            return dict(cached.active_by_odds_key)

        async with self.__class__._cache_lock:
            cached = self.__class__._cache
            if cached and cached.expires_at > now:
                return dict(cached.active_by_odds_key)

            try:
                sports = await self._api.get_sports(timeout_seconds=10.0)
                active_by_key: Dict[str, bool] = {}
                for item in sports:
                    key = str(item.get("key") or "").strip()
                    if not key:
                        continue
                    active_by_key[key] = bool(item.get("active"))

                self.__class__._cache = SportsAvailabilitySnapshot(
                    active_by_odds_key=active_by_key,
                    fetched_at=now,
                    expires_at=now + self._ttl,
                )
                return dict(active_by_key)
            except Exception:
                # Best-effort: if the request fails, keep any previous cache for a shorter window.
                if cached:
                    self.__class__._cache = SportsAvailabilitySnapshot(
                        active_by_odds_key=dict(cached.active_by_odds_key),
                        fetched_at=cached.fetched_at,
                        expires_at=now + timedelta(minutes=10),
                    )
                    return dict(cached.active_by_odds_key)

                self.__class__._cache = SportsAvailabilitySnapshot(
                    active_by_odds_key={},
                    fetched_at=now,
                    expires_at=now + timedelta(minutes=10),
                )
                return {}




