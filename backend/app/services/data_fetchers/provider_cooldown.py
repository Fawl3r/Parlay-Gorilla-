"""
Shared cooldown manager for external data providers.

We use this to avoid spamming upstream APIs (and our logs) when a provider
responds with rate limits (429) or quota/forbidden (403).

This is intentionally process-local (in-memory). In production, we may want a
Redis-backed variant so multiple instances share cooldown state.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class _CooldownState:
    until_epoch_seconds: float
    reason: str
    last_log_epoch_seconds: float = 0.0


class ProviderCooldownManager:
    """Tracks provider cooldown windows keyed by provider name."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._states: Dict[str, _CooldownState] = {}

    def start(self, *, key: str, seconds: float, reason: str) -> None:
        now = time.time()
        until = now + max(0.0, float(seconds))
        with self._lock:
            existing = self._states.get(key)
            # Keep the longer cooldown if one is already active.
            if existing and existing.until_epoch_seconds > until:
                return
            self._states[key] = _CooldownState(until_epoch_seconds=until, reason=str(reason or "unknown"))

    def is_active(self, *, key: str) -> bool:
        now = time.time()
        with self._lock:
            state = self._states.get(key)
            if not state:
                return False
            if now >= state.until_epoch_seconds:
                self._states.pop(key, None)
                return False
            return True

    def remaining_seconds(self, *, key: str) -> float:
        now = time.time()
        with self._lock:
            state = self._states.get(key)
            if not state:
                return 0.0
            return max(0.0, state.until_epoch_seconds - now)

    def reason(self, *, key: str) -> Optional[str]:
        with self._lock:
            state = self._states.get(key)
            return state.reason if state else None

    def should_log(self, *, key: str, min_interval_seconds: float = 300.0) -> bool:
        """
        Rate-limit logs for a given provider.

        Returns True if we should log now, otherwise False.
        """
        now = time.time()
        with self._lock:
            state = self._states.get(key)
            if not state:
                return False
            if now - state.last_log_epoch_seconds >= float(min_interval_seconds):
                state.last_log_epoch_seconds = now
                self._states[key] = state
                return True
            return False


# Shared singleton for process-local cooldowns.
provider_cooldowns = ProviderCooldownManager()


