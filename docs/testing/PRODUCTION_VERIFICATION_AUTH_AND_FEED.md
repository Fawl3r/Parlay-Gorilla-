# Production verification: auth and live feed

After deploying the backend (including migration `046_add_user_metadata_columns`), run these checks **in order**.

## 1. Migration applied

Confirm startup logs show Alembic successfully upgraded to head (e.g. `046_add_user_metadata_columns`). There should be no "duplicate column" or migration errors.

## 2. Auth smoke test

Run the auth smoke test against your production base URL:

```bash
python scripts/prod_auth_smoketest.py --base-url https://your-domain.com --mode auto
```

**Verify:**

- `POST /api/auth/login` returns `200` for a known user
- `GET /api/auth/me` returns `200` after login (Bearer and cookie)

## 3. Feed endpoint (all windows)

Hit these endpoints and confirm **200** and that **no returned game has null or missing `start_time`**:

- `GET /api/games/feed?window=live`
- `GET /api/games/feed?window=today`
- `GET /api/games/feed?window=upcoming`

```bash
BASE=https://your-domain.com
for w in live today upcoming; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/games/feed?window=$w")
  echo "window=$w -> $code"
done
# Expect: 200 for each
```

Optionally assert response shape: each item in the JSON list must have a non-null string `start_time`.

## 4. LiveMarquee sanity

Confirm the UI does not show "No games scheduled" when the backend returns items for the same window (e.g. live or today). If the feed returns 200 with data, the marquee should reflect it.
