export type SportSlug =
  | "nfl"
  | "nba"
  | "wnba"
  | "nhl"
  | "mlb"
  | "ncaaf"
  | "ncaab"
  | "epl"
  | "mls"
  | "soccer_epl"
  | "soccer_usa_mls"

// Sport display names (kept intentionally small + user-facing).
export const SPORT_NAMES: Record<string, string> = {
  nfl: "NFL",
  nba: "NBA",
  wnba: "WNBA",
  nhl: "NHL",
  mlb: "MLB",
  ncaaf: "College Football",
  ncaab: "College Basketball",
  // Soccer (preferred slugs from backend sports config)
  epl: "Premier League",
  mls: "MLS",
  // Backward-compatible aliases
  soccer_epl: "Premier League",
  soccer_usa_mls: "MLS",
}

// Sport tab icons (emoji) for selectors; backend owns list, this is display-only.
export const SPORT_ICONS: Record<string, string> = {
  nfl: "🏈",
  nba: "🏀",
  wnba: "🏀",
  nhl: "🏒",
  mlb: "⚾",
  ncaaf: "🏈",
  ncaab: "🏀",
  epl: "⚽",
  mls: "⚽",
  soccer_epl: "⚽",
  soccer_usa_mls: "⚽",
}

// Sport-specific background images.
// Note: These are just decorative; we keep overall UI in the landing-page neon palette.
export const SPORT_BACKGROUNDS: Record<string, string> = {
  nfl: "/images/nflll.png",
  nba: "/images/basketbal.png",
  wnba: "/images/basketbal.png",
  nhl: "/images/hockey1.png",
  mlb: "/images/MLB.png",
  ncaaf: "/images/nflll.png",
  ncaab: "/images/basketbal.png",
  // Soccer (preferred slugs)
  epl: "/images/soccer1.png",
  mls: "/images/soccer1.png",
  // Backward-compatible aliases
  soccer_epl: "/images/soccer1.png",
  soccer_usa_mls: "/images/soccer1.png",
}


