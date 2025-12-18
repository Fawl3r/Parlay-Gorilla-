# 🚀 Deployment Checklist (Render-only)

This project is designed to run **entirely on Render** (frontend + backend + Postgres + Redis).

## ✅ Pre-Deployment Checklist

### 1. Code Preparation
- [ ] All code committed to GitHub
- [ ] `.env` files are NOT committed (in `.gitignore`)
- [ ] Frontend builds successfully (`npm run build` in `frontend/`)
- [ ] Backend tests pass (`python -m pytest` in `backend/`)

### 2. Secrets Ready
- [ ] `THE_ODDS_API_KEY`
- [ ] `OPENAI_API_KEY` (or set `OPENAI_ENABLED=false`)
- [ ] `RESEND_API_KEY` (optional but recommended for verification + password reset emails)

## 🚀 Deployment Steps (Render Blueprint)

### Step 1: Deploy Everything via `render.yaml`
1. Go to Render → **New +** → **Blueprint**
2. Connect your GitHub repo and select this project
3. Render will detect the repo’s root `render.yaml` and create:
   - `parlay-gorilla-postgres` (Render PostgreSQL)
   - `parlay-gorilla-redis` (Render Key Value)
   - `parlay-gorilla-backend` (FastAPI)
   - `parlay-gorilla-frontend` (Next.js)

### Step 2: Set Required Environment Variables
Render will wire `DATABASE_URL`, `REDIS_URL`, and generate `JWT_SECRET` automatically.

You still need to set:
- **Backend (`parlay-gorilla-backend`)**
  - `THE_ODDS_API_KEY`
  - `OPENAI_API_KEY` (or `OPENAI_ENABLED=false`)
  - `FRONTEND_URL` and `APP_URL` (set both to your frontend URL)
  - `BACKEND_URL` (set to your backend URL)
- **Frontend (`parlay-gorilla-frontend`)**
  - `NEXT_PUBLIC_SITE_URL` (set to your frontend URL)

## ✅ Post-Deployment Verification
- [ ] Frontend loads at your Render frontend URL
- [ ] Health check works via frontend proxy: `GET /health`
- [ ] Register + login works (`/auth/signup`, `/auth/login`)
- [ ] Can generate a parlay
- [ ] No 500s in Render logs for the backend

## 📝 Cost Notes
- The provided `render.yaml` is configured for a **$14/mo baseline**:
  - Backend: **starter**
  - Postgres: **basic-256mb**
  - Frontend: **free** (may spin down; upgrade to starter for always-on)



