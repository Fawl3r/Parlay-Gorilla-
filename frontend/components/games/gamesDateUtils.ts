export function formatDateString(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

export function formatDisplayDate(dateStr: string): string {
  if (dateStr === "today") return "Today"
  if (dateStr === "tomorrow") {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })
  }

  const [year, month, day] = dateStr.split("-").map(Number)
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })
}

export function getTargetDate(dateStr: string): Date {
  if (dateStr === "today") return new Date()
  if (dateStr === "tomorrow") {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow
  }
  const [year, month, day] = dateStr.split("-").map(Number)
  return new Date(year, month - 1, day)
}

export function addDays(base: Date, deltaDays: number): Date {
  const d = new Date(base)
  d.setDate(d.getDate() + deltaDays)
  return d
}

/**
 * Returns the calendar date (YYYY-MM-DD) for a given date in the user's local timezone.
 * Use this to compare game start_time to a selected date so games show on the correct day.
 */
export function getLocalDateString(date: Date): string {
  return formatDateString(date)
}

/**
 * True if the game's start_time (ISO string) falls on the selected calendar day (local).
 * Use for consistent date filtering; "today" resolves to current local date.
 */
export function isGameOnDate(gameStartTimeIso: string, selectedDateStr: string): boolean {
  const target = getTargetDate(selectedDateStr)
  const targetYmd = formatDateString(target)
  const gameDate = new Date(gameStartTimeIso)
  const gameYmd = getLocalDateString(gameDate)
  return gameYmd === targetYmd
}




