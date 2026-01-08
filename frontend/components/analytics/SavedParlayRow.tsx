"use client"

import { CheckCircle, Clock, MinusCircle, XCircle, ChevronDown } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SavedParlayResponse } from "@/lib/api"
import { getMarketLabel, getPickLabel } from "@/lib/parlayFormatting"
import type { LegResponse } from "@/lib/api"
import { SPORT_COLORS, type SportOption } from "@/components/parlay-builder/types"

type SavedParlayWithResults = SavedParlayResponse & {
  results?: {
    status?: string
    hit?: boolean | null
    legs_hit?: number
    legs_missed?: number
    resolved_at?: string | null
    leg_results?: Array<Record<string, any>>
  } | null
}

function shortenHash(hash: string) {
  if (!hash) return ""
  if (hash.length <= 16) return hash
  return `${hash.slice(0, 6)}…${hash.slice(-6)}`
}

function formatLegLabel(leg: Record<string, any>): string {
  if (!leg) return "Leg"
  if (typeof leg.pick === "string" && leg.pick.trim()) {
    const point = leg.point !== undefined && leg.point !== null ? ` ${leg.point}` : ""
    return `${leg.pick}${point}`.trim()
  }
  if (typeof leg.outcome === "string" && leg.outcome.trim()) return leg.outcome
  return "Leg"
}

function getLegSport(leg: Record<string, any>): SportOption {
  const raw = String(leg?.sport || "").trim().toUpperCase()
  const allowed = new Set<SportOption>(["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "MLS", "EPL"])
  if (allowed.has(raw as SportOption)) return raw as SportOption
  return "NFL"
}

function getLegGameLabel(leg: Record<string, any>): string {
  const game = String(leg?.game || "").trim()
  if (game) return game

  const away = String(leg?.away_team || "").trim()
  const home = String(leg?.home_team || "").trim()
  if (away && home) return `${away} @ ${home}`

  const gameId = String(leg?.game_id || "").trim()
  if (gameId) return `Game ${shortenHash(gameId)}`
  return "Matchup"
}

function getLegPickLabel(leg: Record<string, any>): string {
  // AI legs follow `LegResponse` shape (outcome/home_team/away_team), use the formatter for consistency.
  if (typeof leg?.outcome === "string" && typeof leg?.market_type === "string") {
    try {
      return getPickLabel(leg as LegResponse)
    } catch {
      // Fall back to basic formatting below.
    }
  }
  return formatLegLabel(leg)
}

export function SavedParlayRow({
  item,
}: {
  item: SavedParlayWithResults
}) {
  const legsCount = Array.isArray(item.legs) ? item.legs.length : 0
  const created = item.created_at ? new Date(item.created_at) : null

  const typeBadge =
    item.parlay_type === "custom"
      ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/30"
      : "bg-purple-500/15 text-purple-200 border-purple-500/30"

  const results = item.results || null
  const status = (results?.status || "").toLowerCase().trim()
  const statusBadge =
    status === "hit"
      ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/30"
      : status === "missed"
        ? "bg-red-500/15 text-red-200 border-red-500/30"
        : status === "push"
          ? "bg-sky-500/15 text-sky-200 border-sky-500/30"
          : status === "pending"
            ? "bg-amber-500/15 text-amber-200 border-amber-500/30"
            : "bg-white/[0.03] text-gray-200 border-white/10"

  const legResults = Array.isArray(results?.leg_results) ? results?.leg_results : []
  const missedLegs = legResults.filter((l) => String(l?.status || "").toLowerCase() === "missed")
  const pushLegs = legResults.filter((l) => String(l?.status || "").toLowerCase() === "push")

  return (
    <div className="border border-white/10 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-semibold text-white truncate">{item.title}</div>
            <Badge variant="outline" className={cn("text-xs border", typeBadge)}>
              {item.parlay_type === "custom" ? "Custom" : "AI Generated"}
            </Badge>
            <Badge variant="outline" className="text-xs border-white/10 text-gray-300 bg-white/[0.03]">
              {legsCount} legs
            </Badge>
            {!!status && (
              <Badge variant="outline" className={cn("text-xs border inline-flex items-center gap-1", statusBadge)}>
                {status === "hit" ? <CheckCircle className="h-3 w-3" /> : null}
                {status === "missed" ? <XCircle className="h-3 w-3" /> : null}
                {status === "push" ? <MinusCircle className="h-3 w-3" /> : null}
                {status === "pending" ? <Clock className="h-3 w-3" /> : null}
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </Badge>
            )}
          </div>
          {created && (
            <div className="text-xs text-gray-400 mt-1">
              {created.toLocaleDateString()} • {created.toLocaleTimeString()}
            </div>
          )}
          {!!status && (
            <div className="mt-2 text-xs text-gray-300/80">
              {typeof results?.legs_hit === "number" && typeof results?.legs_missed === "number" ? (
                <span>
                  {results.legs_hit} hit • {results.legs_missed} missed
                  {pushLegs.length ? ` • ${pushLegs.length} push` : ""}
                </span>
              ) : null}
              {missedLegs.length ? (
                <div className="mt-1 text-xs text-red-200/90">
                  Missed: {missedLegs.slice(0, 2).map(formatLegLabel).join(", ")}
                  {missedLegs.length > 2 ? ` +${missedLegs.length - 2} more` : ""}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </div>

      {legsCount > 0 && (
        <details className="mt-3 border-t border-white/10 pt-3">
          <summary className="cursor-pointer select-none text-sm text-emerald-200 hover:text-emerald-100 inline-flex items-center gap-2">
            <ChevronDown className="h-4 w-4 opacity-80" />
            View picks ({legsCount})
          </summary>
          <div className="mt-3 space-y-2">
            {(item.legs || []).map((leg: any, index: number) => {
              const sport = getLegSport(leg)
              const colors = SPORT_COLORS[sport] || SPORT_COLORS.NFL
              const marketType = String(leg?.market_type || "").trim()
              const odds = String(leg?.odds || "").trim()
              const confidenceRaw = leg?.confidence ?? leg?.confidence_score
              const confidence = typeof confidenceRaw === "number" ? confidenceRaw : Number(confidenceRaw)
              const hasConfidence = Number.isFinite(confidence)

              return (
                <div
                  key={`${String(leg?.market_id || leg?.game_id || item.id)}-${index}`}
                  className="rounded-lg border border-white/10 bg-black/30 p-3"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={cn(
                        "text-[10px] font-medium px-2 py-0.5 rounded-full border",
                        colors.bg,
                        colors.text,
                        colors.border
                      )}
                    >
                      {sport}
                    </span>
                    <span className="text-xs text-gray-300/80 truncate">{getLegGameLabel(leg)}</span>
                  </div>

                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="font-semibold text-emerald-200 truncate">{getLegPickLabel(leg)}</div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {marketType ? getMarketLabel(marketType) : "Market"}
                        {odds ? ` • Odds ${odds}` : ""}
                      </div>
                    </div>
                    {hasConfidence ? (
                      <div className="text-sm font-bold text-emerald-200">{Number(confidence).toFixed(0)}%</div>
                    ) : null}
                  </div>
                </div>
              )
            })}
          </div>
        </details>
      )}
    </div>
  )
}



