"""
API-Sports enrichment cache: Redis when available, else in-memory with TTL.

TTLs: standings 6h, team_stats 12h, form 2h, injuries 60m, teams 24h.
Keys: apisports:enrich:{dataset}:{sport}:{league_id}:{season}:{optional_extra}
For team_stats use extra=str(team_id) -> per-team cache key.
Timestamp key: same key with suffix :at (ISO string) for source_timestamps.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.services.redis.redis_client_provider import get_redis_provider

logger = logging.getLogger(__name__)

PREFIX = "apisports:enrich:"
TS_SUFFIX = ":at"
# TTLs in seconds
TTL_STANDINGS = 6 * 3600
TTL_TEAM_STATS = 12 * 3600
TTL_FORM = 2 * 3600
TTL_INJURIES = 60 * 60
TTL_TEAMS = 24 * 3600

# In-memory fallback: key -> (value, expires_at); key+TS_SUFFIX not stored, we use _memory_ts
_memory: Dict[str, tuple[Any, float]] = {}
_memory_ts: Dict[str, float] = {}  # key -> time.time() when set (for cached_at)
_memory_ttls = {
    "standings": TTL_STANDINGS,
    "team_stats": TTL_TEAM_STATS,
    "form": TTL_FORM,
    "injuries": TTL_INJURIES,
    "teams": TTL_TEAMS,
}


def _key(dataset: str, sport: str, league_id: int, season: str, extra: str = "") -> str:
    parts = [PREFIX, dataset, sport, str(league_id), str(season)]
    if extra:
        parts.append(extra)
    return ":".join(parts)


def _memory_get(key: str) -> Optional[Any]:
    if key not in _memory:
        return None
    val, expires = _memory[key]
    if time.time() > expires:
        del _memory[key]
        _memory_ts.pop(key, None)
        return None
    return val


def _memory_get_timestamp(key: str) -> Optional[str]:
    if key not in _memory_ts or key not in _memory:
        return None
    ts = _memory_ts[key]
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _memory_set(key: str, value: Any, ttl_seconds: int) -> None:
    now = time.time()
    _memory[key] = (value, now + ttl_seconds)
    _memory_ts[key] = now


def _telemetry_dataset(dataset: str) -> str:
    """Normalize cache dataset name for telemetry (teams -> teams_index)."""
    return "teams_index" if dataset == "teams" else dataset


async def get_cached(dataset: str, sport: str, league_id: int, season: str, extra: str = "") -> Optional[Any]:
    """Get cached enrichment data. Returns None if miss or expired."""
    value, _ = await get_cached_with_timestamp(dataset, sport, league_id, season, extra)
    return value


async def get_cached_with_timestamp(
    dataset: str, sport: str, league_id: int, season: str, extra: str = ""
) -> Tuple[Optional[Any], Optional[str]]:
    """
    Get cached enrichment data and when it was cached.
    Returns (value, cached_at_iso) or (None, None) on miss/expired.
    """
    key = _key(dataset, sport, league_id, season, extra)
    try:
        r = get_redis_provider()
        if r.is_configured():
            client = r.get_client()
            k = key.encode("utf-8") if isinstance(key, str) else key
            raw = await client.get(k)
            if raw is None:
                return (None, None)
            try:
                from app.services.apisports.telemetry_helpers import inc_cache_hit
                inc_cache_hit(_telemetry_dataset(dataset))
            except Exception:
                pass
            value = json.loads(raw.decode("utf-8"))
            ts_key = key + TS_SUFFIX
            ts_raw = await client.get(ts_key.encode("utf-8") if isinstance(ts_key, str) else ts_key)
            cached_at = ts_raw.decode("utf-8") if ts_raw else None
            return (value, cached_at)
    except Exception as e:
        logger.debug("Enrichment cache Redis get failed, trying memory: %s", e)
    val = _memory_get(key)
    if val is not None:
        try:
            from app.services.apisports.telemetry_helpers import inc_cache_hit
            inc_cache_hit(_telemetry_dataset(dataset))
        except Exception:
            pass
        cached_at = _memory_get_timestamp(key)
        return (val, cached_at)
    return (None, None)


async def set_cached(
    dataset: str,
    sport: str,
    league_id: int,
    season: str,
    value: Any,
    extra: str = "",
) -> None:
    """Store enrichment data in cache with dataset-appropriate TTL; also store cached_at timestamp."""
    key = _key(dataset, sport, league_id, season, extra)
    ttl = _memory_ttls.get(dataset, TTL_STANDINGS)
    cached_at = datetime.now(timezone.utc).isoformat()
    try:
        r = get_redis_provider()
        if r.is_configured():
            client = r.get_client()
            k = key.encode("utf-8") if isinstance(key, str) else key
            payload = json.dumps(value) if not isinstance(value, (str, bytes)) else value
            if isinstance(payload, str):
                payload = payload.encode("utf-8")
            await client.set(k, payload, ex=ttl)
            ts_key = key + TS_SUFFIX
            k_ts = ts_key.encode("utf-8") if isinstance(ts_key, str) else ts_key
            await client.set(k_ts, cached_at.encode("utf-8"), ex=ttl)
            return
    except Exception as e:
        logger.debug("Enrichment cache Redis set failed, using memory: %s", e)
    _memory_set(key, value, ttl)
