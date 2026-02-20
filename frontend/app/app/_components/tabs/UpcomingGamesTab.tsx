"use client"

import * as React from "react"
import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { Calendar, ChevronLeft, ChevronRight, Filter, LayoutGrid, List, Loader2, RefreshCw } from "lucide-react"

import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { cn } from "@/lib/utils"

import { GameRow } from "@/components/games/GameRow"
import { DashboardGamesTable } from "@/components/games/DashboardGamesTable"
import { SPORT_NAMES, SPORT_ICONS, type SportSlug } from "@/components/games/gamesConfig"
import { addDays, formatDateString, formatDisplayDate, getTargetDate } from "@/components/games/gamesDateUtils"
import { useGamesForSportDate, type MarketFilter } from "@/components/games/useGamesForSportDate"
import { getSportBreakInfo } from "@/components/games/sportBreakConfig"
import { buildDedupeKey } from "@/lib/games/GameDeduper"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useSportsAvailability } from "@/lib/sports/useSportsAvailability"

type GamesViewMode = "table" | "cards"

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
  const [showInSeasonOnly, setShowInSeasonOnly] = useState(false)

  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user

  const {
    sports,
    inSeasonSports,
    error: sportsError,
    isStale: sportsStale,
    isSportEnabled,
    isSportInSeason,
    getSportBadge,
    normalizeSlug,
  } = useSportsAvailability()
  /** Active (in-season) sports first, then inactive. */
  const sportsSortedActiveFirst = useMemo(() => {
    const inSeasonSlugs = new Set(inSeasonSports.map((s) => normalizeSlug(s.slug)))
    return [...inSeasonSports, ...sports.filter((s) => !inSeasonSlugs.has(normalizeSlug(s.slug)))]
  }, [inSeasonSports, sports, normalizeSlug])
  const { games, listMeta, oddsPreferredKeys, loading, refreshing, error, refresh, suggestedDate } = useGamesForSportDate({ sport, date })

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()
  const sportsForSelector = showInSeasonOnly ? inSeasonSports : sportsSortedActiveFirst

  // When sport changes, reset date to "today" so we show the next upcoming games for the new sport (not the previous sport's date).
  useEffect(() => {
    setDate("today")
  }, [sport])

  // Option A: when "today" has no games but API returned games, show next date and sync date state
  useEffect(() => {
    if (suggestedDate && date === "today") setDate(suggestedDate)
  }, [suggestedDate, date])

  // If current sport becomes disabled (or not in season and we can prefer in-season), switch to first in-season or first enabled
  useEffect(() => {
    if (sports.length === 0) return
    if (isSportEnabled(sport)) return
    const firstInSeason = sports.find((s) => isSportInSeason(s.slug))
    const firstEnabled = sports.find((s) => isSportEnabled(s.slug))
    const next = firstInSeason ?? firstEnabled
    if (next) {
      const slug = normalizeSlug(next.slug) as SportSlug
      if (slug && slug !== sport) onSportChange(slug)
    }
  }, [sports, sport, isSportInSeason, isSportEnabled, normalizeSlug, onSportChange])

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
        {/* Sport selector (mobile dropdown) — from backend; disabled when is_enabled === false */}
        <div className="sm:hidden pb-2">
          {sportsError && (
            <div className="py-2 text-center text-sm font-medium text-red-400">
              Couldn&apos;t reach backend. Try refresh.
              {sportsStale && (
                <div className="text-xs mt-1 text-gray-500">
                  Showing last saved sports list. <span className="text-[10px] uppercase tracking-wide text-gray-500" aria-label="Stale data">Stale data</span>
                </div>
              )}
            </div>
          )}
          {sportsForSelector.length > 0 && (
            <Select
              value={sport}
              onValueChange={(value) => {
                if (isSportEnabled(value)) onSportChange(value as SportSlug)
              }}
            >
              <SelectTrigger
                className="h-11 w-full rounded-xl border border-white/10 bg-white/5 text-white focus:ring-emerald-400/40"
                onClick={(e) => e.stopPropagation()}
                onPointerDown={() => { scrollPositionRef.current = window.scrollY }}
              >
                <SelectValue placeholder="Select sport" />
              </SelectTrigger>
              <SelectContent
                className="border-white/10 bg-[#0a0a0f] text-white z-[100]"
                position="popper"
                sideOffset={4}
                onCloseAutoFocus={(e) => e.preventDefault()}
              >
                {sportsForSelector.map((s) => {
                  const slug = normalizeSlug(s.slug) as SportSlug
                  const enabled = isSportEnabled(slug)
                  const label = s.display_name || SPORT_NAMES[slug] || slug.toUpperCase()
                  const icon = SPORT_ICONS[slug] ?? "•"
                  return (
                    <SelectItem
                      key={slug}
                      value={slug}
                      disabled={!enabled}
                      className="focus:bg-white/10 focus:text-white"
                    >
                      {icon} {label}
                      {!enabled ? ` (${getSportBadge(slug) || "Not in season"})` : ""}
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          )}
        </div>

        {/* Sport tabs (tablet/desktop) — from backend; disabled when is_enabled === false */}
        <div className="hidden sm:flex items-center justify-between pb-2 gap-2">
          <div className="flex items-center gap-2 overflow-x-auto scrollbar-hide">
          {sportsError && (
            <div className="py-2 text-sm font-medium text-red-400">
              Couldn&apos;t reach backend. Try refresh.
              {sportsStale && (
                <span className="ml-2 text-xs text-gray-500">
                  (Showing last saved list.) <span className="text-[10px] uppercase text-gray-500" aria-label="Stale data">Stale data</span>
                </span>
              )}
            </div>
          )}
          {sportsForSelector.length > 0 && sportsForSelector.map((s) => {
              const slug = normalizeSlug(s.slug) as SportSlug
              const active = sport === slug
              const enabled = isSportEnabled(slug)
              const disabled = !enabled
              const label = s.display_name || SPORT_NAMES[slug] || slug.toUpperCase()
              const icon = SPORT_ICONS[slug] ?? "•"
              const badge = getSportBadge(slug)
              return (
                <button
                  key={slug}
                  type="button"
                  onClick={() => (disabled ? undefined : onSportChange(slug))}
                  disabled={disabled}
                  className={cn(
                    "px-4 py-2 rounded-lg text-sm font-semibold transition-all text-center inline-flex flex-col items-center",
                    active ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-300 hover:bg-white/10",
                    disabled && "opacity-40 cursor-not-allowed hover:bg-white/5"
                  )}
                  title={disabled ? badge || "Not in season" : undefined}
                >
                  <span className="flex items-center gap-2">
                    <span>{icon}</span>
                    <span className="whitespace-nowrap">{label}</span>
                  </span>
                  {disabled && badge ? <span className="mt-1 text-[10px] font-bold uppercase text-gray-400 leading-tight">{badge}</span> : null}
                </button>
              )
            }) }
          </div>
          <button
            type="button"
            onClick={() => setShowInSeasonOnly((v) => !v)}
            className={cn(
              "ml-2 inline-flex items-center gap-1 rounded-full border px-3 py-1 text-[11px] font-medium whitespace-nowrap",
              showInSeasonOnly
                ? "border-emerald-400 text-emerald-300 bg-emerald-500/10"
                : "border-white/10 text-gray-400 hover:bg-white/10"
            )}
          >
            <Filter className="h-3 w-3" />
            {showInSeasonOnly ? "In-season only" : "All sports"}
          </button>
        </div>

        {/* Option A banner: no games today — showing next scheduled date */}
        {suggestedDate && games.length > 0 && (
          <div className="mt-2 py-2 px-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">
            No games today — showing next scheduled games ({formatDisplayDate(suggestedDate)}).
          </div>
        )}

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
        ) : error ? (
          <div className="text-center py-20">
            <div className="text-gray-400 font-semibold mb-2">Couldn&apos;t load games. Try refresh.</div>
            <div className="text-sm text-gray-500">{error.message}</div>
          </div>
        ) : games.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-gray-400 font-semibold mb-2">No games scheduled.</div>
            {listMeta?.status_label && (
              <div className="text-sm text-gray-500">{listMeta.status_label}</div>
            )}
            {(() => {
              const state = listMeta?.sport_state
              const nextAt = listMeta?.next_game_at
              const daysToNext = listMeta?.days_to_next ?? 0
              const enableDays = listMeta?.preseason_enable_days ?? 14
              if (state === "OFFSEASON" && nextAt) {
                return <div className="text-sm text-gray-500 mt-1">Returns {new Date(nextAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</div>
              }
              if (state === "PRESEASON" && nextAt) {
                const startDate = new Date(nextAt).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
                const unlocksIn = daysToNext > 0 && enableDays > 0 && daysToNext > enableDays ? daysToNext - enableDays : null
                return (
                  <>
                    <div className="text-sm text-gray-500 mt-1">Preseason starts {startDate}</div>
                    {unlocksIn != null && unlocksIn > 0 && <div className="text-sm text-gray-500">Unlocks in {unlocksIn} days</div>}
                  </>
                )
              }
              const breakInfo = getSportBreakInfo(sport)
              if (breakInfo) {
                return (
                  <div className="text-sm text-gray-500 mt-1">
                    {sportName} on {breakInfo.breakLabel} — next games {breakInfo.nextGamesDate}
                  </div>
                )
              }
              return null
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



