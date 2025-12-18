# Cloudflare DNS + CDN Setup (Production Domains)

Target domains:
- `parlaygorilla.com` → redirects to `www.parlaygorilla.com` (handled by Render when `www` is added)
- `www.parlaygorilla.com` → **frontend** (Next.js)
- `api.parlaygorilla.com` → **backend API** (FastAPI)

## 1) Configure Custom Domains in Render

In the Render dashboard:

- **Frontend service** (`parlay-gorilla-frontend`)
  - Add custom domain: `www.parlaygorilla.com`
  - Render will **automatically add** `parlaygorilla.com` and **redirect it to** `www.parlaygorilla.com`

- **Backend service** (`parlay-gorilla-backend`)
  - Add custom domain: `api.parlaygorilla.com`

## 2) Cloudflare DNS Records (initially DNS-only)

In Cloudflare → **DNS**:

Create these records (Proxy status **DNS only / gray cloud** until Render finishes verification + issues TLS):

- **CNAME** `@` → `<your-frontend-service>.onrender.com`
- **CNAME** `www` → `<your-frontend-service>.onrender.com`
- **CNAME** `api` → `<your-backend-service>.onrender.com`

Notes:
- The target values are the Render service **`.onrender.com`** hostnames shown in the Render dashboard.
- Using **DNS only** during setup is important so Render can verify ownership and issue certificates.

## 3) Cloudflare SSL/TLS mode

Cloudflare → **SSL/TLS** → **Overview**:
- Set encryption mode to **Full**

After Render shows certificates are issued and valid, you can switch to **Full (strict)**.

## 4) Turn on Cloudflare proxying (CDN)

Once Render shows the custom domains are verified and certificates are active:

- Change the Cloudflare DNS records for `@`, `www`, and `api` to **Proxied (orange cloud)**.

## 5) Cache rules (recommended)

Cloudflare → **Caching** → **Cache Rules** (or Rules → Cache Rules):

- **Bypass cache for API**
  - If: hostname equals `api.parlaygorilla.com`
  - Then: **Bypass cache**

The frontend can use Cloudflare’s default caching (static assets cached automatically).

## 6) App configuration (already wired)

This repo’s `render.yaml` is configured for the above domains:
- Frontend `NEXT_PUBLIC_SITE_URL=https://www.parlaygorilla.com`
- Backend `FRONTEND_URL=https://www.parlaygorilla.com`
- Backend `BACKEND_URL=https://api.parlaygorilla.com`
- Backend `APP_URL=https://www.parlaygorilla.com`



