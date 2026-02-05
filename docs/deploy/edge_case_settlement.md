# Edge-Case Settlement Timing

This document describes how the Parlay Gorilla settlement system handles late games, suspended/postponed games, stat corrections, and multi-day events. **Correctness and transparency matter more than speed** for real-money trust.

---

## 1. Late Games

**Failure mode:** Games delayed beyond scheduled start, or finishing the next calendar day, could be skipped if settlement assumed "game completes on start date."

**Guardrails:**
- Settlement **does not** assume date-based completion. It relies **only** on game `status == FINAL` (and scores).
- The settlement worker selects FINAL games over a **30-day lookback** so late or next-day finishes are included.
- Duplicate settlement is prevented: only legs in `PENDING` or `LIVE` are updated; re-running on the same game is a no-op.

**Fallbacks:**
- No "pending_due_to_delay" state is required: legs stay `PENDING` until the game is `FINAL`.
- If a game is delayed by hours or days, legs remain PENDING until the upstream source marks it FINAL.

**Observability:** Normal settlement logs (`settle_parlay_legs_for_game: Processing N legs for game X`) and worker logs (`Processed N FINAL games`) remain the source of truth.

---

## 2. Suspended / Postponed / No Contest

**Failure mode:** Weather suspensions, postponements, or "No Contest" could be incorrectly settled or left stuck.

**Guardrails:**
- `GameStatusNormalizer` maps `suspended`, `postponed`, `no_contest`, `cancelled` to canonical values and **never** maps them to `FINAL`.
- Settlement runs **only** when `game.status` is `FINAL`. Suspended/Postponed games are skipped; legs stay `PENDING`.
- When status returns to `FINAL` (game resumed), settlement runs as usual.

**Void when game never resumes:**
- Games with status `no_contest` or `cancelled` are treated as never resuming.
- The settlement worker, each cycle, finds such games (within last 30 days) and calls `void_legs_for_non_resumed_game(game_id, reason="game_no_contest_or_cancelled")`.
- Affected legs are set to `VOID` with a clear `result_reason`. Parlay status is recalculated (all legs resolved); payout logic already handles VOID in `ParlayStatusCalculator`.

**Suspended / Postponed (may resume):**
- No automatic void. Legs stay `PENDING` until the game is either `FINAL` or later reclassified as `no_contest`/`cancelled` by the data source.

---

## 3. Stat Corrections

**Failure mode:** Stats updated after a game is marked FINAL (e.g. within 24–72 hours) could lead to silent outcome changes.

**Guardrails:**
- Each parlay leg has **`settlement_locked_at`** (timestamp). It is set when the leg is first settled.
- One controlled **re-evaluation window** (e.g. 24–72 hours) can be implemented: only legs with `settlement_locked_at` within that window are eligible for re-eval when game scores/stats change.
- Any stat-based outcome change **must be logged explicitly** (never silent). Re-eval logic should log: game_id, leg_id, old_result, new_result, reason.

**Current behavior:** First settlement sets `settlement_locked_at`. Re-evaluation logic can be added later (e.g. a separate job that re-runs the leg result calculator for recently settled legs and logs + updates if result changed).

---

## 4. Multi-Day Events

**Failure mode:** Events spanning multiple days or series could cause early parlay settlement before all legs are resolved.

**Guardrails:**
- Each leg is treated **independently**. Parlay status is derived only from leg statuses.
- **ParlayStatusCalculator** updates parlay status to WON/LOST/PUSH/VOID **only when all legs** are in a terminal state (WON, LOST, PUSH, VOID).
- If any leg is still PENDING or LIVE, the parlay remains PENDING or LIVE. No early parlay settlement.

---

## Summary Table

| Scenario              | Behavior                                                                 |
|-----------------------|---------------------------------------------------------------------------|
| Late / next-day game  | 30-day FINAL window; no date-based skip; duplicate attempt is no-op    |
| Suspended/Postponed   | Not settled until FINAL; legs stay PENDING                                |
| No Contest/Cancelled  | Legs voided by worker; parlay recalculated                                |
| Stat correction       | `settlement_locked_at` supports one re-eval window; changes must be logged |
| Multi-day / series    | Per-leg resolution; parlay status only when all legs terminal             |
