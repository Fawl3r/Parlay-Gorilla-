from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.promo_code import PromoRewardType


class PromoCodeCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reward_type: PromoRewardType
    expires_at: datetime
    max_uses_total: int = Field(default=1, ge=1, le=100_000)
    code: Optional[str] = Field(default=None, min_length=4, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("expires_at")
    @classmethod
    def _validate_expires_at(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("expires_at must include timezone (e.g., 2026-01-01T00:00:00Z)")
        return v

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        value = v.strip().upper()
        if not value:
            return None
        if any(ch.isspace() for ch in value):
            raise ValueError("code cannot contain spaces")
        return value


class PromoCodeBulkCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    count: int = Field(default=10, ge=1, le=500)
    reward_type: PromoRewardType
    expires_at: datetime
    max_uses_total: int = Field(default=1, ge=1, le=100_000)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("expires_at")
    @classmethod
    def _validate_expires_at(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("expires_at must include timezone (e.g., 2026-01-01T00:00:00Z)")
        return v


class PromoCodeResponse(BaseModel):
    id: str
    code: str
    reward_type: PromoRewardType
    expires_at: str
    max_uses_total: int
    redeemed_count: int
    is_active: bool
    deactivated_at: Optional[str] = None
    created_at: str


class PromoCodeListResponse(BaseModel):
    codes: list[PromoCodeResponse]
    total: int
    page: int
    page_size: int


class PromoCodeRedeemRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=64)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, v: str) -> str:
        value = (v or "").strip().upper()
        if not value:
            raise ValueError("code is required")
        if any(ch.isspace() for ch in value):
            raise ValueError("code cannot contain spaces")
        return value


class PromoCodeRedeemResponse(BaseModel):
    success: bool
    reward_type: PromoRewardType
    message: str
    credits_added: int = 0
    new_credit_balance: Optional[int] = None
    premium_until: Optional[str] = None


