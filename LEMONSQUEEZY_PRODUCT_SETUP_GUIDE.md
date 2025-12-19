# 🍋 LemonSqueezy Product Setup Guide

Complete step-by-step guide for creating all products and variants in LemonSqueezy to get the variant IDs needed for Parlay Gorilla.

---

## 📋 Prerequisites

1. **LemonSqueezy Account**: Sign up at [app.lemonsqueezy.com](https://app.lemonsqueezy.com)
2. **Store Created**: You should have a store set up
3. **API Access**: You'll need your Store ID (found in Settings → General)

---

## 🎯 Products to Create

You need to create **7 products** total:

### Subscriptions (3 products):
1. **Premium Monthly** - $39.99/month recurring
2. **Premium Annual** - $399.99/year recurring  
3. **Lifetime Membership** - $500.00 one-time

### Credit Packs (4 products):
4. **10 Credits** - $9.99 one-time
5. **25 Credits** - $19.99 one-time
6. **50 Credits** - $34.99 one-time (includes 5 bonus = 55 total)
7. **100 Credits** - $59.99 one-time (includes 15 bonus = 115 total)

---

## 📝 Step-by-Step: Creating Products

### Part 1: Create Subscription Products

#### 1. Premium Monthly Subscription

1. **Go to Products**:
   - Dashboard → **Products** → **New Product**

2. **Product Details**:
   - **Name**: `Gorilla Premium Monthly`
   - **Description**: 
     ```
     200 AI parlays per rolling 30-day period, 25 custom builder actions/day, upset finder, and all premium features.
     
     Features:
     • 200 AI parlays / 30 days (rolling)
     • Custom parlay builder (25 per day)
     • Gorilla Upset Finder
     • Multi-sport parlays
     • Deep analysis with insights
     • Full confidence breakdowns
     • Live game insights
     • Unlimited parlay history
     • ROI tracking
     • Priority support
     • Ad-free experience
     ```
   - **Product Type**: Select **Subscription**
   - **Billing Interval**: Select **Monthly**
   - **Price**: `$39.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `Monthly Subscription` (or leave default)
   - **Price**: `$39.99`
   - **Billing Interval**: `Monthly`
   - **Trial Period**: Leave empty (or set if you want trials)

4. **Save Product**:
   - Click **Save** or **Create Product**

5. **Copy Variant ID**:
   - After saving, you'll see the product page
   - Click on the **variant** (or go to Variants tab)
   - Copy the **Variant ID** (looks like: `123456`)
   - **Save this** → You'll need it for `LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID`

---

#### 2. Premium Annual Subscription

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `Gorilla Premium Annual`
   - **Description**: 
     ```
     Save ~$80/year. Same premium tools + limits, billed yearly.
     
     Features:
     • 200 AI parlays / 30 days (rolling)
     • Custom parlay builder (25 per day)
     • Gorilla Upset Finder
     • Multi-sport parlays
     • Deep analysis with insights
     • Full confidence breakdowns
     • Live game insights
     • Unlimited parlay history
     • ROI tracking
     • Priority support
     • Ad-free experience
     ```
   - **Product Type**: Select **Subscription**
   - **Billing Interval**: Select **Yearly** (or Annual)
   - **Price**: `$399.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `Annual Subscription`
   - **Price**: `$399.99`
   - **Billing Interval**: `Yearly` (or Annual)
   - **Trial Period**: Leave empty

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID`

---

#### 3. Lifetime Membership

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `Gorilla Lifetime`
   - **Description**: 
     ```
     One-time payment for lifetime access to all premium features. Pay with card. Never pay again!
     
     Features:
     • Unlimited AI parlays
     • Custom parlay builder (unlimited)
     • Gorilla Upset Finder
     • Multi-sport parlays
     • Deep analysis with insights
     • Full confidence breakdowns
     • Live game insights
     • Unlimited parlay history
     • ROI tracking
     • Priority support
     • Ad-free experience
     ```
   - **Product Type**: Select **One-time** (not subscription)
   - **Price**: `$500.00`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `Lifetime Membership`
   - **Price**: `$500.00`
   - **Product Type**: `One-time` (not recurring)

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_LIFETIME_VARIANT_ID`

---

### Part 2: Create Credit Pack Products

#### 4. 10 Credits Pack

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `10 Credits`
   - **Description**: 
     ```
     10 credits for Parlay Gorilla. Use credits to generate AI parlays and access premium features.
     
     Each credit pack purchase gives you credits that can be used for:
     • AI parlay generation (10 credits per parlay)
     • Custom parlay builder actions
     • Premium feature access
     ```
   - **Product Type**: Select **One-time**
   - **Price**: `$9.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `10 Credits Pack`
   - **Price**: `$9.99`
   - **Product Type**: `One-time`

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_CREDITS_10_VARIANT_ID`

---

#### 5. 25 Credits Pack

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `25 Credits`
   - **Description**: 
     ```
     25 credits for Parlay Gorilla. Best value for most users!
     
     Use credits to generate AI parlays and access premium features.
     Each credit pack purchase gives you credits that can be used for:
     • AI parlay generation (10 credits per parlay)
     • Custom parlay builder actions
     • Premium feature access
     ```
   - **Product Type**: Select **One-time**
   - **Price**: `$19.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `25 Credits Pack`
   - **Price**: `$19.99`
   - **Product Type**: `One-time`

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_CREDITS_25_VARIANT_ID`

---

#### 6. 50 Credits Pack

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `50 Credits`
   - **Description**: 
     ```
     50 credits + 5 bonus credits = 55 total credits for Parlay Gorilla!
     
     Use credits to generate AI parlays and access premium features.
     Each credit pack purchase gives you credits that can be used for:
     • AI parlay generation (10 credits per parlay)
     • Custom parlay builder actions
     • Premium feature access
     ```
   - **Product Type**: Select **One-time**
   - **Price**: `$34.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `50 Credits Pack`
   - **Price**: `$34.99`
   - **Product Type**: `One-time`

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_CREDITS_50_VARIANT_ID`

---

#### 7. 100 Credits Pack

1. **Create New Product**:
   - Products → **New Product**

2. **Product Details**:
   - **Name**: `100 Credits`
   - **Description**: 
     ```
     100 credits + 15 bonus credits = 115 total credits for Parlay Gorilla!
     
     Use credits to generate AI parlays and access premium features.
     Each credit pack purchase gives you credits that can be used for:
     • AI parlay generation (10 credits per parlay)
     • Custom parlay builder actions
     • Premium feature access
     ```
   - **Product Type**: Select **One-time**
   - **Price**: `$59.99`
   - **Currency**: `USD`

3. **Variant Settings**:
   - **Variant Name**: `100 Credits Pack`
   - **Price**: `$59.99`
   - **Product Type**: `One-time`

4. **Save and Copy Variant ID**:
   - Save the product
   - Copy the **Variant ID**
   - **Save this** → You'll need it for `LEMONSQUEEZY_CREDITS_100_VARIANT_ID`

---

## 🔑 How to Find Variant IDs

After creating each product, you can find the Variant ID in several ways:

### Method 1: From Product Page
1. Go to **Products** → Click on the product
2. Click on the **Variants** tab
3. You'll see the variant listed with an **ID** (numeric)
4. Copy this ID

### Method 2: From URL
1. When viewing a variant, the URL will look like:
   ```
   https://app.lemonsqueezy.com/products/{product_id}/variants/{variant_id}
   ```
2. The `variant_id` in the URL is what you need

### Method 3: From API
1. Use the LemonSqueezy API to list variants:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        -H "Accept: application/vnd.api+json" \
        https://api.lemonsqueezy.com/v1/variants
   ```

---

## 📝 Update Your .env File

Once you have all the variant IDs, update your `backend/.env` file:

```env
# LemonSqueezy subscription variants
LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID=123456
LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID=123457
LEMONSQUEEZY_LIFETIME_VARIANT_ID=123458

# LemonSqueezy credit pack variants
LEMONSQUEEZY_CREDITS_10_VARIANT_ID=123459
LEMONSQUEEZY_CREDITS_25_VARIANT_ID=123460
LEMONSQUEEZY_CREDITS_50_VARIANT_ID=123461
LEMONSQUEEZY_CREDITS_100_VARIANT_ID=123462
```

**Replace the numbers above with your actual variant IDs.**

---

## ✅ Verification Checklist

After creating all products, verify:

- [ ] Premium Monthly subscription created ($39.99/month)
- [ ] Premium Annual subscription created ($399.99/year)
- [ ] Lifetime membership created ($500.00 one-time)
- [ ] 10 Credits pack created ($9.99)
- [ ] 25 Credits pack created ($19.99)
- [ ] 50 Credits pack created ($34.99)
- [ ] 100 Credits pack created ($59.99)
- [ ] All variant IDs copied to `.env` file
- [ ] Products are set to **Active** in LemonSqueezy
- [ ] Webhook configured (if not already done)

---

## 🔗 Additional Setup

### Webhook Configuration

Make sure your webhook is configured:

1. Go to **Settings** → **Webhooks**
2. Add webhook URL: `{YOUR_BACKEND_URL}/api/webhooks/lemonsqueezy`
   - Example: `https://api.parlaygorilla.com/api/webhooks/lemonsqueezy`
3. Select events to listen for:
   - `subscription_created`
   - `subscription_updated`
   - `subscription_cancelled`
   - `order_created`
   - `payment_success`
4. Copy the **Webhook Secret** → Add to `.env` as `LEMONSQUEEZY_WEBHOOK_SECRET`

### Store ID

1. Go to **Settings** → **General**
2. Find your **Store ID**
3. Copy it → Add to `.env` as `LEMONSQUEEZY_STORE_ID`

---

## 🧪 Testing

After setting up all products:

1. **Test Checkout Creation**:
   - Use your backend API to create a checkout
   - Verify the checkout URL is generated correctly
   - Test purchasing each product type

2. **Test Webhooks**:
   - Make a test purchase
   - Verify webhook is received
   - Check that subscription/credits are added correctly

3. **Verify Variant IDs**:
   - Check that all variant IDs in `.env` match your LemonSqueezy products
   - Test each product type to ensure they work

---

## 📚 Quick Reference: Product Summary

| Product | Type | Price | Variant ID Env Var |
|---------|------|-------|-------------------|
| Premium Monthly | Subscription | $39.99/month | `LEMONSQUEEZY_PREMIUM_MONTHLY_VARIANT_ID` |
| Premium Annual | Subscription | $399.99/year | `LEMONSQUEEZY_PREMIUM_ANNUAL_VARIANT_ID` |
| Lifetime | One-time | $500.00 | `LEMONSQUEEZY_LIFETIME_VARIANT_ID` |
| 10 Credits | One-time | $9.99 | `LEMONSQUEEZY_CREDITS_10_VARIANT_ID` |
| 25 Credits | One-time | $19.99 | `LEMONSQUEEZY_CREDITS_25_VARIANT_ID` |
| 50 Credits | One-time | $34.99 | `LEMONSQUEEZY_CREDITS_50_VARIANT_ID` |
| 100 Credits | One-time | $59.99 | `LEMONSQUEEZY_CREDITS_100_VARIANT_ID` |

---

## 🆘 Troubleshooting

### Variant ID Not Working

- **Check**: Variant ID is numeric (not product ID)
- **Check**: Product is set to **Active** in LemonSqueezy
- **Check**: Variant ID matches the one in LemonSqueezy dashboard
- **Check**: Store ID is correct in `.env`

### Checkout Not Creating

- **Check**: `LEMONSQUEEZY_API_KEY` is set correctly
- **Check**: `LEMONSQUEEZY_STORE_ID` matches your store
- **Check**: API key has proper permissions
- **Check**: Backend logs for error messages

### Webhooks Not Receiving

- **Check**: Webhook URL is publicly accessible
- **Check**: Webhook secret matches in `.env`
- **Check**: Webhook events are enabled in LemonSqueezy
- **Check**: Backend webhook endpoint is working

---

## 📖 Additional Resources

- [LemonSqueezy Dashboard](https://app.lemonsqueezy.com)
- [LemonSqueezy API Docs](https://docs.lemonsqueezy.com/api)
- [LemonSqueezy Help Center](https://docs.lemonsqueezy.com/help)

---

**Need Help?** Check the main project README or backend documentation for more details on integration.

