# Parlay Gorilla

**Parlay Gorilla** is an AI-powered sports analytics and parlay research platform. It helps users explore matchup insights, game analysis, and parlay ideas across major leagues—NFL, NBA, MLB, NHL, and Soccer—with a focus on clarity and responsible use. It is **not** a sportsbook; it provides research and tools only.

---

## What the app does

- **Game analysis** — AI-generated matchup breakdowns, key edges, injury impact, and pick-style recommendations for upcoming games.
- **Gorilla Parlay** — AI-suggested parlays (conservative, balanced, or higher-risk) based on the same analysis engine.
- **Custom parlay builder** — Hand-pick legs from analysis and build your own parlays with combined odds and hit probability.
- **Sports hub** — Browse games by sport and date; filter by in-season leagues and analysis availability.
- **Parlay history & results** — Track past parlays and leg-level outcomes (hit/miss/push).
- **Analytics & tools** — Top edges, odds heatmap (Premium), upset finder, and model-backed probabilities where available.
- **Gorilla Bot** — In-app help and knowledge base for features, limits, and account questions.
- **Subscriptions & credits** — Free tier with usage limits; Premium and credit packs for more AI parlays and builder usage.

The frontend is a Next.js app (SSR, API proxy to backend). The backend is a FastAPI service that handles auth, analysis, parlays, odds, billing (Stripe), and external data (odds feeds, API-Sports for injuries/rosters, etc.).

---

## Repo structure

| Path | Description |
|------|-------------|
| `backend/` | FastAPI API: auth, games, analysis, parlay generation, odds, billing, webhooks, scheduler |
| `frontend/` | Next.js 16 app (React 19): sports hub, analysis pages, parlay builder, billing, profile |
| `social_bot/` | Simple X (Twitter) bot: one post per run (edge/trap/parlay/math), scheduled externally |
| `docs/` | Deployment, payments, troubleshooting, business copy; index at `docs/README.md` |

---

## Tech stack

- **Backend:** Python 3, FastAPI, SQLAlchemy (async), PostgreSQL, Redis, OpenAI, Stripe, Odds API, API-Sports (injuries/teams). Optional: Sui (verification), LemonSqueezy, web push.
- **Frontend:** Next.js 16, React 19, Tailwind CSS. Deploys to **Cloudflare Workers** via OpenNext (`@opennextjs/cloudflare`); local dev with Node.
- **Social bot:** Python, OpenAI, X API (Bearer or OAuth1).

---

## Quickstart (local dev)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # macOS/Linux
pip install -r requirements.txt
copy .env.example .env         # then fill in DB, Redis, API keys, etc.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: **http://localhost:8000**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: **http://localhost:3000** (rewrites `/api/*` and `/health` to the backend URL in env).

Set `NEXT_PUBLIC_API_URL` / `PG_BACKEND_URL` (and optional `BACKEND_URL`) in `frontend/.env.local` to `http://localhost:8000` so the UI talks to your local API.

### Social bot (optional)

See **social_bot/README.md**. Copy `social_bot/.env.example` → `social_bot/.env`, add OpenAI and X credentials. Run once: `python social_bot/bot.py --print-only` then `python social_bot/bot.py`.

---

## Tests

From repo root:

```bash
python -m pytest -q
```

Frontend unit tests: `cd frontend && npm run test:unit`. E2E: `npm run test:e2e` (Playwright).

---

## Docs

- **docs/README.md** — Full docs index (deployment, payments, legal, troubleshooting, Gorilla Bot KB).
- **docs/deploy/CLOUDFLARE_FRONTEND_MIGRATION.md** — Deploy frontend to Cloudflare Workers; includes Error 1102 and env setup.
- **docs/deploy/RENDER_DEPLOYMENT_GUIDE.md** — Backend on Render.

---

## License & disclaimer

See **LICENSE** in the repo. The product provides sports analytics and informational insights only; it is not a sportsbook and does not guarantee outcomes.