# Memory Optimization & Generator Guard

This document covers the root cause of past parlay-generator OOMs, the guard and caps we use to prevent them, recommended Render sizing, and how to read memory instrumentation.

---

## Crash Root Cause

Parlay generation used to load the full **Game → Markets → Odds** graph via SQLAlchemy `selectinload`. That meant:

- One query pulled all games in the window, then for each game all markets, then for each market all odds.
- Peak memory spiked with the number of games × markets × odds (ORM objects, relationships, and Python overhead).
- Under concurrent requests or large windows, the process could hit OOM and crash.

We fixed this by:

1. **Minimal queries:** Fetch only the columns we need (game id, sport, start_time, teams, etc.) and odds rows (game_id, market_id, market_type, book, outcome, price, implied_prob) without ORM relationship loading.
2. **Caps:** Hard limits on games considered, markets per game, odds rows processed, and candidate legs.
3. **Generator guard:** Limit how many heavy generator requests run at once (per process or across instances via Redis).

---

## Generator Guard

The **generator guard** limits concurrent execution of expensive parlay-generation work so that multiple requests don’t pile up and blow memory.

### Behavior

- **Endpoints protected:** `/parlay/suggest`, `/parlay/suggest/triple`, `/parlay/analyze`.
- **Acquire:** Before heavy work, the handler tries to acquire a slot (Redis-backed semaphore when Redis is available; in-process `BoundedSemaphore` when Redis is down).
- **If no slot:** Respond with **429** and body: *"We're generating lots of parlays right now. Please try again in a moment."* and emit `parlay.generator_busy`.
- **Release:** Slot is always released in a `finally` block after the guarded section.

### Configuration (env)

| Variable | Default | Description |
|----------|---------|-------------|
| `GENERATOR_MAX_CONCURRENT` | `2` | Max concurrent generator requests (per Redis key or per process when Redis is down). |
| `GENERATOR_ACQUIRE_TIMEOUT_S` | `0.25` | How long to wait for a slot before treating as busy (seconds). |
| `GENERATOR_BUSY_HTTP_STATUS` | `429` | HTTP status when no slot is available. |
| `PARLAY_GENERATION_TIMEOUT_S` | `30` | Hard timeout (seconds) for the generation step on `/parlay/suggest` and `/parlay/suggest/triple`. If exceeded, the request returns 504 and `parlay.generation_timeout` is logged. |

Tuning:

- **Single instance:** `GENERATOR_MAX_CONCURRENT=2` is a safe default to avoid memory spikes.
- **Multi-instance (Render):** With Redis configured, the guard uses a shared Redis key so the limit is global across instances. You can raise `GENERATOR_MAX_CONCURRENT` slightly if you have more memory and want more throughput, but keep it low enough to avoid OOM under peak load.

---

## Parlay Caps (Memory Bounds)

These settings bound how much data we pull and how many candidate legs we build per request:

| Variable | Default | Description |
|----------|---------|-------------|
| `PARLAY_MAX_GAMES_CONSIDERED` | `20` | Max games in the candidate window. |
| `PARLAY_MAX_MARKETS_PER_GAME` | `2` | Max main markets (e.g. h2h, spreads, totals) per game. |
| `PARLAY_MAX_LEGS_CONSIDERED` | `150` | Max candidate legs retained; excess is truncated and `parlay.candidates_truncated` is emitted. |
| `PARLAY_MAX_PROPS_PER_GAME` | `2` | Max player-props markets per game. |
| `PARLAY_MAX_ODDS_ROWS_PROCESSED` | `600` | Max odds rows processed per request (minimal-odds query cap). |
| `CANDIDATE_LEGS_CACHE_TTL_SECONDS` | `45` | TTL for the per-sport/day candidate-legs cache. Short cache (30–60s) avoids repeated heavy builds during ad bursts; same slate is reused across requests. |

Raising these increases memory use; only increase if you have headroom and need broader coverage.

### Candidate-legs cache

Candidate legs (the list of eligible picks per sport/day) are cached for a short period (`CANDIDATE_LEGS_CACHE_TTL_SECONDS`, default 45s). The cache key is per sport, UTC date, week, and whether player props are included. During traffic bursts, many users hit the same slate; a cache hit skips the heavy DB/odds work and returns the cached list (with per-request `max_legs` cap applied). Redis is used when configured; otherwise an in-process fallback is used.

---

## Recommended Render Sizing

- **Web service:** At least **512 MB** RAM for the backend; **1 GB** is safer for parlay generation with the guard and caps in place.
- **Redis:** Use a small Redis instance (e.g. free or starter) for the generator guard and dedupe; same region as the web service for low latency.
- **Observe:** After deploy, watch memory metrics and logs (see below). If you see frequent `parlay.generator_busy` or `parlay.candidates_truncated`, consider slightly increasing concurrency or caps only if memory stays within limits.

---

## Memory Instrumentation & Events

### Log labels (RSS)

The backend logs **RSS (MB)** at key points with a `label` and optional `extra`:

| Label | When |
|-------|------|
| `candidate_legs_before_game_query` | Before fetching minimal game rows. |
| `candidate_legs_after_game_query` | After minimal game rows; before odds fetch. |
| `candidate_legs_after_odds_fetch` | After minimal odds rows; before building candidate legs. |
| `candidate_legs_after_build` | After candidate legs are built (includes count). |
| `parlay_suggest_after_response_built` | After building the response for `/parlay/suggest`. |
| `parlay_triple_after_response_built` | After building the response for `/parlay/suggest/triple`. |

Use these to see where memory grows (e.g. a big jump after odds fetch or after build). Correlate with request volume and guard/busy events.

### Events (for alerts/dashboards)

- **`parlay.generator_busy`** — A request was rejected because the generator guard had no free slot. Indicates concurrency limit is hit; users see 429 and retry.
- **`parlay.generation_timeout`** — The generation step (build parlay or triple) exceeded `PARLAY_GENERATION_TIMEOUT_S`. Request returns 504; payload includes `trace_id`, `endpoint`, `user_id`.
- **`parlay.candidates_truncated`** — Candidate list was capped (e.g. by `parlay_max_legs_considered` or by hitting the cap while building). Payload includes `sport`, `candidate_count`, `max_legs_cap`.

Use these to tune guard limits, timeout, caps, and to detect sustained load.

---

## Summary

| Concern | Mitigation |
|--------|------------|
| OOM from full ORM load | Minimal game + odds queries; no `selectinload` on Game→markets→odds. |
| Too many concurrent generators | Generator guard (Redis or in-process) with 429 when busy. |
| Unbounded candidate work | Caps on games, markets per game, odds rows, and candidate legs. |
| Long-running generation | `PARLAY_GENERATION_TIMEOUT_S` (e.g. 30s); 504 + `parlay.generation_timeout` on timeout. |
| Repeated heavy builds in bursts | Candidate-legs cache (per sport/day, 30–60s TTL). |
| Visibility | Memory log labels and `parlay.generator_busy` / `parlay.generation_timeout` / `parlay.candidates_truncated` events. |

All of this is designed to be safe for multi-instance Render: guard uses Redis when available, and caps apply per request so each instance stays within bounds.
