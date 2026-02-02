/**
 * Success tracking for AI Picks: count successful builds, first success, graduation nudge.
 * Used for first-success celebration and Beginner → Standard graduation nudge.
 */

const KEY_SUCCESS_COUNT = "pg_successful_builds"
const KEY_FIRST_SUCCESS_DONE = "pg_first_success_done"
const KEY_GRADUATION_NUDGE_DISMISSED = "pg_graduation_nudge_dismissed"

const GRADUATION_THRESHOLD = 3

function getCount(): number {
  if (typeof window === "undefined") return 0
  try {
    const raw = localStorage.getItem(KEY_SUCCESS_COUNT)
    if (raw === null) return 0
    const n = parseInt(raw, 10)
    return Number.isFinite(n) ? Math.max(0, n) : 0
  } catch {
    return 0
  }
}

function setCount(n: number): void {
  try {
    localStorage.setItem(KEY_SUCCESS_COUNT, String(Math.max(0, n)))
  } catch {
    // ignore
  }
}

/** Call when user successfully generates a parlay. Returns new count and whether this was first success. */
export function recordParlaySuccess(): { count: number; isFirstSuccess: boolean } {
  const wasFirst = typeof window !== "undefined" && localStorage.getItem(KEY_FIRST_SUCCESS_DONE) !== "true"
  const prev = getCount()
  const next = prev + 1
  setCount(next)
  if (wasFirst && typeof window !== "undefined") {
    try {
      localStorage.setItem(KEY_FIRST_SUCCESS_DONE, "true")
    } catch {
      // ignore
    }
  }
  return { count: next, isFirstSuccess: wasFirst }
}

/** Current number of successful parlay builds (for graduation nudge). */
export function getSuccessCount(): number {
  return getCount()
}

export function isGraduationNudgeDismissed(): boolean {
  if (typeof window === "undefined") return false
  try {
    return localStorage.getItem(KEY_GRADUATION_NUDGE_DISMISSED) === "true"
  } catch {
    return false
  }
}

export function setGraduationNudgeDismissed(): void {
  try {
    localStorage.setItem(KEY_GRADUATION_NUDGE_DISMISSED, "true")
  } catch {
    // ignore
  }
}

export const GRADUATION_THRESHOLD_BUILDS = GRADUATION_THRESHOLD
