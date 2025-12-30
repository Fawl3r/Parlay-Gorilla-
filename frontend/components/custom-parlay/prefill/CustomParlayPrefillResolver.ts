"use client"

import type { GameResponse } from "@/lib/api"
import type { SelectedPick } from "@/components/custom-parlay/types"

export type CustomParlayPrefillRequest = {
  sport?: string
  gameId?: string
  marketType?: "h2h" | "spreads" | "totals"
  pick?: string
  point?: number
}

function normalize(s: string): string {
  return String(s || "").trim().toLowerCase()
}

function parseFirstNumber(text: string): number | undefined {
  const match = String(text || "").match(/[+-]?\d+(?:\.\d+)?/)
  if (!match) return undefined
  const n = Number(match[0])
  return Number.isFinite(n) ? n : undefined
}

function approxEq(a: number | undefined, b: number | undefined): boolean {
  if (a === undefined || b === undefined) return false
  return Math.abs(a - b) < 0.001
}

export class CustomParlayPrefillResolver {
  static resolve(game: GameResponse, req: CustomParlayPrefillRequest): SelectedPick | null {
    const gameId = String(req.gameId || "").trim()
    const marketType = (req.marketType || "").trim() as CustomParlayPrefillRequest["marketType"]
    const pick = String(req.pick || "").trim()
    if (!gameId || !marketType || !pick) return null
    if (String(game.id || "") !== gameId) return null

    const market = game.markets.find((m) => m.market_type === marketType)
    if (!market || !Array.isArray(market.odds) || market.odds.length === 0) return null

    const home = String(game.home_team || "")
    const away = String(game.away_team || "")
    const pickLower = normalize(pick)

    const findOdds = () => {
      if (marketType === "h2h") {
        const targetIsHome = normalize(home) === pickLower
        return (
          market.odds.find((o) => {
            const out = normalize(o.outcome)
            return targetIsHome ? out.includes("home") || out.includes(normalize(home)) : out.includes("away") || out.includes(normalize(away))
          }) ?? market.odds[0]
        )
      }

      if (marketType === "totals") {
        const wantOver = pickLower.includes("over")
        const wantUnder = pickLower.includes("under")
        const wantPoint = req.point ?? parseFirstNumber(pick)
        return (
          market.odds.find((o) => {
            const out = normalize(o.outcome)
            if (wantOver && !out.includes("over")) return false
            if (wantUnder && !out.includes("under")) return false
            const p = parseFirstNumber(o.outcome)
            if (wantPoint !== undefined && p !== undefined && !approxEq(p, wantPoint)) return false
            return true
          }) ?? market.odds[0]
        )
      }

      // spreads
      const wantHome = pickLower === "home" || pickLower.includes(normalize(home))
      const wantAway = pickLower === "away" || pickLower.includes(normalize(away))
      const wantPoint = req.point ?? parseFirstNumber(pick)

      return (
        market.odds.find((o) => {
          const out = normalize(o.outcome)
          if (wantHome && !(out.includes("home") || out.includes(normalize(home)))) return false
          if (wantAway && !(out.includes("away") || out.includes(normalize(away)))) return false
          const p = parseFirstNumber(o.outcome)
          if (wantPoint !== undefined && p !== undefined && !approxEq(p, wantPoint)) return false
          return true
        }) ?? market.odds[0]
      )
    }

    const odd = findOdds()
    if (!odd) return null

    const pointFromOdds = parseFirstNumber(odd.outcome)
    const point = req.point ?? pointFromOdds

    const pickDisplay = (() => {
      if (marketType === "h2h") return `${pick} ML`
      if (marketType === "totals") return `${pickLower.toUpperCase()} ${point ?? ""}`.trim()

      // spreads
      const sideName = pickLower === "home" ? home : pickLower === "away" ? away : pick
      const p = point ?? 0
      const signed = p > 0 ? `+${p}` : String(p)
      return `${sideName} ${signed}`.trim()
    })()

    return {
      game_id: String(game.id),
      market_type: marketType,
      pick,
      odds: odd.price,
      point,
      market_id: market.id,
      gameDisplay: `${away} @ ${home}`,
      pickDisplay,
      homeTeam: home,
      awayTeam: away,
      sport: game.sport,
      oddsDisplay: odd.price,
    }
  }
}


