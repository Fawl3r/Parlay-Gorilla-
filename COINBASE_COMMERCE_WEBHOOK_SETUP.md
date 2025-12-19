# 🔗 Coinbase Commerce Webhook Setup Guide

Complete guide to setting up webhooks for Coinbase Commerce payments in Parlay Gorilla.

## 📋 Prerequisites

Before setting up webhooks, you need:
- [ ] Coinbase Commerce account created
- [ ] API key generated
- [ ] Your backend deployed and accessible via HTTPS (e.g., on Render)
- [ ] Your backend URL (e.g., `https://api.parlaygorilla.com` or `https://parlay-gorilla-backend.onrender.com`)

---

## 🚀 Step-by-Step Setup

### Step 1: Get Your Backend Webhook URL

Your webhook endpoint is:
```
https://YOUR-BACKEND-URL/api/webhooks/coinbase
```

**Examples:**
- Production: `https://api.parlaygorilla.com/api/webhooks/coinbase`
- Render (temporary): `https://parlay-gorilla-backend.onrender.com/api/webhooks/coinbase`

**⚠️ Important:** Your backend MUST be accessible via HTTPS. Coinbase Commerce requires HTTPS for webhooks.

---

### Step 2: Access Coinbase Commerce Dashboard

1. **Go to Coinbase Commerce Dashboard**: https://commerce.coinbase.com/dashboard
2. **Log in** to your Coinbase Commerce account
3. **Navigate to Settings**: Click on **Settings** in the left sidebar

---

### Step 3: Create Webhook

1. **Go to Webhooks Section**:
   - In Settings, click on **"Webhooks"** (or look for "Webhooks" in the menu)
   - You should see a list of existing webhooks (if any)

2. **Click "Create Webhook"** or **"Add Webhook"**

3. **Fill in Webhook Details**:
   - **Webhook URL**: Enter your backend webhook URL
     ```
     https://YOUR-BACKEND-URL/api/webhooks/coinbase
     ```
   - **Events to Subscribe**: Select the events you want to receive:
     - ✅ `charge:confirmed` - **REQUIRED** (payment confirmed, activate subscription/credits)
     - ✅ `charge:failed` - **RECOMMENDED** (payment failed)
     - ✅ `charge:pending` - **OPTIONAL** (payment pending)
     - ⚠️ `charge:created` - Usually not needed (charge created but not paid)

4. **Click "Create Webhook"** or **"Save"**

---

### Step 4: Get Webhook Secret

After creating the webhook:

1. **Find your webhook** in the list
2. **Click on the webhook** to view details
3. **Copy the Webhook Secret**:
   - Look for "Secret" or "Webhook Secret" field
   - Click "Show" or "Reveal" to see the secret
   - **Copy this secret** - you'll need it for your backend

**⚠️ Important:** Keep this secret secure! Never commit it to git or share it publicly.

---

### Step 5: Add Webhook Secret to Backend

Add the webhook secret to your backend environment variables:

#### If Using Render:

1. Go to your Render dashboard
2. Navigate to `parlay-gorilla-backend` service
3. Go to **Environment** tab
4. Click **"Add Environment Variable"**
5. Add:
   ```
   Key: COINBASE_COMMERCE_WEBHOOK_SECRET
   Value: [paste your webhook secret here]
   ```
6. Click **"Save Changes"** - Render will auto-redeploy

#### If Using Local Development:

Add to your `backend/.env` file:
```env
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret_here
```

---

### Step 6: Verify Webhook is Working

1. **Check Webhook Status in Coinbase Dashboard**:
   - Go back to Coinbase Commerce → Settings → Webhooks
   - Your webhook should show as "Active" or "Enabled"
   - You may see recent delivery attempts

2. **Test with a Payment**:
   - Make a test purchase using Coinbase Commerce
   - After payment is confirmed, check:
     - Coinbase Dashboard → Webhooks → Your webhook → Recent deliveries
     - Should show successful delivery (200 status)
   - Check your backend logs for webhook processing

3. **Check Backend Logs**:
   - In Render: Go to backend service → **Logs** tab
   - Look for messages like:
     - `"Coinbase webhook received: charge:confirmed"`
     - `"Coinbase charge confirmed for user..."`

---

## 🔍 Webhook Events Handled

Your backend handles these Coinbase Commerce events:

### ✅ `charge:confirmed`
- **When**: Payment is confirmed on blockchain
- **What happens**:
  - Subscription activated (lifetime, monthly, or annual)
  - Credit packs awarded (if credit pack purchase)
  - Affiliate commissions created
  - Payment event logged

### ✅ `charge:failed`
- **When**: Payment fails or expires
- **What happens**:
  - Payment event logged
  - User notified (if applicable)

### ✅ `charge:pending`
- **When**: Payment is pending blockchain confirmation
- **What happens**:
  - Payment event logged
  - Status tracked

---

## 🔒 Security

Your webhook endpoint includes security features:

1. **HMAC Signature Verification**:
   - Verifies `X-CC-Webhook-Signature` header
   - Uses your webhook secret to validate requests
   - Rejects invalid signatures

2. **Idempotency**:
   - Prevents duplicate processing
   - Uses event ID to track processed events

3. **Event Logging**:
   - All webhook events logged to `payment_events` table
   - Full payload stored for debugging

---

## 🧪 Testing Webhooks

### Option 1: Test with Real Payment (Recommended)

1. Create a test charge in Coinbase Commerce
2. Complete the payment
3. Check webhook delivery in Coinbase dashboard
4. Verify backend processed the event

### Option 2: Use Coinbase Test Mode

1. Switch to Coinbase Commerce test mode
2. Create test charges
3. Webhooks will be sent to your endpoint
4. Check logs for processing

### Option 3: Manual Testing (Advanced)

You can manually send test webhook payloads using curl:

```bash
curl -X POST https://YOUR-BACKEND-URL/api/webhooks/coinbase \
  -H "Content-Type: application/json" \
  -H "X-CC-Webhook-Signature: [calculated signature]" \
  -d '{
    "event": {
      "type": "charge:confirmed",
      "data": {
        "id": "test-charge-id",
        "metadata": {
          "user_id": "test-user-id",
          "plan_code": "PG_LIFETIME"
        }
      }
    }
  }'
```

**Note:** You'll need to calculate the HMAC signature correctly for this to work.

---

## 🐛 Troubleshooting

### Webhook Not Receiving Events?

1. **Check Webhook URL**:
   - Ensure it's correct and accessible via HTTPS
   - Test the URL in browser (should return 405 Method Not Allowed, not 404)

2. **Check Webhook Status in Coinbase**:
   - Go to Coinbase Dashboard → Webhooks
   - Check if webhook shows errors or failed deliveries
   - Look at recent delivery attempts

3. **Check Backend Logs**:
   - Look for webhook-related errors
   - Check if signature verification is failing

### Signature Verification Failing?

1. **Verify Webhook Secret**:
   - Ensure `COINBASE_COMMERCE_WEBHOOK_SECRET` is set correctly
   - Check for extra spaces or newlines
   - Make sure it matches the secret in Coinbase dashboard

2. **Check Header Name**:
   - Backend expects: `X-CC-Webhook-Signature`
   - Coinbase sends this header automatically

### Webhook Receiving but Not Processing?

1. **Check Event Type**:
   - Ensure you subscribed to the right events
   - Backend handles: `charge:confirmed`, `charge:failed`, `charge:pending`

2. **Check Backend Logs**:
   - Look for processing errors
   - Check database connection
   - Verify user_id in metadata

3. **Check Database**:
   - Ensure database is accessible
   - Check if payment_events table exists
   - Verify migrations are up to date

---

## 📝 Environment Variables Summary

Add these to your backend environment:

```env
# Required for Coinbase Commerce
COINBASE_COMMERCE_API_KEY=your_api_key_here
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret_here
```

**Where to get them:**
- `COINBASE_COMMERCE_API_KEY`: Settings → API Keys → Create new key
- `COINBASE_COMMERCE_WEBHOOK_SECRET`: Settings → Webhooks → Your webhook → Secret

---

## ✅ Setup Checklist

- [ ] Coinbase Commerce account created
- [ ] API key generated and added to backend
- [ ] Backend deployed and accessible via HTTPS
- [ ] Webhook created in Coinbase Commerce dashboard
- [ ] Webhook URL set to: `https://YOUR-BACKEND-URL/api/webhooks/coinbase`
- [ ] Events subscribed: `charge:confirmed`, `charge:failed`, `charge:pending`
- [ ] Webhook secret copied from Coinbase dashboard
- [ ] `COINBASE_COMMERCE_WEBHOOK_SECRET` added to backend environment
- [ ] Webhook tested with a payment
- [ ] Backend logs show successful webhook processing

---

## 🔗 Quick Links

- [Coinbase Commerce Dashboard](https://commerce.coinbase.com/dashboard)
- [Coinbase Commerce Webhook Docs](https://docs.commerce.coinbase.com/docs/webhooks)
- [Coinbase Commerce API Docs](https://docs.commerce.coinbase.com/api)
- [Your Backend Webhook Endpoint](https://YOUR-BACKEND-URL/api/webhooks/coinbase)

---

## 📚 Additional Resources

- See `backend/app/api/routes/webhooks/coinbase_webhook_routes.py` for webhook implementation
- See `backend/app/services/coinbase_subscription_fulfillment_service.py` for subscription fulfillment logic
- See `RENDER_SETUP_GUIDE.md` for full deployment guide

---

## 💡 Tips

1. **Use Test Mode First**: Test webhooks in Coinbase test mode before going live
2. **Monitor Webhook Deliveries**: Check Coinbase dashboard regularly for failed deliveries
3. **Keep Secrets Secure**: Never commit webhook secrets to git
4. **Log Everything**: Backend logs all webhook events for debugging
5. **Test with Small Payments**: Test with small amounts first

---

**Once setup is complete, your Coinbase Commerce payments will automatically:**
- ✅ Activate subscriptions
- ✅ Award credit packs
- ✅ Create affiliate commissions
- ✅ Log payment events

🎉 **You're all set!**

