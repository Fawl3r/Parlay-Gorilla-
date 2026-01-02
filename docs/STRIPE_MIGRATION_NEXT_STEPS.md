# Stripe Migration - Next Steps

## ✅ Completed

All code changes are complete:
- ✅ Stripe backend service and webhooks
- ✅ Frontend integration
- ✅ Database migration
- ✅ Compliance copy updates
- ✅ Test files
- ✅ Documentation

## 🚀 Immediate Next Steps

### 1. Run Database Migration

```bash
cd backend
alembic upgrade head
```

This will:
- Add `stripe_customer_id` and `stripe_subscription_id` columns to `users` table
- Migrate existing subscription plans from `lemonsqueezy` to `stripe` provider
- Migrate existing subscriptions from `lemonsqueezy` to `stripe` provider

### 2. Set Up Stripe Account & Products

1. **Create Stripe Account** (if not already done)
   - Go to https://dashboard.stripe.com
   - Complete account setup

2. **Create Products & Prices in Stripe Dashboard**
   - Create product: "Parlay Gorilla Pro Monthly"
     - Price: $39.99/month (recurring)
     - Copy the Price ID (starts with `price_`)
   - Create product: "Parlay Gorilla Pro Annual"
     - Price: $399.99/year (recurring)
     - Copy the Price ID (starts with `price_`)

3. **Update Database with Stripe Price IDs**

   Option A: Via Admin Panel (if available)
   - Update `subscription_plans` table:
     - Set `provider` = `'stripe'`
     - Set `provider_price_id` = your Stripe Price ID
     - For plan codes: `PG_PRO_MONTHLY` and `PG_PRO_ANNUAL`

   Option B: Via SQL
   ```sql
   UPDATE subscription_plans 
   SET provider = 'stripe', 
       provider_price_id = 'price_xxxxx' 
   WHERE code = 'PG_PRO_MONTHLY';
   
   UPDATE subscription_plans 
   SET provider = 'stripe', 
       provider_price_id = 'price_xxxxx' 
   WHERE code = 'PG_PRO_ANNUAL';
   ```

### 3. Configure Environment Variables

Add to your `.env` file (or production environment):

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_test_xxxxx  # Use sk_live_xxxxx for production
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# Stripe Price IDs (fallback if not in database)
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxxxx
STRIPE_PRICE_ID_PRO_ANNUAL=price_xxxxx

# Stripe URLs (optional - defaults provided)
STRIPE_SUCCESS_URL={app_url}/billing/success?provider=stripe
STRIPE_CANCEL_URL={app_url}/billing?canceled=true
```

### 4. Set Up Stripe Webhook

1. **Go to Stripe Dashboard** → Webhooks
2. **Click "Add endpoint"**
3. **Enter URL:**
   - Production: `https://api.parlaygorilla.com/api/webhooks/stripe`
   - Development: Use ngrok or Stripe CLI (see below)
4. **Select Events:**
   - ✅ `checkout.session.completed`
   - ✅ `customer.subscription.created`
   - ✅ `customer.subscription.updated`
   - ✅ `customer.subscription.deleted`
   - ✅ `invoice.paid`
   - ✅ `invoice.payment_failed`
5. **Copy Webhook Signing Secret** (starts with `whsec_`)
6. **Add to environment:** `STRIPE_WEBHOOK_SECRET=whsec_xxxxx`

### 5. Test Locally (Development)

#### Using Stripe CLI (Recommended)

```bash
# Install Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# In another terminal, trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created
```

#### Using ngrok

```bash
# Install ngrok: https://ngrok.com/
ngrok http 8000

# Use the ngrok URL in Stripe Dashboard webhook configuration
# Example: https://abc123.ngrok.io/api/webhooks/stripe
```

### 6. Run Smoke Tests

```bash
# Set test credentials (optional)
export TEST_EMAIL=test@example.com
export TEST_PASSWORD=TestPassword123!
export BACKEND_URL=http://localhost:8000

# Run smoke tests
python scripts/smoke_test_auth_and_billing.py
```

### 7. Test End-to-End Flow

1. **Start Backend:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test Subscription Flow:**
   - Go to `/pricing`
   - Click "Upgrade" on a plan
   - Should redirect to Stripe Checkout (test mode)
   - Use test card: `4242 4242 4242 4242`
   - Complete checkout
   - Verify webhook received in Stripe Dashboard
   - Verify subscription activated in database

4. **Test Portal:**
   - Go to `/billing`
   - Click "Manage Plan"
   - Should redirect to Stripe Customer Portal
   - Test canceling subscription
   - Verify webhook received

## 🔍 Verification Checklist

- [ ] Database migration ran successfully
- [ ] Stripe products and prices created
- [ ] Price IDs added to database or config
- [ ] Environment variables set
- [ ] Webhook endpoint configured in Stripe Dashboard
- [ ] Webhook secret added to environment
- [ ] Local testing with Stripe CLI/ngrok works
- [ ] Smoke tests pass
- [ ] End-to-end subscription flow works
- [ ] Portal access works
- [ ] Webhooks are being received and processed

## 📊 Monitoring

After going live, monitor:

1. **Stripe Dashboard:**
   - Webhook delivery logs
   - Failed webhook deliveries
   - Payment failures

2. **Backend Logs:**
   - Webhook processing errors
   - Checkout creation failures
   - Portal session creation failures

3. **Database:**
   - `payment_events` table for webhook events
   - `subscriptions` table for subscription status
   - `users` table for `stripe_customer_id` and `stripe_subscription_id`

## 🧹 Cleanup (After Verification)

Once Stripe is fully verified and working:

1. **Remove LemonSqueezy Files** (optional - kept for migration safety):
   ```bash
   # Backend
   rm backend/app/services/lemonsqueezy_*.py
   rm backend/app/api/routes/webhooks/lemonsqueezy_webhook_routes.py
   
   # Frontend
   rm frontend/lib/lemonsqueezy/*.ts
   rm frontend/tests/unit/LemonSqueezyAffiliateUrlBuilder.test.ts
   ```

2. **Remove LemonSqueezy Routes** (optional):
   - Remove from `backend/app/api/routes/webhooks/__init__.py`
   - Remove from `backend/app/api/routes/billing/subscription_routes.py`

3. **Remove LemonSqueezy Environment Variables** (optional):
   - Remove from `.env.example`
   - Remove from production environment

## 🆘 Troubleshooting

### Webhook Not Received

- Check webhook URL is correct
- Verify webhook secret matches
- Check server logs for errors
- Use Stripe Dashboard → Webhooks → View logs

### Signature Verification Failed

- Ensure `STRIPE_WEBHOOK_SECRET` is correct
- Verify using correct secret for environment (test vs live)
- Check webhook endpoint receives raw request body

### Checkout Creation Fails

- Verify `STRIPE_SECRET_KEY` is set
- Check Price ID exists in Stripe Dashboard
- Verify Price ID matches plan code

### Subscription Not Activating

- Check webhook was received (Stripe Dashboard)
- Check `payment_events` table for errors
- Verify user has `stripe_customer_id` set
- Check backend logs for processing errors

## 📚 Additional Resources

- [Stripe Webhook Setup Guide](./STRIPE_WEBHOOK_SETUP.md)
- [Stripe API Documentation](https://stripe.com/docs/api)
- [Stripe Testing Guide](https://stripe.com/docs/testing)

