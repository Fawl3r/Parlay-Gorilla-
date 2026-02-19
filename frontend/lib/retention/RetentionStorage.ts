"use client"

/**
 * Retention Engine — client-only localStorage. No backend, no API.
 * Keys prefixed to avoid collisions.
 */

const PREFIX = "PG_RETENTION_"
const VIEWED_SLUGS_KEY = `${PREFIX}viewed_slugs`
const VIEWED_AT_KEY = `${PREFIX}viewed_at`
const PROGRESSION_KEY = `${PREFIX}progression`
const STREAK_KEY = `${PREFIX}streak`
const LAST_VISIT_DATE_KEY = `${PREFIX}last_visit_date`
const MARKET_SNAPSHOT_KEY = `${PREFIX}market_snapshot`
const LAST_RESEARCH_AS_OF_KEY = `${PREFIX}last_research_as_of`
const MAX_VIEWED_SLUGS = 200
const MAX_MARKET_ENTRIES = 30

export interface ProgressionState {
  analysesViewedCount: number
  sportsExplored: string[]
  visitsThisWeek: number
  level: 1 | 2 | 3
  label: string
}

export interface MarketSnapshotEntry {
  slug: string
  matchup: string
  confidence: number
  edgeLabel?: string
  sport?: string
  viewedAt: string
}

export interface StreakState {
  currentStreak: number
  lastVisitDate: string
}

function todayDateString(): string {
  return new Date().toISOString().slice(0, 10)
}

function getWeekStartString(): string {
  const d = new Date()
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  const monday = new Date(d.getFullYear(), d.getMonth(), diff)
  return monday.toISOString().slice(0, 10)
}

function safeJsonParse<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function safeJsonSet(key: string, value: unknown): void {
  if (typeof window === "undefined") return
  try {
    localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // quota or disabled
  }
}

/** Record that user viewed an analysis (call from analysis detail page). */
export function recordAnalysisView(params: {
  slug: string
  sport?: string
  confidence?: number
  matchup?: string
  edgeLabel?: string
}): void {
  const { slug, sport, confidence, matchup, edgeLabel } = params
  const viewed = safeJsonParse<string[]>(VIEWED_SLUGS_KEY, [])
  const atMap = safeJsonParse<Record<string, string>>(VIEWED_AT_KEY, {})
  if (!viewed.includes(slug)) {
    viewed.unshift(slug)
    if (viewed.length > MAX_VIEWED_SLUGS) viewed.pop()
    safeJsonSet(VIEWED_SLUGS_KEY, viewed)
  }
  atMap[slug] = new Date().toISOString()
  safeJsonSet(VIEWED_AT_KEY, atMap)

  const prog = safeJsonParse<{ count: number; sports: string[]; weekStart: string; weekVisits: number }>(
    PROGRESSION_KEY,
    { count: 0, sports: [], weekStart: "", weekVisits: 0 }
  )
  prog.count = (prog.count || 0) + 1
  const weekStart = getWeekStartString()
  if (prog.weekStart !== weekStart) {
    prog.weekStart = weekStart
    prog.weekVisits = 1
  } else {
    prog.weekVisits = (prog.weekVisits || 0) + 1
  }
  if (sport && !prog.sports.includes(sport)) {
    prog.sports = [...prog.sports, sport].slice(-20)
  }
  safeJsonSet(PROGRESSION_KEY, prog)

  if (confidence != null && matchup) {
    const entries = safeJsonParse<MarketSnapshotEntry[]>(MARKET_SNAPSHOT_KEY, [])
    const existing = entries.findIndex((e) => e.slug === slug)
    const entry: MarketSnapshotEntry = {
      slug,
      matchup,
      confidence,
      edgeLabel,
      sport,
      viewedAt: new Date().toISOString(),
    }
    if (existing >= 0) entries.splice(existing, 1)
    entries.unshift(entry)
    if (entries.length > MAX_MARKET_ENTRIES) entries.pop()
    safeJsonSet(MARKET_SNAPSHOT_KEY, entries)
  }
}

/** Record a session visit (call on landing/dashboard/analysis load). */
export function recordVisit(): void {
  if (typeof window === "undefined") return
  const today = todayDateString()
  const last = localStorage.getItem(LAST_VISIT_DATE_KEY)
  let streak = safeJsonParse<StreakState>(STREAK_KEY, { currentStreak: 0, lastVisitDate: "" })

  if (last === today) {
    // already recorded today
    return
  }

  if (!last) {
    streak = { currentStreak: 1, lastVisitDate: today }
  } else {
    const lastDate = new Date(last)
    const todayDate = new Date(today)
    const diffDays = Math.round((todayDate.getTime() - lastDate.getTime()) / 86400000)
    if (diffDays === 1) {
      streak = { currentStreak: streak.currentStreak + 1, lastVisitDate: today }
    } else if (diffDays > 1) {
      streak = { currentStreak: 1, lastVisitDate: today }
    }
  }
  safeJsonSet(STREAK_KEY, streak)
  safeJsonSet(LAST_VISIT_DATE_KEY, today)
}

/** Cache last research as_of when user sees analysis with enrichment. */
export function setLastResearchAsOf(iso: string): void {
  safeJsonSet(LAST_RESEARCH_AS_OF_KEY, iso)
}

export function getLastResearchAsOf(): string | null {
  const raw = typeof window !== "undefined" ? localStorage.getItem(LAST_RESEARCH_AS_OF_KEY) : null
  return raw || null
}

/** Whether user has viewed this analysis slug before. */
export function hasViewedSlug(slug: string): boolean {
  const viewed = safeJsonParse<string[]>(VIEWED_SLUGS_KEY, [])
  return viewed.includes(slug)
}

/** Get progression for display (level 1–3, label). */
export function getProgression(): ProgressionState {
  const prog = safeJsonParse<{ count: number; sports: string[]; weekStart: string; weekVisits: number }>(
    PROGRESSION_KEY,
    { count: 0, sports: [], weekStart: "", weekVisits: 0 }
  )
  const count = prog.count || 0
  const sports = prog.sports || []
  const visitsThisWeek = prog.weekStart === getWeekStartString() ? prog.weekVisits || 0 : 0

  let level: 1 | 2 | 3 = 1
  let label = "Explorer"
  if (count >= 20 || sports.length >= 3 || visitsThisWeek >= 5) {
    level = 3
    label = "Advanced Analyst"
  } else if (count >= 5 || sports.length >= 2 || visitsThisWeek >= 2) {
    level = 2
    label = "Analyst"
  }

  return {
    analysesViewedCount: count,
    sportsExplored: sports,
    visitsThisWeek,
    level,
    label,
  }
}

export function getStreak(): StreakState {
  return safeJsonParse<StreakState>(STREAK_KEY, { currentStreak: 0, lastVisitDate: "" })
}

export function getMarketSnapshotEntries(): MarketSnapshotEntry[] {
  return safeJsonParse<MarketSnapshotEntry[]>(MARKET_SNAPSHOT_KEY, [])
}

/** Deterministic index from date + list length for "today's featured" rotation. */
export function getFeaturedIndex(listLength: number, dateStr?: string): number {
  if (listLength <= 0) return 0
  const day = dateStr || todayDateString()
  let hash = 0
  for (let i = 0; i < day.length; i++) {
    hash = (hash << 5) - hash + day.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash) % listLength
}
