# Custom Builder QuickStart Templates — Metrics

## Template Completion Rate (primary success metric)

**Definition:** A user who had `custom_builder_template_applied` then triggered `custom_builder_analyze_clicked` within **2 minutes** (same session).

- **Why it matters:** If this rate is low, templates fill the slip but users don’t take the next step. Fix follow-through (scroll, pulse, helper copy), not the template engine.
- **How to compute:** Join `app_events` by `session_id` (or `user_id`); for each `custom_builder_template_applied` event, check if there is a `custom_builder_analyze_clicked` with `created_at` within 2 minutes after. Ratio = (sessions with both within 2 min) / (sessions with template_applied).

## Dashboard aggregates (admin / internal)

- **Clicks by template_id:** `custom_builder_template_clicked` count per template.
- **Applied by template_id:** `custom_builder_template_applied` count per template.
- **Partial rate by template_id:** `custom_builder_template_partial` / (applied + partial) per template — indicates thin slates.

These are available under **Admin → Dashboard → Templates**.
