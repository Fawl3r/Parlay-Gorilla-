# 🚀 Quick Deploy (Render-only) — Get Live Fast

This project is designed to run **entirely on Render**:
- **Frontend**: Render Web Service (Next.js)
- **Backend**: Render Web Service (FastAPI)
- **Database**: Render PostgreSQL
- **Redis**: Render Key Value

## Prerequisites

- GitHub account (repo connected to Render)
- Render account
- `THE_ODDS_API_KEY`
- `OPENAI_API_KEY` (or set `OPENAI_ENABLED=false` in backend env)
- `RESEND_API_KEY` (optional, enables verification + password reset emails)

## Step 1: Push to GitHub

```bash
git add .
git commit -m "Render-only deployment"
git push origin main
```

## Step 2: Deploy via Render Blueprint (`render.yaml`)

1. Go to Render → **New +** → **Blueprint**
2. Connect your GitHub repo and select this project
3. Render will detect the repo’s root `render.yaml` and create:
   - `parlay-gorilla-postgres` (PostgreSQL)
   - `parlay-gorilla-redis` (Key Value / Redis)
   - `parlay-gorilla-backend` (FastAPI)
   - `parlay-gorilla-frontend` (Next.js)

## Step 2.5: Custom Domains (Cloudflare)

If you’re using Cloudflare for DNS + CDN, follow `CLOUDFLARE_DNS_CDN_SETUP.md` to set up:
- `www.parlaygorilla.com` → frontend
- `parlaygorilla.com` → redirects to `www` (Render-managed when `www` is added)
- `api.parlaygorilla.com` → backend API

## Step 3: Set Environment Variables in Render

### Backend (`parlay-gorilla-backend`)

Set:
- `THE_ODDS_API_KEY`
- `OPENAI_API_KEY` (or `OPENAI_ENABLED=false`)
- `FRONTEND_URL` and `APP_URL` (set both to your frontend URL)
- `BACKEND_URL` (set to your backend URL)
- `RESEND_API_KEY` (optional)

Notes:
- `DATABASE_URL` is wired from Render PostgreSQL automatically (Blueprint).
- `REDIS_URL` is wired from Render Key Value automatically (Blueprint).
- `JWT_SECRET` is generated automatically (Blueprint).

### Frontend (`parlay-gorilla-frontend`)

Set:
- `NEXT_PUBLIC_SITE_URL` (set to your frontend URL)

Notes:
- `PG_BACKEND_URL` is wired automatically via private network (Blueprint).
- You generally **do not** need `NEXT_PUBLIC_API_URL` when using the Next.js proxy rewrites.

## Step 4: Verify

- Frontend loads at your Render frontend URL
- `GET /health` works (via frontend proxy)
- Register/login works (`/auth/signup`, `/auth/login`)
- Generate a parlay

## Cost Notes

The repo’s `render.yaml` is configured for a **$14/mo baseline**:
- Backend: **starter**
- Postgres: **basic-256mb**
- Redis: **free**
- Frontend: **free** (may spin down; upgrade to starter for always-on)


