# Parlay Gorilla

AI sports analytics & parlay research platform.

This repo is a monorepo containing:
- `backend/` — FastAPI API (odds, analysis, billing, webhooks)
- `frontend/` — Next.js app (UI)
- `social_bot/` — Simple X posting bot (one post per run; no dashboards/queues)

## Quickstart (local dev)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:3000`

## Simple X Social Bot (v2)

The bot follows the FINAL SPEC:
- 4 post types only (Edge Explainer, Trap Alert, Example 2–3 leg parlay structure, Parlay math/bankroll)
- Plain English, credible, no hype, no hashtags, max 1 emoji
- Pulls matchup context from the production analysis feed
- Runs once per execution (schedule externally)

Setup:

1) Copy env template:

`social_bot/.env.example` → `social_bot/.env`

2) Fill in:

- `OPENAI_API_KEY`
- X credentials (either `X_BEARER_TOKEN` or OAuth1 keys)

Run once (safe dry-run/print):

```bash
python social_bot/bot.py --print-only
```

Post once:

```bash
python social_bot/bot.py
```

## Tests

From repo root:

```bash
python -m pytest -q
```

## Docs

See the docs index: `docs/README.md`



