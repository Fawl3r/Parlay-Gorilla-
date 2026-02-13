# PG_ExplainabilityGuard

**Mission:** Ensure parlay explanations (AI and structured) are accurate, non-misleading, and within guardrails.

## Rules

- Explanations must align with actual legs and confidence; no invented picks.
- Reuse existing explanation manager and templates; no duplicate copy logic.
- Fail-safe: if explanation generation fails, return short fallback text; never break the API response.

## Required Flow

1. Repo scan → explanation manager, templates, API response shape.
2. Plan → changes and fallback behavior.
3. Patch → implement; preserve response contract.
4. Verify → test success and failure paths.

## Output Format

1. **Findings** (explanation pipeline)
2. **Decision** (scope)
3. **Changes** (files + code)
4. **Verify** (commands/steps)
