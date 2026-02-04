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

### 512MB Instance – OOM Mitigation (Recommended for Free/Starter)

If the backend runs on 512MB and parlay generator OOMs, set these in Render **Environment**:

```
# Single worker (multiple workers duplicate memory)
WEB_CONCURRENCY=1

# Lower prefetch so we don't load too much at once
PROBABILITY_PREFETCH_CONCURRENCY=2
PROBABILITY_PREFETCH_MAX_GAMES=12
PROBABILITY_PREFETCH_TOTAL_TIMEOUT_SECONDS=6

# Optional: stricter parlay candidate caps (defaults in code: 40 games, 200 legs)
# PARLAY_MAX_GAMES_CONSIDERED=40
# PARLAY_MAX_LEGS_CONSIDERED=200
```

**Start command** (in Render Service → Settings): use one worker only, e.g.  
`gunicorn -k uvicorn.workers.UvicornWorker -w 1 -t 120 --max-requests 200 --max-requests-jitter 50 backend.app.main:app`

### Optional Variables (Set If You Have Them)

```
# The Odds API Fallback (recommended)
THE_ODDS_API_FALLBACK_KEY=your_fallback_key_here

# Enhanced Features
API_SPORTS_API_KEY=your_key_here
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

**Stripe (Card Payments - Subscriptions & Credit Packs):**
```
STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO_ANNUAL=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_PRO_LIFETIME=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_CREDITS_10=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_CREDITS_25=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_CREDITS_50=price_xxxxxxxxxxxxx
STRIPE_PRICE_ID_CREDITS_100=price_xxxxxxxxxxxxx
STRIPE_SUCCESS_URL={app_url}/billing/success?provider=stripe
STRIPE_CANCEL_URL={app_url}/billing?canceled=true
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

