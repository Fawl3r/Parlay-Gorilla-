# Public Launch Readiness Checklist

This checklist confirms hardening for **public-scale traffic** and **real-money trust** on the existing FastAPI + PostgreSQL + Render stack. No architecture rewrite; minimal, targeted changes only.

---

## Section A: Edge-Case Settlement

- [x] **Late games:** Settlement does not assume date-based completion; 30-day FINAL window; duplicate attempts are no-op.
- [x] **Suspended/Postponed:** Game status normalized; settlement runs only on FINAL; legs stay PENDING until FINAL.
- [x] **No Contest/Cancelled:** Legs voided by worker; parlay status recalculated; clear result_reason.
- [x] **Stat corrections:** `settlement_locked_at` on parlay_legs; one re-evaluation window possible; changes must be logged.
- [x] **Multi-day events:** Each leg independent; parlay status only when all legs terminal (no early settlement).

**Doc:** [edge_case_settlement.md](./edge_case_settlement.md)

---

## Section B: Out-of-Season Sport Logic

- [x] **Season detection:** SeasonStateService + SportAvailabilityResolver.
- [x] **Block AI parlay gen for OFF_SEASON:** Builder raises with user-safe message; no odds/candidate load.
- [x] **Clear logs:** Intentional skip logged (sport, state, message).
- [x] **API calls skipped** for unavailable sport (builder exits before heavy work).

**Doc:** [season_handling.md](./season_handling.md)

---

## Section C: Observability & Telegram Alerts

- [x] **Settlement failures:** Alert on settlement worker exception.
- [x] **Circuit breaker:** Alert when circuit opens (repeated errors).
- [x] **Rate-limit hits:** Alert on 429 (api.rate_limit_hit).
- [x] **Empty game pools:** Existing parlay.generate.fail.not_enough_games alert.
- [x] **Database connection errors:** Alert on health/db failure.
- [x] **Unhandled exceptions:** Existing api.unhandled_exception with environment + stack.
- [x] **Throttling:** TelegramNotifier 1 msg/10s; AlertingService spike detection; dedupe 10 min.
- [x] **Payload:** Environment, error type, message, short stack where relevant.

**Doc:** [observability_alerts.md](./observability_alerts.md)  
**Config:** `TELEGRAM_ALERTS_ENABLED`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in backend .env and Render.

---

## Section D: Load Protection

- [x] **Rate limiting:** Public endpoints (parlay 20/h, custom 30/h, auth stricter); 429 with friendly message.
- [x] **Request deduplication:** Parlay suggest same user + same options within 45s → 409 with message (Redis, fail-open).
- [x] **Graceful degradation:** 503/504 with user-facing messages; global exception handler; no crash.
- [x] **No queues added:** Guards, limits, fallbacks only.

**Doc:** [load_protection.md](./load_protection.md)

---

## Pre-Launch Verification

1. **Run migration:** `047_settlement_lock_and_game_status` (adds `parlay_legs.settlement_locked_at`).
2. **Env (Render + backend .env):** Telegram keys set if alerts are desired; `FEATURE_SETTLEMENT` enabled only when ready.
3. **Smoke test:** Health, health/db, one parlay suggest, one rate-limit hit (optional).
4. **Settlement:** Ensure game statuses from score pipeline use normalized status (suspended/postponed/no_contest not mapped to FINAL).

---

## Summary

- **Correctness and transparency** over speed.
- **$0** additional cost (Telegram + existing Redis).
- All changes are **minimal and commented**; four deploy docs and this checklist document behavior and readiness.
