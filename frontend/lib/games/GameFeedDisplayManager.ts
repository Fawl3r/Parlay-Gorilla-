/**
 * Centralizes game feed display logic: status mapping, chip labels, and time/meta formatters.
 * No backend or API changes; works with existing GameFeedResponse (sport only).
 */

export type WindowType = "live" | "final" | "upcoming"

/** Statuses that mean the game is finished. */
export const FINAL_STATUSES: ReadonlySet<string> = new Set([
  "FT",
  "AET",
  "PEN",
  "COMPLETED",
  "FINAL",
  "FINAL/OT",
  "FINAL OT",
  "POSTPONED",
  "CANCELED",
  "CANCELLED",
])

/** Statuses that mean the game is in progress. */
export const LIVE_STATUSES: ReadonlySet<string> = new Set([
  "LIVE",
  "IN PROGRESS",
  "IN_PROGRESS",
  "Q1",
  "Q2",
  "Q3",
  "Q4",
  "1H",
  "2H",
  "HT",
  "OT",
  "SO",
  "P",
])

const SIX_HOURS_MS = 6 * 60 * 60 * 1000

/** League/code -> category label (sport chip). */
const LEAGUE_TO_CATEGORY: Record<string, string> = {
  NFL: "Football",
  NCAAF: "Football",
  CFB: "Football",
  NBA: "Basketball",
  NCAAB: "Basketball",
  CBB: "Basketball",
  MLB: "Baseball",
  NHL: "Hockey",
  EPL: "Soccer",
  MLS: "Soccer",
  UCL: "Soccer",
  UEL: "Soccer",
  SERIE_A: "Soccer",
  LA_LIGA: "Soccer",
  BUNDESLIGA: "Soccer",
  LIGUE_1: "Soccer",
  FIFA: "Soccer",
  FIFA_WC: "Soccer",
  FIFA_U20: "Soccer",
  FIFA_U17: "Soccer",
  FIFA_W: "Soccer",
  FIFA_U20_W: "Soccer",
  FIFA_U17_W: "Soccer",
  FIFA_WWC: "Soccer",
  FIFA_U20_WWC: "Soccer",
  FIFA_U17_WWC: "Soccer",
}

/**
 * Normalize raw status string for comparison (uppercase, trimmed).
 */
export function normalizeStatus(raw: string): string {
  return (raw || "").trim().toUpperCase().replace(/\s+/g, " ")
}

/**
 * Get display window type from raw status.
 */
export function getWindowType(rawStatus: string): WindowType {
  const status = normalizeStatus(rawStatus)
  if (FINAL_STATUSES.has(status)) return "final"
  if (LIVE_STATUSES.has(status)) return "live"
  return "upcoming"
}

/**
 * Sport chip = category (Football, Basketball, etc.).
 */
export function getCategoryLabel(sportOrLeague: string): string {
  const key = (sportOrLeague || "").trim().toUpperCase().replace(/\s+/g, "_")
  return LEAGUE_TO_CATEGORY[key] ?? "Other"
}

/**
 * League chip = league code (NFL, NBA, EPL, etc.).
 */
export function getLeagueLabel(sportOrLeague: string): string {
  const s = (sportOrLeague || "").trim()
  if (!s) return "—"
  return s.toUpperCase()
}

/**
 * Format "Starts in Xh Ym" from milliseconds until start.
 */
export function formatStartsIn(ms: number): string {
  if (ms <= 0) return "Starting"
  const totalMinutes = Math.floor(ms / 60_000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours > 0 && minutes > 0) return `Starts in ${hours}h ${minutes}m`
  if (hours > 0) return `Starts in ${hours}h`
  if (minutes > 0) return `Starts in ${minutes}m`
  return "Starting"
}

/**
 * Format local time (e.g. "7:15 PM").
 */
export function formatLocalTime(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  })
}

/**
 * Within 6h: "Starts in Xh Ym". Else: local time (e.g. "7:15 PM").
 */
export function formatUpcomingMeta(startTimeIso: string, now: Date): string {
  const start = new Date(startTimeIso)
  const ms = start.getTime() - now.getTime()
  if (ms <= SIX_HOURS_MS && ms > 0) return formatStartsIn(ms)
  return formatLocalTime(start)
}

/**
 * Header helper: "Updated Xs ago" / "Updated Xm ago".
 */
export function formatUpdatedAgo(lastUpdatedAt: Date | number, now: Date): string {
  const then = typeof lastUpdatedAt === "number" ? new Date(lastUpdatedAt) : lastUpdatedAt
  const sec = Math.floor((now.getTime() - then.getTime()) / 1000)
  if (sec < 60) return `Updated ${sec}s ago`
  const min = Math.floor(sec / 60)
  return `Updated ${min}m ago`
}
