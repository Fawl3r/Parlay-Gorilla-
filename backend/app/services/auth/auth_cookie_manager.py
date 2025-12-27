"""HTTP cookie management for auth tokens (hybrid cookie + bearer support)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Response

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class AuthCookieManager:
    """Sets/clears the access token cookie in a consistent way."""

    cookie_name: str = "access_token"

    def set_access_token_cookie(self, response: Response, token: str) -> None:
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            httponly=True,
            secure=settings.is_production,
            samesite="lax",
            path="/",
        )

    def clear_access_token_cookie(self, response: Response) -> None:
        response.delete_cookie(key=self.cookie_name, path="/")


