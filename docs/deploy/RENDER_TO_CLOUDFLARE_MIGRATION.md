# Render → Cloudflare Migration

Track moving production off Render onto **Cloudflare** (Pages + DNS) and **Oracle Cloud** (backend API). Use this doc to plan and tick off steps.

---

## Current Render Stack (from `render.yaml`)

| Service | Type | Purpose |
|--------|------|--------|
| **parlay-gorilla-postgres** | PostgreSQL (basic-256mb) | Primary app DB |
| **parlay-gorilla-redis** | Key Value (Redis) | Odds cache, scheduler leader, generator guard, verification queue |
| **parlay-gorilla-frontend** | Web (Node) | Next.js at www.parlaygorilla.com |
| **parlay-gorilla-backend** | Web (Python) | FastAPI at api.parlaygorilla.com |
| **parlay-gorilla-verification-worker** | Worker (Node) | Consumes Redis queue → SUI verification |

---

## Target Architecture

| Piece | Target | Notes |
|-------|--------|------|
| **Frontend** | **Cloudflare Pages** | Next.js; custom domain www.parlaygorilla.com. See [Setup Oracle + Cloudflare](./../setup-oracle-and-cloudflare.md) Part 2. |
| **Backend API** | **Oracle Cloud VM** | FastAPI via Docker; api.parlaygorilla.com via Cloudflare DNS (A → VM). Same doc, Part 1. |
| **Verification** | **Oracle (Python verifier)** | Use `VERIFICATION_DELIVERY=db`; pause/remove Render verification worker. |
| **Postgres** | **Decision** | Keep Render DB temporarily, or migrate to **Neon** / **Supabase** and point Oracle `.env` and (if used) Cloudflare-backed services at new URL. |
| **Redis** | **Decision** | Backend requires `REDIS_URL` in production. Options: **Upstash Redis** (works well with Cloudflare/edge), keep Render Redis for now, or replace usage with DB/other store. |

---

## Migration Checklist

### Already / In progress

- [ ] **Oracle VM** created and deploy working (e.g. GitHub “Deploy to Oracle”).
- [ ] **Cloudflare DNS**: `api.parlaygorilla.com` → A record → Oracle VM IP (Proxied or DNS only).
- [ ] **Cloudflare Pages**: Frontend project exists; env `NEXT_PUBLIC_API_URL` / `PG_BACKEND_URL` = `https://api.parlaygorilla.com`.
- [ ] **Custom domain** on Pages: `www.parlaygorilla.com` (and optional apex redirect).

### Database

- [ ] Decide: stay on Render Postgres **or** migrate to Neon/Supabase.
- [ ] If migrating: export/import data, run migrations on new DB, update `DATABASE_URL` on Oracle VM and anywhere else (e.g. workers).
- [ ] Update Oracle `.env`: `DATABASE_URL` = new URL when cutover.

### Redis

- [ ] Decide: **Upstash Redis** (recommended if going Cloudflare-native), keep **Render Redis** temporarily, or replace with DB/other.
- [ ] If Upstash: create instance, get URL, set `REDIS_URL` on Oracle VM.
- [ ] Backend uses Redis for: odds cache, scheduler leader, generator guard; verification can stay DB-only (`VERIFICATION_DELIVERY=db`).

### Cutover

- [ ] **Render verification worker** paused or deleted (verification on Oracle only).
- [ ] **Render backend** paused or deleted (traffic to Oracle only).
- [ ] **Render frontend** paused or deleted (traffic to Cloudflare Pages only).
- [ ] Smoke test: www + api health, login, critical flows. If `api.parlaygorilla.com` is unreachable or shows ERR_QUIC_PROTOCOL_ERROR, follow [Backend Cloudflare Cutover Runbook](./BACKEND_CLOUDFLARE_CUTOVER_RUNBOOK.md).

### Optional cleanup (after stable on Cloudflare/Oracle)

- [ ] **Render Postgres & Redis** – delete only after DB/Redis migration is done and you’ve decommissioned all Render services.
- [ ] Repo: keep `render.yaml` for reference or remove; update or archive Render-specific docs (`RENDER_*.md`, `docs/deploy/RENDER_DEPLOYMENT_GUIDE.md`, etc.).
- [ ] Compliance/vendor list: replace Render with Cloudflare (+ Oracle + chosen DB/Redis) in `compliance/soc2/vendor_inventory.md`.

---

## Quick Links

- **Full setup (Oracle + Cloudflare)**: [docs/setup-oracle-and-cloudflare.md](../setup-oracle-and-cloudflare.md)
- **Oracle provisioning**: [docs/oracle-a1-auto-provision.md](../oracle-a1-auto-provision.md)
- **Backend env**: `backend/.env.example`, `RENDER_BACKEND_ENV_COMPLETE.md` (env names stay the same; values point to new infra)

---

## Redis on Cloudflare / Edge

Cloudflare does not offer a built-in Redis. For a Cloudflare-friendly stack:

- **Upstash Redis**: serverless Redis with HTTP API; works from Workers and from your Oracle backend via `REDIS_URL` (Upstash gives a Redis-compatible URL). No long-lived TCP from Workers needed.
- Alternative: keep Render Redis (or another hosted Redis) until you fully leave Render; only the backend VM needs to reach it.

---

*Last updated: migration in progress (Render → Cloudflare + Oracle).*
