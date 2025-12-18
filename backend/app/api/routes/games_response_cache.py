from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.schemas.game import GameResponse


@dataclass(frozen=True)
class GamesCacheEntry:
    data: List[GameResponse]
    cached_at: datetime


class GamesResponseCache:
    """Small in-process cache for `GameResponse[]` lists."""

    def __init__(self, *, ttl_seconds: int):
        self._ttl = timedelta(seconds=int(ttl_seconds))
        self._entries: Dict[str, GamesCacheEntry] = {}

    def get(self, key: str) -> Optional[List[GameResponse]]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if datetime.now() - entry.cached_at >= self._ttl:
            self._entries.pop(key, None)
            return None
        return entry.data

    def age_seconds(self, key: str) -> Optional[float]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        return (datetime.now() - entry.cached_at).total_seconds()

    def set(self, key: str, data: List[GameResponse]) -> None:
        self._entries[key] = GamesCacheEntry(data=data, cached_at=datetime.now())

    def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()


# Singleton cache (10 minutes)
games_response_cache = GamesResponseCache(ttl_seconds=600)



