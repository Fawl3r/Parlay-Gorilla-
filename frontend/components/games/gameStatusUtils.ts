/**
 * Single source of truth for mapping provider statuses into normalized buckets.
 * Used for DraftKings-style Upcoming / Live / Final tabs and status pills.
 */

export type NormalizedGameStatus = "UPCOMING" | "LIVE" | "FINAL"

const UPCOMING_RAW = ["scheduled", "pre", "not_started", "not started"]
const LIVE_RAW = ["inprogress", "live", "in_progress", "halftime", "in progress"]
const FINAL_RAW = ["final", "completed", "finished", "closed", "complete", "post"]

/**
 * Normalize provider status (and optional start time) into UPCOMING | LIVE | FINAL.
 * Fallback: start_time > now => UPCOMING, else LIVE (conservative for unknown).
 */
export function normalizeGameStatus(
  rawStatus: string,
  startTimeIso: string,
  now: Date = new Date()
): NormalizedGameStatus {
  const raw = (rawStatus ?? "").trim().toLowerCase().replace(/\s+/g, " ")
  if (UPCOMING_RAW.some((s) => raw === s || raw.includes(s))) return "UPCOMING"
  if (LIVE_RAW.some((s) => raw === s || raw.includes(s))) return "LIVE"
  if (FINAL_RAW.some((s) => raw === s || raw.includes(s))) return "FINAL"
  const start = new Date(startTimeIso).getTime()
  if (!Number.isFinite(start)) return "LIVE"
  if (start > now.getTime()) return "UPCOMING"
  return "LIVE"
}

/**
 * Display label for status pill (Scheduled | Live | Final).
 */
export function getDisplayStatusPill(normalized: NormalizedGameStatus): string {
  switch (normalized) {
    case "UPCOMING":
      return "Scheduled"
    case "LIVE":
      return "Live"
    case "FINAL":
      return "Final"
    default:
      return "Scheduled"
  }
}
