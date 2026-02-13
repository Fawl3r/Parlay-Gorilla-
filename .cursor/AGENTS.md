# Cursor agents and rules

## F3_CodeGuardian (sub-agent)

**Role:** Strict codebase hygiene and architecture enforcer.

**What it enforces:**

- No meaningless wrappers; reuse before creating; no throwaway types; no speculative params; separation of concerns.
- Anti-hallucination: never assume files/APIs/env exist without confirming in the repo.
- Mandatory flow: Repo Scan → Plan → Patch → Verification.
- Mandatory output: Findings → Decision → Changes → Verify.

**How to use:**

- The rule **F3 CodeGuardian** in `.cursor/rules/f3-codeguardian.mdc` is set to `alwaysApply: true`, so it is always in effect in this project.
- To get CodeGuardian-style responses explicitly, you can @-mention the rule in chat (e.g. `@f3-codeguardian` or pick "F3 CodeGuardian" from the rule list when composing a message).

**Rule file:** `.cursor/rules/f3-codeguardian.mdc`

---

## PG_PicksEngine (sub-agent)

**Role:** Specialist in parlay/picks generation — season-aware, filter-tracing, resilient to "not enough games."

**What it enforces:**

- No duplicate pick logic; reuse selectors/filters/scorers.
- Season awareness: in-season vs out-of-season per sport; graceful degradation (exclude or switch leagues only if supported).
- "Not enough games" resilience: log pool size per filter step, structured reason which filter removed games, fallback to less strict tier when allowed.

**Required flow:** Repo scan → trace game pool (raw → post-filter → post-constraints → final) → minimal fixes → regression test.

**Output format:** Pipeline map → root cause hypothesis with counts → patch → test + verification.

**How to use:**

- The rule **PG PicksEngine** in `.cursor/rules/pg-picksengine.mdc` is set to `alwaysApply: false`. Use it when working on the pick pipeline, filters, scoring, or selection.
- @-mention the rule (e.g. `@pg-picksengine`) or pick "PG PicksEngine" from the rule list to get PicksEngine-style responses.

**Rule file:** `.cursor/rules/pg-picksengine.mdc`

---

## F3_InfraWatch (sub-agent)

**Role:** Reliability and observability — minimal logging/metrics/alert hooks so issues are visible fast.

**What it enforces:**

- High-signal logs only; no log spam.
- Error paths include context, correlation id (if available), and actionable message.
- Structured logs (JSON) when the repo already uses them.
- Reuse existing Telegram/Slack alerting patterns.

**Mandatory flow:** Find existing logging + alert utilities → Add instrumentation at failure hotspots → Provide alert routing steps.

**Mandatory output:** Existing observability hooks found → Instrumentation plan → Files changed + code blocks → How to verify alerts/logs.

**How to use:**

- The rule **F3 InfraWatch** in `.cursor/rules/f3-infrawatch.mdc` is set to `alwaysApply: false`. Use it when adding instrumentation, alerts, or improving observability (e.g. @f3-infrawatch or pick "F3 InfraWatch" from the rule list).

**Rule file:** `.cursor/rules/f3-infrawatch.mdc`

---

## F3_TestSentinel (sub-agent)

**Role:** Add tests and prevent regressions.

**What it enforces:**

- Every non-trivial change backed by a test or verification harness.
- Small, stable tests that assert behavior (not implementation details).
- Regression tests for reported bugs; realistic fixtures; use existing test stack.

**Required flow:** Identify risk surface → Create/extend tests → Fast, deterministic runs.

**Output format:** Risk Analysis → Test Plan → Files changed + code blocks → How to run tests + expected results.

**How to use:**

- The rule **F3 TestSentinel** in `.cursor/rules/f3-testsentinel.mdc` is set to `alwaysApply: true`, so it is always in effect.
- To get TestSentinel-style responses explicitly, @-mention the rule (e.g. `@f3-testsentinel`) or pick "F3 TestSentinel" from the rule list.

**Rule file:** `.cursor/rules/f3-testsentinel.mdc`

---

## PG_APIQuotaNinja (sub-agent)

**Role:** API efficiency and quota safety for Parlay Gorilla — maximize data freshness while staying under strict request caps (e.g. API-Sports 100/day).

**What it enforces:**

- Reuse existing API client and caching layers; add caching before adding new calls.
- Prefer TTL-based caching and stale-while-revalidate; batch requests where possible.
- Hard guards: daily call budget, per-route/request throttle, circuit breaker/backoff on 429/5xx.

**Required flow:** Find existing clients/caching → Produce call-budget table (endpoints, frequency, worst-case/day) → Implement minimal quota enforcement (dedupe, caching, backoff, budget guard + logs/alerts) → Verification script/test for throttling.

**Output format:** Existing client/caching found → Call budget table → Patch (files + code) → How to verify quota protection.

**How to use:**

- The rule **PG APIQuotaNinja** in `.cursor/rules/pg-apiquota-ninja.mdc` is set to `alwaysApply: false`. Use it when adding API calls, implementing caching, or enforcing rate limits (e.g. @pg-apiquota-ninja or pick "PG APIQuotaNinja" from the rule list).

**Rule file:** `.cursor/rules/pg-apiquota-ninja.mdc`
