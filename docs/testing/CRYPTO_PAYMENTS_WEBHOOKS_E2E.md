# Crypto Payments + Webhooks (Coinbase Commerce) — E2E Test Checklist

**⚠️ DEPRECATED — DISABLED FOR LEMONSQUEEZY COMPLIANCE**

Crypto payments have been disabled to ensure LemonSqueezy approval. This document is kept for reference only. Do not re-enable without compliance review.

---

This checklist verifies the **crypto payment flow** and **Coinbase Commerce webhooks** end-to-end, including signature verification, idempotency, and correct DB/UI state.

## Prerequisites

- **Backend reachable via HTTPS** (Coinbase requires HTTPS webhook targets).
  - Production: `https://api.parlaygorilla.com`
  - Local dev: expose `http://localhost:8000` via a tunnel (ngrok / Cloudflare Tunnel / LocalTunnel).
- **Environment variables set** (backend):
  - `COINBASE_COMMERCE_API_KEY`
  - `COINBASE_COMMERCE_WEBHOOK_SECRET`
  - `APP_URL` (used for redirect URLs)
  - `BACKEND_URL` (used in docs/scripts)
- **Webhook configured in Coinbase Commerce dashboard**
  - URL: `{BACKEND_URL}/api/webhooks/coinbase`
  - Events: `charge:confirmed` (required), `charge:failed` (recommended), `charge:pending` (optional)

Reference:
- `WEBHOOK_URLS_PRODUCTION.md`
- `COINBASE_COMMERCE_WEBHOOK_SETUP.md`

## What “good” looks like

- Coinbase deliveries show **200 OK** for webhook POSTs.
- Backend logs show webhook receipt + processing (no crashes).
- DB shows:
  - A `payment_events` row for each webhook event.
  - For `charge:confirmed`:
    - Subscription purchases create/update `subscriptions` + sync `users.subscription_*`.
    - Credit pack purchases create exactly one `credit_pack_purchases` row and increment `users.credit_balance` exactly once.
- **Idempotency works**:
  - Resending the same event does not double-apply fulfillment.
  - Provider-order idempotency prevents double credit award / double subscription creation.

## Automated safety net (recommended before manual E2E)

Run:

```bash
cd backend
pytest -q
```

This includes signature enforcement tests in `backend/tests/test_webhook_signature_verification.py`.

## Manual E2E Scenarios

### Scenario A — Crypto subscription checkout → webhook → active access

1. In the UI, start a crypto subscription checkout (Coinbase provider).
2. Complete the payment in Coinbase (test mode if available).
3. Confirm Coinbase webhook deliveries show 200.
4. Verify backend state:
   - `payment_events` contains the webhook event (provider=`coinbase`, event_type=`charge:confirmed`)
   - `subscriptions` contains a new row with:
     - `provider='coinbase'`
     - `provider_subscription_id` = Coinbase `charge_id`
   - `users` row has updated:
     - `subscription_status` (active)
     - `subscription_plan` (plan_code)

### Scenario B — Crypto credit pack checkout → webhook → credits awarded once

1. In the UI, buy a credit pack with crypto (Coinbase).
2. Complete payment.
3. Verify:
   - UI balance increases (Billing page / Access status).
   - DB:
     - `credit_pack_purchases` has exactly one row for `(provider='coinbase', provider_order_id=<charge_id>)`.
     - `users.credit_balance` increased by pack credits.

### Scenario C — Crypto one-time parlay purchase → webhook → purchase available

1. In the UI, buy a one-time parlay purchase using crypto (Coinbase).
2. Complete payment.
3. Verify:
   - The user has an available one-time purchase (expires after configured window).
   - DB:
     - `parlay_purchases` has a record for the user that transitions to `available`.

### Scenario D — Webhook signature enforcement (security)

Goal: Ensure webhook requests without a valid signature are rejected **when** `COINBASE_COMMERCE_WEBHOOK_SECRET` is set.

1. Send a webhook request **without** `X-CC-Webhook-Signature`.
2. Expect **401**.
3. Send the same payload **with** a valid signature.
4. Expect **200**.

Tip: If you’re testing in the real dashboard, the dashboard should always send the signature header. This scenario is most useful with manual `curl` or a small script.

### Scenario E — Duplicate delivery / resend (idempotency)

1. In Coinbase dashboard, resend the same `charge:confirmed` webhook delivery.
2. Verify:
   - Response is still 200.
   - No double credits / no duplicate subscription.
   - `payment_events` does not create a second row with the same `event_id`.

## Troubleshooting quick hits

- **401 Invalid signature**:
  - Confirm `COINBASE_COMMERCE_WEBHOOK_SECRET` exactly matches the Coinbase dashboard secret (no whitespace/newlines).
  - Confirm you’re signing the **raw request body bytes**.
- **200 OK but nothing changed**:
  - Inspect `payment_events.processed` + `processing_error` and backend logs.
  - Verify webhook payload includes expected `metadata`:
    - `user_id`
    - and one of: `plan_code` / `credit_pack_id` / `purchase_type`


