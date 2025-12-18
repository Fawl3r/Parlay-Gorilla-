"""Web Push notification subscription endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.schemas.notifications import (
    WebPushSubscribeRequest,
    WebPushSubscribeResponse,
    WebPushUnsubscribeRequest,
    WebPushUnsubscribeResponse,
    WebPushVapidPublicKeyResponse,
)
from app.services.notifications.push_subscription_repository import PushSubscriptionRepository

router = APIRouter()


def _parse_expiration_time(value: Optional[float]) -> Optional[datetime]:
    """
    Parse PushSubscription.expirationTime (ms since epoch) to a UTC datetime.

    Some clients may send seconds; treat large values as milliseconds.
    """
    if value is None:
        return None
    try:
        ts = float(value)
    except Exception:
        return None
    # Heuristic: >= 10^12 is almost certainly milliseconds.
    if ts >= 1_000_000_000_000:
        ts = ts / 1000.0
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


@router.get(
    "/notifications/push/vapid-public-key",
    response_model=WebPushVapidPublicKeyResponse,
    summary="Get VAPID public key for Web Push",
)
async def get_vapid_public_key() -> WebPushVapidPublicKeyResponse:
    public_key = (getattr(settings, "web_push_vapid_public_key", "") or "").strip()
    enabled = bool(getattr(settings, "web_push_enabled", False)) and bool(public_key)
    return WebPushVapidPublicKeyResponse(enabled=enabled, public_key=public_key if enabled else "")


@router.post(
    "/notifications/push/subscribe",
    response_model=WebPushSubscribeResponse,
    summary="Subscribe browser for Web Push notifications",
)
async def subscribe_web_push(
    payload: WebPushSubscribeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> WebPushSubscribeResponse:
    if not getattr(settings, "web_push_enabled", False):
        raise HTTPException(status_code=404, detail="Web Push is not enabled")

    endpoint = (payload.endpoint or "").strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")

    keys = payload.keys
    p256dh = (keys.p256dh or "").strip()
    auth = (keys.auth or "").strip()
    if not p256dh or not auth:
        raise HTTPException(status_code=400, detail="Missing subscription keys")

    user_agent = (request.headers.get("user-agent") or "").strip() or None
    expiration_time = _parse_expiration_time(payload.expiration_time)

    repo = PushSubscriptionRepository(db)
    sub = await repo.upsert(
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        expiration_time=expiration_time,
        user_agent=user_agent,
    )
    return WebPushSubscribeResponse(success=True, subscription_id=str(sub.id))


@router.post(
    "/notifications/push/unsubscribe",
    response_model=WebPushUnsubscribeResponse,
    summary="Unsubscribe browser from Web Push notifications",
)
async def unsubscribe_web_push(
    payload: WebPushUnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> WebPushUnsubscribeResponse:
    endpoint = (payload.endpoint or "").strip()
    if not endpoint:
        raise HTTPException(status_code=400, detail="Missing endpoint")

    repo = PushSubscriptionRepository(db)
    deleted = await repo.delete_by_endpoint(endpoint=endpoint)
    return WebPushUnsubscribeResponse(success=True, deleted=deleted)


