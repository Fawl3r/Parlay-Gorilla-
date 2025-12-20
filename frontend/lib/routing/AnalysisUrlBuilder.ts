import { calculateNflWeek } from "@/lib/routing/NflWeekCalculator"

function cleanTeam(name: string): string {
  return String(name || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

/**
 * Build analysis URL slug for a game
 * Matches backend slug format:
 * - NFL: {sport}/{away}-vs-{home}-week-{week}-{year}
 * - Other: {sport}/{away}-vs-{home}-{date}
 */
export function buildAnalysisUrl(
  sport: string,
  awayTeam: string,
  homeTeam: string,
  startTime: string,
  week?: number | null
): string {
  const sportLower = String(sport || "").toLowerCase().trim()

  const awayClean = cleanTeam(awayTeam)
  const homeClean = cleanTeam(homeTeam)

  const gameDate = new Date(startTime)
  const yearUtc = Number.isFinite(gameDate.getTime()) ? gameDate.getUTCFullYear() : new Date().getUTCFullYear()

  // NFL must match backend canonical slug format (week-based).
  if (sportLower === "nfl") {
    const providedWeek = typeof week === "number" && Number.isFinite(week) ? week : null
    const computedWeek = providedWeek ?? calculateNflWeek(gameDate)
    const weekToken = computedWeek ?? "None" // matches backend `None` string in worst-case

    return `/analysis/nfl/${awayClean}-vs-${homeClean}-week-${weekToken}-${yearUtc}`
  }

  const dateStr = Number.isFinite(gameDate.getTime())
    ? gameDate.toISOString().slice(0, 10) // YYYY-MM-DD (UTC)
    : new Date().toISOString().slice(0, 10)

  return `/analysis/${sportLower}/${awayClean}-vs-${homeClean}-${dateStr}`
}


