# 🔔 Stripe Webhook Configuration Guide

This guide walks you through setting up Stripe webhooks for Parlay Gorilla.

## 📍 Webhook Endpoint URL

**Production:**
```
https://api.parlaygorilla.com/api/webhooks/stripe
```

**Test Mode (for testing):**
```
https://api.parlaygorilla.com/api/webhooks/stripe
```
*(Same endpoint - Stripe handles test vs live events automatically)*

---

## 🎯 Step-by-Step Setup

### 1. Navigate to Stripe Dashboard

1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Click **Developers** → **Webhooks** in the left sidebar
3. Click **Add endpoint** (or **+ Add** if you already have webhooks)

### 2. Configure Endpoint

**Endpoint URL:**
```
https://api.parlaygorilla.com/api/webhooks/stripe
```

**Description (optional):**
```
Parlay Gorilla - Subscriptions & Credit Packs
```

**Events to send:**
Select **"Select events to listen to"** and choose these events:

#### ✅ Required Events (Select These):

**Checkout & Payments:**
- `checkout.session.completed` - When a checkout session completes (subscriptions, credit packs, one-time payments)

**Subscriptions:**
- `customer.subscription.created` - New subscription activated
- `customer.subscription.updated` - Subscription renewed, plan changed, or status updated
- `customer.subscription.deleted` - Subscription cancelled or expired

**Invoices:**
- `invoice.paid` - Recurring subscription payment succeeded (renewal)
- `invoice.payment_failed` - Recurring subscription payment failed

### 3. Save and Get Webhook Secret

1. Click **Add endpoint**
2. After saving, click on the webhook endpoint you just created
3. In the **Signing secret** section, click **Reveal** or **Click to reveal**
4. Copy the **Signing secret** (starts with `whsec_`)

### 4. Add Webhook Secret to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on **`parlay-gorilla-backend`** service
3. Go to **Environment** tab
4. Add or update this variable:

```
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

5. Click **Save Changes** - Render will automatically redeploy

---

## 🔍 Verify Webhook Configuration

### Test the Webhook

1. In Stripe Dashboard, go to your webhook endpoint
2. Click **Send test webhook**
3. Select event type: `checkout.session.completed`
4. Click **Send test webhook**
5. Check the **Logs** tab to see if the webhook was received successfully

### Check Backend Logs

1. In Render Dashboard, go to **`parlay-gorilla-backend`** service
2. Click **Logs** tab
3. Look for webhook processing messages:
   - ✅ `Processed Stripe webhook event: checkout.session.completed`
   - ❌ If you see errors, check the error message

### Test a Real Purchase

1. Make a test purchase (subscription or credit pack)
2. Check Stripe Dashboard → **Webhooks** → Your endpoint → **Logs**
3. You should see successful webhook deliveries (green checkmarks)

---

## 🔐 Security Notes

- **Webhook Signature Verification**: The webhook handler automatically verifies the Stripe signature using your `STRIPE_WEBHOOK_SECRET`
- **Idempotency**: Duplicate webhook deliveries are automatically ignored (tracked by `event_id`)
- **HTTPS Required**: Stripe only sends webhooks to HTTPS endpoints (your production URL is HTTPS)

---

## 🐛 Troubleshooting

### Webhook Not Receiving Events

1. **Check URL**: Ensure the endpoint URL is exactly: `https://api.parlaygorilla.com/api/webhooks/stripe`
2. **Check Events**: Verify you selected the correct events in Stripe Dashboard
3. **Check Render**: Ensure your backend service is running and accessible
4. **Check Logs**: Look at Render logs for any errors

### Webhook Signature Verification Failed

1. **Check Secret**: Ensure `STRIPE_WEBHOOK_SECRET` in Render matches the secret from Stripe Dashboard
2. **Check Environment**: Make sure you're using the correct secret for test vs live mode
3. **Regenerate Secret**: In Stripe Dashboard, you can click **Reveal** again to get the current secret

### Events Not Processing

1. **Check Event Types**: Ensure you selected all required events in Stripe Dashboard
2. **Check Backend Logs**: Look for error messages in Render logs
3. **Check Database**: Verify the `payment_events` table is being updated (events are logged there)

---

## 📋 Quick Checklist

- [ ] Created webhook endpoint in Stripe Dashboard
- [ ] Set endpoint URL to: `https://api.parlaygorilla.com/api/webhooks/stripe`
- [ ] Selected all required events:
  - [ ] `checkout.session.completed`
  - [ ] `customer.subscription.created`
  - [ ] `customer.subscription.updated`
  - [ ] `customer.subscription.deleted`
  - [ ] `invoice.paid`
  - [ ] `invoice.payment_failed`
- [ ] Copied webhook signing secret from Stripe
- [ ] Added `STRIPE_WEBHOOK_SECRET` to Render environment variables
- [ ] Tested webhook with test event
- [ ] Verified webhook logs show successful deliveries

---

## 🔗 Related Documentation

- [Stripe Webhooks Documentation](https://stripe.com/docs/webhooks)
- [Render Environment Variables Guide](../RENDER_BACKEND_ENV_COMPLETE.md)
- [Stripe Setup Checklist](../STRIPE_PRE_TEST_CHECKLIST.md)

---

**Last Updated:** Based on current webhook handler implementation in `backend/app/api/routes/webhooks/stripe_webhook_routes.py`
