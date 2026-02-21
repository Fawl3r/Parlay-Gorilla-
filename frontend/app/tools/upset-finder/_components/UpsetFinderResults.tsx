"use client"

import Link from "next/link"
import { TrendingUp, Loader2, Plus, Crown, RefreshCw, MessageCircle } from "lucide-react"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"
import { motion } from "framer-motion"
import type { UpsetCandidateTools, UpsetFinderToolsAccess, UpsetFinderToolsMeta } from "@/lib/api/types/tools"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { UpsetFinderEmptyStateModelBuilder, type UpsetFinderEmptyStateActionId } from "./UpsetFinderEmptyStateModelBuilder"
import { dispatchGorillaBotOpen } from "@/lib/gorilla-bot/events"
import { ToolChatPromptBuilder } from "@/lib/gorilla-bot/ToolChatPromptBuilder"

function formatPercent(prob0to1: number) {
  if (!Number.isFinite(prob0to1)) return "0.0%"
  return `${(prob0to1 * 100).toFixed(1)}%`
}

function formatEdge(edgePct: number) {
  if (!Number.isFinite(edgePct)) return "0%"
  const s = edgePct >= 0 ? `+${edgePct.toFixed(1)}` : edgePct.toFixed(1)
  return `${s}%`
}

function formatAmericanOdds(value: number) {
  if (!Number.isFinite(value)) return "—"
  return value > 0 ? `+${value}` : `${value}`
}

const toolChatPrompts = new ToolChatPromptBuilder()

export interface UpsetFinderResultsProps {
  candidates: UpsetCandidateTools[]
  meta: UpsetFinderToolsMeta | null
  access: UpsetFinderToolsAccess | null
  sport: string
  days: number
  minEdgePct: number
  loading: boolean
  error: string | null
  onAction: (action: UpsetFinderEmptyStateActionId) => void
}

export function UpsetFinderResults({
  candidates,
  meta,
  access,
  sport,
  days,
  minEdgePct,
  loading,
  error,
  onAction,
}: UpsetFinderResultsProps) {
  const modelBuilder = new UpsetFinderEmptyStateModelBuilder()
  const { nudgeInstallCta } = usePwaInstallNudge()

  const noCandidates = candidates.length === 0
  const gamesWithOdds = meta?.games_with_odds ?? 0
  const gamesScanned = meta?.games_scanned ?? 0
  const missingOdds = meta?.missing_odds ?? 0
  const isCapped = Boolean(meta?.games_scanned_capped)

  const metaChips = meta ? (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      <span className="text-xs text-gray-400 rounded-full bg-white/5 border border-white/10 px-2 py-0.5">
        Scanned: {gamesScanned}
      </span>
      <span className="text-xs text-gray-400 rounded-full bg-white/5 border border-white/10 px-2 py-0.5">
        With odds: {gamesWithOdds}
      </span>
      <span className="text-xs text-gray-400 rounded-full bg-white/5 border border-white/10 px-2 py-0.5">
        Missing odds: {missingOdds}
      </span>
      {isCapped ? (
        <span className="text-xs text-gray-400 rounded-full bg-white/5 border border-white/10 px-2 py-0.5">
          Capped
        </span>
      ) : null}
    </div>
  ) : null

  if (loading) {
    return (
      <div className="flex justify-center items-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        <span className="ml-3 text-gray-400">Loading upset candidates...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-2">
        {metaChips}
        <div className="mb-6 bg-red-500/15 border border-red-500/30 rounded-lg p-4 text-red-200 text-sm flex flex-col gap-3">
          <span>{error}</span>
          <Button variant="outline" size="sm" onClick={() => onAction("refresh")} className="w-fit border-red-500/40 text-red-200 hover:bg-red-500/20">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </div>
      </div>
    )
  }

  if (noCandidates) {
    const empty = modelBuilder.build({
      access,
      meta,
      candidatesCount: 0,
      days,
      minEdgePct,
    })
    return (
      <div className="py-2">
        {metaChips}
        <div className="text-center text-gray-400 py-10">
          <TrendingUp className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">{empty.title}</h3>
          <p>{empty.message}</p>

          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {empty.actions.map((a) => {
              const isUnlock = a.id === "unlock"
              return (
                <Button
                  key={a.id}
                  variant={isUnlock ? "default" : "outline"}
                  size="sm"
                  onClick={() => onAction(a.id)}
                  className={cn(isUnlock ? "bg-emerald-500 hover:bg-emerald-400 text-black font-bold" : "border-white/20")}
                >
                  {a.id === "unlock" ? <Crown className="h-4 w-4 mr-2" /> : null}
                  {a.id === "refresh" ? <RefreshCw className="h-4 w-4 mr-2" /> : null}
                  {a.label}
                </Button>
              )
            })}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      {metaChips}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {candidates.map((u, idx) => {
          const prefillSport = sport === "all" ? u.league.toLowerCase() : sport
          const addToParlayUrl = `/app?tab=custom-builder&sport=${encodeURIComponent(prefillSport)}&prefill_game_id=${encodeURIComponent(u.game_id)}&prefill_market_type=h2h&prefill_pick=${encodeURIComponent(u.underdog_team)}`
          const edgeClass =
            u.edge >= 0
              ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-200"
              : "bg-rose-500/15 border-rose-500/30 text-rose-200"

          const booksCount = u.books_count ?? 0
          const best = u.best_underdog_ml ?? null
          const median = u.median_underdog_ml ?? null
          const spread = u.price_spread ?? null
          const flags = u.flags ?? []

          const showBestLine = best != null && booksCount > 0
          const showMedianSpread = median != null || spread != null
          const showLineShopping = typeof spread === "number" && spread >= 80
          const isThinMarket = flags.includes("low_books")
          const isVerifyOdds = flags.includes("stale_odds_suspected")

          return (
            <motion.div
              key={`${u.game_id}-${u.underdog_team}-${idx}`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-white font-bold truncate">
                    {u.away_team} @ {u.home_team}
                  </div>
                  <div className="text-xs text-white/60">
                    {u.league} • Underdog: {u.underdog_team} ({u.underdog_ml > 0 ? `+${u.underdog_ml}` : u.underdog_ml})
                  </div>

                  {showBestLine ? (
                    <div className="mt-1 text-xs text-white/70">
                      Best: {formatAmericanOdds(best)} ({booksCount} books)
                    </div>
                  ) : null}
                  {showMedianSpread ? (
                    <div className="mt-0.5 text-xs text-white/60">
                      {median != null ? `Median: ${formatAmericanOdds(median)}` : null}
                      {median != null && spread != null ? " • " : null}
                      {spread != null ? `Spread: ${spread}` : null}
                    </div>
                  ) : null}

                  <div className="mt-1 text-xs text-white/60">
                    Model {formatPercent(u.model_prob)} vs Implied {formatPercent(u.implied_prob)} • Confidence{" "}
                    {formatPercent(u.confidence)}
                  </div>

                  {isThinMarket || isVerifyOdds || showLineShopping ? (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {isThinMarket ? (
                        <span className="text-[11px] rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-amber-300">
                          Thin market
                        </span>
                      ) : null}
                      {isVerifyOdds ? (
                        <span className="text-[11px] rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-rose-300">
                          Verify odds
                        </span>
                      ) : null}
                      {showLineShopping ? (
                        <span className="text-[11px] rounded-full bg-white/5 border border-white/10 px-2 py-0.5 text-gray-300">
                          Line shopping
                        </span>
                      ) : null}
                    </div>
                  ) : null}
                </div>

                <div className="shrink-0 flex flex-col items-end gap-2">
                  <div className={cn("px-2.5 py-1 rounded-full border text-sm font-black", edgeClass)}>
                    Edge {formatEdge(u.edge)}
                  </div>
                  <Link
                    href={addToParlayUrl}
                    onClick={() => nudgeInstallCta()}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-medium hover:bg-emerald-500/30 transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add to Parlay
                  </Link>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="border-white/20 bg-white/5 text-white/90 hover:bg-white/10"
                    onClick={() => {
                      const sportToExplain = sport === "all" ? u.league : sport
                      dispatchGorillaBotOpen({
                        prefill: toolChatPrompts.buildUpsetCandidatePrefill({
                          sport: String(sportToExplain || ""),
                          days,
                          minEdgePct,
                          candidate: u,
                        }),
                      })
                    }}
                  >
                    <MessageCircle className="h-3.5 w-3.5 mr-2" />
                    Ask Bot
                  </Button>
                </div>
              </div>

              {u.reasons?.length ? (
                <p className="mt-3 text-xs text-white/60 leading-snug">{u.reasons.join(". ")}</p>
              ) : null}
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
