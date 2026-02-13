# Frontend: Render → Cloudflare Migration

This guide moves the Parlay Gorilla **frontend** from Render (Node web service) to **Cloudflare** using the OpenNext adapter. The app runs as a Cloudflare Worker with full Next.js SSR and rewrites (e.g. `/api/*` → backend).

**Backend, Postgres, and Redis stay on Render** unless you change them separately (e.g. per `docs/setup-oracle-and-cloudflare.md`).

---

## What’s in the repo

- **frontend**: OpenNext Cloudflare adapter (`@opennextjs/cloudflare`), Wrangler, and scripts.
- **render.yaml**: Frontend service is commented out; backend/worker/DB/Redis unchanged.
- **docs/setup-oracle-and-cloudflare.md**: Already describes Cloudflare DNS + Pages env; use the same env vars for this frontend.

---

## 1. Install deps (if not already)

From repo root:

```bash
cd frontend
npm install
```

This installs `@opennextjs/cloudflare` and `wrangler` (devDependencies).

---

## 2. Environment variables on Cloudflare

Your Next.js rewrites use `PG_BACKEND_URL` / `NEXT_PUBLIC_API_URL`. Set these where the Worker runs.

### Option A: Deploy with Wrangler CLI

Create `frontend/.dev.vars` for local preview (optional):

```bash
cp frontend/.dev.vars.example frontend/.dev.vars
# Edit .dev.vars: NEXTJS_ENV=development (or production)
```

For production, set env in Cloudflare:

- **Dashboard**: Workers & Pages → your Worker → Settings → Variables and Secrets.
- **Wrangler**: use `[vars]` in `wrangler.jsonc` for non-secrets, or Secrets for sensitive values.

Required (match your backend URL):

| Variable | Example | Notes |
|----------|---------|--------|
| `PG_BACKEND_URL` | `https://api.parlaygorilla.com` | Used by Next.js rewrites (SSR + `/api/*`, `/health`) |
| `NEXT_PUBLIC_API_URL` | `https://api.parlaygorilla.com` | Client-side and sitemap |
| `NEXT_PUBLIC_SITE_URL` | `https://www.parlaygorilla.com` | Public site URL (sitemap, etc.) |

If you use a single backend URL, set all three to that (e.g. `https://api.parlaygorilla.com`).

---

## 3. Build and run locally (Cloudflare runtime)

```bash
cd frontend
npm run build:cloudflare
npm run preview:cloudflare
```

This builds Next.js, runs the OpenNext Cloudflare step, and serves the app locally via Wrangler so you can test before deploy.

---

## 4. Deploy to Cloudflare

### 4a. One-off deploy (CLI)

1. Log in: `npx wrangler login`
2. From `frontend`: `npm run deploy:cloudflare`

Your Worker will be created/updated and get a `*.workers.dev` URL.

### 4b. Connect GitHub (Workers Builds)

1. **Cloudflare Dashboard** → **Workers & Pages** → **Workers** → create a Worker with **Deploy with Git**; connect repo and branch (e.g. `main`).
2. Select repo and branch (e.g. `main`).
3. **Build settings**:
   - **Root directory**: `frontend`
   - **Build command**: `npx opennextjs-cloudflare build` (or `npm run build:cloudflare`)
   - **Deploy command**: `npx opennextjs-cloudflare deploy`  
     If your project uses “Pages” with a custom build, you may need to set the build output to the Worker format. For **Workers** connected to Git, use the **Wrangler** build flow: build command `npm run build:cloudflare`, then deploy step `npx opennextjs-cloudflare deploy` (or equivalent in your CI).  
     **Simplest**: Use **Workers** → **Create Worker** → **Deploy with Git**, then set Root directory = `frontend`, Build = `npm run build:cloudflare`, and Deploy command = `npx opennextjs-cloudflare deploy` (or `npm run deploy:cloudflare` which runs build + deploy).
4. Add the env vars from step 2 in the Worker/Pages project **Settings** → **Variables**.

After the first successful deploy, note the Worker URL (e.g. `parlay-gorilla-frontend.<account>.workers.dev`).

---

## 5. Custom domain (www.parlaygorilla.com)

1. **Workers & Pages** → your frontend project → **Settings** → **Domains & Routes**.
2. Add custom domain: `www.parlaygorilla.com` (and apex `parlaygorilla.com` with redirect to www if desired).
3. If the domain is already on Cloudflare, DNS is updated automatically; otherwise add the CNAME they show.

---

## 6. Turn off the frontend on Render

- If you used the commented block in `render.yaml`, the Render frontend service is already inactive.
- If you had created the frontend service manually, open **Render Dashboard** → **parlay-gorilla-frontend** → **Settings** → **Suspend service** (or delete it).

Do this only after you’ve verified the Cloudflare frontend and DNS.

---

## 7. Checklist

- [ ] `cd frontend && npm install`
- [ ] Set Cloudflare env: `PG_BACKEND_URL`, `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL`
- [ ] Run `npm run build:cloudflare` and `npm run preview:cloudflare` locally
- [ ] Deploy via CLI (`npm run deploy:cloudflare`) or Git (Workers + build command above)
- [ ] Add custom domain (e.g. `www.parlaygorilla.com`) to the Worker
- [ ] Suspend or delete the Render frontend service
- [ ] Smoke test: open `https://www.parlaygorilla.com`, login, and check API/health

---

## Troubleshooting

- **Rewrites / API 404**: Ensure `PG_BACKEND_URL` (and optionally `NEXT_PUBLIC_API_URL`) are set in the Cloudflare Worker env and point to your backend (e.g. `https://api.parlaygorilla.com`).
- **Build fails**: Use Node 18+ in the build environment. If you use a monorepo, set Root directory to `frontend` so `package.json` and `next.config.js` are in the build context.
- **Wrangler version**: Next.js 16.1+ with OpenNext requires Wrangler **4.59.2+**. The repo pins `wrangler@^4.59.2` in `frontend/package.json`. Use the project’s local Wrangler (`npx wrangler` or `npm run deploy:cloudflare`), not an older global install.

**Error 1102 (Worker exceeded resource limits)**  
The Worker hit CPU or memory limits. On **Workers Free**, CPU is 10 ms/request (fixed); OpenNext cold starts often exceed it. On **Workers Paid**, default is 30 s; this repo sets `limits.cpu_ms: 300000` in `frontend/wrangler.jsonc` (max 5 min). Upgrade to Paid if you see 1102 on first load. Use Workers & Pages → Logs (invocation logs) and the Ray ID from the error page to debug. See [Cloudflare Workers limits](https://developers.cloudflare.com/workers/platform/limits/).

For backend on Oracle + Cloudflare DNS, see **docs/setup-oracle-and-cloudflare.md**.
