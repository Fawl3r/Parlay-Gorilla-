# Solana Inscriptions (Custom Parlays) — Parlay Gorilla

This doc describes how **custom user-saved parlays** are anchored on Solana using the IQ Labs `code_in_sdk` (IQ6900 protocol).

## What gets inscribed (and what does not)

- **Custom parlays**: inscribed **only when the user clicks Save Parlay**.
- **AI-generated parlays**: can be saved and shown in the dashboard, but **are never inscribed**.

On-chain data is **hash-only proof payload**, not the full parlay JSON.

## Data model

Custom/AI saved parlays live in `saved_parlays`:
- `parlay_type`: `custom` | `ai_generated`
- `content_hash`: sha256 hex of a canonical payload
- `inscription_status`: `none` | `queued` | `confirmed` | `failed`
- `inscription_tx`: Solana transaction signature (when confirmed)

## Hashing rules

We compute a deterministic SHA-256 hash from a canonical payload containing:
- `schema_version`: `pg_parlay_v1`
- `app_version`: `APP_VERSION` (backend config)
- `parlay_id`, `user_id`, `created_at_utc`
- `parlay_type`
- `legs[]` snapshot (sorted deterministically)

## Runtime components

### 1) FastAPI backend (producer + API)

Endpoints:
- `POST /api/parlays/custom/save` → creates/updates a saved parlay and sets `inscription_status=queued`, then enqueues a Redis job.
- `POST /api/parlays/ai/save` → saves AI parlay with `inscription_status=none` (no enqueue).
- `GET /api/parlays/saved?type=all|custom|ai` → list saved parlays, includes `solscan_url` for confirmed custom.
- `POST /api/parlays/{id}/inscription/retry` → allowed only for `custom + failed`, re-queues the job.

### 2) Node inscriptions worker (consumer)

Location: `backend/inscriptions-worker`

Responsibilities:
- BLPOP Redis queue jobs
- Load `saved_parlays` from Postgres
- Refuse to inscribe anything where `parlay_type != custom`
- Call IQ SDK `userInit()` once at startup
- Call `codeIn()` with the **hash-only proof payload**
- Update DB `inscription_status`, `inscription_tx`, `inscribed_at`
- Retry with exponential backoff (max 5 attempts)

## Environment variables

### Backend (`backend/.env`)

- `DATABASE_URL` (Postgres)
- `REDIS_URL` (required for inscriptions + distributed scheduler)
- `SOLANA_CLUSTER` (`mainnet` | `devnet`) — affects Solscan links
- `SOLSCAN_BASE_URL` (optional, default `https://solscan.io/tx`)

### Worker (`backend/inscriptions-worker/.env` or process env)

Required:
- `DATABASE_URL` (Postgres; can also use `PG_DATABASE_URL`)
- `REDIS_URL`
- `SIGNER_PRIVATE_KEY` (base58 signer key) **DO NOT LOG**
- `RPC` (Solana RPC endpoint)

Optional:
- `IQ_HANDLE` (default: `ParlayGorilla`)
- `IQ_DATATYPE` (default: `parlay_proof`)

## Running locally

1) Start Postgres + Redis (or use existing infra)
- `backend/docker-compose.yml` includes both.

2) Run backend API
- Start FastAPI as usual (see `backend/README.md` / scripts).

3) Run worker

From `backend/inscriptions-worker`:
- `npm install`
- `npm run build`
- `npm run start`

## Verification UX

In the Analytics dashboard:
- Custom saved parlays show an inscription status.
- When confirmed, the UI shows:
  - shortened `inscription_hash` + copy button
  - `View on Solscan` link (opens new tab)



