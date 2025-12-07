"use client"

import { GameResponse } from "@/lib/api"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { OddsDisplay } from "@/components/OddsDisplay"
import { TeamLogo } from "@/components/TeamLogo"
import { formatDate } from "@/lib/utils"
import { Calendar } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

interface GameCardProps {
  game: GameResponse
  selectedSportsbook?: string
}

export function GameCard({ game, selectedSportsbook = "all" }: GameCardProps) {
  const isLive = game.status === "live" || game.status === "inprogress"
  const isCompleted = game.status === "completed" || game.status === "final"

  // Filter markets by selected sportsbook
  const filteredMarkets =
    selectedSportsbook === "all"
      ? game.markets
      : game.markets.filter((market) => market.book === selectedSportsbook)

  return (
    <Card className="group relative overflow-hidden border-2 border-primary/30 bg-card/95 backdrop-blur-sm transition-all duration-300 hover:border-primary/60 hover:shadow-xl card-elevated hover:card-elevated-hover neon-glow-effect">
      {isLive && (
        <div className="absolute right-0 top-0 z-10 rounded-bl-xl bg-destructive px-4 py-2 shadow-xl scoreboard">
          <span className="flex items-center gap-2 text-xs font-bold text-destructive-foreground">
            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-destructive-foreground" />
            LIVE
          </span>
        </div>
      )}
      <CardHeader className="pb-4">
        {/* Team Matchup Visual - Premium Design */}
        <div className="mb-6 flex items-center justify-center gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex flex-col items-center gap-3"
          >
            <div className="relative">
              <TeamLogo teamName={game.away_team} sport={game.sport} size="lg" />
              <div className="absolute -inset-1 rounded-full bg-primary/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span className="text-xs font-semibold text-foreground max-w-[100px] text-center truncate">
              {game.away_team}
            </span>
          </motion.div>
          
          <div className="flex flex-col items-center gap-2">
            <motion.div
              className="relative"
              animate={{ opacity: [0.8, 1, 0.8], scale: [1, 1.05, 1] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <div className="absolute inset-0 bg-primary/30 blur-lg rounded-full" />
              <div className="relative text-2xl font-extrabold gradient-text">
                VS
              </div>
            </motion.div>
            <div className="h-1 w-20 bg-gradient-to-r from-transparent via-primary to-transparent" />
          </div>
          
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex flex-col items-center gap-3"
          >
            <div className="relative">
              <TeamLogo teamName={game.home_team} sport={game.sport} size="lg" />
              <div className="absolute -inset-1 rounded-full bg-accent/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <span className="text-xs font-semibold text-foreground max-w-[100px] text-center truncate">
              {game.home_team}
            </span>
          </motion.div>
        </div>

        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(game.start_time)}
              </div>
              {game.week && (
                <Badge variant="outline" className="text-xs">
                  Week {game.week}
                </Badge>
              )}
              {game.sport && (
                <Badge variant="outline" className="text-xs">
                  {game.sport.toUpperCase()}
                </Badge>
              )}
            </div>
          </div>
          <Badge
            variant={isLive ? "destructive" : isCompleted ? "secondary" : "outline"}
            className={cn(
              "shrink-0 text-xs uppercase",
              isLive && "animate-pulse"
            )}
          >
            {game.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <OddsDisplay markets={filteredMarkets} />
      </CardContent>
    </Card>
  )
}

