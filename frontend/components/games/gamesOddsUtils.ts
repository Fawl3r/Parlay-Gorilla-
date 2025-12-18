import type { GameResponse } from "@/lib/api"

function parseAmericanOdds(price: string): number | null {
  const p = String(price || "").trim()
  if (!p) return null
  const n = Number(p.replace("+", ""))
  return Number.isFinite(n) ? n : null
}

function impliedProbabilityFromAmerican(price: string): number | null {
  const american = parseAmericanOdds(price)
  if (american === null) return null
  if (american === 0) return null
  if (american < 0) {
    const odds = Math.abs(american)
    return odds / (odds + 100)
  }
  return 100 / (american + 100)
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value
  if (typeof value === "string") {
    const n = Number.parseFloat(value)
    if (Number.isFinite(n)) return n
  }
  return null
}

function normalizeImpliedProbability(raw: unknown, price: string): number | null {
  const direct = toNumber(raw)
  if (direct !== null && direct > 0 && direct < 1) return direct
  return impliedProbabilityFromAmerican(price)
}

function inferIsHomeOutcome(game: GameResponse, outcomeRaw: string, index: number): boolean {
  const outcome = String(outcomeRaw || "").toLowerCase()
  if (outcome === "home") return true
  if (outcome === "away") return false

  const home = String(game.home_team || "").toLowerCase()
  const away = String(game.away_team || "").toLowerCase()
  if (outcome && home && (outcome === home || outcome.includes(home) || home.includes(outcome))) return true
  if (outcome && away && (outcome === away || outcome.includes(away) || away.includes(outcome))) return false

  // Common Odds API convention for h2h: [away, home]
  return index === 1
}

/**
 * Calculate a lightweight win probability based on implied odds with a small regression
 * toward 50/50. This is deterministic and intended for the Games list UI.
 *
 * The per-game analysis page uses the backend model for real probabilities.
 */
export function calculateModelWinProbabilities(game: GameResponse): { home: number; away: number } {
  const h2hMarket = game.markets.find((m) => m.market_type === "h2h")
  if (!h2hMarket || h2hMarket.odds.length < 2) return { home: 0.5, away: 0.5 }

  // Try to compute from home odds; fall back to positional mapping.
  const homeOdd = h2hMarket.odds.find((o, idx) => inferIsHomeOutcome(game, o.outcome, idx))
  const rawImplied = normalizeImpliedProbability((homeOdd as any)?.implied_prob, String((homeOdd as any)?.price || ""))
  const impliedHome = rawImplied !== null ? rawImplied : 0.5

  // Small adjustment toward fair odds.
  const adjustment = (impliedHome - 0.5) * 0.08
  const home = clamp01(impliedHome + adjustment, 0.08, 0.92)
  const away = 1 - home
  return { home, away }
}

function clamp01(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return 0.5
  return Math.max(min, Math.min(max, value))
}

export type UpsetCandidate = { side: "home" | "away"; team: string; edgePct: number }

export function findUpsetCandidate(game: GameResponse): UpsetCandidate | null {
  const h2hMarket = game.markets.find((m) => m.market_type === "h2h")
  if (!h2hMarket || h2hMarket.odds.length === 0) return null

  const probs = calculateModelWinProbabilities(game)

  let best: UpsetCandidate | null = null
  for (let idx = 0; idx < h2hMarket.odds.length; idx += 1) {
    const odd = h2hMarket.odds[idx] as any
    const price = String(odd?.price || "")
    if (!price.startsWith("+")) continue

    const implied = normalizeImpliedProbability(odd?.implied_prob, price)
    if (implied === null) continue

    const isHome = inferIsHomeOutcome(game, odd?.outcome, idx)
    const modelProb = isHome ? probs.home : probs.away
    const edgePct = (modelProb - implied) * 100

    // Require a minimum edge to avoid spam.
    if (edgePct < 2.5) continue

    const candidate: UpsetCandidate = {
      side: isHome ? "home" : "away",
      team: isHome ? game.home_team : game.away_team,
      edgePct,
    }

    if (!best || candidate.edgePct > best.edgePct) best = candidate
  }

  return best
}




