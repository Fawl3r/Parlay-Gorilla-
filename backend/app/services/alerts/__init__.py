"""Lightweight ops/deploy alerts (Telegram). No-op if env not set."""

from app.services.alerts.telegram_alerts import send_telegram_alert

__all__ = ["send_telegram_alert"]
