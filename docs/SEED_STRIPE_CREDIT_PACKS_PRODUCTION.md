# 🌱 Seed Stripe Credit Packs on Production

This guide shows you how to run the credit pack seeding script on your production database.

## ✅ Option 1: Render Shell (Recommended)

This is the easiest method since all environment variables are already configured in Render.

### Steps:

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Login if needed

2. **Navigate to Backend Service:**
   - Click: **Services** → `parlay-gorilla-backend`

3. **Open Shell:**
   - Click: **Shell** tab (or "Open Shell" button)
   - This opens an interactive terminal with production environment

4. **Run the Script:**
   ```bash
   cd backend
   python scripts/seed_stripe_credit_packs.py
   ```

5. **Verify Success:**
   - You should see output like:
     ```
     ============================================================
     Seeding Stripe Credit Pack Plans
     ============================================================
     
     📝 Creating new plan 'PG_CREDITS_10'...
        ✅ Created successfully!
        Name: 10 Credits
        Price: $9.99
        Stripe Price ID: price_1Snl9tBY5GL34hiruQIsgmaL
        Credits: 10
     
     ... (similar for other packs)
     
     ============================================================
     ✅ Credit pack seeding complete!
     ============================================================
     Summary:
       Created: 4
       Updated: 0
       Skipped: 0
     ```

---

## ✅ Option 2: Run Locally with Production DATABASE_URL

If you prefer to run locally, you'll need to set the production DATABASE_URL.

### Steps:

1. **Get Production DATABASE_URL:**
   - Go to Render Dashboard
   - Navigate to: **Databases** → `parlay-gorilla-postgres`
   - Click: **Connections** tab
   - Copy the **Internal Database URL** (starts with `postgresql://`)

2. **Get Stripe Price IDs from Render:**
   - Go to: **Services** → `parlay-gorilla-backend` → **Environment** tab
   - Copy these values:
     - `STRIPE_PRICE_ID_CREDITS_10`
     - `STRIPE_PRICE_ID_CREDITS_25`
     - `STRIPE_PRICE_ID_CREDITS_50`
     - `STRIPE_PRICE_ID_CREDITS_100`

3. **Run Locally (PowerShell):**
   ```powershell
   cd backend
   
   # Set production database URL
   $env:DATABASE_URL="postgresql://user:pass@dpg-xxx-a.oregon-postgres.render.com/parlaygorilla"
   
   # Set Stripe Price IDs
   $env:STRIPE_PRICE_ID_CREDITS_10="price_1Snl9tBY5GL34hiruQIsgmaL"
   $env:STRIPE_PRICE_ID_CREDITS_25="price_1SnlB0BY5GL34hirjhHN0OEu"
   $env:STRIPE_PRICE_ID_CREDITS_50="price_1SnlBrBY5GL34hirM0PjBja4"
   $env:STRIPE_PRICE_ID_CREDITS_100="price_1SnlCyBY5GL34hirRNJzeEdB"
   
   # Run the script
   python scripts/seed_stripe_credit_packs.py
   ```

4. **Or Run Locally (Bash):**
   ```bash
   cd backend
   
   # Set production database URL
   export DATABASE_URL="postgresql://user:pass@dpg-xxx-a.oregon-postgres.render.com/parlaygorilla"
   
   # Set Stripe Price IDs
   export STRIPE_PRICE_ID_CREDITS_10="price_1Snl9tBY5GL34hiruQIsgmaL"
   export STRIPE_PRICE_ID_CREDITS_25="price_1SnlB0BY5GL34hirjhHN0OEu"
   export STRIPE_PRICE_ID_CREDITS_50="price_1SnlBrBY5GL34hirM0PjBja4"
   export STRIPE_PRICE_ID_CREDITS_100="price_1SnlCyBY5GL34hirRNJzeEdB"
   
   # Run the script
   python scripts/seed_stripe_credit_packs.py
   ```

---

## 🔍 Verify the Plans Were Created

After running the script, verify the plans exist in your database:

### Option A: Check via API

```bash
# Get all subscription plans (if you have an API endpoint)
curl https://api.parlaygorilla.com/api/subscription-plans
```

### Option B: Check via Database Query

If you have database access, run:

```sql
SELECT code, name, price_cents, provider, provider_price_id 
FROM subscription_plans 
WHERE code LIKE 'PG_CREDITS%'
ORDER BY code;
```

You should see:
- `PG_CREDITS_10` - $9.99
- `PG_CREDITS_25` - $19.99
- `PG_CREDITS_50` - $34.99
- `PG_CREDITS_100` - $59.99

---

## 🐛 Troubleshooting

### "No Stripe Price ID found" Error

- **Cause:** Environment variables not set
- **Fix:** Ensure all `STRIPE_PRICE_ID_CREDITS_*` variables are set in Render or locally

### "Connection refused" Error

- **Cause:** Database URL incorrect or database not accessible
- **Fix:** 
  - Verify the DATABASE_URL is correct
  - Use "Internal Database URL" from Render (not External)
  - Ensure your IP is allowed (if using External URL)

### "Plan already exists" Message

- **This is normal!** The script will update existing plans if they already exist
- Check the output - it should say "Updated" instead of "Created"

### Script Runs But No Plans Created

- Check the script output for any errors
- Verify the database connection is working
- Check Render logs for any database errors

---

## 📋 What the Script Does

The script creates/updates 4 subscription plans in the `subscription_plans` table:

1. **PG_CREDITS_10** - 10 Credits for $9.99
2. **PG_CREDITS_25** - 25 Credits for $19.99
3. **PG_CREDITS_50** - 50 Credits for $34.99 (includes 5 bonus credits)
4. **PG_CREDITS_100** - 100 Credits for $59.99 (includes 15 bonus credits)

Each plan is configured with:
- Provider: `stripe`
- Billing cycle: `one_time`
- Stripe Price ID from environment variables
- Pricing from `billing_config.py`

---

## ✅ Next Steps

After seeding the plans:

1. **Test Credit Pack Purchase:**
   - Go to your billing page
   - Try purchasing a credit pack
   - Verify credits are added to your account

2. **Verify Webhook Processing:**
   - Check Stripe Dashboard → Webhooks → Logs
   - Verify `checkout.session.completed` events are being received
   - Check Render logs for webhook processing

3. **Monitor for Errors:**
   - Watch Render logs for any payment processing errors
   - Check Stripe Dashboard for failed payments

---

**Last Updated:** Based on `backend/scripts/seed_stripe_credit_packs.py`

