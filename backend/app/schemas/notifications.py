from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WebPushSubscriptionKeys(BaseModel):
    p256dh: str = Field(..., min_length=1, max_length=255)
    auth: str = Field(..., min_length=1, max_length=255)


class WebPushSubscribeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    endpoint: str = Field(..., min_length=10, max_length=4000)
    keys: WebPushSubscriptionKeys
    expiration_time: Optional[float] = Field(default=None, alias="expirationTime")


class WebPushUnsubscribeRequest(BaseModel):
    endpoint: str = Field(..., min_length=10, max_length=4000)


class WebPushVapidPublicKeyResponse(BaseModel):
    enabled: bool
    public_key: str


class WebPushSubscribeResponse(BaseModel):
    success: bool
    subscription_id: str


class WebPushUnsubscribeResponse(BaseModel):
    success: bool
    deleted: int


