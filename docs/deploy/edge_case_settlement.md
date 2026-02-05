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

**30-day window:** FINAL games are selected with `start_time >= now - 30 days`. Games delayed **longer than 30 days** (rare) will not be picked up by the automatic worker. For those, use a **manual settle** path: run a script or admin action that calls `settle_parlay_legs_for_game(game_id)` for the specific game, or extend the window in the worker if your sport often has very late finals.

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

**Suspended / Postponed (may resume) — “who decided” rule:**
- **Do NOT auto-void** postponed or suspended games. They may resume (e.g. 2 days later). Voiding them would incorrectly cancel legs that later complete.
- We **only** auto-void **no_contest** and **cancelled** (statuses that mean the game will never complete).
- Postponed/suspended are voided only if: (1) they remain non-final past an explicit threshold (e.g. 7 days) in a separate, optional job, or (2) the provider later marks them cancelled. That logic is not implemented by default to avoid accidentally voiding games that resume.

---

## 3. Stat Corrections

**Failure mode:** Stats updated after a game is marked FINAL (e.g. within 24–72 hours) could lead to silent outcome changes.

**Guardrails:**
- Each parlay leg has **`settlement_locked_at`** (timestamp). It is set when the leg is first settled.
- **Re-evaluation window:** Config `SETTLEMENT_STAT_CORRECTION_REEVAL_HOURS` (default 72). Only legs with `settlement_locked_at` within that window are eligible for re-eval.

**Trigger path:**
- **Automatic:** Each settlement cycle the worker calls `re_eval_stat_corrections()`. Legs settled within the last 72h (or configured hours) are re-run through the leg result calculator; if game scores changed and outcome flips, the leg is updated.
- **Manual:** An admin endpoint or internal script can call `SettlementService(db).re_eval_stat_corrections(within_hours=72)` (optionally scoped by game_id in a future change). Use for targeted re-run with audit logging.

**When a correction changes outcome:**
- Emit Telegram alert **`settlement.stat_correction_applied`** with leg_id, game_id, parlay_id, old_result, new_result, environment.
- Log an **auditable record** at WARNING: `settlement.stat_correction_applied leg_id=... game_id=... parlay_id=... old=... new=...`. `result_reason` on the leg is appended with `[STAT_CORRECTION: old->new]`.

**Status normalization (consistent across providers):**  
`GameStatusNormalizer` maps all common variants so settlement and void logic see a single canonical set:
- **FINAL:** final, finished, closed, complete, post, ft, game over, ended, full time, fulltime.
- **Suspended:** suspended, suspend, susp.
- **Postponed:** postponed, postpone, ppd, delayed; abandoned → postponed.
- **No contest:** no contest, no_contest, noconstant, cancelled, canceled.

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
| Stat correction       | Automatic re-eval within 72h each cycle; alert + audit log on change; manual trigger available |
| Multi-day / series    | Per-leg resolution; parlay status only when all legs terminal             |
