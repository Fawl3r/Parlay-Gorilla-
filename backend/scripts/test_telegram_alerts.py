"""
Test script to verify Telegram alerts are fully working.

Uses TELEGRAM_ALERTS_ENABLED, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID from .env or environment.
Run from backend directory:

    cd backend
    python scripts/test_telegram_alerts.py

Or with explicit env (no .env):
    TELEGRAM_ALERTS_ENABLED=true TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python scripts/test_telegram_alerts.py
"""

from __future__ import annotations

import asyncio
import os
import sys

# Add backend root so "app" resolves
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main() -> int:
    print("=" * 60)
    print("Telegram Alerts Test")
    print("=" * 60)

    # Load config (reads .env via pydantic-settings when app is imported)
    try:
        from app.core.config import settings
    except Exception as e:
        print(f"\nConfig load failed: {e}")
        print("Run from backend directory: cd backend && python scripts/test_telegram_alerts.py")
        return 1

    enabled = getattr(settings, "telegram_alerts_enabled", False)
    token = (
        getattr(settings, "telegram_bot_token", None)
        or os.getenv("TELEGRAM_BOT_TOKEN")
        or ""
    ).strip()
    chat_id = (
        getattr(settings, "telegram_chat_id", None)
        or os.getenv("TELEGRAM_CHAT_ID")
        or ""
    ).strip()

    print(f"\nConfig:")
    print(f"  TELEGRAM_ALERTS_ENABLED: {enabled}")
    print(f"  TELEGRAM_BOT_TOKEN set:  {bool(token)} ({'first 8 chars: ' + token[:8] + '...' if token else 'missing'})")
    print(f"  TELEGRAM_CHAT_ID set:     {bool(chat_id)} (value: {chat_id[:20] + '...' if len(chat_id or '') > 20 else chat_id or 'missing'})")

    if not token or not chat_id:
        print("\nTelegram alerts are disabled or misconfigured.")
        print("Set in backend .env or Render:")
        print("  TELEGRAM_ALERTS_ENABLED=true")
        print("  TELEGRAM_BOT_TOKEN=<from @BotFather>")
        print("  TELEGRAM_CHAT_ID=<your chat id>")
        return 1

    if not enabled:
        print("\nTELEGRAM_ALERTS_ENABLED is false. Set to true to enable alerts.")
        return 1

    # Test 1: Plain send (direct notifier)
    print("\n--- Test 1: Plain message ---")
    try:
        from app.services.alerting.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier()
        text = "Parlay Gorilla alert test – if you see this, Telegram alerts are working."
        ok = await notifier.send(text)
        if ok:
            print("  OK: Plain message sent. Check your Telegram chat.")
        else:
            print("  FAIL: send() returned False (check rate limit 1 msg/10s or Telegram API).")
            return 1
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    # Test 2: AlertingService.send_event (full pipeline: sanitize + spike + send_event)
    print("\n--- Test 2: Event (AlertingService) ---")
    await asyncio.sleep(11)  # notifier rate limit is 1 msg/10 sec
    try:
        from app.services.alerting import get_alerting_service

        alerting = get_alerting_service()
        ok = await alerting.emit(
            "telegram.test_event",
            "info",
            {
                "environment": getattr(settings, "environment", "unknown"),
                "message": "Full pipeline test – event + severity + payload.",
            },
        )
        if ok:
            print("  OK: Event sent via AlertingService. Check your Telegram chat.")
        else:
            print("  FAIL: emit() returned False (dedupe or rate limit).")
            return 1
    except Exception as e:
        print(f"  FAIL: {e}")
        return 1

    print("\n" + "=" * 60)
    print("All Telegram alert tests passed.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
