# Render Deployment Checklist

Everything you need to do on Render to get Parlay Gorilla working in production.

---

## 1. Create / Use Blueprint (render.yaml)

- **Option A:** In [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint** → Connect repo and select this repo. Render will create all services from `render.yaml`.
- **Option B:** If services already exist, ensure they match the names in `render.yaml` so env links (e.g. `fromService`, `fromDatabase`) resolve.

---

## 2. Services Created by Blueprint

| Service | Type | Purpose |
|--------|------|--------|
| `parlay-gorilla-postgres` | PostgreSQL | Primary database |
| `parlay-gorilla-redis` | Key Value | Odds cache, scheduler leader election |
| `parlay-gorilla-backend` | Web (Python) | FastAPI API |
| `parlay-gorilla-frontend` | Web (Node) | Next.js app |
| `parlay-gorilla-verification-worker` | Worker (Node) | SUI verification records (optional) |

---

## 3. Backend Environment Variables (parlay-gorilla-backend)

**Auto-wired by Blueprint (no action):**

- `DATABASE_URL` ← from PostgreSQL
- `REDIS_URL` ← from Key Value
- `ENVIRONMENT`, `DEBUG`, `USE_SQLITE`, `OPENAI_ENABLED`, `FRONTEND_URL`, `BACKEND_URL`, `APP_URL`
- `GORILLA_BOT_*`, `APISPORTS_BASE_URL`, `APISPORTS_DAILY_QUOTA`, `JWT_SECRET` (generated)

**You must set in Render Dashboard (Secrets / env):**

| Variable | Required | Notes |
|----------|----------|--------|
| `THE_ODDS_API_KEY` | Yes | From [The Odds API](https://the-odds-api.com) |
| `OPENAI_API_KEY` | Yes (if Gorilla Bot/OpenAI on) | From OpenAI |
| `JWT_SECRET` | Yes | Set a strong secret if not using Blueprint-generated |
| `API_SPORTS_API_KEY` | Optional | api-sports.io; leave blank to use ESPN fallback only |

**Optional – Telegram alerts (parlay/odds/repair failures + unhandled exceptions):**

| Variable | Notes |
|----------|--------|
| `TELEGRAM_ALERTS_ENABLED` | Set to `true` to enable |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | Chat or group ID for alerts |

See `backend/docs/TELEGRAM_ALERTS.md` for setup.

**Optional – Payments (Lemonsqueezy / Coinbase Commerce):**  
Set only if you use them: `LEMONSQUEEZY_*`, `COINBASE_COMMERCE_*`.

**Optional – Verification worker (SUI):**  
Only for `parlay-gorilla-verification-worker`: `SUI_RPC_URL`, `SUI_PRIVATE_KEY`, `SUI_PACKAGE_ID`.

---

## 4. Run Migrations on Production DB

Backend `start.sh` runs `alembic upgrade head` on every deploy. If the DB is fresh:

1. First deploy may fail if migrations error; check **Logs**.
2. To run migrations manually (e.g. from Render Shell):
   - Open **parlay-gorilla-backend** → **Shell**.
   - `cd backend && alembic upgrade head`

For a **new** Render PostgreSQL instance, the first deploy usually succeeds; migrations run before uvicorn starts.

---

## 5. (Optional) Backfill Games

After first successful deploy, optionally populate games:

- **From your machine** (with `DATABASE_URL` pointing at Render Postgres internal URL from Dashboard):
  ```bash
  cd backend && python scripts/backfill_all_sports_data.py
  ```
- Or call the API (if you expose an admin endpoint):  
  `POST /api/games/backfill-all-sports` (ensure auth/rate-limit as needed).

---

## 6. Verify Deployment

- **Health:** `GET https://api.parlaygorilla.com/health`
- **Parlay generation diagnostic:** `GET https://api.parlaygorilla.com/api/health/parlay-generation`
- **Frontend:** `https://www.parlaygorilla.com`

---

## 7. Quick Checklist

- [ ] Blueprint applied or services created with correct names
- [ ] `THE_ODDS_API_KEY` and `OPENAI_API_KEY` set on backend
- [ ] `JWT_SECRET` set (or left as Blueprint-generated)
- [ ] `USE_SQLITE=false` (already in render.yaml)
- [ ] Migrations ran (automatic via start.sh or manually in Shell)
- [ ] (Optional) Telegram: `TELEGRAM_ALERTS_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- [ ] (Optional) Backfill games
- [ ] Health and parlay-generation endpoints return 200

Once these are done, the app is ready to use on Render.
