# Agents Index

When to invoke each agent (Cursor: @-mention or pick from rule list).

## 10-second usage

- **Invoke first:** **F3_CodeGuardian** (scan for reuse, plan minimal diffs), then the domain agent for the area you’re touching (e.g. **PG_PicksEngine** for parlay logic, **PG_APIQuotaNinja** for APIs).
- **Block merges:** **F3_TestSentinel** (tests must pass) and **Safety Mode must be GREEN** (see BUILD_CHECKLIST.md). **F3_InfraWatch** before merge when touching failures/alerts.
- **Conditional:** Use **PG_PicksEngine**, **PG_ExplainabilityGuard**, **PG_ConfidenceEngineer**, **PG_PayoutRiskGuard** only when touching parlay/pick logic; **PG_APIQuotaNinja** / **PG_AnomalyDetector** when touching APIs or data; **PG_RevenueSentinel** / **PG_ComplianceShield** when touching paywalls or billing.

## Core engineering

| Agent | When to use |
|-------|-------------|
| **F3_CodeGuardian** | Code review, refactors, any change where duplication or abstraction is a risk. Always applied. |
| **F3_TestSentinel** | Adding tests, fixing bugs, verifying non-trivial behavior. Always applied. |
| **F3_InfraWatch** | Adding logs, metrics, or alerts; debugging production issues. |

## Parlay Gorilla build/product

| Agent | When to use |
|-------|-------------|
| **PG_FeatureBuilder** | New feature end-to-end (backend + frontend + tests). |
| **PG_PicksEngine** | Pick pipeline, filters, "not enough games", season awareness. |
| **PG_APIQuotaNinja** | API calls, caching, rate limits, quota (e.g. API-Sports, Odds API). |
| **PG_ConfidenceEngineer** | Confidence scores, hit probability, calibration. |
| **PG_ExplainabilityGuard** | Parlay explanations (AI/structured), fallback copy. |
| **PG_AnomalyDetector** | Detecting anomalies in outcomes, API errors, usage. |
| **PG_FailsafeOrchestrator** | Safety Mode, degradation, freeze (GREEN/YELLOW/RED). |
| **PG_RevenueSentinel** | Subscriptions, credits, pay-per-use, webhooks. |
| **PG_ComplianceShield** | Disclaimers, terms, responsible gaming, payment compliance. |
| **PG_PayoutRiskGuard** | Settlement, grading, affiliate payouts, double-payout risk. |
| **PG_ModelDriftWatcher** | Model/data drift, win-rate vs expected, confidence distribution. |
| **PG_BacktestHistorian** | Historical backtests, reporting, read-only analytics. |

## Pipeline order (feature work)

1. **F3_CodeGuardian** — scan for reuse; plan minimal diffs.
2. **PG_FeatureBuilder** or domain agent (e.g. PG_PicksEngine) — implement.
3. **F3_TestSentinel** — add/update tests.
4. **F3_InfraWatch** (if touching failures/alerts) — add logging/alerting.

Rule files live in `.cursor/rules/`; agent prompts in `.cursor/agents/`.
