# 📋 Render Environment Variables - Quick Reference

Copy and paste these values into your Render dashboard after deploying.

## 🔴 Backend Service (`parlay-gorilla-backend`)

### Required Variables (Set These)

```
THE_ODDS_API_KEY=your_odds_api_key_here
THE_ODDS_API_FALLBACK_KEY=your_fallback_key_here
OPENAI_API_KEY=your_openai_api_key_here
FRONTEND_URL=https://parlay-gorilla-frontend.onrender.com
BACKEND_URL=https://parlay-gorilla-backend.onrender.com
APP_URL=https://parlay-gorilla-frontend.onrender.com
```

**Note:** Update `FRONTEND_URL`, `BACKEND_URL`, and `APP_URL` if you're using custom domains.

### Optional Variables (Set If You Have Them)

```
SPORTSRADAR_API_KEY=your_key_here
RESEND_API_KEY=re_your_api_key_here
RESEND_FROM="Parlay Gorilla <onboarding@resend.dev>"  # or your verified domain sender
OPENWEATHER_API_KEY=your_key_here
PEXELS_API_KEY=your_key_here
```

### Payment Providers (Set If You Set Them Up)

```
LEMONSQUEEZY_API_KEY=your_key_here
LEMONSQUEEZY_STORE_ID=your_store_id_here
LEMONSQUEEZY_WEBHOOK_SECRET=your_webhook_secret_here
LEMONSQUEEZY_CREDITS_10_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_25_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_50_VARIANT_ID=your_variant_id_here
LEMONSQUEEZY_CREDITS_100_VARIANT_ID=your_variant_id_here
```

```
COINBASE_COMMERCE_API_KEY=your_key_here
COINBASE_COMMERCE_WEBHOOK_SECRET=your_webhook_secret_here
```

### Inscriptions Worker (Set If You Set It Up)

```
SIGNER_PRIVATE_KEY=your_solana_private_key_here
RPC=https://api.mainnet-beta.solana.com
```

## ✅ Auto-Wired by Render (Don't Set These)

These are automatically set by Render from the `render.yaml` Blueprint:
- `DATABASE_URL` - From PostgreSQL database
- `REDIS_URL` - From Key Value store  
- `JWT_SECRET` - Auto-generated
- `ENVIRONMENT` - Set to `production`
- `DEBUG` - Set to `false`
- `USE_SQLITE` - Set to `false`
- `OPENAI_ENABLED` - Set to `true`

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

