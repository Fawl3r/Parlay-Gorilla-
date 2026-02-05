# Marketing-Scale Load Protection

This document describes how Parlay Gorilla protects against traffic spikes (e.g. from marketing launches) without over-engineering: rate limiting, request deduplication where safe, and graceful degradation with friendly user-facing messages.

---

## Objectives

- **Traffic bursts:** Absorb spikes without crashing; respond with clear limits.
- **Concurrent parlay generation:** Cap expensive operations per user/IP.
- **API exhaustion:** Avoid exhausting external APIs or DB connections.
- **Database contention:** Avoid runaway queries; fail gracefully.

---

## Guardrails

### 1. Rate limiting (existing + consistent)

- **SlowAPI** is used with a per-user or per-IP key (`get_rate_limit_key`).
- **Parlay generation:** `@rate_limit("20/hour")` on `/parlay/suggest`.
- **Custom parlay / analyze:** `@rate_limit("30/hour")` on analyze and counter.
- **Auth:** Stricter limits (e.g. 10/min login, 5/hour password reset).
- **Default:** When no decorator is applied, the app still uses a default limit where SlowAPI is mounted.
- **Production:** Rate limits are never disabled in production (`disable_rate_limits` is only for non-production E2E tests).

When a client exceeds the limit they receive **429 Too Many Requests** with a **friendly message:**  
*"Too many requests. Please slow down and try again in a few minutes."*

### 2. Request deduplication (parlay suggest)

- **Where:** `POST /parlay/suggest` only.
- **Logic:** Same user + same (sports, num_legs, risk_profile) within **45 seconds** → treat as duplicate.
- **Implementation:** Redis key `parlay_dedup:{user_id}:{hash(sports,num_legs,risk)}` with TTL 45s. If key exists, return **409 Conflict** with *"Please wait a moment before requesting the same parlay again."*
- **Fail open:** If Redis is unavailable or errors, the request proceeds (no dedupe); we do not block users.

### 3. Graceful degradation (never crash)

- **503 under load:** When parlay building times out or hits resource limits (e.g. MemoryError), the API returns **503** with a user-friendly message (e.g. *"We're under heavy load. Try fewer picks or single sport."*).
- **504 timeout:** Long-running parlay build returns **504** with *"This is taking longer than expected. Try again with fewer legs."*
- **Global exception handler:** Unhandled exceptions return 500 with a generic message and log + alert; the app does not crash.
- **Health checks:** Return 200 or 503 with clear status; never throw.

### 4. No queues

- No message queues or job queues were added for this load protection. Guards, limits, and fallbacks are sufficient for the current scale.

---

## Summary

| Risk              | Mitigation                                      |
|-------------------|--------------------------------------------------|
| Traffic bursts    | Rate limits per user/IP; 429 with friendly text  |
| Duplicate requests| 45s parlay-dedup (Redis); 409 with message      |
| API exhaustion   | Per-endpoint caps (20–30/hour for heavy paths)  |
| DB/load errors    | 503/504 + friendly message; global handler      |
| Crashes           | Try/except and global handler; alerting          |

All behavior is **minimal and targeted**; no architectural change and no new infrastructure beyond existing Redis (optional for dedupe).
