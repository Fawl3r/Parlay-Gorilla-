import type { UpsetCandidateTools } from "@/lib/api/types/tools"

type HeatmapCellLike = {
  game: string
  market_type: string
  outcome: string
  odds: string
  book: string
  implied_prob: number
  model_prob: number
  edge: number
}

function pct(prob0to1: number) {
  if (!Number.isFinite(prob0to1)) return "N/A"
  return `${(prob0to1 * 100).toFixed(1)}%`
}

function edgePct(value: number) {
  if (!Number.isFinite(value)) return "N/A"
  const s = value >= 0 ? `+${value.toFixed(1)}` : value.toFixed(1)
  return `${s}%`
}

function safeText(value: unknown) {
  return String(value ?? "").trim()
}

export class ToolChatPromptBuilder {
  buildUpsetCandidatePrefill(args: {
    sport: string
    days: number
    minEdgePct: number
    candidate: UpsetCandidateTools
  }): string {
    const sportLabel = safeText(args.sport || args.candidate.league).toUpperCase()
    const u = args.candidate
    const flags = Array.isArray(u.flags) && u.flags.length > 0 ? u.flags.join(", ") : "none"
    const reasons = Array.isArray(u.reasons) && u.reasons.length > 0 ? u.reasons.join(". ") : "(none provided)"

    const best = u.best_underdog_ml != null ? `Best: ${u.best_underdog_ml > 0 ? `+${u.best_underdog_ml}` : u.best_underdog_ml}` : ""
    const median = u.median_underdog_ml != null ? `Median: ${u.median_underdog_ml > 0 ? `+${u.median_underdog_ml}` : u.median_underdog_ml}` : ""
    const spread = u.price_spread != null ? `Spread: ${u.price_spread}` : ""
    const lineSummary = [best, median, spread].filter(Boolean).join(" • ") || "Line data: (not available)"

    return [
      "I'm using Parlay Gorilla's Upset Finder. Explain this candidate in plain English (what the numbers mean and any risk/quality flags).",
      `Tool filters: sport=${sportLabel}, window=${Math.max(1, Math.trunc(args.days))} days, min_edge=${Math.max(0, args.minEdgePct)}%.`,
      `Matchup: ${safeText(u.away_team)} @ ${safeText(u.home_team)}.`,
      `Underdog: ${safeText(u.underdog_team)} (${u.underdog_ml > 0 ? `+${u.underdog_ml}` : u.underdog_ml}).`,
      `Model=${pct(u.model_prob)} vs Implied=${pct(u.implied_prob)} → Edge=${edgePct(u.edge)}.`,
      lineSummary,
      `Flags: ${flags}.`,
      `Reasons: ${reasons}`,
      "Answer format: 1) what edge means here 2) what to double-check (odds quality / market depth) 3) what questions I should ask next.",
    ].join("\n")
  }

  buildHeatmapOverviewPrefill(args: {
    sport: string
    market: string
    topCells: HeatmapCellLike[]
  }): string {
    const sportLabel = safeText(args.sport).toUpperCase()
    const marketLabel = safeText(args.market || "all")
    const rows = (args.topCells || []).slice(0, 6)
    const summary =
      rows.length > 0
        ? rows
            .map(
              (c, idx) =>
                `${idx + 1}. ${safeText(c.game)} | ${safeText(c.market_type)} | ${safeText(c.outcome)} ${safeText(
                  c.odds
                )} @ ${safeText(c.book)} | Model ${pct(c.model_prob)} vs Impl ${pct(c.implied_prob)} | Edge ${edgePct(
                  c.edge
                )}`
            )
            .join("\n")
        : "(No rows available)"

    return [
      "I'm using Parlay Gorilla's Odds Heatmap. Summarize what stands out and how to interpret these edges.",
      `Context: sport=${sportLabel}, market_filter=${marketLabel}.`,
      "Top rows:",
      summary,
      "Answer format: 1) what edge means 2) potential pitfalls (stale odds, thin markets, noise) 3) what to research next.",
    ].join("\n")
  }
}

