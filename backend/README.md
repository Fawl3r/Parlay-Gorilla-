# Parlay Gorilla Backend

## Quick Start

### 1. Start Docker PostgreSQL

```bash
docker-compose up -d postgres
```

This will start:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### 2. Configure Environment

Copy `.env` and update with your keys:
- `THE_ODDS_API_KEY` - Your Odds API key
- `OPENAI_API_KEY` - Your OpenAI API key

#### Payments (Credit Packs + Subscriptions)

- **Webhook endpoints** (configure in provider dashboards):
  - **LemonSqueezy**: `POST {BACKEND_URL}/api/webhooks/lemonsqueezy`
  - **Coinbase Commerce**: `POST {BACKEND_URL}/api/webhooks/coinbase`
- **Redirect URL base**: `APP_URL` (must be your public frontend URL)

Required env vars (see `backend/.env.example`):
- **LemonSqueezy**: `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_WEBHOOK_SECRET`
- **Credit pack variants (card)**: `LEMONSQUEEZY_CREDITS_10_VARIANT_ID`, `LEMONSQUEEZY_CREDITS_25_VARIANT_ID`, `LEMONSQUEEZY_CREDITS_50_VARIANT_ID`, `LEMONSQUEEZY_CREDITS_100_VARIANT_ID`
- **Coinbase**: `COINBASE_COMMERCE_API_KEY`, `COINBASE_COMMERCE_WEBHOOK_SECRET`
- **Affiliate payouts (PayPal)**: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`
- **Affiliate payouts (Crypto / Circle USDC)**: `CIRCLE_API_KEY`, `CIRCLE_ENVIRONMENT`

### 3. Initialize Database

```bash
python setup_database.py
```

### 4. Fetch Live Games

```bash
python fetch_live_games.py
```

### 5. Start Backend Server

```bash
python -m uvicorn app.main:app --reload --port 8000
```

## Database Configuration

### Production (Render PostgreSQL)

1. Create a **Render PostgreSQL** service
2. Copy the **Internal Database URL**
3. Set:

```env
USE_SQLITE=false
DATABASE_URL=postgresql://user:password@dpg-xxxx-a.oregon-postgres.render.com/parlaygorilla
```

### Local Development (Docker)
- Connection: `postgresql+asyncpg://devuser:devpass@localhost:5432/parlaygorilla`
- Auto-configured in `.env`
- Run: `docker-compose up -d postgres`

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /api/metrics` - Application metrics
- `GET /api/health/detailed` - Detailed health check

### Games & Odds
- `GET /api/sports/{sport}/games` - Get games for a sport
- `GET /api/weeks/nfl` - Get NFL week information

### Parlays
- `POST /api/parlay/suggest` - Generate AI parlay
- `POST /api/parlay/20-leg` - Generate 20-leg degen parlay
- `POST /api/parlay/analyze` - Analyze custom parlay
- `GET /api/parlay/history` - Get parlay history

### Advanced Parlays
- `POST /api/parlay/variants/same-game` - Same-game parlay
- `POST /api/parlay/variants/round-robin` - Round-robin builder
- `POST /api/parlay/variants/teaser` - Teaser builder

### Social Features
- `POST /api/social/share` - Share a parlay
- `GET /api/social/share/{token}` - Get shared parlay
- `POST /api/social/share/{token}/like` - Like a shared parlay
- `GET /api/social/feed` - Get social feed
- `GET /api/social/leaderboard` - Get leaderboard

### Authentication
- `POST /api/auth/register` - Register user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user
- `POST /api/auth/verify-email` - Verify email
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password

## Account Numbers & On-Chain Proofs (No PII)

Each user is assigned a **non-PII `account_number`** (20-char hex string) on creation. This is used for
Solana inscription proofs so we never put emails or personal data on-chain.

- **Custom saved parlays** (`POST /api/parlays/custom/save`) are queued for inscription (Redis-backed).
- The **inscription payload** includes:
  - `account_number`
  - `parlay_id`
  - `hash` (deterministic content hash)
  - `created_at`
  - `schema`
- The payload **must not** include email, username, display name, or any other personal data.

### Analysis
- `GET /api/analysis/{sport}/upcoming` - List analyses
- `GET /api/analysis/{sport}/{slug}` - Analysis detail (fast core + background full article; `refresh=true` forces core regen)
- `POST /api/analysis/generate` - Generate analysis

## Gorilla Bot (Knowledgebase Q&A)

Gorilla Bot is the in-app assistant that answers product questions using a curated knowledgebase.

- `POST /api/gorilla-bot/chat` - Ask Gorilla Bot (auth required)
- Knowledgebase docs live in `docs/gorilla-bot/kb`
- Reindex after doc updates:

```bash
python scripts/gorilla_bot_index_kb.py
```

## Data Sources

- **Odds & scheduling:** The Odds API is primary for odds and for the games list (scheduling). API-Sports is the scheduling fallback when needed.
- **Sports data:** API-Sports is the primary source for stats, results, form, and standings; ESPN is fallback.

## API-Sports Integration (Quota-Safe, DB-First)

API-Sports is the primary sports data source (stats, results, form, standings) and the scheduling fallback. **Quota: 100 requests/day** (free tier). All user-facing endpoints read from DB only; no live API-Sports calls in request path.

### How quota works
- **Hard cap**: 100 requests/day (America/Chicago). Enforced by `QuotaManager` (Redis or DB fallback).
- **Rate limit**: Soft token bucket (1 req / 15s, burst 2) to avoid bursts.
- **Circuit breaker**: After 5 consecutive failures, API usage pauses for 30 minutes.
- **Budget** (configurable): ~60 fixtures, ~25 team stats, ~10 standings, ~5 reserve.

### Running refresh locally
- Refresh runs in the **scheduler** every 60 minutes when `enable_background_jobs` is True.
- To trigger manually (admin only): `POST /api/admin/apisports/refresh` (requires admin auth).
- Quota status: `GET /api/admin/apisports/quota`.

### Verifying you don't exceed 100/day
- Check `GET /api/admin/apisports/quota`: `used_today` and `remaining`.
- Logs: `[SCHEDULER] API-Sports refresh: used=X remaining=Y`.
- If Redis is used, daily counter resets at midnight America/Chicago.

### Env vars (see `.env.example`)
- `API_SPORTS_API_KEY` – API key (optional; leave blank to disable).
- `APISPORTS_DAILY_QUOTA`, `APISPORTS_TTL_*`, `APISPORTS_BUDGET_*` – tuning.

**Local checkout and testing:** see [docs/API_SPORTS_LOCAL_CHECKOUT.md](docs/API_SPORTS_LOCAL_CHECKOUT.md) for step-by-step run, migrations, and hitting quota/refresh locally.

**Production deployment:** see [docs/API_SPORTS_PRODUCTION_DEPLOYMENT.md](docs/API_SPORTS_PRODUCTION_DEPLOYMENT.md) for Render deployment, env vars, migration, and verification steps.

## Background Jobs

Configured via APScheduler:
- Odds sync every 24 hours (or when analytics update)
- Scraper runs every 30 minutes
- Analysis core pre-generation daily at 6 AM (upcoming games)
- **API-Sports refresh** every 60 minutes (quota-safe)

## Analysis Generation Settings

The analysis pipeline returns a fast “core” response (summary, ATS/O-U, picks, model probs) and optionally generates a long-form `full_article` in background.

Configure via `backend/.env`:
- `ANALYSIS_CORE_TIMEOUT_SECONDS`
- `ANALYSIS_CORE_AI_POLISH_TIMEOUT_SECONDS`
- `ANALYSIS_FULL_ARTICLE_ENABLED`
- `ANALYSIS_FULL_ARTICLE_TIMEOUT_SECONDS`
