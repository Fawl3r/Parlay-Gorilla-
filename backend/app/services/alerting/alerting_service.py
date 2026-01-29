"""
Alerting service: emit(event, severity, payload), spike detection, payload sanitizer.
Wires to TelegramNotifier; dedupe and rate limit are handled there.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.services.alerting.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

SPIKE_WINDOW_SECONDS = 600
SPIKE_THRESHOLD = 3
MAX_PAYLOAD_LIST_SAMPLE = 3
STACK_TRACE_LINE_LIMIT = 25

_alerting_service: Optional["AlertingService"] = None


def _sanitize_value(value: Any, key: str) -> Any:
    """Trim large values; sample lists (e.g. candidates) to max N items."""
    if value is None:
        return None
    if isinstance(value, str):
        if key in ("stack_trace", "message") and len(value) > 2000:
            return value[:2000] + "..."
        if len(value) > 500:
            return value[:500] + "..."
        return value
    if isinstance(value, list):
        if key == "candidates" or "candidate" in key.lower():
            return value[:MAX_PAYLOAD_LIST_SAMPLE]
        if len(value) > MAX_PAYLOAD_LIST_SAMPLE:
            return value[:MAX_PAYLOAD_LIST_SAMPLE] + [f"...+{len(value) - MAX_PAYLOAD_LIST_SAMPLE} more"]
        return value
    if isinstance(value, dict):
        return {k: _sanitize_value(v, k) for k, v in value.items()}
    return value


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Trim large fields; candidates sample max 3."""
    if not payload:
        return {}
    return {k: _sanitize_value(v, k) for k, v in payload.items()}


def trim_stack_trace(tb: str, max_lines: int = STACK_TRACE_LINE_LIMIT) -> str:
    """Keep top max_lines of stack trace."""
    if not tb or not tb.strip():
        return tb or ""
    lines = tb.strip().split("\n")
    if len(lines) <= max_lines:
        return tb
    return "\n".join(lines[:max_lines]) + "\n... (trimmed)"


class AlertingService:
    """
    Central alerting: emit(event, severity, payload, next_actions).
    Spike detector: per (event, sport) >= 3 in 10 min -> skip send.
    Payload sanitizer applied before sending.
    """

    def __init__(self, notifier: Optional[TelegramNotifier] = None):
        self._notifier = notifier or TelegramNotifier()
        self._spike_counts: Dict[str, List[float]] = defaultdict(list)
        self._spike_lock = asyncio.Lock()

    async def _is_spike(self, event: str, sport: Optional[str]) -> bool:
        """True if (event, sport) has >= SPIKE_THRESHOLD occurrences in SPIKE_WINDOW_SECONDS."""
        key = f"{event}:{sport or 'default'}"
        now = time.time()
        async with self._spike_lock:
            self._spike_counts[key] = [t for t in self._spike_counts[key] if now - t < SPIKE_WINDOW_SECONDS]
            self._spike_counts[key].append(now)
            return len(self._spike_counts[key]) >= SPIKE_THRESHOLD

    async def emit(
        self,
        event: str,
        severity: str,
        payload: Dict[str, Any],
        next_actions: Optional[List[str]] = None,
        next_action_hint: Optional[str] = None,
        sport: Optional[str] = None,
    ) -> bool:
        """
        Emit an alert. Sanitizes payload, checks spike, then sends via TelegramNotifier.
        Returns True if sent, False if skipped (spike, disabled, etc.).
        """
        payload = dict(payload or {})
        if sport is not None:
            payload["sport"] = sport
        if next_action_hint:
            payload["next_action_hint"] = next_action_hint
        if next_actions:
            payload["next_actions"] = next_actions
        payload = sanitize_payload(payload)

        if await self._is_spike(event, sport):
            logger.debug("AlertingService spike suppressed: %s", event)
            return False

        full_payload = dict(payload)
        return await self._notifier.send_event(event, severity, full_payload)


def get_alerting_service() -> AlertingService:
    """Return singleton AlertingService."""
    global _alerting_service
    if _alerting_service is None:
        _alerting_service = AlertingService()
    return _alerting_service
