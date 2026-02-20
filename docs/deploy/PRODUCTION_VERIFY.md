# Production verification — lock-in

**Location:** `docs/deploy/PRODUCTION_VERIFY.md`

Use this after a deploy (or anytime) to confirm production is serving the latest commit. No secrets in this file; use env for `OPS_VERIFY_TOKEN`.

---

## 1. Frontend (Vercel)

No token. Use **www** (production domain):

```bash
curl -fsS https://www.parlaygorilla.com/api/version
```

**Expected:** `{"git_sha":"<sha>"}` with a real commit SHA (not `"unknown"`).

---

## 2. Backend (Oracle)

From a trusted machine, with `OPS_VERIFY_TOKEN` set in env (never paste it):

```bash
curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify
```

**Expected:** `{"ok":true,"git_sha":"<sha>"}` with the same commit SHA.

---

## 3. Full sync check (script)

From repo root, with `OPS_VERIFY_TOKEN` set:

```bash
BACKEND_URL=https://api.parlaygorilla.com FRONTEND_URL=https://www.parlaygorilla.com OPS_VERIFY_TOKEN=$OPS_VERIFY_TOKEN python backend/scripts/production_diagnose.py
```

**Expected:** `STATE: SYNCED` at the end.

---

## 4. Backend-only sync (CI-style)

```bash
BACKEND_URL=https://api.parlaygorilla.com OPS_VERIFY_TOKEN=$OPS_VERIFY_TOKEN python backend/scripts/verify_production_sync.py
```

**Expected:** `PASS: Production backend matches local commit: <sha>`.

---

## Summary

| Check              | Command / script                                      | Success when                          |
|--------------------|--------------------------------------------------------|----------------------------------------|
| Frontend SHA       | `curl -fsS https://www.parlaygorilla.com/api/version`  | JSON with real `git_sha`               |
| Backend SHA        | `curl ... -H "x-ops-token: $OPS_VERIFY_TOKEN" .../ops/verify` | `{"ok":true,"git_sha":"<sha>"}` |
| Full production    | `production_diagnose.py` with FRONTEND_URL + BACKEND_URL | `STATE: SYNCED`                    |
| Backend vs local   | `verify_production_sync.py`                            | `PASS: Production backend matches...` |

More detail: [PROD_VALIDATION_30_SECONDS.md](PROD_VALIDATION_30_SECONDS.md), [PRODUCTION_SYNC_RUNBOOK.md](PRODUCTION_SYNC_RUNBOOK.md).
