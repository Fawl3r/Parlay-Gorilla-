# Stripe Webhook Testing Guide

## Problem: Purchase completed but product not granted

If you made a test purchase in Stripe but didn't receive credits/subscription, the webhook likely didn't fire or failed.

## Quick Diagnosis

### 1. Check if webhook was received

Check your backend logs for:
- `Processed Stripe webhook event: checkout.session.completed`
- `Successfully processed credit pack purchase`
- `Successfully processed lifetime subscription purchase`

### 2. Check payment_events table

**Option A: Using SQL (in Render shell or database console):**
```sql
SELECT event_id, event_type, processed, processing_error, occurred_at 
FROM payment_events 
WHERE provider = 'stripe' 
ORDER BY occurred_at DESC 
LIMIT 10;
```

**Option B: Using Python script (in Render shell):**
```bash
python -c "
import asyncio
from app.database.session import AsyncSessionLocal
from app.models.payment_event import PaymentEvent
from sqlalchemy import select, desc

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(PaymentEvent)
            .where(PaymentEvent.provider == 'stripe')
            .order_by(desc(PaymentEvent.occurred_at))
            .limit(10)
        )
        events = result.scalars().all()
        if not events:
            print('No Stripe webhook events found')
        else:
            for e in events:
                print(f'{e.occurred_at}: {e.event_type} - {e.processed} - {e.processing_error or \"OK\"}')

asyncio.run(check())
"
```

Look for:
- `checkout.session.completed` events
- `processed = 'processed'` or `processed = 'failed'`
- Any error messages in `processing_error` column

### 3. Verify webhook configuration in Stripe

**For Test Mode:**
1. Go to Stripe Dashboard → Developers → Webhooks
2. Make sure you have a webhook endpoint configured
3. Endpoint URL should be: `{YOUR_BACKEND_URL}/api/webhooks/stripe`
4. Events to listen for:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`

### 4. Test webhook locally (if developing)

Use Stripe CLI to forward webhooks:
```bash
stripe listen --forward-to localhost:8000/api/webhooks/stripe
```

Then trigger a test event:
```bash
stripe trigger checkout.session.completed
```

## Common Issues

### Issue 1: Webhook not configured
**Symptom:** No webhook events in logs or database
**Fix:** Configure webhook endpoint in Stripe dashboard

### Issue 2: Webhook secret mismatch
**Symptom:** `SignatureVerificationError` in logs
**Fix:** 
- Get webhook signing secret from Stripe dashboard
- Update `STRIPE_WEBHOOK_SECRET` in your `.env` file
- Restart backend

### Issue 3: Webhook endpoint not accessible
**Symptom:** Webhook delivery failures in Stripe dashboard
**Fix:** 
- For local dev: Use Stripe CLI or ngrok/cloudflared tunnel
- For production: Ensure backend URL is publicly accessible

### Issue 4: Metadata missing
**Symptom:** `Credit pack purchase missing required metadata` in logs
**Fix:** Check that checkout session includes:
- `metadata.user_id`
- `metadata.purchase_type` (should be "credit_pack" or "lifetime_subscription")
- `metadata.credit_pack_id` (for credit packs)

## Manual Fulfillment (For Testing)

If webhook failed, you can manually fulfill a purchase:

### For Credit Packs:

**Using the script (recommended):**
```bash
python scripts/manual_fulfill_purchase.py \
  --type credit_pack \
  --session-id cs_test_xxxxx \
  --user-id YOUR_USER_ID \
  --pack-id credits_25
```

**Or using Python directly:**
```python
# In Python shell
import asyncio
from app.database.session import AsyncSessionLocal
from app.services.credit_pack_fulfillment_service import CreditPackFulfillmentService

async def manual_fulfill():
    async with AsyncSessionLocal() as db:
        service = CreditPackFulfillmentService(db)
        result = await service.fulfill_credit_pack_purchase(
            provider="stripe",
            provider_order_id="cs_test_xxxxx",  # Your checkout session ID
            user_id="your-user-id",
            credit_pack_id="credits_25",  # or credits_10, credits_50, credits_100
        )
        print(f"Applied: {result.applied}, Credits added: {result.credits_added}")

asyncio.run(manual_fulfill())
```

### For Lifetime Subscriptions:

**Using the script (recommended):**
```bash
python scripts/manual_fulfill_purchase.py \
  --type lifetime \
  --session-id cs_test_xxxxx \
  --user-id YOUR_USER_ID \
  --plan-code PG_LIFETIME_CARD
```

**Or check if subscription record exists:**
```sql
SELECT * FROM subscriptions 
WHERE user_id = 'your-user-id' 
AND is_lifetime = true;
```

If missing, check webhook logs for errors.

## Testing Checklist

- [ ] Webhook endpoint configured in Stripe dashboard
- [ ] Webhook secret set in environment variables
- [ ] Backend URL is accessible (or using tunnel for local dev)
- [ ] Checkout session includes correct metadata
- [ ] Webhook events appear in payment_events table
- [ ] No errors in backend logs during webhook processing

## Next Steps

1. Check Stripe dashboard → Webhooks → Recent deliveries
2. Look for failed deliveries and error messages
3. Check backend logs for webhook processing errors
4. Verify metadata in checkout session
5. If needed, manually fulfill the purchase using the script above

