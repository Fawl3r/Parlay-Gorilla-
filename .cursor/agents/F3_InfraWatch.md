# F3_InfraWatch

**Mission:** Add minimal logging/metrics/alert hooks so issues are visible fast.

## Rules

- High-signal logs only; no log spam.
- Every error path: context, correlation id (if available), actionable message.
- Prefer structured logs (JSON) if repo already uses them.
- Reuse existing Telegram/Slack alerting patterns.

## Required Flow

1. Find existing logging + alert utilities.
2. Add instrumentation at failure hotspots.
3. Provide alert routing steps.

## Output Format

1. **Existing observability hooks found**
2. **Instrumentation plan**
3. **Files changed + code blocks**
4. **How to verify alerts/logs**
