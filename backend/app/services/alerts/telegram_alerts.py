"""
Minimal Telegram alert helper for deploy failure and job staleness.
Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (or TELEGRAM_ALERT_CHAT_ID). No-op if unset.
Timeout 5s; never crashes the caller; never logs or echoes tokens.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_TIMEOUT = 5.0
_BASE = "https://api.telegram.org/bot"


def send_telegram_alert(message: str) -> None:
    """
    Send a plain text message to Telegram. Sync wrapper; runs async send.
    No-op if TELEGRAM_BOT_TOKEN or chat ID not set. Never raises; never logs secrets.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            asyncio.create_task(_send_async(message))
        else:
            asyncio.run(_send_async(message))
    except Exception as e:
        logger.debug("telegram_alert send skipped: %s", e)


async def send_telegram_alert_async(message: str) -> bool:
    """
    Async version: send message to Telegram. Returns True if sent, False otherwise.
    No-op if token or chat_id unset. Timeout 5s; never raises.
    """
    return await _send_async(message)


async def _send_async(message: str) -> bool:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = (
        (os.environ.get("TELEGRAM_ALERT_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()
    )
    if not token or not chat_id or not message:
        return False
    try:
        import httpx
        url = f"{_BASE}{token}/sendMessage"
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(
                url,
                json={"chat_id": chat_id, "text": message[:4096], "parse_mode": "HTML"},
            )
            if r.status_code != 200:
                logger.warning("Telegram alert send failed: %s", r.status_code)
                return False
            return True
    except asyncio.TimeoutError:
        logger.debug("Telegram alert timeout")
        return False
    except Exception as e:
        logger.debug("Telegram alert error: %s", e)
        return False
