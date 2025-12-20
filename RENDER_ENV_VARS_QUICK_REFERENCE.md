# 📋 Render Environment Variables - Quick Reference

Copy and paste these values into your Render dashboard after deploying.

## 🔴 Backend Service (`parlay-gorilla-backend`)

### ✅ Auto-Wired by Render (DO NOT SET)

These are automatically set by Render:
- `DATABASE_URL` - From PostgreSQL database
- `REDIS_URL` - From Key Value store
- `JWT_SECRET` - Auto-generated
- `ENVIRONMENT` - Set to `production`
- `DEBUG` - Set to `false`
- `USE_SQLITE` - Set to `false`
- `OPENAI_ENABLED` - Set to `true`
- `FRONTEND_URL` - Set to `https://www.parlaygorilla.com`
- `BACKEND_URL` - Set to `https://api.parlaygorilla.com`
- `APP_URL` - Set to `https://www.parlaygorilla.com`

### Required Variables (Set These)

```
THE_ODDS_API_KEY=your_odds_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Note:** `FRONTEND_URL`, `BACKEND_URL`, and `APP_URL` are auto-set by Render from `render.yaml` - you don't need to set them manually.

### Optional Variables (Set If You Have Them)

```
# The Odds API Fallback (recommended)
THE_ODDS_API_FALLBACK_KEY=your_fallback_key_here

# Enhanced Features
SPORTSRADAR_API_KEY=your_key_here
OPENWEATHER_API_KEY=your_key_here
PEXELS_API_KEY=your_key_here

# Email Service (for verification & password reset)
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM="Parlay Gorilla <noreply@parlaygorilla.com>"  # optional, once domain verified
```

### Payment Providers (Set If You Set Them Up)

**LemonSqueezy (Card Payments):**
```
LEMONSQUEEZY_API_KEY=your_key_here
LEMONSQUEEZY_STORE_ID=your_store_id_here
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_here
LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_LIFETIME_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_10_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_25_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_50_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_100_VARIANT_ID=your_variant_id_here
```

**Coinbase Commerce (Crypto Payments):**
```
COINBASE_COMMERCE_API_KEY=your_key_here
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret_here
```

### Inscriptions Worker (Set If You Set It Up)

```
SIGNER_PRIVATE_KEY=your_solana_private_key_here
RPC=https://api.mainnet-beta.solana.com
```

## 📚 See Complete Guide

For a complete list with all variables, descriptions, and your current values, see:
- **[RENDER_BACKEND_ENV_COMPLETE.md](./RENDER_BACKEND_ENV_COMPLETE.md)** - Full comprehensive guide

## 🟢 Frontend Service (`parlay-gorilla-frontend`)

### Auto-Wired by Render (Don't Set These)

These are automatically set by Render from the `render.yaml` Blueprint:
- `PG_BACKEND_URL` - From backend service (private network)
- `NEXT_PUBLIC_SITE_URL` - Set to `https://www.parlaygorilla.com` (or your domain)
- `NEXT_PUBLIC_API_URL` - Set to `https://api.parlaygorilla.com` (or your domain)

**Note:** If using custom domains, update `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_API_URL` in `render.yaml` before deploying.

## 📝 How to Set Variables in Render

1. Go to your Render dashboard
2. Click on your service (e.g., `parlay-gorilla-backend`)
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Paste the key and value
6. Click **Save Changes**
7. Render will automatically redeploy

## 🔗 Quick Links

- [Render Dashboard](https://dashboard.render.com)
- [Render Environment Variables Docs](https://render.com/docs/environment-variables)
- [Full Setup Guide](./RENDER_SETUP_GUIDE.md)

