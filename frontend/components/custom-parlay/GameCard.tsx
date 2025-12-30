"use client"

import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import type { GameResponse } from "@/lib/api"
import { TeamBadge } from "@/components/TeamBadge"
import type { SelectedPick } from "@/components/custom-parlay/types"
import { formatGameTime } from "@/components/custom-parlay/uiHelpers"

export function GameCard({
  game,
  onSelectPick,
  selectedPicks,
}: {
  game: GameResponse
  onSelectPick: (pick: SelectedPick) => void
  selectedPicks: SelectedPick[]
}) {
  const [expanded, setExpanded] = useState(false)

  const isPickSelected = (gameId: string, marketType: string, pick: string) => {
    return selectedPicks.some(
      (p) => p.game_id === gameId && p.market_type === (marketType as any) && p.pick.toLowerCase() === pick.toLowerCase()
    )
  }

  const moneylineMarket = game.markets.find((m) => m.market_type === "h2h")
  const spreadsMarket = game.markets.find((m) => m.market_type === "spreads")
  const totalsMarket = game.markets.find((m) => m.market_type === "totals")

  const handlePickSelect = (
    marketType: "h2h" | "spreads" | "totals",
    pick: string,
    odds: string,
    point: number | undefined,
    marketId: string | undefined,
    displayTeamName?: string
  ) => {
    const displayName = marketType === "spreads" ? String(displayTeamName || pick) : pick
    const pickDisplay =
      marketType === "h2h"
        ? `${displayName} ML`
        : marketType === "spreads"
        ? `${displayName} ${point !== undefined ? (point > 0 ? `+${point}` : point) : ""}`
        : `${displayName.toUpperCase()} ${point ?? ""}`

    onSelectPick({
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
    })
  }

  return (
    <motion.div
      layout
      className="bg-black/40 border border-white/10 rounded-xl overflow-hidden hover:border-white/20 transition-colors"
    >
      <div className="p-3 sm:p-4 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <TeamBadge teamName={game.away_team} sport={game.sport} size="sm" />
              <span className="text-white font-medium">{game.away_team}</span>
            </div>
            <span className="text-white/40">@</span>
            <div className="flex items-center gap-2">
              <TeamBadge teamName={game.home_team} sport={game.sport} size="sm" />
              <span className="text-white font-medium">{game.home_team}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
            <span className="text-white/60 text-sm">{formatGameTime(game.start_time)}</span>
            <motion.span animate={{ rotate: expanded ? 180 : 0 }} className="text-white/40">
              ▼
            </motion.span>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10"
          >
            <div className="p-3 sm:p-4 space-y-3 sm:space-y-4">
              {moneylineMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Moneyline</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {moneylineMarket.odds.map((odd) => {
                      const isHome =
                        odd.outcome.toLowerCase().includes("home") ||
                        odd.outcome.toLowerCase().includes(game.home_team.toLowerCase())
                      const teamName = isHome ? game.home_team : game.away_team
                      const selected = isPickSelected(game.id, "h2h", teamName)

                      return (
                        <button
                          key={odd.id}
                          onClick={() =>
                            handlePickSelect("h2h", teamName, odd.price, undefined, moneylineMarket.id, teamName)
                          }
                          className={`p-2.5 sm:p-3 rounded-lg border transition-all min-h-[60px] sm:min-h-[auto] ${
                            selected
                              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                              : "bg-white/5 border-white/10 text-white hover:bg-white/10"
                          }`}
                        >
                          <div className="text-sm font-medium">{teamName}</div>
                          <div className="text-lg font-bold">{odd.price}</div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {spreadsMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Spread</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {spreadsMarket.odds.map((odd, index) => {
                      const outcomeLower = odd.outcome.toLowerCase()
                      const homeTeamLower = game.home_team.toLowerCase()
                      const awayTeamLower = game.away_team.toLowerCase()

                      const containsHomeTeam = outcomeLower.includes(homeTeamLower)
                      const containsAwayTeam = outcomeLower.includes(awayTeamLower)
                      const containsHomeKeyword = outcomeLower.includes("home")
                      const containsAwayKeyword = outcomeLower.includes("away")

                      let teamName: string
                      let pickValue: "home" | "away"

                      if (containsHomeTeam && !containsAwayTeam) {
                        teamName = game.home_team
                        pickValue = "home"
                      } else if (containsAwayTeam && !containsHomeTeam) {
                        teamName = game.away_team
                        pickValue = "away"
                      } else if (containsHomeKeyword && !containsAwayKeyword) {
                        teamName = game.home_team
                        pickValue = "home"
                      } else if (containsAwayKeyword && !containsHomeKeyword) {
                        teamName = game.away_team
                        pickValue = "away"
                      } else {
                        if (index === 0) {
                          teamName = game.home_team
                          pickValue = "home"
                        } else {
                          teamName = game.away_team
                          pickValue = "away"
                        }
                      }

                      const point = parseFloat(odd.outcome.match(/[+-]?\d+\.?\d*/)?.[0] || "0")
                      const selected = isPickSelected(game.id, "spreads", pickValue)

                      return (
                        <button
                          key={odd.id}
                          onClick={() =>
                            handlePickSelect("spreads", pickValue, odd.price, point, spreadsMarket.id, teamName)
                          }
                          className={`p-2.5 sm:p-3 rounded-lg border transition-all min-h-[60px] sm:min-h-[auto] ${
                            selected
                              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                              : "bg-white/5 border-white/10 text-white hover:bg-white/10"
                          }`}
                        >
                          <div className="text-sm font-medium">{teamName}</div>
                          <div className="text-lg font-bold">
                            {point > 0 ? `+${point}` : point} ({odd.price})
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}

              {totalsMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Total</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {totalsMarket.odds.map((odd) => {
                      const isOver = odd.outcome.toLowerCase().includes("over")
                      const point = parseFloat(odd.outcome.match(/\d+\.?\d*/)?.[0] || "0")
                      const pickValue = isOver ? "over" : "under"
                      const selected = isPickSelected(game.id, "totals", pickValue)

                      return (
                        <button
                          key={odd.id}
                          onClick={() =>
                            handlePickSelect("totals", pickValue, odd.price, point, totalsMarket.id)
                          }
                          className={`p-2.5 sm:p-3 rounded-lg border transition-all min-h-[60px] sm:min-h-[auto] ${
                            selected
                              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
                              : "bg-white/5 border-white/10 text-white hover:bg-white/10"
                          }`}
                        >
                          <div className="text-sm font-medium">{isOver ? "Over" : "Under"}</div>
                          <div className="text-lg font-bold">
                            {point} ({odd.price})
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}


