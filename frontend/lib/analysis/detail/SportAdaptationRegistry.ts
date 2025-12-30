export type MarketType = "h2h" | "spreads" | "totals"

export type SportAdaptation = {
  sportSlug: string
  sportIcon: string
  betTabs: Array<{ marketType: MarketType; label: string }>
  units: {
    offense: string
    defense: string
  }
}

const DEFAULT: SportAdaptation = {
  sportSlug: "unknown",
  sportIcon: "🏟️",
  betTabs: [
    { marketType: "h2h", label: "Moneyline" },
    { marketType: "spreads", label: "Spread" },
    { marketType: "totals", label: "Total" },
  ],
  units: { offense: "Offense", defense: "Defense" },
}

export class SportAdaptationRegistry {
  static resolve(sportIdentifier: string): SportAdaptation {
    const slug = String(sportIdentifier || "").toLowerCase().trim()

    // Soccer leagues share the same adaptation.
    if (["mls", "epl", "laliga", "ucl", "soccer"].includes(slug)) {
      return {
        sportSlug: slug,
        sportIcon: "⚽",
        betTabs: [
          { marketType: "h2h", label: "Moneyline" },
          { marketType: "spreads", label: "Spread" },
          { marketType: "totals", label: "Total" },
        ],
        units: { offense: "Attack", defense: "Defense" },
      }
    }

    if (slug === "nhl") {
      return {
        sportSlug: "nhl",
        sportIcon: "🏒",
        betTabs: [
          { marketType: "h2h", label: "Moneyline" },
          { marketType: "spreads", label: "Puck Line" },
          { marketType: "totals", label: "Total" },
        ],
        units: { offense: "Offense", defense: "Defense" },
      }
    }

    if (slug === "mlb") {
      return {
        sportSlug: "mlb",
        sportIcon: "⚾",
        betTabs: [
          { marketType: "h2h", label: "Moneyline" },
          { marketType: "spreads", label: "Run Line" },
          { marketType: "totals", label: "Total" },
        ],
        units: { offense: "Batting", defense: "Pitching" },
      }
    }

    if (slug === "nba" || slug === "ncaab") {
      return {
        sportSlug: slug,
        sportIcon: "🏀",
        betTabs: DEFAULT.betTabs,
        units: DEFAULT.units,
      }
    }

    if (slug === "nfl" || slug === "ncaaf") {
      return {
        sportSlug: slug,
        sportIcon: "🏈",
        betTabs: DEFAULT.betTabs,
        units: DEFAULT.units,
      }
    }

    if (slug === "ufc" || slug === "boxing") {
      return {
        sportSlug: slug,
        sportIcon: "🥊",
        betTabs: [{ marketType: "h2h", label: "Moneyline" }],
        units: { offense: "Striking", defense: "Defense" },
      }
    }

    return { ...DEFAULT, sportSlug: slug || DEFAULT.sportSlug }
  }
}


