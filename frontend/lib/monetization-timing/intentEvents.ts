"use client"

/**
 * Intent event hooks — console only. No external analytics.
 * Prepares future measurement; events are internal.
 */

export type IntentEventType =
  | "analysis_viewed"
  | "builder_interaction"
  | "blurred_content_viewed"
  | "return_visit"
  | "upgrade_prompt_shown"
  | "upgrade_dismissed"
  | "upgrade_learn_more_clicked"
  | "upgrade_view_plans_clicked"

export function emitIntentEvent(
  event: IntentEventType,
  detail?: Record<string, unknown>
): void {
  if (typeof window === "undefined") return
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_PG_DEBUG_INTENT !== "true") return
  console.debug("[PG Intent]", event, detail ?? "")
}
