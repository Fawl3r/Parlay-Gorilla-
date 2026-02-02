# Custom Builder QuickStart Templates — Metrics

## Session ID (already in place)

All frontend events include `session_id` (from `pg_session_id` in sessionStorage). This makes Template Completion Rate computation clean: join by `session_id` and filter by time delta, no fuzzy window logic.

---

## Template Completion Rate (primary success metric)

**Definition:** A user who had `custom_builder_template_applied` then triggered `custom_builder_analyze_clicked` within **2 minutes** (same session).

- **Why it matters:** If this rate is low, templates fill the slip but users don’t take the next step. Fix follow-through (scroll, pulse, helper copy), not the template engine.
- **How to compute:** Join `app_events` by `session_id` (or `user_id`); for each `custom_builder_template_applied` event, check if there is a `custom_builder_analyze_clicked` with `created_at` within 2 minutes after. Ratio = (sessions with both within 2 min) / (sessions with template_applied).

## Dashboard aggregates (admin / internal)

- **Clicks by template_id:** `custom_builder_template_clicked` count per template.
- **Applied by template_id:** `custom_builder_template_applied` count per template.
- **Partial rate by template_id:** `custom_builder_template_partial` / (applied + partial) per template — indicates thin slates.

These are available under **Admin → Dashboard → Templates**.

---

## Production safety checklist (before merging Commit C)

- **Custom Builder UX:** Apply template → scroll on mobile + desktop; Analyze pulse resets after 1.2s; beginner helper only once per session (sessionStorage).
- **Partial template:** With picks → toast action "Analyze what I've got" calls analyze once; with zero picks → "Include all upcoming" scrolls to games area.
- **Analytics:** Confirm in `app_events`: `custom_builder_template_followthrough_shown`, template clicked/applied/partial, analyze_clicked/success/fail.
- **Regression:** Clear slip still clears persisted slip (refresh after clearing).

---

## What to watch (first 72h after deploy)

- **Partial rate by template:** Safer 2 lowest, Solid 3 medium, Longshot 4 highest. If Longshot >70%, consider lowering required count for thin slates (only after data).
- **Template Completion Rate:** Target ≥45% at start, ≥60% once follow-through is working. If low, improve prominence of Analyze (button, pulse, "Next step" icon), not the engine.
