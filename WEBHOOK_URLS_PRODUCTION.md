# 🔗 Production Webhook URLs

Quick reference for webhook URLs now that `https://www.parlaygorilla.com` is live.

---

## ✅ Production Webhook URLs

### LemonSqueezy Webhook
```
https://api.parlaygorilla.com/api/webhooks/lemonsqueezy
```

**Where to configure:**
1. Go to [LemonSqueezy Dashboard](https://app.lemonsqueezy.com) → Settings → Webhooks
2. Add or update webhook URL to: `https://api.parlaygorilla.com/api/webhooks/lemonsqueezy`
3. Select events:
   - ✅ `subscription_created`
   - ✅ `subscription_updated`
   - ✅ `subscription_cancelled`
   - ✅ `subscription_payment_success`
   - ✅ `subscription_payment_failed`
   - ✅ `order_created`
   - ✅ `order_completed`
4. Copy the webhook secret and add to backend environment: `LEMONSQUEEZY_WEBHOOK_SECRET`

---

### Coinbase Commerce Webhook
```
https://api.parlaygorilla.com/api/webhooks/coinbase
```

**Where to configure:**
1. Go to [Coinbase Commerce Dashboard](https://commerce.coinbase.com/dashboard) → Settings → Webhooks
2. Add or update webhook URL to: `https://api.parlaygorilla.com/api/webhooks/coinbase`
3. Select events:
   - ✅ `charge:confirmed` (REQUIRED)
   - ✅ `charge:failed` (RECOMMENDED)
   - ✅ `charge:pending` (OPTIONAL)
4. Copy the webhook secret and add to backend environment: `COINBASE_COMMERCE_WEBHOOK_SECRET`

---

## 🔐 Environment Variables

**YES - These MUST be set in Render's environment variables for production!**

The `.env` file is only for local development. In production on Render, you need to add these manually:

### How to Add to Render:

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click on `parlay-gorilla-backend` service**
3. **Go to "Environment" tab**
4. **Click "Add Environment Variable"**
5. **Add these two variables:**

```env
# LemonSqueezy Webhook Secret
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_from_lemonsqueezy

# Coinbase Commerce Webhook Secret
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret_from_coinbase
```

6. **Click "Save Changes"** - Render will automatically redeploy

**Important Notes:**
- These are secrets - never commit them to git
- Get the secrets from each payment provider's dashboard after creating the webhook
- Render will redeploy automatically after you save
- The webhook endpoints won't work without these secrets (signature verification will fail)

---

## ✅ Verification Checklist

- [ ] LemonSqueezy webhook URL updated to `https://api.parlaygorilla.com/api/webhooks/lemonsqueezy`
- [ ] LemonSqueezy webhook secret copied to backend environment
- [ ] Coinbase Commerce webhook URL updated to `https://api.parlaygorilla.com/api/webhooks/coinbase`
- [ ] Coinbase Commerce webhook secret copied to backend environment
- [ ] Backend restarted/redeployed after adding secrets
- [ ] Test webhook delivery (make a test purchase and verify webhook is received)

---

## 🧪 Testing

After configuring webhooks:

1. **LemonSqueezy**: Make a test purchase and check:
   - LemonSqueezy Dashboard → Webhooks → Your webhook → Deliveries (should show 200 OK)
   - Backend logs should show: `"LemonSqueezy webhook received"`

2. **Coinbase Commerce**: Make a test payment and check:
   - Coinbase Dashboard → Webhooks → Your webhook → Recent deliveries (should show 200 OK)
   - Backend logs should show: `"Coinbase webhook received: charge:confirmed"`

---

## 📚 Full Documentation

- [LemonSqueezy Webhook Testing Guide](./LEMONSQUEEZY_WEBHOOK_TESTING_GUIDE.md)
- [Coinbase Commerce Webhook Setup](./COINBASE_COMMERCE_WEBHOOK_SETUP.md)

---

**Last Updated:** Production domain is live at `https://www.parlaygorilla.com` with backend at `https://api.parlaygorilla.com`

