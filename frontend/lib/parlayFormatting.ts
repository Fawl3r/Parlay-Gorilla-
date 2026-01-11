import { LegResponse } from "@/lib/api"

export const getMarketLabel = (marketType: string): string => {
  switch (marketType) {
    case "h2h":
      return "Moneyline"
    case "spreads":
      return "Spread"
    case "totals":
      return "Total"
    default:
      return marketType.toUpperCase()
  }
}

export const getConfidenceTextClass = (score: number) => {
  if (score >= 70) return "text-emerald-300"
  if (score >= 50) return "text-amber-300"
  return "text-rose-400"
}

export const getConfidenceBgClass = (color: string) => {
  switch (color) {
    case "green":
      return "bg-green-500"
    case "yellow":
      return "bg-yellow-500"
    case "red":
      return "bg-red-500"
    default:
      return "bg-gray-500"
  }
}

export const getPickLabel = (leg: LegResponse): string => {
  let homeTeam = leg.home_team
  let awayTeam = leg.away_team

  if ((!homeTeam || !awayTeam) && leg.game?.includes("@")) {
    const [away, home] = leg.game.split("@").map((s) => s.trim())
    awayTeam = away || awayTeam
    homeTeam = home || homeTeam
  }

  if (leg.market_type === "h2h") {
    const outcomeLower = leg.outcome.toLowerCase()
    if (outcomeLower === "home" && homeTeam) return homeTeam
    if (outcomeLower === "away" && awayTeam) return awayTeam
    return leg.outcome
  }

  if (leg.market_type === "spreads") {
    if (/[+-]?\d+\.?\d*/.test(leg.outcome)) {
      return leg.outcome
    }
    const outcomeLower = leg.outcome.toLowerCase()
    const number = leg.outcome.replace(/[^0-9.+-]/g, "")
    if (outcomeLower.includes("home") && homeTeam) {
      return `${homeTeam} ${number}`
    }
    if (outcomeLower.includes("away") && awayTeam) {
      return `${awayTeam} ${number}`
    }
    return leg.outcome
  }

  if (leg.market_type === "totals") {
    const outcomeLower = leg.outcome.toLowerCase()
    if (outcomeLower.startsWith("over") || outcomeLower.startsWith("under")) {
      return `${outcomeLower.charAt(0).toUpperCase()}${outcomeLower.slice(1)}`
    }
    return `Over ${leg.outcome}`
  }

  return leg.outcome
}

