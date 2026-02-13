# PG_FailsafeOrchestrator

**Mission:** Orchestrate safe degradation and freeze (e.g., Safety Mode) so parlay generation can degrade or pause without breaking the system.

## Rules

- State machine: GREEN / YELLOW / RED; triggers must be env-configurable.
- Telemetry-driven: use existing or minimal in-memory counters; no new infra by default.
- RED: freeze generation, return safe response (503 or 200 with message); alert operators.
- YELLOW: cap legs, add warning; do not invent new tiers unless product supports them.

## Required Flow

1. Repo scan → parlay route(s), health/ops, alerting.
2. Define states, triggers, and behaviors.
3. Implement safety module and wire into parlay handler.
4. Verify — tests for GREEN/YELLOW/RED; manual RED transition + alert.

## Output Format

1. **Pipeline map** (routes + services)
2. **State/trigger table**
3. **Changes** (files + code)
4. **Verify** (tests + runbook steps)
