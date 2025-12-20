# 🧪 LemonSqueezy Webhook Testing Guide

Complete guide for setting up and testing LemonSqueezy webhooks locally and in production.

---

## 📋 Prerequisites

1. **LemonSqueezy Account**: Active account with products created
2. **Backend Running**: Your FastAPI backend must be running
3. **Webhook Secret**: You'll get this from LemonSqueezy dashboard
4. **Public URL**: For local testing, you'll need a tunnel (ngrok, localtunnel, etc.)

---

## 🔧 Step 1: Set Up Local Tunnel (For Testing)

To test webhooks locally, you need to expose your local backend to the internet.

### Option A: Using ngrok (Recommended)

1. **Install ngrok**:
   - Download from [ngrok.com](https://ngrok.com/download)
   - Or install via package manager:
     ```bash
     # Windows (chocolatey)
     choco install ngrok
     
     # macOS (homebrew)
     brew install ngrok
     
     # Linux
     wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
     tar -xzf ngrok-v3-stable-linux-amd64.tgz
     ```

2. **Start ngrok tunnel**:
   ```bash
   ngrok http 8000
   ```
   
   This will give you a URL like: `https://abc123.ngrok.io`

3. **Copy the HTTPS URL** (not HTTP):
   - Example: `https://abc123.ngrok.io`
   - This is your public backend URL for webhook testing

### Option B: Using localtunnel

1. **Install localtunnel**:
   ```bash
   npm install -g localtunnel
   ```

2. **Start tunnel**:
   ```bash
   lt --port 8000
   ```
   
   This will give you a URL like: `https://abc123.loca.lt`

### Option C: Using Cloudflare Tunnel (If Already Set Up)

If you already have Cloudflare Tunnel configured:
- Use your existing tunnel URL
- Example: `https://your-backend.your-domain.com`

---

## 🔗 Step 2: Configure Webhook in LemonSqueezy

1. **Log in to LemonSqueezy**:
   - Go to [app.lemonsqueezy.com](https://app.lemonsqueezy.com)
   - Sign in to your account

2. **Navigate to Webhooks**:
   - Click **Settings** in the left sidebar
   - Click **Webhooks** (or go to: [Settings → Webhooks](https://app.lemonsqueezy.com/settings/webhooks))

3. **Add New Webhook**:
   - Click **"Add webhook"** or **"Create webhook"**
   - Enter your webhook URL:
     ```
     {YOUR_PUBLIC_URL}/api/webhooks/lemonsqueezy
     ```
   
   **Examples:**
   - Local testing: `https://abc123.ngrok.io/api/webhooks/lemonsqueezy`
   - Production: `https://api.parlaygorilla.com/api/webhooks/lemonsqueezy` ✅ **USE THIS FOR PRODUCTION**

4. **Select Events to Listen For**:
   Check the following events (required for full functionality):
   - ✅ `subscription_created`
   - ✅ `subscription_updated`
   - ✅ `subscription_cancelled`
   - ✅ `subscription_payment_success`
   - ✅ `subscription_payment_failed`
   - ✅ `order_created`
   - ✅ `order_completed`

5. **Save the Webhook**:
   - Click **"Save"** or **"Create webhook"**

6. **Copy the Webhook Secret**:
   - After creating, LemonSqueezy will show a **Webhook Secret**
   - **IMPORTANT**: Copy this immediately - you won't be able to see it again!
   - If you lose it, you'll need to delete and recreate the webhook

---

## 🔐 Step 3: Configure Environment Variables

Update your `backend/.env` file:

```env
# LemonSqueezy Configuration
LEMONSQUEEZY_API_KEY=your_api_key_here
LEMONSQUEEZY_STORE_ID=your_store_id_here
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_here

# Backend URL (for webhook testing, use your tunnel URL)
BACKEND_URL=https://abc123.ngrok.io
# Or for production:
# BACKEND_URL=https://api.parlaygorilla.com
```

**Important Notes:**
- The `LEMONSQUEEZY_WEBHOOK_SECRET` is used to verify webhook signatures
- If the secret is missing, webhooks will still work but without signature verification (not recommended for production)
- Restart your backend server after updating `.env`

---

## 🧪 Step 4: Test the Webhook

### Method 1: Test with LemonSqueezy Test Mode

1. **Enable Test Mode** (if available):
   - Some payment providers have a test mode
   - Check LemonSqueezy dashboard for test mode settings

2. **Create a Test Purchase**:
   - Use a test credit card (if available)
   - Or use LemonSqueezy's test payment methods
   - Complete a purchase to trigger webhook events

3. **Check Webhook Delivery**:
   - Go to **Settings** → **Webhooks** in LemonSqueezy
   - Click on your webhook
   - View **"Webhook deliveries"** or **"Event log"**
   - You should see events with status (success/failed)

### Method 2: Manual Webhook Testing with curl

You can manually send a test webhook payload to verify your endpoint works:

```bash
# Test webhook endpoint (without signature verification)
curl -X POST http://localhost:8000/api/webhooks/lemonsqueezy \
  -H "Content-Type: application/json" \
  -d '{
    "meta": {
      "event_name": "subscription_created",
      "webhook_id": "test-webhook-123"
    },
    "data": {
      "id": "123456",
      "type": "subscriptions",
      "attributes": {
        "user_email": "test@example.com",
        "customer_id": "789",
        "status": "active",
        "renews_at": "2024-02-01T00:00:00Z",
        "first_subscription_item": {
          "custom_data": {
            "user_id": "your-test-user-id-here",
            "plan_code": "PG_PREMIUM_MONTHLY"
          }
        }
      }
    }
  }'
```

**Note**: This test won't have signature verification. For full testing, you need real webhook events from LemonSqueezy.

### Method 3: Check Backend Logs

1. **Start your backend** with logging enabled:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --port 8000
   ```

2. **Watch for webhook logs**:
   - Look for: `"LemonSqueezy webhook received"`
   - Check for any errors or warnings
   - Verify events are being processed

3. **Check Database**:
   - Webhook events are logged to the `payment_events` table
   - Check if events are being stored:
     ```sql
     SELECT * FROM payment_events 
     WHERE provider = 'lemonsqueezy' 
     ORDER BY created_at DESC 
     LIMIT 10;
     ```

---

## ✅ Step 5: Verify Webhook is Working

### Check Webhook Delivery Status

1. **In LemonSqueezy Dashboard**:
   - Go to **Settings** → **Webhooks**
   - Click on your webhook
   - View the **"Deliveries"** or **"Event log"** tab
   - Check for:
     - ✅ **200 OK** responses (success)
     - ❌ **401/403** (signature verification failed)
     - ❌ **500** (server error)

### Verify Backend Processing

1. **Check Payment Events Table**:
   ```python
   # In your backend, check payment_events
   from app.models.payment_event import PaymentEvent
   from sqlalchemy import select
   
   # Query recent events
   events = await db.execute(
       select(PaymentEvent)
       .where(PaymentEvent.provider == "lemonsqueezy")
       .order_by(PaymentEvent.created_at.desc())
       .limit(10)
   )
   ```

2. **Check User Subscriptions**:
   - Verify subscriptions are being created/updated
   - Check user credits are being added (for credit packs)
   - Confirm subscription status is correct

3. **Check Logs**:
   - Look for: `"Created LemonSqueezy subscription for user..."`
   - Check for any error messages
   - Verify affiliate commissions are being calculated (if applicable)

---

## 🐛 Troubleshooting

### Webhook Not Receiving Events

**Problem**: No webhook events are being received.

**Solutions**:
1. ✅ Verify webhook URL is correct and publicly accessible
2. ✅ Check that your backend is running and accessible
3. ✅ Test the webhook URL manually:
   ```bash
   curl https://your-tunnel-url.ngrok.io/api/webhooks/lemonsqueezy
   ```
   Should return a 405 (Method Not Allowed) or similar - this means the endpoint exists
4. ✅ Check ngrok/localtunnel is still running
5. ✅ Verify firewall/network isn't blocking requests

### Signature Verification Failed (401 Error)

**Problem**: Webhook returns 401 "Invalid signature" or "Missing signature".

**Solutions**:
1. ✅ Verify `LEMONSQUEEZY_WEBHOOK_SECRET` is set correctly in `.env`
2. ✅ Check for extra spaces or newlines in the secret
3. ✅ Ensure the secret matches exactly what's in LemonSqueezy dashboard
4. ✅ If you lost the secret, delete and recreate the webhook in LemonSqueezy
5. ✅ Restart your backend after updating the secret

### Webhook Returns 500 Error

**Problem**: Webhook endpoint returns 500 Internal Server Error.

**Solutions**:
1. ✅ Check backend logs for detailed error messages
2. ✅ Verify database connection is working
3. ✅ Check that all required environment variables are set
4. ✅ Verify user exists in database (if webhook references a user_id)
5. ✅ Check for database constraint violations

### Events Not Processing

**Problem**: Webhooks are received (200 OK) but nothing happens.

**Solutions**:
1. ✅ Check `payment_events` table - events should be logged
2. ✅ Verify event type is one of the supported types
3. ✅ Check `custom_data` contains required fields (`user_id`, `plan_code`, etc.)
4. ✅ Look for "skipped" or "failed" status in payment_events
5. ✅ Check backend logs for processing errors

### Duplicate Events

**Problem**: Same webhook event is processed multiple times.

**Solutions**:
1. ✅ This is normal - LemonSqueezy may retry webhooks
2. ✅ The system uses `event_id` for idempotency - duplicate events are automatically skipped
3. ✅ Check logs for: `"Duplicate LemonSqueezy webhook event_id=...; skipping"`

---

## 📝 Webhook Event Reference

### Supported Events

| Event Name | Description | When It Fires |
|------------|-------------|---------------|
| `subscription_created` | New subscription activated | User subscribes to a plan |
| `subscription_updated` | Subscription renewed or changed | Subscription renews or plan changes |
| `subscription_cancelled` | Subscription cancelled | User cancels subscription |
| `subscription_payment_success` | Recurring payment succeeded | Monthly/yearly payment processed |
| `subscription_payment_failed` | Recurring payment failed | Payment attempt failed |
| `order_created` | New order created | One-time purchase (credits, lifetime, parlay) |
| `order_completed` | Order completed | Order payment confirmed |

### Event Payload Structure

```json
{
  "meta": {
    "event_name": "subscription_created",
    "webhook_id": "unique-event-id-123"
  },
  "data": {
    "id": "subscription-id",
    "type": "subscriptions",
    "attributes": {
      "user_email": "user@example.com",
      "customer_id": "customer-id",
      "status": "active",
      "renews_at": "2024-02-01T00:00:00Z",
      "first_subscription_item": {
        "custom_data": {
          "user_id": "uuid-here",
          "plan_code": "PG_PREMIUM_MONTHLY"
        }
      }
    }
  }
}
```

---

## 🔄 Production Setup

When moving to production:

1. **Update Webhook URL**:
   - Change from tunnel URL to your production backend URL
   - Example: `https://api.parlaygorilla.com/api/webhooks/lemonsqueezy`

2. **Verify Environment Variables**:
   - Ensure `BACKEND_URL` points to production
   - Verify `LEMONSQUEEZY_WEBHOOK_SECRET` is set correctly

3. **Test with Real Purchases**:
   - Make a small test purchase
   - Verify webhook is received and processed
   - Check that subscription/credits are added correctly

4. **Monitor Webhook Health**:
   - Set up alerts for webhook failures
   - Monitor `payment_events` table for errors
   - Check LemonSqueezy dashboard for delivery status

---

## 📚 Additional Resources

- [LemonSqueezy Webhooks Documentation](https://docs.lemonsqueezy.com/api/webhooks)
- [LemonSqueezy Dashboard](https://app.lemonsqueezy.com)
- [ngrok Documentation](https://ngrok.com/docs)
- [Backend README](./backend/README.md)

---

## ✅ Quick Checklist

- [ ] Local tunnel set up (ngrok/localtunnel)
- [ ] Backend running and accessible via tunnel URL
- [ ] Webhook created in LemonSqueezy dashboard
- [ ] Webhook URL configured correctly
- [ ] All required events selected
- [ ] Webhook secret copied to `.env`
- [ ] `LEMONSQUEEZY_WEBHOOK_SECRET` set in `.env`
- [ ] Backend restarted after `.env` changes
- [ ] Test purchase made
- [ ] Webhook received (check LemonSqueezy dashboard)
- [ ] Events logged in `payment_events` table
- [ ] Subscription/credits added correctly

---

**Need Help?** Check the backend logs and LemonSqueezy webhook delivery status for detailed error messages.

