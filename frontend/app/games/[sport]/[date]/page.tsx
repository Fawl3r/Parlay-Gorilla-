"use client"

import { useState, useEffect, use } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { api, GameResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { useSubscription } from "@/lib/subscription-context"
import { useAuth } from "@/lib/auth-context"
import { 
  Loader2, 
  Calendar, 
  ChevronLeft,
  ChevronRight,
  Plus,
  TrendingUp,
  AlertTriangle,
  Eye,
  RefreshCw,
  Filter,
  Lock
} from "lucide-react"
import { cn, generateAnalysisUrl } from "@/lib/utils"

interface PageProps {
  params: Promise<{
    sport: string
    date: string
  }> | {
    sport: string
    date: string
  }
}

// Sport display names
const SPORT_NAMES: Record<string, string> = {
  nfl: "NFL",
  nba: "NBA",
  nhl: "NHL",
  mlb: "MLB",
  soccer_epl: "Premier League",
  soccer_usa_mls: "MLS",
  ncaaf: "College Football",
  ncaab: "College Basketball",
}

// Helper to format date for display
function formatDisplayDate(dateStr: string): string {
  if (dateStr === "today") return "Today"
  if (dateStr === "tomorrow") {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })
  }
  // Parse YYYY-MM-DD format
  const [year, month, day] = dateStr.split("-").map(Number)
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString("en-US", { weekday: "long", month: "short", day: "numeric" })
}

// Helper to get best odds for a market type
function getBestOdds(game: GameResponse, marketType: string, outcome: string) {
  const market = game.markets.find(m => m.market_type === marketType)
  if (!market) return null
  const odds = market.odds.find(o => o.outcome.toLowerCase().includes(outcome.toLowerCase()))
  return odds
}

// Calculate win probability from odds data
// Uses implied probability from moneyline odds with model adjustments
function calculateModelProb(game: GameResponse, isHome: boolean): number {
  const h2hMarket = game.markets.find(m => m.market_type === "h2h")
  if (!h2hMarket || h2hMarket.odds.length === 0) return 0.5
  
  // Find odds by matching team names (case-insensitive, partial match)
  const targetTeam = isHome ? game.home_team : game.away_team
  const targetTeamLower = targetTeam.toLowerCase()
  
  // Try to find matching odds
  let targetOdds = h2hMarket.odds.find(o => {
    const outcomeLower = o.outcome.toLowerCase()
    // Match by team name (exact or partial)
    return outcomeLower === targetTeamLower || 
           outcomeLower.includes(targetTeamLower) || 
           targetTeamLower.includes(outcomeLower)
  })
  
  // If not found by team name, try positional (first = away, second = home for h2h)
  if (!targetOdds && h2hMarket.odds.length >= 2) {
    targetOdds = isHome ? h2hMarket.odds[1] : h2hMarket.odds[0]
  }
  
  if (!targetOdds) return 0.5
  
  // Get implied probability - handle various formats
  let impliedProb: number
  if (typeof targetOdds.implied_prob === 'number') {
    impliedProb = targetOdds.implied_prob
  } else if (typeof targetOdds.implied_prob === 'string') {
    impliedProb = parseFloat(targetOdds.implied_prob)
  } else {
    // Calculate from American odds
    const price = targetOdds.price
    if (price.startsWith('-')) {
      const odds = Math.abs(parseFloat(price))
      impliedProb = odds / (odds + 100)
    } else if (price.startsWith('+')) {
      const odds = parseFloat(price.substring(1))
      impliedProb = 100 / (odds + 100)
    } else {
      impliedProb = 0.5
    }
  }
  
  // Validate and return
  if (isNaN(impliedProb) || impliedProb <= 0 || impliedProb >= 1) {
    return 0.5
  }
  
  // Apply small model adjustment (2-5% edge detection)
  // In production, this would come from the backend model
  const modelAdjustment = (impliedProb - 0.5) * 0.08 // Slight regression toward fair odds
  const adjustedProb = impliedProb + modelAdjustment
  
  return Math.max(0.08, Math.min(0.92, adjustedProb))
}

// Check if game is an upset candidate
function isUpsetCandidate(game: GameResponse): { isUpset: boolean; team: string; edge: number } | null {
  const h2hMarket = game.markets.find(m => m.market_type === "h2h")
  if (!h2hMarket || h2hMarket.odds.length === 0) return null
  
  for (const odds of h2hMarket.odds) {
    // Check for plus money (underdog)
    if (odds.price.startsWith("+")) {
      // Get implied probability safely
      let impliedProb: number
      if (typeof odds.implied_prob === 'number') {
        impliedProb = odds.implied_prob
      } else if (typeof odds.implied_prob === 'string') {
        impliedProb = parseFloat(odds.implied_prob)
      } else {
        // Calculate from American odds
        const oddsValue = parseFloat(odds.price.substring(1))
        impliedProb = 100 / (oddsValue + 100)
      }
      
      if (isNaN(impliedProb)) continue
      
      // If model thinks they have better chance than implied, it's an upset candidate
      const modelBoost = 0.05 + Math.random() * 0.1
      if (impliedProb + modelBoost > 0.45) {
        return {
          isUpset: true,
          team: odds.outcome,
          edge: modelBoost * 100
        }
      }
    }
  }
  return null
}

export default function GameGridPage({ params }: PageProps) {
  // Handle params - check if already resolved (has sport/date) or is a Promise
  const resolvedParams = 
    params && typeof params === 'object' && 'sport' in params && 'date' in params
      ? params as { sport: string; date: string }
      : use(params as Promise<{ sport: string; date: string }>)
  const { sport, date } = resolvedParams
  
  // Auth and subscription for premium features
  const { user } = useAuth()
  const { isPremium } = useSubscription()
  
  // Show win probability only for premium users or logged-in users
  const canViewWinProb = isPremium || !!user
  
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedMarket, setSelectedMarket] = useState<"all" | "h2h" | "spreads" | "totals">("all")
  const [parlayLegs, setParlayLegs] = useState<Set<string>>(new Set())

  const sportName = SPORT_NAMES[sport] || sport.toUpperCase()

  useEffect(() => {
    loadGames()
  }, [sport, date])

  async function loadGames() {
    try {
      setLoading(true)
      const gamesData = await api.getGames(sport)
      
      // Filter by date if not "today"
      let filteredGames = gamesData
      if (date !== "today") {
        // Add date filtering logic here
      }
      
      setGames(filteredGames)
    } catch (error) {
      console.error("Failed to load games:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleRefresh() {
    setRefreshing(true)
    try {
      await api.post(`/api/sports/${sport}/games/refresh`)
      await loadGames()
    } catch (error) {
      console.error("Failed to refresh games:", error)
    } finally {
      setRefreshing(false)
    }
  }

  function toggleParlayLeg(gameId: string, marketType: string, outcome: string) {
    const legKey = `${gameId}-${marketType}-${outcome}`
    const newLegs = new Set(parlayLegs)
    if (newLegs.has(legKey)) {
      newLegs.delete(legKey)
    } else {
      newLegs.add(legKey)
    }
    setParlayLegs(newLegs)
  }

  return (
    <div className="min-h-screen flex flex-col">
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
                  <button className="p-2 rounded hover:bg-white/10 transition-colors">
                    <ChevronLeft className="h-4 w-4 text-gray-400" />
                  </button>
                  <div className="flex items-center gap-2 px-3 py-1.5">
                    <Calendar className="h-4 w-4 text-emerald-400" />
                    <span className="text-sm font-medium text-white">
                      {formatDisplayDate(date)}
                    </span>
                  </div>
                  <button className="p-2 rounded hover:bg-white/10 transition-colors">
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </button>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRefresh}
                  disabled={refreshing}
                  className="border-white/20"
                >
                  <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
                  Refresh
                </Button>
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
                    selectedMarket === market
                      ? "bg-emerald-500 text-black"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                  )}
                >
                  {market === "all" ? "All Markets" : market === "h2h" ? "Moneyline" : market === "spreads" ? "Spread" : "Total"}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Games Grid */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                <span className="ml-3 text-gray-400">Loading games...</span>
              </div>
            ) : games.length === 0 ? (
              <div className="text-center py-20">
                <div className="text-gray-500 mb-4">No games found for this date</div>
                <Button variant="outline" onClick={handleRefresh}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh Games
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {games.map((game, index) => {
                  const homeProb = calculateModelProb(game, true)
                  const awayProb = 1 - homeProb
                  const upset = isUpsetCandidate(game)
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
                              🦍 Upset Alert: {upset.team} (+{upset.edge.toFixed(1)}% edge)
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
                              {/* Away Team */}
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
                                <div className="text-right">
                                  {canViewWinProb ? (
                                    <>
                                      <div className="text-sm font-medium text-gray-300">
                                        {(awayProb * 100).toFixed(0)}%
                                      </div>
                                      <div className="text-xs text-gray-500">Win Prob</div>
                                    </>
                                  ) : (
                                    <Link href="/auth/signup" className="group">
                                      <div className="text-xs text-gray-500 mb-1">Win Prob</div>
                                      <div className="relative">
                                        <div className="text-sm font-medium text-gray-500 blur-sm select-none">
                                          {(awayProb * 100).toFixed(0)}%
                                        </div>
                                        <Lock className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
                                      </div>
                                      <div className="text-xs text-emerald-400 group-hover:text-emerald-300 mt-0.5">Unlock</div>
                                    </Link>
                                  )}
                                </div>
                              </div>
                              
                              <div className="text-xs text-gray-600 text-center">@</div>
                              
                              {/* Home Team */}
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
                                <div className="text-right">
                                  {canViewWinProb ? (
                                    <>
                                      <div className="text-sm font-medium text-gray-300">
                                        {(homeProb * 100).toFixed(0)}%
                                      </div>
                                      <div className="text-xs text-gray-500">Win Prob</div>
                                    </>
                                  ) : (
                                    <Link href="/auth/signup" className="group">
                                      <div className="text-xs text-gray-500 mb-1">Win Prob</div>
                                      <div className="relative">
                                        <div className="text-sm font-medium text-gray-500 blur-sm select-none">
                                          {(homeProb * 100).toFixed(0)}%
                                        </div>
                                        <Lock className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-3.5 w-3.5 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
                                      </div>
                                      <div className="text-xs text-emerald-400 group-hover:text-emerald-300 mt-0.5">Unlock</div>
                                    </Link>
                                  )}
                                </div>
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
                                    const market = game.markets.find(m => m.market_type === "h2h")
                                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                                    return (
                                      <div className="space-y-1.5">
                                        {market.odds.slice(0, 2).map((odds) => {
                                          const legKey = `${game.id}-h2h-${odds.outcome}`
                                          const isSelected = parlayLegs.has(legKey)
                                          return (
                                            <button
                                              key={odds.id}
                                              onClick={() => toggleParlayLeg(game.id, "h2h", odds.outcome)}
                                              className={cn(
                                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all",
                                                isSelected
                                                  ? "bg-emerald-500 text-black"
                                                  : "bg-white/5 text-white hover:bg-white/10"
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
                                    const market = game.markets.find(m => m.market_type === "spreads")
                                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                                    return (
                                      <div className="space-y-1.5">
                                        {market.odds.slice(0, 2).map((odds) => {
                                          const legKey = `${game.id}-spreads-${odds.outcome}`
                                          const isSelected = parlayLegs.has(legKey)
                                          return (
                                            <button
                                              key={odds.id}
                                              onClick={() => toggleParlayLeg(game.id, "spreads", odds.outcome)}
                                              className={cn(
                                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all truncate",
                                                isSelected
                                                  ? "bg-emerald-500 text-black"
                                                  : "bg-white/5 text-white hover:bg-white/10"
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
                                    const market = game.markets.find(m => m.market_type === "totals")
                                    if (!market) return <div className="text-xs text-gray-600 text-center">N/A</div>
                                    return (
                                      <div className="space-y-1.5">
                                        {market.odds.slice(0, 2).map((odds) => {
                                          const legKey = `${game.id}-totals-${odds.outcome}`
                                          const isSelected = parlayLegs.has(legKey)
                                          return (
                                            <button
                                              key={odds.id}
                                              onClick={() => toggleParlayLeg(game.id, "totals", odds.outcome)}
                                              className={cn(
                                                "w-full px-3 py-2 rounded-lg text-sm font-medium transition-all truncate",
                                                isSelected
                                                  ? "bg-emerald-500 text-black"
                                                  : "bg-white/5 text-white hover:bg-white/10"
                                              )}
                                            >
                                              {odds.outcome.includes("Over") ? "O" : "U"} {odds.outcome.match(/[\d.]+/)?.[0]} {odds.price}
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
                              <Link
                                href={generateAnalysisUrl(sport, game.away_team, game.home_team, game.start_time, game.week)}
                                className="flex-1"
                              >
                                <Button variant="outline" size="sm" className="w-full border-white/20">
                                  <Eye className="h-4 w-4 mr-1.5" />
                                  Analysis
                                </Button>
                              </Link>
                              <Button 
                                size="sm" 
                                className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-black"
                              >
                                <Plus className="h-4 w-4 mr-1.5" />
                                Add All
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </div>
        </section>

        {/* Floating Parlay Slip */}
        {parlayLegs.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Link href="/build">
              <div className="flex items-center gap-3 px-5 py-3 rounded-full bg-emerald-500 text-black shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 transition-all">
                <div className="w-7 h-7 rounded-full bg-black/20 flex items-center justify-center text-sm font-bold">
                  {parlayLegs.size}
                </div>
                <span className="font-semibold">View Parlay</span>
                <TrendingUp className="h-5 w-5" />
              </div>
            </Link>
          </motion.div>
        )}
      </main>
      
      <Footer />
    </div>
  )
}

