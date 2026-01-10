"""
Stripe reconciliation service.

Purpose:
- Provide a webhook-fallback path to grant subscriptions / credit packs by
  fetching the latest Stripe Checkout Session(s) for a user and applying the
  same fulfillment logic as our webhook handlers.

Why:
- If webhooks are delayed/missed (common in test mode misconfig), users can pay
  successfully but not receive access/credits. This service allows the app to
  self-heal by reconciling from Stripe on-demand.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Literal, Optional

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.webhooks.shared_handlers import _handle_credit_pack_purchase, _handle_parlay_purchase_confirmed
from app.api.routes.webhooks.stripe_webhook_routes import _handle_lifetime_subscription_purchase
from app.core.config import settings
from app.models.user import User
from app.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

StripeReconcileStatus = Literal["applied", "pending", "skipped", "error"]


@dataclass(frozen=True)
class StripeReconcileResult:
    status: StripeReconcileStatus
    message: str
    session_id: str | None = None
    mode: str | None = None
    purchase_type: str | None = None
    subscription_id: str | None = None


class StripeReconciliationService:
    """Webhook-fallback reconciler for Stripe purchases."""

    def __init__(self, db: AsyncSession):
        self._db = db
        self._stripe_service = StripeService(db)

        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    async def reconcile_session_for_user(self, *, user: User, session_id: str) -> StripeReconcileResult:
        if not settings.stripe_secret_key:
            return StripeReconcileResult(status="error", message="Stripe not configured")

        session_id = (session_id or "").strip()
        if not session_id:
            return StripeReconcileResult(status="error", message="session_id is required")

        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except Exception as exc:
            logger.warning("Stripe reconcile: failed to retrieve session %s: %s", session_id, exc)
            return StripeReconcileResult(status="error", message="Unable to retrieve checkout session", session_id=session_id)

        return await self._apply_session(user=user, session=self._to_dict(session))

    async def reconcile_latest_for_user(self, *, user: User, limit: int = 10) -> StripeReconcileResult:
        if not settings.stripe_secret_key:
            return StripeReconcileResult(status="error", message="Stripe not configured")

        customer_id = (getattr(user, "stripe_customer_id", None) or "").strip()
        if not customer_id:
            return StripeReconcileResult(status="error", message="No Stripe customer on file for this user")

        try:
            sessions = stripe.checkout.Session.list(customer=customer_id, limit=max(1, min(int(limit or 10), 25)))
        except Exception as exc:
            logger.warning("Stripe reconcile: failed to list sessions for customer %s: %s", customer_id, exc)
            return StripeReconcileResult(status="error", message="Unable to list checkout sessions")

        data = self._to_dict(sessions).get("data") or []
        if not data:
            return StripeReconcileResult(status="pending", message="No checkout sessions found for this customer")

        # Stripe returns newest first. Pick the most recent complete+paid session owned by this user.
        for raw in data:
            session = self._to_dict(raw)
            if not self._is_session_owned_by_user(user=user, session=session):
                continue

            status = (session.get("status") or "").lower()
            payment_status = (session.get("payment_status") or "").lower()
            if status != "complete":
                continue
            if payment_status not in {"paid", "no_payment_required"}:
                continue

            return await self._apply_session(user=user, session=session)

        return StripeReconcileResult(
            status="pending",
            message="No completed paid checkout session found for this user yet",
        )

    async def _apply_session(self, *, user: User, session: dict[str, Any]) -> StripeReconcileResult:
        session_id = str(session.get("id") or "").strip() or None
        mode = str(session.get("mode") or "").strip() or None
        metadata = session.get("metadata") or {}
        purchase_type = str(metadata.get("purchase_type") or "").strip().lower() or None

        if not session_id:
            return StripeReconcileResult(status="error", message="Checkout session missing id")

        if not self._is_session_owned_by_user(user=user, session=session):
            return StripeReconcileResult(status="skipped", message="Checkout session does not belong to this user", session_id=session_id)

        if mode == "subscription":
            subscription_id = session.get("subscription")
            if isinstance(subscription_id, dict):
                subscription_id = subscription_id.get("id")
            subscription_id = str(subscription_id or "").strip() or None

            if not subscription_id:
                return StripeReconcileResult(
                    status="pending",
                    message="Subscription not created yet for this checkout session",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                )

            try:
                subscription = stripe.Subscription.retrieve(subscription_id)
            except Exception as exc:
                logger.warning("Stripe reconcile: failed to retrieve subscription %s: %s", subscription_id, exc)
                return StripeReconcileResult(
                    status="error",
                    message="Unable to retrieve subscription from Stripe",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                    subscription_id=subscription_id,
                )

            subscription_dict = self._to_dict(subscription)
            sub_status = str(subscription_dict.get("status") or "").strip().lower()

            # If active/trialing, force a full activation upsert.
            if sub_status in {"active", "trialing"}:
                await self._stripe_service._handle_subscription_created(subscription_dict)  # pylint: disable=protected-access
                return StripeReconcileResult(
                    status="applied",
                    message="Subscription activated",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                    subscription_id=subscription_id,
                )

            # Otherwise, update (best-effort) and report pending.
            await self._stripe_service._handle_subscription_updated(subscription_dict)  # pylint: disable=protected-access
            return StripeReconcileResult(
                status="pending",
                message=f"Subscription status is '{sub_status}', waiting for activation",
                session_id=session_id,
                mode=mode,
                purchase_type=purchase_type,
                subscription_id=subscription_id,
            )

        if mode == "payment":
            payment_status = str(session.get("payment_status") or "").strip().lower()
            if payment_status not in {"paid", "no_payment_required"}:
                return StripeReconcileResult(
                    status="pending",
                    message=f"Payment status is '{payment_status}', waiting for payment confirmation",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                )

            user_id = str((metadata or {}).get("user_id") or "").strip()

            if purchase_type == "credit_pack":
                credit_pack_id = str((metadata or {}).get("credit_pack_id") or "").strip()
                if not user_id or not credit_pack_id:
                    return StripeReconcileResult(
                        status="error",
                        message="Missing required metadata for credit pack fulfillment",
                        session_id=session_id,
                        mode=mode,
                        purchase_type=purchase_type,
                    )

                await _handle_credit_pack_purchase(
                    db=self._db,
                    user_id=user_id,
                    credit_pack_id=credit_pack_id,
                    sale_id=session_id,
                    provider="stripe",
                )
                await self._db.commit()
                return StripeReconcileResult(
                    status="applied",
                    message="Credits granted",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                )

            if purchase_type == "parlay_one_time":
                parlay_type = str((metadata or {}).get("parlay_type") or "single").strip()
                if not user_id:
                    return StripeReconcileResult(
                        status="error",
                        message="Missing user_id for parlay fulfillment",
                        session_id=session_id,
                        mode=mode,
                        purchase_type=purchase_type,
                    )

                await _handle_parlay_purchase_confirmed(
                    db=self._db,
                    user_id=user_id,
                    parlay_type=parlay_type,
                    provider="stripe",
                    payload=session,
                )
                await self._db.commit()
                return StripeReconcileResult(
                    status="applied",
                    message="Parlay purchase granted",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                )

            if purchase_type == "lifetime_subscription":
                plan_code = str((metadata or {}).get("plan_code") or "PG_LIFETIME_CARD").strip()
                if not user_id:
                    return StripeReconcileResult(
                        status="error",
                        message="Missing user_id for lifetime subscription fulfillment",
                        session_id=session_id,
                        mode=mode,
                        purchase_type=purchase_type,
                    )

                await _handle_lifetime_subscription_purchase(
                    db=self._db,
                    user_id=user_id,
                    plan_code=plan_code,
                    session_id=session_id,
                    stripe_service=self._stripe_service,
                )
                return StripeReconcileResult(
                    status="applied",
                    message="Lifetime subscription granted",
                    session_id=session_id,
                    mode=mode,
                    purchase_type=purchase_type,
                )

            return StripeReconcileResult(
                status="skipped",
                message="No fulfillable purchase_type found for this checkout session",
                session_id=session_id,
                mode=mode,
                purchase_type=purchase_type,
            )

        return StripeReconcileResult(
            status="skipped",
            message=f"Unsupported checkout session mode '{mode}'",
            session_id=session_id,
            mode=mode,
            purchase_type=purchase_type,
        )

    @staticmethod
    def _is_session_owned_by_user(*, user: User, session: dict[str, Any]) -> bool:
        metadata = session.get("metadata") or {}
        session_user_id = str(metadata.get("user_id") or "").strip()
        if session_user_id and session_user_id == str(user.id):
            return True

        # Fallback: match by Stripe customer id (best effort).
        customer_id = str(session.get("customer") or "").strip()
        user_customer_id = str(getattr(user, "stripe_customer_id", None) or "").strip()
        return bool(customer_id and user_customer_id and customer_id == user_customer_id)

    @staticmethod
    def _to_dict(obj: Any) -> dict[str, Any]:
        try:
            # Stripe objects behave like dict, but may include nested StripeObject types.
            return dict(obj or {})
        except Exception:
            return obj if isinstance(obj, dict) else {}


