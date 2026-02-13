# Workflow Pipeline — Build Features Safely

Exact step-by-step sequence for feature work in this repo.

## 1. Scan (mandatory)

- Identify **backend** entry: `backend/app/main.py`; routes under `backend/app/api/routes/`.
- Identify **frontend** app router: `frontend/app/`; API in `frontend/lib/api/`.
- Search for **reuse**: same purpose = one function; confirm files/symbols exist before referencing.
- Confirm **env/config**: only use vars from `backend/app/core/config.py` and `backend/.env.example`; add new ones explicitly.

## 2. Plan

- Decide scope: backend-only, frontend-only, or both.
- List exact files to touch; avoid speculative params or new types unless reused.
- If feature touches parlay generation: note Safety Mode (GREEN/YELLOW/RED) and telemetry.

## 3. Implement

- **Backend:** Routes thin; business logic in services under `backend/app/services/`.
- **Frontend:** Use existing `ApiFacade` / services in `frontend/lib/api/`; minimal UI changes.
- **Config:** New env vars → `backend/app/core/config.py` + `backend/.env.example`.
- **Safety/telemetry:** If parlay-related, wire telemetry and Safety Mode per `SAFETY_MODE_SPEC.md`.

## 4. Verify

- Run backend tests: `cd backend && pytest -q`.
- Run frontend tests if UI changed: `cd frontend && npm run test:unit`.
- Smoke: start API, hit health and any new endpoint; check logs for errors.

## 5. Optional: Observability

- If failure paths or alerts added: use **F3_InfraWatch** flow; reuse `get_alerting_service().emit()` for Telegram.

## Pipeline map (key paths)

- Parlay generation: `backend/app/api/routes/parlay.py` → `suggest_parlay`; services: `ParlayBuilderService`, `MixedSportsParlayBuilder`, `get_parlay_eligibility`.
- Health/ops: `backend/app/api/routes/health.py`, `backend/app/api/routes/ops.py`.
- Admin: `backend/app/api/routes/admin/` (prefix `/api/admin`); auth: `require_admin`.
- Alerting: `backend/app/services/alerting/` → `get_alerting_service().emit()`.
