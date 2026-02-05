"""
Telegram notifier for operator alerts: dedupe TTL 10 min, rate limit 1 msg/10 sec.
No-op if TELEGRAM_ALERTS_ENABLED=false or missing config.

Env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID only (not TELEGRAM_DEFAULT_CHAT_ID).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.redis.redis_client_provider import get_redis_provider

logger = logging.getLogger(__name__)

DEDUPE_TTL_SECONDS = 600
RATE_LIMIT_INTERVAL_SECONDS = 10
BASE_URL = "https://api.telegram.org/bot"


class TelegramNotifier:
    """
    Send operator alerts to Telegram.
    - send(text)
    - send_event(event, severity, payload)
    Dedupe 10 min (Redis or in-memory); rate limit 1 msg/10 sec.
    """

    def __init__(
        self,
        *,
        enabled: Optional[bool] = None,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        # Operator alerts use TELEGRAM_CHAT_ID only (not TELEGRAM_DEFAULT_CHAT_ID)
        self._enabled = (
            (enabled if enabled is not None else getattr(settings, "telegram_alerts_enabled", False))
            and (bot_token or getattr(settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN"))
            and (chat_id or getattr(settings, "telegram_chat_id", None) or os.getenv("TELEGRAM_CHAT_ID"))
        )
        self._bot_token = (bot_token or getattr(settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()
        self._chat_id = (chat_id or getattr(settings, "telegram_chat_id", None) or os.getenv("TELEGRAM_CHAT_ID") or "").strip()
        self._redis = get_redis_provider()
        self._last_sent: float = 0.0
        self._seen_keys: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _dedupe_key(self, event: str, payload: Dict[str, Any]) -> str:
        h = hashlib.sha256()
        h.update(event.encode())
        for k in sorted(payload.keys()):
            v = payload.get(k)
            if v is not None:
                h.update(f"{k}:{v}".encode())
        return h.hexdigest()[:32]

    async def _should_skip_dedupe(self, key: str) -> bool:
        """Return True if we should send (not a duplicate)."""
        now = time.time()
        if self._redis.is_configured():
            try:
                client = self._redis.get_client()
                redis_key = f"alerting:dedupe:{key}"
                if await client.get(redis_key):
                    return False
                await client.set(redis_key, "1", ex=DEDUPE_TTL_SECONDS)
                return True
            except Exception as e:
                logger.warning("TelegramNotifier Redis dedupe failed: %s", e)
                await self._emit_redis_dedupe_fail_open(e)
        if self._seen_keys.get(key, 0) + DEDUPE_TTL_SECONDS > now:
            return False
        self._seen_keys[key] = now
        return True

    async def _emit_redis_dedupe_fail_open(self, err: Exception) -> None:
        """Send one-off alert that Redis dedupe failed (fail-open to in-memory). No dedupe/rate limit to avoid recursion."""
        if not self._enabled or not self._bot_token or not self._chat_id:
            return
        try:
            from app.core.config import settings
            env = getattr(settings, "environment", "unknown")
            text = f"<b>redis.dedupe_fail_open</b>\nSeverity: warning\nenvironment: {env}\nerror: {str(err)[:300]}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{BASE_URL}{self._bot_token}/sendMessage"
                await client.post(url, json={"chat_id": self._chat_id, "text": text[:4096], "parse_mode": "HTML"})
        except Exception as send_err:
            logger.debug("redis.dedupe_fail_open send failed: %s", send_err)

    async def _rate_limit(self) -> bool:
        """Return True if we may send (rate limit passed)."""
        async with self._lock:
            now = time.time()
            if now - self._last_sent < RATE_LIMIT_INTERVAL_SECONDS:
                return False
            self._last_sent = now
            return True

    async def send(self, text: str) -> bool:
        """Send a plain text message. Respects enabled, dedupe, rate limit."""
        if not self._enabled or not text:
            return False
        if not await self._rate_limit():
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"{BASE_URL}{self._bot_token}/sendMessage"
                resp = await client.post(
                    url,
                    json={"chat_id": self._chat_id, "text": text[:4096], "parse_mode": "HTML"},
                )
                if resp.status_code != 200:
                    logger.warning("TelegramNotifier send failed: %s %s", resp.status_code, resp.text[:200])
                    return False
                return True
        except Exception as e:
            logger.warning("TelegramNotifier send error: %s", e)
            return False

    async def send_event(
        self,
        event: str,
        severity: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Format event + severity + payload and send (with dedupe)."""
        if not self._enabled:
            return False
        key = self._dedupe_key(event, payload)
        if not await self._should_skip_dedupe(key):
            return False
        if not await self._rate_limit():
            return False
        parts = [f"<b>{event}</b>", f"Severity: {severity}"]
        for k, v in (payload or {}).items():
            if v is not None and k != "event":
                parts.append(f"{k}: {v}")
        text = "\n".join(parts)[:4096]
        return await self.send(text)
