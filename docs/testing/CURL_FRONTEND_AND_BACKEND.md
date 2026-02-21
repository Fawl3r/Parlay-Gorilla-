# Frontend vs backend curl reference

Use these to verify the same endpoints from the **frontend origin** (Next.js rewrites to backend) and **direct backend**.

## Games feed (live / today / upcoming)

| Context | Base URL | Example |
|--------|----------|--------|
| **Frontend** (browser path) | Same-origin: `https://www.parlaygorilla.com` (prod) or `http://localhost:3000` (dev). Next.js rewrites `/api/*` to backend. | `https://www.parlaygorilla.com/api/games/feed?window=today` |
| **Backend** (direct API) | `https://api.parlaygorilla.com` (prod) or `http://localhost:8000` (local) | `https://api.parlaygorilla.com/api/games/feed?window=today` |

### Frontend curls (what the browser hits)

```bash
# Production — requests go to www, Next rewrites to api.parlaygorilla.com
BASE=https://www.parlaygorilla.com
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=live"
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=today"
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=upcoming"

# Local dev (Next.js on 3000 or 3004) — rewrites to backend (NEXT_PUBLIC_API_URL or localhost:8000)
BASE=http://localhost:3000
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=today"
```

### Backend curls (direct to FastAPI)

```bash
# Production API
BASE=https://api.parlaygorilla.com
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=live"
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=today"
curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=upcoming"

# Local backend (uvicorn port 8000)
BASE=http://localhost:8000
curl -s "$BASE/api/games/feed?window=today"
```

### Optional: sport filter

Both frontend and backend accept `sport`:

```bash
curl -s "https://www.parlaygorilla.com/api/games/feed?window=today&sport=NFL"
curl -s "https://api.parlaygorilla.com/api/games/feed?window=today&sport=NFL"
```

## Health

| Context | curl |
|--------|-----|
| Frontend | `curl -s -o /dev/null -w "%{http_code}" https://www.parlaygorilla.com/health` |
| Backend | `curl -s -o /dev/null -w "%{http_code}" https://api.parlaygorilla.com/health` |

## Auth (backend only; frontend uses same path via rewrite)

```bash
# Login (get cookie/token for subsequent requests)
curl -s -X POST "https://api.parlaygorilla.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}'

# Me (with cookie or Authorization: Bearer <token>)
curl -s "https://api.parlaygorilla.com/api/auth/me" -H "Authorization: Bearer <token>"
```

## Summary

- **Frontend curl** = URL the browser uses: **frontend origin** + path (e.g. `www.parlaygorilla.com/api/...`). Next.js rewrites to the backend; no CORS for same-origin.
- **Backend curl** = **API origin** + path (e.g. `api.parlaygorilla.com/api/...` or `localhost:8000/api/...`). Use for direct API checks and local dev without Next.
