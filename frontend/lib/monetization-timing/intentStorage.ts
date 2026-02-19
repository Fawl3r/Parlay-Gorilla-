"use client"

/**
 * Intent Signal Storage — frontend-only localStorage.
 * No personal data, no backend sync. Lightweight counters only.
 */

const KEY = "PG_INTENT"
const FIRST_VISIT_KEY = "PG_INTENT_FIRST_VISIT"
const TODAY_KEY = "PG_INTENT_TODAY"

export interface IntentCounters {
  analyses_viewed_count: number
  analyses_viewed_today: number
  sports_explored_count: number
  builder_interactions: number
  return_visits: number
  consecutive_days_active: number
  blurred_content_views: number
}

export interface IntentDismissal {
  last_dismissed_at: string
  last_prompt_type: string
}

const DEFAULT_COUNTERS: IntentCounters = {
  analyses_viewed_count: 0,
  analyses_viewed_today: 0,
  sports_explored_count: 0,
  builder_interactions: 0,
  return_visits: 0,
  consecutive_days_active: 0,
  blurred_content_views: 0,
}

function todayDateString(): string {
  return new Date().toISOString().slice(0, 10)
}

function safeGet<T>(key: string, parse: (raw: string) => T, fallback: T): T {
  if (typeof window === "undefined") return fallback
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return parse(raw)
  } catch {
    return fallback
  }
}

function safeSet(key: string, value: string): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(key, value)
  } catch {
    /* quota or disabled */
  }
}

function getCounters(): IntentCounters {
  const stored = safeGet(
    KEY,
    (raw) => JSON.parse(raw) as Partial<IntentCounters>,
    {}
  )
  const today = todayDateString()
  const storedToday = safeGet(TODAY_KEY, (x) => x, "")
  const counters: IntentCounters = { ...DEFAULT_COUNTERS, ...stored }
  if (storedToday !== today) {
    counters.analyses_viewed_today = 0
    safeSet(TODAY_KEY, today)
  }
  return counters
}

function persistCounters(c: IntentCounters): void {
  safeSet(KEY, JSON.stringify(c))
}

/** Record that user viewed an analysis. Call with sport to update sports_explored. */
export function recordAnalysisView(sport?: string): void {
  const c = getCounters()
  c.analyses_viewed_count += 1
  c.analyses_viewed_today += 1
  if (sport && typeof sport === "string") {
    const sportsKey = "PG_INTENT_SPORTS"
    const list = safeGet(sportsKey, (raw) => JSON.parse(raw) as string[], [])
    const normalized = sport.toLowerCase().trim()
    if (normalized && !list.includes(normalized)) {
      list.push(normalized)
      safeSet(sportsKey, JSON.stringify(list.slice(-50)))
      c.sports_explored_count = list.length
    }
  }
  persistCounters(c)
}

/** Record a builder interaction (custom builder / add to parlay flow). */
export function recordBuilderInteraction(): void {
  const c = getCounters()
  c.builder_interactions += 1
  persistCounters(c)
}

/** Record return visit and update consecutive days. Call on app/dashboard load. */
export function recordReturnVisit(): void {
  const today = todayDateString()
  const firstVisit = safeGet(FIRST_VISIT_KEY, (x) => x, "")
  const lastVisitKey = "PG_INTENT_LAST_VISIT"
  const lastVisit = safeGet(lastVisitKey, (x) => x, "")

  if (!firstVisit) {
    safeSet(FIRST_VISIT_KEY, today)
    safeSet(lastVisitKey, today)
    return
  }

  if (lastVisit === today) return

  const c = getCounters()
  c.return_visits += 1
  if (lastVisit) {
    const last = new Date(lastVisit)
    const curr = new Date(today)
    const diffDays = Math.round((curr.getTime() - last.getTime()) / 86400000)
    if (diffDays === 1) c.consecutive_days_active += 1
    else if (diffDays > 1) c.consecutive_days_active = 1
  } else {
    c.consecutive_days_active = 1
  }
  safeSet(lastVisitKey, today)
  persistCounters(c)
}

/** Record that user saw blurred premium content. */
export function recordBlurredContentView(): void {
  const c = getCounters()
  c.blurred_content_views += 1
  persistCounters(c)
}

/** Read current counters (for score calculation). */
export function getIntentCounters(): IntentCounters {
  return getCounters()
}

/** Check if this is the first visit (no upgrade prompts on first visit). */
export function isFirstVisit(): boolean {
  const first = safeGet(FIRST_VISIT_KEY, (x) => x, "")
  return !first
}

/** Set first visit date when we want to mark first session (e.g. after first meaningful action). */
export function setFirstVisitIfNeeded(): void {
  const first = safeGet(FIRST_VISIT_KEY, (x) => x, "")
  if (!first) safeSet(FIRST_VISIT_KEY, todayDateString())
}

/** Get dismissal state for cooldown. */
export function getDismissal(): IntentDismissal | null {
  const raw = safeGet("PG_INTENT_DISMISSAL", (x) => x, "")
  if (!raw) return null
  try {
    return JSON.parse(raw) as IntentDismissal
  } catch {
    return null
  }
}

/** Record that user dismissed an upgrade prompt. */
export function recordDismissal(promptType: string): void {
  safeSet(
    "PG_INTENT_DISMISSAL",
    JSON.stringify({
      last_dismissed_at: new Date().toISOString(),
      last_prompt_type: promptType,
    })
  )
}
