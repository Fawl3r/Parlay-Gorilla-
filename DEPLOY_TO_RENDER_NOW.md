# 🚀 Deploy to Render - Quick Start Guide

Get your site live on Render in 15 minutes so you can get your domain up!

## ✅ Prerequisites Checklist

Before starting, make sure:
- [ ] Your code is committed to GitHub
- [ ] You have a GitHub account
- [ ] You have a Render account (sign up at https://render.com - it's free)

## 📋 Step-by-Step Deployment

### Step 1: Push Code to GitHub (If Not Already Done)

```bash
# Make sure you're in the project root
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

**Verify:** Your code is on GitHub at `https://github.com/YOUR_USERNAME/F3-Parlay-Gorilla` (or your repo name)

---

### Step 2: Deploy via Render Blueprint

1. **Go to Render Dashboard**: https://dashboard.render.com
2. **Click "New +"** → **"Blueprint"**
3. **Connect GitHub**:
   - If not connected, click "Connect GitHub"
   - Authorize Render to access your repos
   - Select your repository: `F3 Parlay Gorilla` (or your repo name)
4. **Render will auto-detect `render.yaml`** and show preview:
   - ✅ `parlay-gorilla-postgres` (Database)
   - ✅ `parlay-gorilla-redis` (Cache)
   - ✅ `parlay-gorilla-backend` (API)
   - ✅ `parlay-gorilla-frontend` (Website)
5. **Click "Apply"** to create everything

⏱️ **Wait 5-10 minutes** for services to deploy

---

### Step 3: Get Your Render URLs

After deployment, note these URLs (you'll need them):

1. Go to **Dashboard** → Find `parlay-gorilla-frontend` service
   - Copy the URL: `https://parlay-gorilla-frontend.onrender.com` (or similar)
2. Go to **Dashboard** → Find `parlay-gorilla-backend` service
   - Copy the URL: `https://parlay-gorilla-backend.onrender.com` (or similar)

---

### Step 4: Set Backend Environment Variables

1. Go to `parlay-gorilla-backend` service → **Environment** tab
2. Click **"Add Environment Variable"** and add these:

#### Required Variables (Copy from your `.env` file):

```
THE_ODDS_API_KEY=your_odds_api_key_here
THE_ODDS_API_FALLBACK_KEY=your_fallback_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

#### URL Variables (Use YOUR Render URLs from Step 3):

```
FRONTEND_URL=https://parlay-gorilla-frontend.onrender.com
BACKEND_URL=https://parlay-gorilla-backend.onrender.com
APP_URL=https://parlay-gorilla-frontend.onrender.com
```

**Replace the URLs above with YOUR actual Render URLs!**

#### Optional (But Recommended):

```
SPORTSRADAR_API_KEY=VWTUmCDH7i0VMLqC2i0GjbissbNe7GELF7XihpiP
OPENWEATHER_API_KEY=3c7b0addb7de780a3c7a1d2cc89fba77
RESEND_API_KEY=re_Zoqz4zwY_D9LgQBBDbznobq9VLEzxevLr
RESEND_FROM=Parlay Gorilla <onboarding@resend.dev>
```

3. Click **"Save Changes"** - Render will auto-redeploy

**✅ Auto-Wired (Don't Set These):**
- `DATABASE_URL` - Auto-wired from PostgreSQL
- `REDIS_URL` - Auto-wired from Redis
- `JWT_SECRET` - Auto-generated
- `ENVIRONMENT=production`
- `DEBUG=false`

---

### Step 5: Set Frontend Environment Variables

1. Go to `parlay-gorilla-frontend` service → **Environment** tab
2. Add this variable (use YOUR frontend URL):

```
NEXT_PUBLIC_SITE_URL=https://parlay-gorilla-frontend.onrender.com
```

**Replace with YOUR actual frontend URL!**

3. Click **"Save Changes"**

**✅ Auto-Wired (Don't Set These):**
- `PG_BACKEND_URL` - Auto-wired from backend
- `NEXT_PUBLIC_API_URL` - Set in render.yaml

---

### Step 6: Wait for Deployment & Test

1. **Wait for all services to show "Live"** (green status)
2. **Test your frontend**: Visit your frontend URL
3. **Test health check**: Visit `https://YOUR-BACKEND-URL.onrender.com/health`
4. **Test registration**: Try signing up at `/auth/signup`

---

## 🎯 What You'll Have

✅ **Live Website**: `https://parlay-gorilla-frontend.onrender.com`  
✅ **Live API**: `https://parlay-gorilla-backend.onrender.com`  
✅ **Working Database**: PostgreSQL (managed by Render)  
✅ **Working Redis**: For caching and jobs  

**You can now use these URLs to:**
- Sign up for LemonSqueezy
- Set up your custom domain
- Test your affiliate system

---

## 🔧 Troubleshooting

### Backend won't start?

1. **Check logs**: Backend service → **Logs** tab
2. **Common issues**:
   - Missing `THE_ODDS_API_KEY` → Add it in Environment
   - Missing `OPENAI_API_KEY` → Add it or set `OPENAI_ENABLED=false`
   - Database connection error → Wait 2-3 minutes for DB to finish provisioning

### Frontend won't build?

1. **Check logs**: Frontend service → **Logs** tab
2. **Common issues**:
   - Build timeout → Upgrade to `starter` plan ($7/month)
   - Missing env vars → Check that `NEXT_PUBLIC_SITE_URL` is set

### Database migration needed?

The backend will auto-create tables on first startup. If you see migration errors:

1. Go to backend service → **Shell** tab
2. Run: `alembic upgrade head`

---

## 🌐 Setting Up Custom Domain (After Deployment)

Once your site is live on Render:

1. **Get your domain** (e.g., `parlaygorilla.com`)
2. **In Render Dashboard**:
   - Go to `parlay-gorilla-frontend` → **Settings** → **Custom Domains**
   - Add your domain: `www.parlaygorilla.com`
   - Go to `parlay-gorilla-backend` → **Settings** → **Custom Domains**
   - Add your domain: `api.parlaygorilla.com`
3. **Update DNS** (at your domain provider):
   - Add CNAME: `www` → `parlay-gorilla-frontend.onrender.com`
   - Add CNAME: `api` → `parlay-gorilla-backend.onrender.com`
4. **Update Environment Variables**:
   - Backend: Update `FRONTEND_URL`, `BACKEND_URL`, `APP_URL` to use your custom domain
   - Frontend: Update `NEXT_PUBLIC_SITE_URL` and `NEXT_PUBLIC_API_URL` to use your custom domain

---

## 💰 Cost Estimate

**Free Tier (Good for Testing):**
- Frontend: Free (may spin down after inactivity)
- Backend: Free (may spin down after inactivity)
- Database: Free (expires after 90 days)
- Redis: Free
- **Total: $0/month**

**Starter Tier (Recommended for Production):**
- Frontend: $7/month (always-on)
- Backend: $7/month (always-on)
- Database: $7/month (persistent)
- Redis: Free
- **Total: ~$21/month**

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render Blueprint deployed
- [ ] Backend environment variables set
- [ ] Frontend environment variables set
- [ ] All services showing "Live"
- [ ] Frontend loads at Render URL
- [ ] Health check works (`/health`)
- [ ] Can register a new user
- [ ] Can generate a parlay

**Once all checked, you're live! 🎉**

---

## 📚 Next Steps

1. **Sign up for LemonSqueezy** using your Render URL
2. **Set up custom domain** (optional but recommended)
3. **Configure LemonSqueezy webhooks** to point to your backend URL
4. **Test the full payment flow**

---

## 🔗 Quick Links

- [Render Dashboard](https://dashboard.render.com)
- [Render Documentation](https://render.com/docs)
- [Your Backend Logs](https://dashboard.render.com/web/YOUR-BACKEND-ID/logs)
- [Your Frontend Logs](https://dashboard.render.com/web/YOUR-FRONTEND-ID/logs)

