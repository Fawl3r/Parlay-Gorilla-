"""
Affiliate attribution service using cookies set by `/api/affiliates/click`.

Why:
- Visitors arrive with `?ref=CODE` and we record clicks + set httpOnly cookies:
  - pg_affiliate_ref
  - pg_affiliate_click
- During signup/login, we consume these cookies to attribute the user to an affiliate.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.affiliate_service import AffiliateService

logger = logging.getLogger(__name__)


class AffiliateCookieAttributionService:
    """Consumes referral cookies and attributes the authenticated user."""

    REF_COOKIE_KEY = "pg_affiliate_ref"
    CLICK_COOKIE_KEY = "pg_affiliate_click"

    def __init__(self, db: AsyncSession):
        self._db = db

    async def attribute_user_if_present(self, *, user: User, request: Request, response: Response) -> None:
        """
        Attribute the user to an affiliate if referral cookies are present.

        Always clears the cookies if they are present, to avoid repeated attempts.
        """
        referral_code = self._get_cookie(request, self.REF_COOKIE_KEY)
        click_id = self._get_cookie(request, self.CLICK_COOKIE_KEY)

        if not referral_code and not click_id:
            return

        try:
            if user.referred_by_affiliate_id:
                return

            if not referral_code:
                return

            service = AffiliateService(self._db)
            ok = await service.attribute_user_to_affiliate(
                user_id=str(user.id),
                referral_code=referral_code,
                click_id=click_id,
            )
            if ok:
                logger.info("Attributed user=%s to affiliate referral_code=%s", user.id, referral_code)
        except Exception as e:
            # Best-effort: never block auth flows.
            logger.warning("Affiliate cookie attribution failed for user=%s: %s", getattr(user, "id", None), e)
        finally:
            # Consume cookies (best-effort)
            self._delete_cookie(response, self.REF_COOKIE_KEY)
            self._delete_cookie(response, self.CLICK_COOKIE_KEY)

    def _get_cookie(self, request: Request, key: str) -> Optional[str]:
        value = request.cookies.get(key)
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    def _delete_cookie(self, response: Response, key: str) -> None:
        try:
            response.delete_cookie(key=key)
        except Exception:
            # Response may not support delete_cookie in certain edge cases; ignore.
            pass


