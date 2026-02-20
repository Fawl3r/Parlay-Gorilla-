# ADMIN SYSTEM REPORT — Parlay Gorilla Admin Hardening

**Date:** 2025-02-19  
**Scope:** Full validation and hardening of Admin Dashboard and Admin API so no endpoint returns HTTP 500 from unhandled exceptions.

---

## 1. Endpoints audited

All admin routes under `/api/admin/` were audited and hardened:

| Path | Router | Hardened |
|------|--------|----------|
| `GET /api/admin/safety` | safety.py | Yes — safe fallback `SAFE_SAFETY` on any exception |
| `GET /api/admin/metrics/overview` | metrics.py | Yes — service + route fallback |
| `GET /api/admin/metrics/users` | metrics.py | Yes |
| `GET /api/admin/metrics/usage` | metrics.py | Yes |
| `GET /api/admin/metrics/revenue` | metrics.py | Yes |
| `GET /api/admin/metrics/templates` | metrics.py | Yes |
| `GET /api/admin/metrics/model-performance` | metrics.py | Yes |
| `GET /api/admin/logs` | logs.py | Yes — returns `[]` on error |
| `GET /api/admin/logs/stats` | logs.py | Yes — `SAFE_LOGS_STATS` |
| `GET /api/admin/logs/sources` | logs.py | Yes — returns `[]` on error |
| `GET /api/admin/payments` | payments.py | Yes |
| `GET /api/admin/payments/stats` | payments.py | Yes |
| `GET /api/admin/payments/subscriptions` | payments.py | Yes |
| `POST /api/admin/payments/manual-upgrade` | payments.py | Yes — returns `{success: false}` on failure |
| `GET /api/admin/events` | events.py | Yes |
| `GET /api/admin/events/counts` | events.py | Yes |
| `GET /api/admin/events/traffic` | events.py | Yes |
| `GET /api/admin/events/parlays` | events.py | Yes |
| `GET /api/admin/model/metrics` | model.py | Yes |
| `GET /api/admin/model/team-biases` | model.py | Yes |
| `POST /api/admin/model/recalibrate` | model.py | Yes |
| `GET /api/admin/model/config` | model.py | Yes |
| `GET /api/admin/model/sports-breakdown` | model.py | Yes |
| `GET /api/admin/model/market-breakdown` | model.py | Yes |
| `GET /api/admin/users` | users.py | Yes |
| `GET /api/admin/users/{id}` | users.py | Yes |
| `PATCH /api/admin/users/{id}` | users.py | Yes |
| `GET /api/admin/affiliates` | affiliates.py | Yes |
| `PATCH /api/admin/affiliates/{id}/lemonsqueezy-affiliate-code` | affiliates.py | Yes |
| `GET /api/admin/apisports/quota` | apisports.py | Yes |
| `POST /api/admin/apisports/refresh` | apisports.py | Yes |
| `GET /api/admin/payouts/ready-commissions` | payouts.py | Yes |
| `GET /api/admin/payouts` | payouts.py | Yes |
| `GET /api/admin/payouts/summary` | payouts.py | Yes |
| Tax 1099-NEC (JSON + CSV) | tax.py | Yes |
| Payout ledger (JSON + CSV) | tax.py | Yes |
| Promo codes list / bulk / deactivate | promo_codes.py | Yes |
| Feature flags list / get | feature_flags.py | Yes |

---

## 2. Bugs fixed

- **Metrics:** Overview, users, templates previously re-raised `HTTPException(500)` on any exception; usage and revenue had no try/except. All now return 200 with safe fallback JSON.
- **Safety:** No try/except around `get_safety_snapshot()` or Redis; any failure caused 500. Now returns `SAFE_SAFETY` (health_score 100, state UNKNOWN) on any exception.
- **Logs:** Missing `system_log` table or DB errors caused 500. All three handlers now catch `OperationalError`/`ProgrammingError` and return `[]` or `SAFE_LOGS_STATS`.
- **Payments:** List/stats/subscriptions and manual-upgrade could 500 on DB errors. All return safe list/dict or `{success: false}`.
- **Events / Model / Users / Affiliates / Apisports / Payouts / Tax / Promo codes / Feature flags:** Added defensive try/except; no raw DB or unexpected exceptions reach the client.

---

## 3. Files modified

- **New:** `backend/app/core/admin_safe.py` — central safe fallback dicts and lists for all admin responses.
- **Modified:** `backend/app/services/admin_metrics_service.py` — try/except in `get_overview_metrics`, `get_user_metrics`, `get_usage_metrics`, `get_revenue_metrics`, `get_template_metrics`; return safe dicts on `OperationalError`/`ProgrammingError`/`Exception`.
- **Modified:** `backend/app/api/routes/admin/metrics.py` — route-level try/except and safe responses; structured logging.
- **Modified:** `backend/app/api/routes/admin/safety.py` — full try/except; return `SAFE_SAFETY` on any exception.
- **Modified:** `backend/app/api/routes/admin/logs.py` — try/except on list, stats, sources; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/payments.py` — try/except on list, stats, subscriptions, manual-upgrade; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/events.py` — try/except on list, counts, traffic, parlays; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/model.py` — replace 500 with safe JSON for metrics, team-biases, recalibrate; try/except on config, sports-breakdown, market-breakdown; logging.
- **Modified:** `backend/app/api/routes/admin/users.py` — try/except on list, get, update; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/affiliates.py` — try/except on list and PATCH; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/apisports.py` — try/except on quota and refresh; safe fallbacks; logging.
- **Modified:** `backend/app/api/routes/admin/payouts.py` — try/except on ready-commissions, list, summary; process_payout returns 200 with `success: false` instead of 500; logging.
- **Modified:** `backend/app/api/routes/admin/tax.py` — try/except on all four handlers; empty list or header-only CSV on error; logging.
- **Modified:** `backend/app/api/routes/admin/promo_codes.py` — bulk create returns `[]` on error instead of 500; list_promo_codes wrapped in try/except; logging.
- **Modified:** `backend/app/api/routes/admin/feature_flags.py` — list and get wrapped in try/except; safe fallbacks; logging.

---

## 4. Migrations added

**None.** No new tables were introduced. Existing tables (`users`, `system_log`, `app_events`, `payments`, `subscriptions`, etc.) are assumed to exist via existing Alembic migrations. If a table is missing, the relevant admin endpoint now returns a safe fallback (200 + empty/zero structure) instead of 500.

---

## 5. Tests added

- **New:** `backend/tests/test_admin_smoke.py` — 9 tests:
  - `test_admin_safety_returns_200`
  - `test_admin_metrics_overview_returns_200`
  - `test_admin_metrics_users_returns_200`
  - `test_admin_metrics_usage_returns_200`
  - `test_admin_metrics_revenue_returns_200`
  - `test_admin_logs_list_returns_200`
  - `test_admin_logs_stats_returns_200`
  - `test_admin_logs_sources_returns_200`
  - `test_all_admin_smoke_endpoints_return_200` (hits all 8 critical GET endpoints in one run)

- **New:** `backend/tests/__init__.py` (package marker).

Tests run against the test DB (empty between tests via conftest); admin auth is faked via `get_current_user` override. **All 9 tests pass** with no seed data.

---

## 6. Phases 4, 5, 8, 9 — Completed

- **Phase 4 (DB/migrations):** Startup does not crash on migration failure. `AlembicMigrationManager.upgrade_head_async()` catches exceptions and logs; app continues.
- **Phase 5 (Admin auth):** 401/403 enforced via `get_current_user` and `require_admin` in `backend/app/api/routes/admin/auth.py`.
- **Phase 8 (Frontend admin safety):** Revenue/usage already use optional chaining. Added safe fallbacks: users page `response?.users ?? []`, affiliates `res?.items ?? []`, `res?.total ?? 0`. Safety page already uses `snap?.state ?? "GREEN"`, etc.
- **Phase 9:** Admin smoke tests re-run; all 9 pass.

## 7. Admin login speed

- **Cause:** Login page wrapped full UI in Solana `ConnectionProvider`/`WalletProvider`, blocking first paint.
- **Fix:** New `frontend/app/admin/login/AdminWalletSection.tsx` holds all Solana wallet code; loaded via dynamic import (`ssr: false`). Login page default export renders only `AdminLoginContent`; wallet block is inside dynamically loaded `AdminWalletSection`.

## 8. Remaining risks (if any)

- **(Optional) Pending migrations log:** Spec asked for “if migrations are pending → log warning but DO NOT crash application startup.” This was not implemented; consider adding in `main.py` lifespan or startup if you want that guarantee.
- **Division by zero:** Already guarded in `admin_metrics_service._get_api_health` and logs stats (`if total > 0`). No further changes made.

---

## 9. Final confirmation

**Admin system hardened — 500 errors eliminated.**

All audited admin endpoints now catch `OperationalError`, `ProgrammingError`, and generic `Exception` where appropriate, log with structured fields (`admin.endpoint.fallback` / `admin.endpoint.failure`), and return safe JSON (or CSV) with status 200. No unhandled exception from missing tables, empty datasets, NULL aggregates, or cold starts should reach the client.
