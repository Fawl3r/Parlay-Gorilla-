/**
 * QuickStart template engine: build slip from template + games.
 * One pick per game; only valid markets/odds; no same-game stacking.
 */

import type { GameResponse, MarketResponse, OddsResponse } from "@/lib/api"
import type { SelectedPick } from "@/components/custom-parlay/types"

export type TemplateId = "safer_2" | "solid_3" | "longshot_4"

const TEMPLATE_REQUIRED: Record<TemplateId, number> = {
  safer_2: 2,
  solid_3: 3,
  longshot_4: 4,
}

export function getRequiredCount(templateId: TemplateId): number {
  return TEMPLATE_REQUIRED[templateId]
}

function getMarket(game: GameResponse, type: "h2h" | "spreads" | "totals"): MarketResponse | null {
  const m = game.markets?.find((x) => x.market_type === type)
  return m && Array.isArray(m.odds) && m.odds.length > 0 ? m : null
}

function hasValidOdds(market: MarketResponse): boolean {
  return Array.isArray(market.odds) && market.odds.length > 0 && market.odds.some((o) => o.price != null && o.price !== "")
}

function toSelectedPick(
  game: GameResponse,
  marketType: "h2h" | "spreads" | "totals",
  pick: string,
  odds: string,
  point: number | undefined,
  marketId: string,
  pickDisplay: string
): SelectedPick {
  return {
    game_id: game.id,
    market_type: marketType,
    pick,
    odds,
    point,
    market_id: marketId,
    gameDisplay: `${game.away_team} @ ${game.home_team}`,
    pickDisplay,
    homeTeam: game.home_team,
    awayTeam: game.away_team,
    sport: game.sport,
    oddsDisplay: odds,
  }
}

function parsePointFromOutcome(outcome: string): number | undefined {
  const m = String(outcome).match(/[+-]?\d+(?:\.\d+)?/)
  if (!m) return undefined
  const n = Number(m[0])
  return Number.isFinite(n) ? n : undefined
}

function chooseMoneylinePick(game: GameResponse, market: MarketResponse, preferUnderdog: boolean): SelectedPick | null {
  const home = game.home_team
  const away = game.away_team
  const oddsList = market.odds
  if (!oddsList.length) return null
  const o1 = oddsList[0]
  const o2 = oddsList[1]
  const isFirstHome =
    o1.outcome.toLowerCase().includes("home") ||
    o1.outcome.toLowerCase().includes(home.toLowerCase())
  const homeOdds = isFirstHome ? o1 : o2
  const awayOdds = isFirstHome ? o2 : o1
  const homeDecimal = homeOdds.decimal_price ?? 0
  const awayDecimal = awayOdds.decimal_price ?? 0
  const homeIsDog = homeDecimal >= awayDecimal
  const pickDog = preferUnderdog ? homeIsDog : !homeIsDog
  const team = pickDog ? (homeIsDog ? home : away) : homeIsDog ? away : home
  const odd = pickDog ? (homeIsDog ? homeOdds : awayOdds) : homeIsDog ? awayOdds : homeOdds
  return toSelectedPick(game, "h2h", team, odd.price, undefined, market.id, `${team} ML`)
}

function chooseSpreadPick(game: GameResponse, market: MarketResponse, maxAbsPoint: number = 7): SelectedPick | null {
  const home = game.home_team
  const away = game.away_team
  const oddsList = market.odds
  if (!oddsList.length) return null
  const o1 = oddsList[0]
  const o2 = oddsList[1]
  const isFirstHome =
    o1.outcome.toLowerCase().includes("home") || o1.outcome.toLowerCase().includes(home.toLowerCase())
  const homeOdds = isFirstHome ? o1 : o2
  const awayOdds = isFirstHome ? o2 : o1
  const homePoint = parsePointFromOutcome(homeOdds.outcome) ?? 0
  const awayPoint = parsePointFromOutcome(awayOdds.outcome) ?? 0
  if (Math.abs(homePoint) > maxAbsPoint && Math.abs(awayPoint) > maxAbsPoint) return null
  const useHome = Math.abs(homePoint) <= maxAbsPoint
  const team = useHome ? home : away
  const point = useHome ? homePoint : awayPoint
  const odd = useHome ? homeOdds : awayOdds
  const signed = point > 0 ? `+${point}` : String(point)
  return toSelectedPick(game, "spreads", useHome ? "home" : "away", odd.price, point, market.id, `${team} ${signed}`)
}

function chooseTotalsPick(game: GameResponse, market: MarketResponse): SelectedPick | null {
  const oddsList = market.odds
  if (!oddsList.length) return null
  const o1 = oddsList[0]
  const o2 = oddsList[1]
  const isOver1 = o1.outcome.toLowerCase().includes("over")
  const overOdds = isOver1 ? o1 : o2
  const underOdds = isOver1 ? o2 : o1
  const point = parsePointFromOutcome(overOdds.outcome) ?? parsePointFromOutcome(underOdds.outcome)
  const pick = "over"
  const odd = overOdds
  return toSelectedPick(game, "totals", pick, odd.price, point, market.id, `OVER ${point ?? ""}`.trim())
}

function gamesWithValidMarkets(games: GameResponse[]): GameResponse[] {
  return games.filter((g) => {
    if (!g.markets?.length) return false
    return g.markets.some((m) => (m.market_type === "h2h" || m.market_type === "spreads" || m.market_type === "totals") && hasValidOdds(m))
  })
}

export interface BuildTemplateSlipOpts {
  maxPicks: number
  selectedSport: string
}

/**
 * Build slip for template. Never more than one pick per game.
 * Returns up to required picks; may return fewer if slate is thin.
 */
export function buildTemplateSlip(
  templateId: TemplateId,
  games: GameResponse[],
  opts: BuildTemplateSlipOpts
): SelectedPick[] {
  const required = TEMPLATE_REQUIRED[templateId]
  const maxPicks = Math.min(opts.maxPicks, required)
  const eligible = gamesWithValidMarkets(games)
  const picks: SelectedPick[] = []
  const usedGameIds = new Set<string>()

  for (const game of eligible) {
    if (picks.length >= maxPicks) break
    if (usedGameIds.has(game.id)) continue

    let pick: SelectedPick | null = null

    if (templateId === "safer_2") {
      const ml = getMarket(game, "h2h")
      if (ml) pick = chooseMoneylinePick(game, ml, false)
      if (!pick) {
        const spread = getMarket(game, "spreads")
        if (spread) pick = chooseSpreadPick(game, spread, 4)
      }
    } else if (templateId === "solid_3") {
      const ml = getMarket(game, "h2h")
      if (ml) pick = chooseMoneylinePick(game, ml, false)
      if (!pick) {
        const spread = getMarket(game, "spreads")
        if (spread) pick = chooseSpreadPick(game, spread, 7)
      }
      if (!pick) {
        const tot = getMarket(game, "totals")
        if (tot) pick = chooseTotalsPick(game, tot)
      }
    } else {
      const ml = getMarket(game, "h2h")
      if (ml) pick = chooseMoneylinePick(game, ml, true)
      if (!pick) {
        const spread = getMarket(game, "spreads")
        if (spread) pick = chooseSpreadPick(game, spread, 10)
      }
      if (!pick) {
        const tot = getMarket(game, "totals")
        if (tot) pick = chooseTotalsPick(game, tot)
      }
    }

    if (pick) {
      picks.push(pick)
      usedGameIds.add(game.id)
    }
  }

  return picks
}
