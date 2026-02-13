"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { Eye, Lock } from "lucide-react"

import type { GameResponse } from "@/lib/api"
import { generateAnalysisUrl } from "@/lib/utils"
import { getTeamDisplayName } from "@/components/games/teamDisplayName"
import { Button } from "@/components/ui/button"
import { calculateModelWinProbabilities } from "@/components/games/gamesOddsUtils"

type Props = {
  sport: string
  games: GameResponse[]
  canViewWinProb: boolean
}

/**
 * Compact table layout that matches the game analytics page so dashboard games
 * "show properly" like in Insights / analytics.
 */
export function DashboardGamesTable({ sport, games, canViewWinProb }: Props) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-12 gap-2 px-4 py-3 text-xs font-medium text-gray-500 border-b border-white/10 bg-black/20 rounded-t-lg">
        <div className="col-span-5 sm:col-span-4">Matchup</div>
        <div className="col-span-3 sm:col-span-2 text-center">Time</div>
        <div className="col-span-2 text-center">Win Prob</div>
        <div className="col-span-2 sm:col-span-4 text-right">Action</div>
      </div>
      {games.map((game, index) => {
        const probs = calculateModelWinProbabilities(game)
        const maxProb = probs
          ? Math.max(probs.home, probs.away)
          : null
        const gameTime = new Date(game.start_time)
        const awayDisplay = getTeamDisplayName(game.away_team, game.sport)
        const homeDisplay = getTeamDisplayName(game.home_team, game.sport)

        return (
          <motion.div
            key={game.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.02 }}
            className="grid grid-cols-12 gap-2 px-4 py-3 rounded-lg items-center bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
          >
            <div className="col-span-5 sm:col-span-4">
              <div className="text-sm font-semibold text-white">
                {awayDisplay} @ {homeDisplay}
              </div>
              <div className="text-xs text-gray-500">{game.sport.toUpperCase()}</div>
            </div>
            <div className="col-span-3 sm:col-span-2 text-center text-xs text-gray-400">
              {gameTime.toLocaleDateString(undefined, {
                month: "short",
                day: "numeric",
              })}{" "}
              {gameTime.toLocaleTimeString([], {
                hour: "numeric",
                minute: "2-digit",
              })}
            </div>
            <div className="col-span-2 text-center">
              {maxProb !== null ? (
                canViewWinProb ? (
                  <span className="text-sm font-medium text-gray-300">
                    {(maxProb * 100).toFixed(0)}%
                  </span>
                ) : (
                  <Link href="/auth/signup" className="flex items-center justify-center gap-1 text-gray-500 hover:text-emerald-400">
                    <Lock className="h-3 w-3" />
                    <span className="text-xs">Unlock</span>
                  </Link>
                )
              ) : (
                <span className="text-xs text-gray-500">—</span>
              )}
            </div>
            <div className="col-span-2 sm:col-span-4 text-right">
              <Link
                href={generateAnalysisUrl(
                  sport,
                  game.away_team,
                  game.home_team,
                  game.start_time,
                  game.week
                )}
              >
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/20 hover:bg-white/10 text-xs"
                >
                  <Eye className="h-3 w-3 mr-1.5" />
                  View
                </Button>
              </Link>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
