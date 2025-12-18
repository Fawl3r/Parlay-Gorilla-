"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import { Calendar, ChevronLeft, ChevronRight, Filter, Loader2, RefreshCw } from "lucide-react"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"

import { GameRow } from "@/components/games/GameRow"
import { SPORT_BACKGROUNDS, SPORT_NAMES } from "@/components/games/gamesConfig"
import { SportBackground } from "@/components/games/SportBackground"
import { formatDisplayDate } from "@/components/games/gamesDateUtils"
import { useGamesForSportDate, type MarketFilter } from "@/components/games/useGamesForSportDate"

type Props = {
  sport: string
  date: string
}

export function GamesListPage({ sport, date }: Props) {
  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const canViewWinProb = isPremium || !!user
  const canRefreshGames = !!user

  const [selectedMarket, setSelectedMarket] = useState<MarketFilter>("all")
  const [parlayLegs, setParlayLegs] = useState<Set<string>>(new Set())

  const { games, loading, refreshing, error, previousDateHref, nextDateHref, refresh } = useGamesForSportDate({
    sport,
    date,
  })

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()
  const backgroundImage = SPORT_BACKGROUNDS[sport] || "/images/nflll.png"

  const sortedGames = useMemo(() => games, [games])

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
    <div className="min-h-screen flex flex-col relative">
      <SportBackground imageUrl={backgroundImage} overlay="medium" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1">
          {/* Header Section */}
          <section className="relative py-8 border-b border-white/10 bg-black/40 backdrop-blur-sm">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
                    <Link href="/sports" className="hover:text-emerald-400 transition-colors">
                      Sports
                    </Link>
                    <span>/</span>
                    <span className="text-white">{sportName}</span>
                  </div>
                  <h1 className="text-3xl md:text-4xl font-black">
                    <span className="text-white">{sportName} </span>
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                      Games
                    </span>
                  </h1>
                </div>

                <div className="flex items-center gap-3">
                  {/* Date Navigation */}
                  <div className="flex items-center gap-2 bg-white/5 rounded-lg p-1">
                    <Link
                      href={`/games/${sport}/${previousDateHref}`}
                      className="p-2 rounded hover:bg-white/10 transition-colors"
                      aria-label="Previous day"
                    >
                      <ChevronLeft className="h-4 w-4 text-gray-400" />
                    </Link>
                    <div className="flex items-center gap-2 px-3 py-1.5">
                      <Calendar className="h-4 w-4 text-emerald-400" />
                      <span className="text-sm font-medium text-white">{formatDisplayDate(date)}</span>
                    </div>
                    <Link
                      href={`/games/${sport}/${nextDateHref}`}
                      className="p-2 rounded hover:bg-white/10 transition-colors"
                      aria-label="Next day"
                    >
                      <ChevronRight className="h-4 w-4 text-gray-400" />
                    </Link>
                  </div>

                  {canRefreshGames && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={refresh}
                      disabled={refreshing}
                      className="border-white/20"
                    >
                      <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
                      Refresh
                    </Button>
                  )}
                </div>
              </div>

              {/* Market Filter */}
              <div className="flex items-center gap-2 mt-4">
                <Filter className="h-4 w-4 text-gray-500" />
                {(["all", "h2h", "spreads", "totals"] as const).map((market) => (
                  <button
                    key={market}
                    onClick={() => setSelectedMarket(market)}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                      selectedMarket === market ? "bg-emerald-500 text-black" : "bg-white/5 text-gray-400 hover:bg-white/10"
                    )}
                  >
                    {market === "all"
                      ? "All Markets"
                      : market === "h2h"
                        ? "Moneyline"
                        : market === "spreads"
                          ? "Spread"
                          : "Total"}
                  </button>
                ))}
              </div>
            </div>
          </section>

          {/* Games List */}
          <section className="py-8">
            <div className="container mx-auto px-4">
              {loading ? (
                <div className="flex justify-center items-center py-20">
                  <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                  <span className="ml-3 text-gray-400">Loading games...</span>
                </div>
              ) : sortedGames.length === 0 ? (
                <div className="text-center py-20">
                  {error ? (
                    <div
                      className={cn(
                        "rounded-xl p-6 max-w-md mx-auto",
                        error.kind === "rate_limit"
                          ? "bg-yellow-500/10 border border-yellow-500/30"
                          : "bg-red-500/10 border border-red-500/30"
                      )}
                    >
                      <div className={cn("font-semibold mb-2", error.kind === "rate_limit" ? "text-yellow-400" : "text-red-400")}>
                        {error.kind === "rate_limit" ? "Rate Limit" : "Connection Error"}
                      </div>
                      <div className="text-gray-300 text-sm mb-4">{error.message}</div>
                      {error.kind !== "rate_limit" && (
                        <button
                          onClick={() => refresh()}
                          className="px-4 py-2 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
                        >
                          Retry
                        </button>
                      )}
                      {error.kind === "rate_limit" && (
                        <div className="text-xs text-gray-400 mt-2">Games are cached to preserve API quota. Try again in a few minutes.</div>
                      )}
                    </div>
                  ) : (
                    <div className="text-gray-500 mb-4">No games found for this date</div>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {sortedGames.map((game, idx) => (
                    <GameRow
                      key={game.id}
                      sport={sport}
                      game={game}
                      index={idx}
                      canViewWinProb={canViewWinProb}
                      selectedMarket={selectedMarket}
                      parlayLegs={parlayLegs}
                      onToggleParlayLeg={toggleParlayLeg}
                    />
                  ))}
                </div>
              )}
            </div>
          </section>

          {/* Floating Parlay Slip */}
          {parlayLegs.size > 0 && (
            <div className="fixed bottom-6 right-6 z-50">
              <Link href="/build">
                <div className="flex items-center gap-3 px-5 py-3 rounded-full bg-emerald-500 text-black shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 transition-all">
                  <div className="w-7 h-7 rounded-full bg-black/20 flex items-center justify-center text-sm font-bold">
                    {parlayLegs.size}
                  </div>
                  <span className="font-semibold">View Parlay</span>
                </div>
              </Link>
            </div>
          )}
        </main>

        <Footer />
      </div>
    </div>
  )
}



