// Keep in sync with `backend/app/utils/nfl_week.py`
const SEASON_STARTS: Record<number, { month: number; day: number }> = {
  2024: { month: 9, day: 5 },
  2025: { month: 9, day: 4 },
  2026: { month: 9, day: 10 },
}

/**
 * Calculate NFL week number from a game date.
 *
 * Matches backend behavior (including the current seasonYear heuristic):
 * - `seasonYear` defaults to the UTC year of the game date.
 * - Week 1 starts on seasonStart.
 * - Returns `null` when before season start or after week 18.
 */
export function calculateNflWeek(gameTime: Date): number | null {
  if (!(gameTime instanceof Date) || Number.isNaN(gameTime.getTime())) return null

  // Backend treats the input as a date (no timezone conversions).
  // We base calculations on the UTC calendar day to avoid client-local shifts.
  const gameDateUtc = toUtcDateOnly(gameTime)
  const seasonYear = gameDateUtc.getUTCFullYear()
  const seasonStartUtc = getSeasonStartUtc(seasonYear)

  if (gameDateUtc.getTime() < seasonStartUtc.getTime()) return null

  const daysSinceStart = Math.floor(
    (gameDateUtc.getTime() - seasonStartUtc.getTime()) / (24 * 60 * 60 * 1000)
  )
  const week = Math.floor(daysSinceStart / 7) + 1

  if (week > 18) return null
  return week
}

function toUtcDateOnly(d: Date): Date {
  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
}

function getSeasonStartUtc(seasonYear: number): Date {
  const known = SEASON_STARTS[seasonYear]
  if (known) {
    return new Date(Date.UTC(seasonYear, known.month - 1, known.day))
  }

  // Fallback: first Thursday of September (matches backend's heuristic)
  const sept1 = new Date(Date.UTC(seasonYear, 8, 1))
  const pyWeekday = toPythonWeekday(sept1.getUTCDay()) // 0=Mon, 3=Thu
  const daysUntilThursday = ((3 - pyWeekday) % 7 + 7) % 7
  const dayOfMonth = 1 + daysUntilThursday

  return new Date(Date.UTC(seasonYear, 8, dayOfMonth))
}

// JS: 0=Sun..6=Sat -> Python: 0=Mon..6=Sun
function toPythonWeekday(jsWeekday: number): number {
  return (jsWeekday + 6) % 7
}


