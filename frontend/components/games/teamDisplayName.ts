/**
 * Placeholder team names (conferences, TBD) that should get a friendlier display label.
 * Backend filters these from the games list; this is defensive for any that slip through.
 */
const PLACEHOLDER_DISPLAY: Record<string, string> = {
  AFC: "AFC All-Stars",
  NFC: "NFC All-Stars",
  TBD: "TBD",
  TBA: "TBA",
  TBC: "TBC",
}

/**
 * Returns the display name for a team. For NFL placeholder names (e.g. AFC, NFC),
 * returns a user-friendly label (e.g. "AFC All-Stars", "NFC All-Stars").
 */
export function getTeamDisplayName(teamName: string, sport: string): string {
  if (!teamName || typeof teamName !== "string") return teamName || ""
  const key = teamName.trim().toUpperCase()
  if (sport?.toLowerCase() === "nfl" && key in PLACEHOLDER_DISPLAY) {
    return PLACEHOLDER_DISPLAY[key as keyof typeof PLACEHOLDER_DISPLAY]
  }
  return teamName
}
