# Setup Guide (Render-only mindset)

This repo is a monorepo:
- `backend/` → FastAPI
- `frontend/` → Next.js

Production is intended to run **fully on Render** via the repo’s root `render.yaml`.

## Local development

### Backend

1. Create `backend/.env` from `backend/.env.example`
2. Set required keys:
   - `DATABASE_URL` (local Postgres or SQLite for dev)
   - `THE_ODDS_API_KEY`
   - `OPENAI_API_KEY` (or `OPENAI_ENABLED=false`)
3. Start the API:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

1. Create `frontend/.env.local` from `frontend/.env.example`
2. Set:
   - `NEXT_PUBLIC_API_URL=http://localhost:8000`
   - `NEXT_PUBLIC_SITE_URL=http://localhost:3000`
3. Start Next.js:

```bash
cd frontend
npm run dev
```

## Render deployment (one place)

Use the repo’s root `render.yaml` Blueprint. See `QUICK_DEPLOY.md`.



