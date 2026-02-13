"""
Minimal in-memory telemetry for Safety Mode.

Tracks: last refresh timestamps, rolling error/generation/API counts,
estimated API calls today, and daily budget (from config).
Optional Redis persistence for critical keys (no new dependencies).
Safety event ring buffer: last N state transitions.
"""

from __future__ import annotations

import json
import time
from collections import deque
from threading import Lock
from typing import Any, Dict, List, Optional

# Rolling windows: (timestamp, count) or just timestamps for event counts
_WINDOW_5M = 300
_WINDOW_30M = 1800

# Keys persisted to Redis when available (TTL: refresh 48h, cooldown 1h)
_CRITICAL_KEYS_REFRESH = ("last_successful_odds_refresh_at", "last_successful_games_refresh_at")
_CRITICAL_KEYS_COOLDOWN = ("safety_red_since", "safety_yellow_since")
_CRITICAL_KEYS_BUDGET = ("estimated_api_calls_today", "daily_api_budget")
_CRITICAL_KEYS = (*_CRITICAL_KEYS_REFRESH, *_CRITICAL_KEYS_COOLDOWN, *_CRITICAL_KEYS_BUDGET)
_TTL_REFRESH_SEC = 48 * 3600
_TTL_COOLDOWN_SEC = 3600
_TTL_BUDGET_SEC = 24 * 3600

_store: Dict[str, Any] = {}
_timestamps_5m: Dict[str, deque] = {}
_timestamps_30m: Dict[str, deque] = {}
_safety_events: List[Dict[str, Any]] = []
_lock = Lock()


def _now() -> float:
    return time.time()


def _prune(deq: deque, window_sec: float) -> None:
    cutoff = _now() - window_sec
    while deq and deq[0] < cutoff:
        deq.popleft()


def inc(metric: str, n: int = 1) -> None:
    """Increment a counter or add n events to a rolling window."""
    with _lock:
        if metric in ("error_count_5m", "generation_failures_5m"):
            key = metric
            if key not in _timestamps_5m:
                _timestamps_5m[key] = deque()
            for _ in range(n):
                _timestamps_5m[key].append(_now())
            _prune(_timestamps_5m[key], _WINDOW_5M)
        elif metric in ("not_enough_games_failures_30m", "api_429_count_30m", "api_failures_30m"):
            key = metric
            if key not in _timestamps_30m:
                _timestamps_30m[key] = deque()
            for _ in range(n):
                _timestamps_30m[key].append(_now())
            _prune(_timestamps_30m[key], _WINDOW_30M)
        else:
            _store[metric] = _store.get(metric, 0) + n


def set(metric: str, value: Any) -> None:
    """Set a value (e.g. last_successful_games_refresh_at)."""
    with _lock:
        _store[metric] = value


def get(metric: str, default: Any = None) -> Any:
    """Get current value or count in window."""
    with _lock:
        if metric in _timestamps_5m:
            _prune(_timestamps_5m[metric], _WINDOW_5M)
            return len(_timestamps_5m[metric])
        if metric in _timestamps_30m:
            _prune(_timestamps_30m[metric], _WINDOW_30M)
            return len(_timestamps_30m[metric])
        return _store.get(metric, default)


def get_snapshot() -> Dict[str, Any]:
    """Return a copy of current telemetry for admin/ops (no secrets)."""
    with _lock:
        out = {k: v for k, v in _store.items() if not k.startswith("_")}
        for k, deq in list(_timestamps_5m.items()):
            _prune(deq, _WINDOW_5M)
            out[k] = len(deq)
        for k, deq in list(_timestamps_30m.items()):
            _prune(deq, _WINDOW_30M)
            out[k] = len(deq)
    return out


def record_safety_event(from_state: str, to_state: str, reasons: List[str]) -> None:
    """Append a state transition to the ring buffer. Caller trims by buffer size when reading."""
    with _lock:
        _safety_events.append({
            "ts": _now(),
            "from_state": from_state,
            "to_state": to_state,
            "reasons": list(reasons) if reasons else [],
        })


def get_safety_events() -> List[Dict[str, Any]]:
    """Last N safety state transitions (newest last). N from config."""
    try:
        from app.core.config import settings
        size = int(getattr(settings, "safety_mode_event_buffer_size", 10) or 10)
    except Exception:
        size = 10
    with _lock:
        events = list(_safety_events)
    return events[-size:] if len(events) > size else events


async def load_critical_from_redis() -> None:
    """Merge critical keys from Redis into in-memory store (if Redis configured)."""
    try:
        from app.services.redis.redis_client_provider import get_redis_provider
        provider = get_redis_provider()
        if not provider.is_configured():
            return
        client = provider.get_client()
        prefix = "safety_telemetry:"
        for key in _CRITICAL_KEYS:
            val = await client.get(f"{prefix}{key}")
            if val is not None:
                try:
                    decoded = val.decode("utf-8") if isinstance(val, bytes) else val
                    try:
                        num = float(decoded)
                        use = int(num) if num == int(num) else num
                    except ValueError:
                        use = decoded
                    with _lock:
                        _store[key] = use
                except Exception:
                    pass
        # Load events ring buffer
        raw = await client.get(f"{prefix}events")
        if raw is not None:
            try:
                decoded = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                loaded = json.loads(decoded)
                if isinstance(loaded, list) and loaded:
                    with _lock:
                        _safety_events.clear()
                        _safety_events.extend(loaded)
            except Exception:
                pass
    except Exception:
        pass


async def save_critical_to_redis(snapshot: Dict[str, Any]) -> None:
    """Write critical telemetry keys to Redis with TTL (if configured)."""
    try:
        from app.services.redis.redis_client_provider import get_redis_provider
        provider = get_redis_provider()
        if not provider.is_configured():
            return
        client = provider.get_client()
        prefix = "safety_telemetry:"
        telemetry = snapshot.get("telemetry") if isinstance(snapshot.get("telemetry"), dict) else snapshot
        for key in _CRITICAL_KEYS:
            val = telemetry.get(key)
            if val is None:
                continue
            rkey = f"{prefix}{key}"
            str_val = str(val)
            payload = str_val.encode("utf-8") if isinstance(str_val, str) else str_val
            if key in _CRITICAL_KEYS_COOLDOWN:
                await client.set(rkey, payload, ex=_TTL_COOLDOWN_SEC)
            elif key in _CRITICAL_KEYS_BUDGET:
                await client.set(rkey, payload, ex=_TTL_BUDGET_SEC)
            else:
                await client.set(rkey, payload, ex=_TTL_REFRESH_SEC)
        events = get_safety_events()
        if events:
            await client.set(
                f"{prefix}events",
                json.dumps(events).encode("utf-8"),
                ex=_TTL_REFRESH_SEC,
            )
    except Exception:
        pass
