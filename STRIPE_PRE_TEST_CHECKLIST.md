# Stripe Integration Pre-Test Checklist

**Purpose:** Verify all Stripe links and integrations are ready before entering test mode.

**Reference:** [Stripe Documentation](https://docs.stripe.com/)

---

## ✅ 1. Environment Configuration

### Backend Environment Variables

Verify these are set in your `.env` file:

- [ ] `STRIPE_SECRET_KEY` - Your Stripe secret key
  - **Test mode:** Starts with `sk_test_`
  - **Live mode:** Starts with `sk_live_`
  - **Location:** Stripe Dashboard → Developers → API keys

- [ ] `STRIPE_WEBHOOK_SECRET` - Webhook signing secret
  - **Test mode:** Starts with `whsec_test_`
  - **Live mode:** Starts with `whsec_`
  - **Location:** Stripe Dashboard → Developers → Webhooks → [Your webhook] → Signing secret

- [ ] `STRIPE_PRICE_ID_PRO_MONTHLY` - Monthly subscription price ID
  - Format: `price_xxxxxxxxxxxxx`
  - **Location:** Stripe Dashboard → Products → [Your monthly product] → Pricing

- [ ] `STRIPE_PRICE_ID_PRO_ANNUAL` - Annual subscription price ID
  - Format: `price_xxxxxxxxxxxxx`
  - **Location:** Stripe Dashboard → Products → [Your annual product] → Pricing

- [ ] `APP_URL` - Frontend URL for redirects
  - Example: `https://parlaygorilla.com` (production) or `http://localhost:3000` (dev)
  - Used for success/cancel redirects

### Frontend Environment Variables

- [ ] `NEXT_PUBLIC_SITE_URL` - Public site URL
  - Should match `APP_URL` from backend

---

## ✅ 2. Stripe Dashboard Setup

### Products & Prices

- [ ] **Monthly Subscription Product Created**
  - Product name: "Parlay Gorilla Pro Monthly" (or similar)
  - Price: $39.99/month (recurring)
  - Price ID copied to `STRIPE_PRICE_ID_PRO_MONTHLY`

- [ ] **Annual Subscription Product Created**
  - Product name: "Parlay Gorilla Pro Annual" (or similar)
  - Price: $399.99/year (recurring)
  - Price ID copied to `STRIPE_PRICE_ID_PRO_ANNUAL`

- [ ] **Credit Pack Products Created** (if applicable)
  - Each credit pack needs a Stripe Price ID
  - Price IDs should be stored in `subscription_plans` table with pattern `PG_{CREDIT_PACK_ID_UPPERCASE}`

### Webhook Configuration

- [ ] **Webhook Endpoint Created**
  - URL: `{BACKEND_URL}/api/webhooks/stripe`
  - Example: `https://api.parlaygorilla.com/api/webhooks/stripe`
  - **Important:** Must be HTTPS in production

- [ ] **Webhook Events Subscribed**
  - ✅ `checkout.session.completed`
  - ✅ `customer.subscription.created`
  - ✅ `customer.subscription.updated`
  - ✅ `customer.subscription.deleted`
  - ✅ `invoice.paid`
  - ✅ `invoice.payment_failed`

- [ ] **Webhook Secret Copied**
  - Copy the signing secret to `STRIPE_WEBHOOK_SECRET`

### Test Mode vs Live Mode

- [ ] **Test Mode Enabled** (for testing)
  - Toggle in Stripe Dashboard (top right)
  - Use test API keys (`sk_test_...`)
  - Use test webhook secret (`whsec_test_...`)

- [ ] **Live Mode Ready** (for production)
  - Toggle to live mode when ready
  - Use live API keys (`sk_live_...`)
  - Use live webhook secret (`whsec_...`)

---

## ✅ 3. Database Configuration

### Subscription Plans Table

- [ ] **Plans Exist in Database**
  - Check `subscription_plans` table has:
    - `PG_PRO_MONTHLY` with `provider='stripe'`
    - `PG_PRO_ANNUAL` with `provider='stripe'`

- [ ] **Price IDs Set**
  - `provider_product_id` field contains Stripe Price ID
  - OR `STRIPE_PRICE_ID_PRO_MONTHLY` / `STRIPE_PRICE_ID_PRO_ANNUAL` in env vars

### Credit Packs (if applicable)

- [ ] **Credit Pack Plans Exist**
  - Each credit pack has a corresponding plan in `subscription_plans`
  - Plan code pattern: `PG_{CREDIT_PACK_ID_UPPERCASE}`
  - `provider='stripe'` and `provider_product_id` set

---

## ✅ 4. Backend API Routes

### Subscription Checkout

- [ ] **Route:** `POST /api/billing/stripe/checkout`
  - **File:** `backend/app/api/routes/billing/subscription_routes.py`
  - **Status:** ✅ Implemented
  - **Test:** Create checkout session for subscription

### Customer Portal

- [ ] **Route:** `POST /api/billing/stripe/portal`
  - **File:** `backend/app/api/routes/billing/subscription_routes.py`
  - **Status:** ✅ Implemented
  - **Test:** Create portal session for subscription management

### Credit Pack Checkout

- [ ] **Route:** `POST /api/billing/credits/checkout`
  - **File:** `backend/app/api/routes/billing/credit_pack_routes.py`
  - **Status:** ✅ Implemented
  - **Test:** Create checkout session for credit pack

### Parlay Purchase Checkout

- [ ] **Route:** `POST /api/billing/parlay-purchase/checkout`
  - **File:** `backend/app/api/routes/billing/parlay_purchase_routes.py`
  - **Status:** ✅ Implemented
  - **Test:** Create checkout session for one-time parlay purchase

### Webhook Handler

- [ ] **Route:** `POST /api/webhooks/stripe`
  - **File:** `backend/app/api/routes/webhooks/stripe_webhook_routes.py`
  - **Status:** ✅ Implemented
  - **Test:** Webhook receives and processes events

---

## ✅ 5. Frontend Integration

### Pricing Page

- [ ] **Monthly Subscription Button**
  - **File:** `frontend/app/pricing/_components/PricingPlansSection.tsx`
  - **Action:** Calls `createCheckout("stripe", planCode)`
  - **Test:** Click button → redirects to Stripe checkout

- [ ] **Annual Subscription Button**
  - **File:** `frontend/app/pricing/_components/PricingPlansSection.tsx`
  - **Action:** Calls `createCheckout("stripe", planCode)`
  - **Test:** Click button → redirects to Stripe checkout

### Billing Page

- [ ] **Credit Pack Purchase Buttons**
  - **File:** `frontend/app/billing/page.tsx`
  - **Action:** Calls `/api/billing/credits/checkout`
  - **Test:** Click button → redirects to Stripe checkout

- [ ] **Manage Subscription Button**
  - **File:** `frontend/app/billing/page.tsx`
  - **Action:** Calls `createPortal()`
  - **Test:** Click button → redirects to Stripe Customer Portal

### Subscription Context

- [ ] **Checkout Function**
  - **File:** `frontend/lib/subscription-context.tsx`
  - **Function:** `createCheckout(planCode)`
  - **Endpoint:** `POST /api/billing/stripe/checkout`
  - **Test:** Function returns checkout URL

- [ ] **Portal Function**
  - **File:** `frontend/lib/subscription-context.tsx`
  - **Function:** `createPortal()`
  - **Endpoint:** `POST /api/billing/stripe/portal`
  - **Test:** Function returns portal URL

---

## ✅ 6. Redirect URLs

### Success URLs

- [ ] **Subscription Success:** `{APP_URL}/billing/success?provider=stripe`
  - **File:** `backend/app/core/config.py` → `stripe_success_url`
  - **Test:** User redirected here after successful payment

- [ ] **One-Time Payment Success:** `{APP_URL}/billing/success?provider=stripe`
  - **File:** `backend/app/services/stripe_service.py` → `create_one_time_checkout_session()`
  - **Test:** User redirected here after successful credit/parlay purchase

### Cancel URLs

- [ ] **Cancel URL:** `{APP_URL}/billing?canceled=true`
  - **File:** `backend/app/core/config.py` → `stripe_cancel_url`
  - **Test:** User redirected here if they cancel checkout

---

## ✅ 7. Webhook Processing

### Event Handling

- [ ] **checkout.session.completed**
  - Handles one-time payments (credits, parlays)
  - Logs subscription checkouts (waits for `customer.subscription.created`)
  - **File:** `backend/app/api/routes/webhooks/stripe_webhook_routes.py`

- [ ] **customer.subscription.created**
  - Activates subscription in database
  - Updates user subscription fields
  - Resets usage counters
  - **File:** `backend/app/services/stripe_service.py` → `_handle_subscription_created()`

- [ ] **customer.subscription.updated**
  - Updates subscription status
  - Updates renewal dates
  - **File:** `backend/app/services/stripe_service.py` → `_handle_subscription_updated()`

- [ ] **customer.subscription.deleted**
  - Cancels subscription
  - Updates user status
  - **File:** `backend/app/services/stripe_service.py` → `_handle_subscription_deleted()`

- [ ] **invoice.paid**
  - Handles subscription renewals
  - Resets usage counters
  - **File:** `backend/app/services/stripe_service.py` → `_handle_invoice_paid()`

- [ ] **invoice.payment_failed**
  - Marks subscription as past_due
  - **File:** `backend/app/services/stripe_service.py` → `_handle_invoice_payment_failed()`

### Idempotency

- [ ] **Duplicate Event Prevention**
  - Events logged in `payment_events` table
  - Duplicate `event_id` values are ignored
  - **File:** `backend/app/api/routes/webhooks/stripe_webhook_routes.py`

---

## ✅ 8. Test Mode Verification

### Stripe Test Cards

Use these test cards in Stripe test mode:

- [ ] **Successful Payment:** `4242 4242 4242 4242`
  - Any future expiry date
  - Any 3-digit CVC
  - Any ZIP code

- [ ] **Declined Payment:** `4000 0000 0000 0002`
  - Tests declined card handling

- [ ] **Requires Authentication:** `4000 0025 0000 3155`
  - Tests 3D Secure flow

### Test Checklist

- [ ] **Subscription Checkout**
  1. Click "Subscribe" button on pricing page
  2. Complete checkout with test card `4242 4242 4242 4242`
  3. Verify redirect to success page
  4. Check database: `users.subscription_status = "active"`
  5. Check database: `subscriptions` table has new record
  6. Verify user can access premium features

- [ ] **Credit Pack Purchase**
  1. Click "Buy Credits" button on billing page
  2. Complete checkout with test card
  3. Verify redirect to success page
  4. Check database: `users.credit_balance` increased
  5. Check database: `credit_pack_purchases` table has new record
  6. Verify credits can be spent

- [ ] **Parlay Purchase**
  1. Click "Buy Parlay" button (when limit reached)
  2. Complete checkout with test card
  3. Verify redirect to success page
  4. Check database: `parlay_purchases` table has record with `status="available"`
  5. Verify user can generate parlay

- [ ] **Customer Portal**
  1. Click "Manage Subscription" on billing page
  2. Verify redirect to Stripe Customer Portal
  3. Test cancel subscription
  4. Verify subscription cancelled in database

- [ ] **Webhook Testing**
  1. Use Stripe CLI: `stripe listen --forward-to localhost:8000/api/webhooks/stripe`
  2. Trigger test events: `stripe trigger checkout.session.completed`
  3. Verify webhook received and processed
  4. Check logs for success messages

---

## ✅ 9. Error Handling

### Configuration Errors

- [ ] **Missing Stripe Key**
  - Error: "Payment system not configured"
  - **File:** `backend/app/api/routes/billing/subscription_routes.py`

- [ ] **Missing Price ID**
  - Error: "Stripe price ID not configured"
  - **File:** `backend/app/services/stripe_service.py`

### Payment Errors

- [ ] **Declined Card**
  - Stripe handles and shows error to user
  - User can retry with different card

- [ ] **Webhook Errors**
  - Errors logged in `payment_events` table
  - Event marked as `processed="failed"`
  - Webhook returns 200 to prevent retries

---

## ✅ 10. Security

### Webhook Verification

- [ ] **Signature Verification Enabled**
  - Webhook secret configured
  - Signatures verified on all webhook requests
  - **File:** `backend/app/api/routes/webhooks/stripe_webhook_routes.py`

### API Key Security

- [ ] **Secret Key Never Exposed**
  - Only used in backend
  - Never sent to frontend
  - Stored in environment variables only

### Metadata

- [ ] **User ID in Metadata**
  - All checkout sessions include `user_id` in metadata
  - Used for webhook processing
  - **File:** `backend/app/services/stripe_service.py`

---

## ✅ 11. Documentation

- [ ] **Stripe Webhook Verification Guide**
  - **File:** `STRIPE_WEBHOOK_VERIFICATION.md`
  - ✅ Complete and up-to-date

- [ ] **Environment Variables Documented**
  - **File:** `backend/.env.example`
  - ✅ All Stripe variables included

- [ ] **API Routes Documented**
  - Checkout endpoints documented
  - Webhook endpoint documented

---

## 🚨 Critical Issues to Fix Before Test Mode

If any of these are missing, **DO NOT** proceed to test mode:

1. ❌ **Missing `STRIPE_SECRET_KEY`** - Checkout will fail
2. ❌ **Missing `STRIPE_WEBHOOK_SECRET`** - Webhooks won't verify (security risk)
3. ❌ **Missing Price IDs** - Checkout sessions can't be created
4. ❌ **Webhook endpoint not configured** - Payments won't activate subscriptions/credits
5. ❌ **Webhook events not subscribed** - Events won't be received
6. ❌ **Database plans not configured** - Plans won't be found

---

## 📋 Quick Test Commands

### Test Webhook Locally

```bash
# Install Stripe CLI
# https://stripe.com/docs/stripe-cli

# Login to Stripe
stripe login

# Forward webhooks to local server
stripe listen --forward-to localhost:8000/api/webhooks/stripe

# Trigger test events
stripe trigger checkout.session.completed
stripe trigger customer.subscription.created
```

### Test Checkout Session Creation

```bash
# Using curl (replace with your actual values)
curl -X POST http://localhost:8000/api/billing/stripe/checkout \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_code": "PG_PRO_MONTHLY"}'
```

---

## ✅ Final Verification

Before entering test mode, verify:

- [ ] All environment variables set
- [ ] Stripe products and prices created
- [ ] Webhook endpoint configured and accessible
- [ ] All webhook events subscribed
- [ ] Database plans configured
- [ ] Frontend buttons wired correctly
- [ ] Success/cancel URLs working
- [ ] Webhook signature verification enabled
- [ ] Test cards ready for testing

---

## 📞 Support Resources

- **Stripe Dashboard:** https://dashboard.stripe.com
- **Stripe Documentation:** https://docs.stripe.com/
- **Stripe Test Cards:** https://stripe.com/docs/testing
- **Stripe Webhook Testing:** https://stripe.com/docs/webhooks/test

---

**Last Updated:** January 2026  
**Status:** Ready for test mode verification

