"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { AlertTriangle, Eye, Lock, Plus } from "lucide-react"

import type { GameResponse } from "@/lib/api"
import { cn, generateAnalysisUrl } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import type { MarketFilter } from "@/components/games/useGamesForSportDate"
import { calculateModelWinProbabilities, findUpsetCandidate } from "@/components/games/gamesOddsUtils"

type Props = {
  sport: string
  game: GameResponse
  index: number
  canViewWinProb: boolean
  selectedMarket: MarketFilter
  parlayLegs: Set<string>
  onToggleParlayLeg: (gameId: string, marketType: string, outcome: string) => void
}

function TeamWinProb({
  winProb,
  canView,
}: {
  winProb: number
  canView: boolean
}) {
  if (canView) {
    return (
      <div className="text-right">
        <div className="text-sm font-medium text-gray-300">{(winProb * 100).toFixed(0)}%</div>
        <div className="text-xs text-gray-500">Win Prob</div>
      </div>
    )
  }

  return (
    <Link href="/auth/signup" className="group">
      <div className="text-xs text-gray-500 mb-1">Win Prob</div>
      <div className="relative">
        <div className="text-sm font-medium text-gray-500 blur-sm select-none">{(winProb * 100).toFixed(0)}%</div>
        <Lock className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
      </div>
      <div className="text-xs text-emerald-400 group-hover:text-emerald-300 mt-0.5">Unlock</div>
    </Link>
  )
}

export function GameRow({
  sport,
  game,
  index,
  canViewWinProb,
  selectedMarket,
  parlayLegs,
  onToggleParlayLeg,
}: Props) {
  const probs = calculateModelWinProbabilities(game)
  const upset = findUpsetCandidate(game)
  const gameTime = new Date(game.start_time)

  return (
    <motion.div
      key={game.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden hover:border-emerald-500/30 transition-all"
    >
      {/* Game Header */}
      <div className="p-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">
            {gameTime.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" })}
          </span>
          <span className="text-xs font-medium text-emerald-400">
            {gameTime.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}
          </span>
          {game.status !== "scheduled" && (
            <Badge variant="outline" className="text-xs">
              {game.status}
            </Badge>
          )}
        </div>

        {upset && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-500/30">
            <AlertTriangle className="h-3.5 w-3.5 text-purple-400" />
            <span className="text-xs font-semibold text-purple-300">
              🦍 Upset Alert: {upset.side} (+{upset.edgePct.toFixed(1)}% edge)
            </span>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="p-4">
        <div className="grid grid-cols-12 gap-4 items-center">
          {/* Teams */}
          <div className="col-span-12 md:col-span-4">
            <div className="space-y-3">
              {/* Away */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center text-lg font-bold text-gray-400">
                    {game.away_team.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{game.away_team}</div>
                    <div className="text-xs text-gray-500">Away</div>
                  </div>
                </div>
                <TeamWinProb
                  winProb={probs.away}
                  canView={canViewWinProb}
                />
              </div>

              <div className="text-xs text-gray-600 text-center">@</div>

              {/* Home */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center text-lg font-bold text-gray-400">
                    {game.home_team.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-white">{game.home_team}</div>
                    <div className="text-xs text-gray-500">Home</div>
                  </div>
                </div>
                <TeamWinProb
                  winProb={probs.home}
                  canView={canViewWinProb}
                />
              </div>
            </div>
          </div>

          {/* Markets */}
          <div className="col-span-12 md:col-span-6">
            <div className="grid grid-cols-3 gap-3">
              {/* Moneyline */}
              {(selectedMarket === "all" || selectedMarket === "h2h") && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-500 text-center">Moneyline</div>
                  {(() => {
                    const market = game.markets.find((m) => m.market_type === "h2h")
                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                    return (
                      <div className="space-y-1.5">
                        {market.odds.slice(0, 2).map((odds) => {
                          const legKey = `${game.id}-h2h-${odds.outcome}`
                          const isSelected = parlayLegs.has(legKey)
                          return (
                            <button
                              key={odds.id}
                              onClick={() => onToggleParlayLeg(game.id, "h2h", odds.outcome)}
                              className={cn(
                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all",
                                isSelected ? "bg-emerald-500 text-black" : "bg-white/5 text-white hover:bg-white/10"
                              )}
                            >
                              {odds.price}
                            </button>
                          )
                        })}
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* Spread */}
              {(selectedMarket === "all" || selectedMarket === "spreads") && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-500 text-center">Spread</div>
                  {(() => {
                    const market = game.markets.find((m) => m.market_type === "spreads")
                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                    return (
                      <div className="space-y-1.5">
                        {market.odds.slice(0, 2).map((odds) => {
                          const legKey = `${game.id}-spreads-${odds.outcome}`
                          const isSelected = parlayLegs.has(legKey)
                          return (
                            <button
                              key={odds.id}
                              onClick={() => onToggleParlayLeg(game.id, "spreads", odds.outcome)}
                              className={cn(
                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all truncate",
                                isSelected ? "bg-emerald-500 text-black" : "bg-white/5 text-white hover:bg-white/10"
                              )}
                            >
                              {odds.outcome.split(" ").pop()} {odds.price}
                            </button>
                          )
                        })}
                      </div>
                    )
                  })()}
                </div>
              )}

              {/* Total */}
              {(selectedMarket === "all" || selectedMarket === "totals") && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-500 text-center">Total</div>
                  {(() => {
                    const market = game.markets.find((m) => m.market_type === "totals")
                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                    return (
                      <div className="space-y-1.5">
                        {market.odds.slice(0, 2).map((odds) => {
                          const legKey = `${game.id}-totals-${odds.outcome}`
                          const isSelected = parlayLegs.has(legKey)
                          return (
                            <button
                              key={odds.id}
                              onClick={() => onToggleParlayLeg(game.id, "totals", odds.outcome)}
                              className={cn(
                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all truncate",
                                isSelected ? "bg-emerald-500 text-black" : "bg-white/5 text-white hover:bg-white/10"
                              )}
                            >
                              {odds.outcome.includes("Over") ? "O" : "U"} {odds.outcome.match(/[\d.]+/)?.[0]}{" "}
                              {odds.price}
                            </button>
                          )
                        })}
                      </div>
                    )
                  })()}
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="col-span-12 md:col-span-2">
            <div className="flex flex-row md:flex-col gap-2">
              <Link href={generateAnalysisUrl(sport, game.away_team, game.home_team, game.start_time, game.week)} className="flex-1">
                <Button variant="outline" size="sm" className="w-full border-white/20">
                  <Eye className="h-4 w-4 mr-1.5" />
                  Analysis
                </Button>
              </Link>
              <Button size="sm" className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-black">
                <Plus className="h-4 w-4 mr-1.5" />
                Add All
              </Button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}


