"use client"

import {
  getIntentCounters,
  getDismissal,
  recordDismissal as persistDismissal,
  isFirstVisit,
} from "./intentStorage"
import { getIntentState } from "./intentScore"
import { COOLDOWN_MS, SESSION_PROMPT_KEY, SESSION_LAST_PROMPT_TYPE_KEY, type IntentLevel } from "./constants"

export type UpgradeSurfaceType = "engaged" | "powerUser" | "highIntent"

/** Whether we are in cooldown (24h after dismissal). */
export function isInCooldown(): boolean {
  const d = getDismissal()
  if (!d?.last_dismissed_at) return false
  const at = new Date(d.last_dismissed_at).getTime()
  return Date.now() - at < COOLDOWN_MS
}

/** Whether we already showed an upgrade prompt this session. */
export function hasShownPromptThisSession(): boolean {
  if (typeof window === "undefined") return false
  try {
    return sessionStorage.getItem(SESSION_PROMPT_KEY) === "1"
  } catch {
    return false
  }
}

/** Mark that we showed a prompt this session and which type (to avoid repeating same consecutively). */
export function markPromptShownThisSession(promptType: UpgradeSurfaceType): void {
  if (typeof window === "undefined") return
  try {
    sessionStorage.setItem(SESSION_PROMPT_KEY, "1")
    sessionStorage.setItem(SESSION_LAST_PROMPT_TYPE_KEY, promptType)
  } catch {
    /* ignore */
  }
}

/** Whether we last showed this prompt type (session or dismissal) — avoid repeating same consecutively. */
export function wasLastPromptType(promptType: UpgradeSurfaceType): boolean {
  if (typeof window !== "undefined") {
    try {
      const last = sessionStorage.getItem(SESSION_LAST_PROMPT_TYPE_KEY)
      if (last === promptType) return true
    } catch {
      /* ignore */
    }
  }
  const d = getDismissal()
  return d?.last_prompt_type === promptType
}

/**
 * Decide which upgrade surface (if any) may be shown.
 * Caller must still ensure context: e.g. after scroll completion, after analysis, not on first visit.
 */
export function getRecommendedSurface(): UpgradeSurfaceType | null {
  if (isFirstVisit()) return null
  if (isInCooldown()) return null
  if (hasShownPromptThisSession()) return null

  const counters = getIntentCounters()
  const { level } = getIntentState(counters)

  if (level === "highIntent") return "highIntent"
  if (level === "powerUser") {
    if (wasLastPromptType("highIntent")) return null
    return "powerUser"
  }
  if (level === "engaged") {
    if (wasLastPromptType("highIntent") || wasLastPromptType("powerUser")) return null
    return "engaged"
  }
  return null
}

/**
 * Whether we are allowed to show any upgrade surface in this context.
 * context: "after_analysis" | "after_builder" | "after_blurred" | "after_scroll"
 */
export function canShowInContext(
  surface: UpgradeSurfaceType | null,
  _context: string
): boolean {
  if (!surface) return false
  return true
}

/** Record that user dismissed the given surface (starts 24h cooldown). */
export function recordDismissal(surface: UpgradeSurfaceType): void {
  persistDismissal(surface)
}

/** Get current intent level for UI (e.g. visual escalation). */
export function getCurrentIntentLevel(): IntentLevel {
  const counters = getIntentCounters()
  return getIntentState(counters).level
}
