/**
 * In-season break messaging for when a league has no games (All-Star, Winter Games, etc.).
 * Update dates here when breaks change; used in dashboard Games tab empty state.
 */

export type SportBreakInfo = {
  /** Short label for the break (e.g. "All-Star break") */
  breakLabel: string
  /** When regular games resume (e.g. "Feb 19") */
  nextGamesDate: string
}

const BREAKS: Partial<Record<string, SportBreakInfo>> = {
  nba: {
    breakLabel: "All-Star break",
    nextGamesDate: "Feb 19",
  },
  nhl: {
    breakLabel: "winter break",
    nextGamesDate: "Feb 25",
  },
}

export function getSportBreakInfo(sportSlug: string): SportBreakInfo | null {
  const slug = (sportSlug || "").toLowerCase().trim()
  return BREAKS[slug] ?? null
}
