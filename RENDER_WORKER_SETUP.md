# 🔧 Render Worker Service Setup

## Issue: "Service type is not available for this plan"

The `parlay-gorilla-inscriptions-worker` service uses Render's **worker** service type, which requires a **paid plan** (Starter or higher). The free plan only supports web services.

## ✅ Solution Options

### Option 1: Skip the Worker (Recommended for Now)

The inscriptions worker is **optional** - it's only needed if you want to enable Solana blockchain inscriptions for custom parlays. You can:

1. **Deploy without the worker** - Your app will work fine, just without blockchain inscriptions
2. **Add it later** when you upgrade to a paid plan

**The worker is already commented out in `render.yaml`**, so you can deploy successfully now.

### Option 2: Upgrade to Paid Plan

If you want to enable the worker immediately:

1. **Upgrade your Render account** to Starter plan ($7/month) or higher
2. **Uncomment the worker section** in `render.yaml`:
   - Remove the `#` comments from the worker service
   - Change `plan: free` to `plan: starter`
3. **Redeploy** or add the service manually in Render dashboard

### Option 3: Add Worker Manually Later

You can add the worker service manually in Render dashboard after deployment:

1. **Go to Render Dashboard** → Click **"New +"** → **"Background Worker"**
2. **Configure**:
   - **Name**: `parlay-gorilla-inscriptions-worker`
   - **Environment**: Node
   - **Region**: Oregon
   - **Plan**: Starter ($7/month) or higher
   - **Root Directory**: `backend/inscriptions-worker`
   - **Build Command**: `npm install --no-audit --no-fund && npm run build`
   - **Start Command**: `npm run start`
3. **Add Environment Variables**:
   - `REDIS_URL` - From your Redis service
   - `DATABASE_URL` - From your PostgreSQL database
   - `SIGNER_PRIVATE_KEY` - Your Solana private key (if enabling inscriptions)
   - `RPC` - Your Solana RPC URL (if enabling inscriptions)
   - `IQ_HANDLE` - `ParlayGorilla`
   - `IQ_DATATYPE` - `parlay_proof`

---

## 📋 What the Worker Does

The inscriptions worker:
- Processes custom parlay inscriptions on Solana blockchain
- Consumes jobs from Redis queue
- Creates hash-only proof payloads on-chain
- Updates database with inscription status

**This is optional** - your app works fine without it. Users can still save custom parlays, they just won't be inscribed on-chain.

---

## 💰 Cost

- **Free Plan**: Worker services not available
- **Starter Plan**: $7/month per worker service
- **Pro Plan**: $25/month per worker service

---

## ✅ Current Status

The worker is **commented out** in `render.yaml`, so you can:
- ✅ Deploy successfully on the free plan
- ✅ Use all other features
- ✅ Add the worker later when needed

---

## 🚀 Next Steps

1. **Deploy your Blueprint** - It will work without the worker
2. **Test your app** - Everything should work except blockchain inscriptions
3. **Add worker later** - When you're ready, upgrade and uncomment the worker section

---

**You're all set! The deployment will work without the worker.** 🎉

