# Production verification: auth and live feed

After deploying the backend (including migration `046_add_user_metadata_columns`), verify auth and games feed in production.

## 1. Auth smoke test

Run the auth smoke test against your production base URL:

```bash
python scripts/prod_auth_smoketest.py --base-url https://your-domain.com --mode auto
```

**Verify:**

- `POST /api/auth/login` returns `200` for a known user
- `GET /api/auth/me` returns `200` after login (Bearer and cookie)

## 2. Live games feed

**Verify:**

- `GET /api/games/feed?window=live` returns `200` (often `[]` when no live games)

```bash
curl -s -o /dev/null -w "%{http_code}" "https://your-domain.com/api/games/feed?window=live"
# Expect: 200
```

## 3. After migration

Confirm startup logs show Alembic successfully upgraded to head (e.g. `046_add_user_metadata_columns`).
