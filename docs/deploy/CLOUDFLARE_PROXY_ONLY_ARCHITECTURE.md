# Cloudflare: Proxy-Only Architecture (OPTION A)

> **Cloudflare is NOT a deployment platform in this architecture.**

This document is the **source of truth** for Cloudflare’s role in Parlay Gorilla production. It must not be overridden by automation or future agents.

---

## Architecture source of truth

| Layer            | Authority |
|------------------|-----------|
| Frontend         | **Vercel** (deploy on push to `main`) |
| Backend          | **GitHub Actions → Oracle VM** (blue/green systemd deploy) |
| Database + Redis | **Render** |
| DNS / CDN / WAF  | **Cloudflare** (proxy only) |

Cloudflare is used **only** as DNS, proxy, caching, and security. It does **not** run builds, Workers, Wrangler, or Pages.

---

## Cloudflare responsibilities (allowed)

- **DNS** — Resolution for parlaygorilla.com, www.parlaygorilla.com, api.parlaygorilla.com
- **CDN caching** — Respect origin `Cache-Control`; do not cache API routes
- **SSL termination** — HTTPS at the edge
- **WAF protection** — DDoS, bot, and security rules
- **Proxying**
  - `api.parlaygorilla.com` → Oracle backend
  - `parlaygorilla.com` / `www.parlaygorilla.com` → Vercel frontend

---

## Cloudflare forbidden responsibilities

- **Builds** — No Cloudflare build steps
- **CI/CD** — No Cloudflare deploy in any pipeline
- **Workers deploy** — No Workers as application runtime
- **Wrangler deploy** — No `wrangler deploy` or `opennextjs-cloudflare deploy`
- **Frontend hosting** — Frontend is on Vercel only
- **Backend hosting** — Backend is on Oracle only

---

## If you see Cloudflare deploy errors

If CI or a script runs `npx wrangler deploy` or similar and fails (e.g. “Missing entry-point to Worker script or to assets directory”):

1. **Do not** fix it by adding Workers/Pages config or Wrangler to CI.
2. **Do** remove or disable the step that invokes Cloudflare deploy.
3. Frontend deploys via **Vercel** (push to `main`). Backend deploys via **GitHub Actions → Oracle**.

## Cache safety (CDN must respect origin)

Cloudflare must **not** serve stale UI after a Vercel deploy. The frontend (Vercel/Next.js) sets:

- **`/` and `/:path*`** → `Cache-Control: public, max-age=0, must-revalidate` (no long-lived HTML cache).
- **`/_next/static/*`** → `Cache-Control: public, max-age=31536000, immutable` (hashed assets only).
- **API routes** (e.g. `/api/*`) → must not be cached; origin sets `no-store` where needed.

Cloudflare is configured to respect these origin headers. Do not cache API routes at the edge.

See also: [CLOUDFLARE_CACHE_AND_HEADERS.md](CLOUDFLARE_CACHE_AND_HEADERS.md) for cache behavior and purge steps.

---

## Verify deployment

If both return the latest commit SHA after a push → you’re fully good:

- **Frontend:** `curl -fsS https://parlaygorilla.com/api/version`
- **Backend (trusted machine, token in env):** `curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify`

See [PROD_VALIDATION_30_SECONDS.md](PROD_VALIDATION_30_SECONDS.md) for full validation steps.
