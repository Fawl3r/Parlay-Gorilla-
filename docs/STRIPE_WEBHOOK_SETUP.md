# Stripe Webhook Setup Guide

This guide explains how to configure Stripe webhooks for Parlay Gorilla.

## Overview

Stripe webhooks notify Parlay Gorilla when subscription events occur (created, updated, deleted, payment succeeded/failed). The backend processes these events to keep user subscription state in sync.

## Webhook Endpoint

**Production:** `https://api.parlaygorilla.com/api/webhooks/stripe`

**Development:** Use a tool like [ngrok](https://ngrok.com/) or [Stripe CLI](https://stripe.com/docs/stripe-cli) to expose your local server.

## Required Events

Configure your Stripe webhook to send these events:

- `checkout.session.completed` - Checkout completed (subscription or one-time payment)
- `customer.subscription.created` - New subscription activated
- `customer.subscription.updated` - Subscription renewed or changed
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.paid` - Recurring payment succeeded (renewal)
- `invoice.payment_failed` - Recurring payment failed

## Setup Steps

### 1. Create Webhook in Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks)
2. Click "Add endpoint"
3. Enter your webhook URL: `https://api.parlaygorilla.com/api/webhooks/stripe`
4. Select the events listed above
5. Click "Add endpoint"

### 2. Get Webhook Signing Secret

1. After creating the webhook, click on it
2. Copy the "Signing secret" (starts with `whsec_`)
3. Add it to your environment variables as `STRIPE_WEBHOOK_SECRET`

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
STRIPE_SECRET_KEY=sk_test_...  # or sk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO_MONTHLY=price_...
STRIPE_PRICE_ID_PRO_ANNUAL=price_...
```

### 4. Test Webhook (Development)

#### Using Stripe CLI

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created
```

#### Using ngrok

```bash
# Install ngrok
# https://ngrok.com/

# Expose local server
ngrok http 8000

# Use the ngrok URL in Stripe Dashboard webhook configuration
# Example: https://abc123.ngrok.io/api/webhooks/stripe
```

## Webhook Security

The webhook endpoint verifies the Stripe signature using the `STRIPE_WEBHOOK_SECRET`. This ensures requests are actually from Stripe.

**Important:** Never expose your webhook secret. Keep it in environment variables only.

## Event Processing

Each webhook event is:

1. **Verified** - Signature checked against `STRIPE_WEBHOOK_SECRET`
2. **Idempotent** - Duplicate events are ignored (tracked by event ID)
3. **Logged** - All events stored in `payment_events` table
4. **Processed** - Subscription state updated in database

## Troubleshooting

### Webhook Not Received

- Check webhook URL is correct in Stripe Dashboard
- Verify webhook secret matches `STRIPE_WEBHOOK_SECRET`
- Check server logs for errors
- Use Stripe Dashboard → Webhooks → View logs to see delivery attempts

### Signature Verification Failed

- Ensure `STRIPE_WEBHOOK_SECRET` is set correctly
- Verify you're using the correct secret for the environment (test vs live)
- Check that the webhook endpoint receives the raw request body (not parsed JSON)

### Events Not Processing

- Check `payment_events` table for failed events
- Review `processing_error` column for error details
- Verify database connection is working
- Check that user records exist for subscription events

## Testing

See `backend/tests/test_stripe_integration.py` for integration tests.

Run smoke tests:
```bash
python scripts/smoke_test_auth_and_billing.py
```

## Production Checklist

- [ ] Webhook endpoint configured in Stripe Dashboard
- [ ] `STRIPE_WEBHOOK_SECRET` set in production environment
- [ ] All required events selected
- [ ] Webhook URL uses HTTPS
- [ ] Test webhook delivery in Stripe Dashboard
- [ ] Monitor `payment_events` table for failed events
- [ ] Set up alerts for webhook failures



