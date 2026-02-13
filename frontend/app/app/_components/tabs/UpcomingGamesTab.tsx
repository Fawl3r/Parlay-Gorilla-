"use client"

import * as React from "react"
import { useMemo, useState } from "react"
import Link from "next/link"
import { Calendar, ChevronLeft, ChevronRight, Filter, LayoutGrid, List, Loader2, RefreshCw } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"

import { GameRow } from "@/components/games/GameRow"
import { DashboardGamesTable } from "@/components/games/DashboardGamesTable"
import { SPORT_NAMES, type SportSlug } from "@/components/games/gamesConfig"
import { addDays, formatDateString, formatDisplayDate, getTargetDate } from "@/components/games/gamesDateUtils"
import { useGamesForSportDate, type MarketFilter } from "@/components/games/useGamesForSportDate"
import { getSportBreakInfo } from "@/components/games/sportBreakConfig"
import { buildDedupeKey } from "@/lib/games/GameDeduper"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

type GamesViewMode = "table" | "cards"

const SPORT_TABS: Array<{ id: SportSlug; label: string; icon: string }> = [
  { id: "nfl", label: "NFL", icon: "🏈" },
  { id: "nba", label: "NBA", icon: "🏀" },
  { id: "nhl", label: "NHL", icon: "🏒" },
  { id: "mlb", label: "MLB", icon: "⚾" },
  { id: "ncaaf", label: "NCAAF", icon: "🏈" },
  { id: "ncaab", label: "NCAAB", icon: "🏀" },
  { id: "epl", label: "EPL", icon: "⚽" },
  { id: "mls", label: "MLS", icon: "⚽" },
]

type Props = {
  sport: SportSlug
  onSportChange: (sport: SportSlug) => void
}

export function UpcomingGamesTab({ sport, onSportChange }: Props) {
  const [date, setDate] = useState("today")
  const [viewMode, setViewMode] = useState<GamesViewMode>("table")
  const [selectedMarket, setSelectedMarket] = useState<MarketFilter>("all")
  const [parlayLegs, setParlayLegs] = useState<Set<string>>(new Set())
  const scrollPositionRef = React.useRef<number>(0)

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const { games, listMeta, oddsPreferredKeys, loading, refreshing, error, refresh } = useGamesForSportDate({ sport, date })

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()

  const canGoPrev = true
  const canGoNext = true

  const prevDate = useMemo(() => formatDateString(addDays(getTargetDate(date), -1)), [date])
  const nextDate = useMemo(() => formatDateString(addDays(getTargetDate(date), 1)), [date])

  function toggleParlayLeg(gameId: string, marketType: string, outcome: string) {
    const legKey = `${gameId}-${marketType}-${outcome}`
    setParlayLegs((prev) => {
      const next = new Set(prev)
      if (next.has(legKey)) next.delete(legKey)
      else next.add(legKey)
      return next
    })
  }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Toolbar */}
      <div className="bg-white/[0.02] border border-white/10 rounded-xl p-3 sm:p-4">
        {/* Sport selector (mobile dropdown) */}
        <div className="sm:hidden pb-2">
          <Select 
            value={sport} 
            onValueChange={(value) => {
              onSportChange(value as SportSlug)
            }}
          >
            <SelectTrigger 
              className="h-11 w-full rounded-xl border border-white/10 bg-white/5 text-white focus:ring-emerald-400/40"
              onClick={(e) => {
                // Prevent any parent click handlers from interfering
                e.stopPropagation()
              }}
              onPointerDown={(e) => {
                // Store scroll position before dropdown opens
                scrollPositionRef.current = window.scrollY
              }}
            >
              <SelectValue placeholder="Select sport" />
            </SelectTrigger>
            <SelectContent 
              className="border-white/10 bg-[#0a0a0f] text-white z-[100]"
              position="popper"
              sideOffset={4}
              onCloseAutoFocus={(e) => {
                // Prevent auto-focus from scrolling to top on mobile when closing
                e.preventDefault()
              }}
              onInteractOutside={(e) => {
                // Restore scroll position if it changed when clicking outside
                if (Math.abs(window.scrollY - scrollPositionRef.current) > 10) {
                  window.scrollTo({ top: scrollPositionRef.current, behavior: 'instant' })
                }
              }}
            >
              {SPORT_TABS.map((s) => (
                <SelectItem 
                  key={s.id} 
                  value={s.id} 
                  className="focus:bg-white/10 focus:text-white"
                >
                  {s.icon} {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Sport tabs (tablet/desktop) */}
        <div className="hidden sm:flex items-center gap-2 overflow-x-auto scrollbar-hide pb-2">
          {SPORT_TABS.map((s) => {
            const active = sport === s.id
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => onSportChange(s.id)}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-semibold transition-all whitespace-nowrap",
                  active ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10"
                )}
              >
                <span className="mr-2">{s.icon}</span>
                {s.label}
              </button>
            )
          })}
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2 border-t border-white/10">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
              <button
                className={cn("p-2 rounded hover:bg-white/10 transition-colors", !canGoPrev && "opacity-40")}
                onClick={() => canGoPrev && setDate(prevDate)}
                aria-label="Previous day"
              >
                <ChevronLeft className="h-4 w-4 text-gray-400" />
              </button>
              <div className="flex items-center gap-2 px-3 py-1.5">
                <Calendar className="h-4 w-4 text-emerald-400" />
                <span className="text-sm font-medium text-white">{formatDisplayDate(date)}</span>
              </div>
              <button
                className={cn("p-2 rounded hover:bg-white/10 transition-colors", !canGoNext && "opacity-40")}
                onClick={() => canGoNext && setDate(nextDate)}
                aria-label="Next day"
              >
                <ChevronRight className="h-4 w-4 text-gray-400" />
              </button>
            </div>

            <button
              onClick={refresh}
              disabled={refreshing}
              className="px-3 py-2 rounded-lg border border-white/10 bg-white/5 text-gray-300 hover:bg-white/10 transition-all text-sm font-semibold disabled:opacity-50"
            >
              <RefreshCw className={cn("h-4 w-4 inline mr-2", refreshing && "animate-spin")} />
              Refresh
            </button>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs text-gray-500">View:</span>
            <button
              type="button"
              onClick={() => setViewMode("table")}
              className={cn(
                "p-2 rounded-lg transition-colors",
                viewMode === "table" ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-400 hover:bg-white/10"
              )}
              title="Table (like Insights)"
              aria-label="Table view"
            >
              <List className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => setViewMode("cards")}
              className={cn(
                "p-2 rounded-lg transition-colors",
                viewMode === "cards" ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-400 hover:bg-white/10"
              )}
              title="Cards with odds"
              aria-label="Cards view"
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <div className="h-6 w-px bg-white/10" />
            <Filter className="h-4 w-4 text-gray-500" />
            {(["all", "h2h", "spreads", "totals"] as const).map((market) => (
              <button
                key={market}
                onClick={() => setSelectedMarket(market)}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-semibold transition-all",
                  selectedMarket === market ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10"
                )}
              >
                {market === "all"
                  ? "All"
                  : market === "h2h"
                    ? "Moneyline"
                    : market === "spreads"
                      ? "Spread"
                      : "Total"}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto pr-1">
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
            <span className="ml-3 text-gray-400">Loading {sportName} games...</span>
          </div>
        ) : games.length === 0 ? (
          <div className="text-center py-20">
            {(() => {
              const state = listMeta?.sport_state
              const nextAt = listMeta?.next_game_at
              const daysToNext = listMeta?.days_to_next ?? 0
              const enableDays = listMeta?.preseason_enable_days ?? 14
              if (state === "OFFSEASON") {
                const returnsAt = nextAt ? new Date(nextAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : null
                return (
                  <>
                    <div className="text-gray-400 font-semibold mb-2">{sportName} is out of season</div>
                    <div className="text-sm text-gray-500">
                      {returnsAt ? `Returns ${returnsAt}` : "No games in season right now."}
                    </div>
                  </>
                )
              }
              if (state === "PRESEASON" && nextAt) {
                const startDate = new Date(nextAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
                const unlocksIn = daysToNext > 0 && enableDays > 0 && daysToNext > enableDays ? daysToNext - enableDays : null
                return (
                  <>
                    <div className="text-gray-400 font-semibold mb-2">Preseason starts {startDate}</div>
                    {unlocksIn != null && unlocksIn > 0 && (
                      <div className="text-sm text-gray-500">Betting unlocks in {unlocksIn} days</div>
                    )}
                  </>
                )
              }
              const breakInfo = getSportBreakInfo(sport)
              if (breakInfo) {
                return (
                  <>
                    <div className="text-gray-400 font-semibold mb-2">
                      {sportName} on {breakInfo.breakLabel}
                    </div>
                    <div className="text-sm text-gray-500">
                      Next games {breakInfo.nextGamesDate}.
                    </div>
                  </>
                )
              }
              return (
                <>
                  <div className="text-gray-400 font-semibold mb-2">No games found</div>
                  {error && <div className="text-sm text-gray-500">{error.message}</div>}
                </>
              )
            })()}
          </div>
        ) : viewMode === "table" ? (
          <DashboardGamesTable sport={sport} games={games} canViewWinProb={canViewWinProb} />
        ) : (
          <div className="space-y-4">
            {games.map((game, idx) => (
              <GameRow
                key={game.id}
                sport={sport}
                game={game}
                index={idx}
                canViewWinProb={canViewWinProb}
                selectedMarket={selectedMarket}
                parlayLegs={parlayLegs}
                onToggleParlayLeg={toggleParlayLeg}
                highlightOdds={oddsPreferredKeys.has(buildDedupeKey(game))}
              />
            ))}
          </div>
        )}
      </div>

      {/* Floating CTA (kept minimal) */}
      {parlayLegs.size > 0 && (
        <div className="sticky bottom-[calc(env(safe-area-inset-bottom,0px)+78px)] md:bottom-0 pb-2">
          <div className="bg-black/60 border border-white/10 rounded-xl p-3 flex items-center justify-between">
            <div className="text-sm text-gray-300">
              Selected legs: <span className="text-white font-bold">{parlayLegs.size}</span>
            </div>
            <Link
              href="/build"
              className="px-4 py-2 rounded-lg bg-emerald-500 text-black font-bold hover:bg-emerald-400 transition-all"
            >
              View Parlay
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}



