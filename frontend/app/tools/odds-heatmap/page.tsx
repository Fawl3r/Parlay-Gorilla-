"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { DashboardAccountCommandCenter } from "@/components/usage/DashboardAccountCommandCenter"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useSubscription } from "@/lib/subscription-context"
import { api, GameResponse } from "@/lib/api"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"
import { 
  Flame,
  Loader2,
  Filter,
  Plus,
  Crown,
  Lock,
  TrendingUp,
  AlertTriangle,
  RefreshCw,
  Info,
  Check
} from "lucide-react"
import { cn } from "@/lib/utils"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"

type SportOption = { id: string; label: string }

const SPORTS: SportOption[] = [
  { id: "nfl", label: "NFL" },
  { id: "ncaaf", label: "NCAAF" },
  { id: "nba", label: "NBA" },
  { id: "nhl", label: "NHL" },
  { id: "mlb", label: "MLB" },
  { id: "ncaab", label: "NCAAB" },
  { id: "epl", label: "EPL" },
  { id: "laliga", label: "La Liga" },
  { id: "mls", label: "MLS" },
]

interface HeatmapCell {
  game_id: string
  game: string
  home_team: string
  away_team: string
  market_type: string
  outcome: string
  odds: string
  book: string
  implied_prob: number
  model_prob: number
  edge: number
  is_upset: boolean
}

// Helper to calculate edge color
function getEdgeColor(edge: number): string {
  if (edge >= 5) return "bg-emerald-500"
  if (edge >= 3) return "bg-emerald-400"
  if (edge >= 1) return "bg-emerald-300"
  if (edge >= 0) return "bg-gray-500"
  if (edge >= -2) return "bg-red-300"
  if (edge >= -5) return "bg-red-400"
  return "bg-red-500"
}

function getEdgeTextColor(edge: number): string {
  if (edge >= 3) return "text-emerald-400"
  if (edge >= 0) return "text-gray-300"
  return "text-red-400"
}

export default function OddsHeatmapPage() {
  return (
    <ProtectedRoute>
      <OddsHeatmapContent />
    </ProtectedRoute>
  )
}

function OddsHeatmapContent() {
  const { isPremium, isCreditUser } = useSubscription()
  const [games, setGames] = useState<GameResponse[]>([])
  const [heatmapData, setHeatmapData] = useState<HeatmapCell[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSport, setSelectedSport] = useState("nfl")
  const [selectedMarket, setSelectedMarket] = useState<"all" | "h2h" | "spreads" | "totals">("all")
  const [parlayLegs, setParlayLegs] = useState<Set<string>>(new Set())
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})

  // Fetch in-season status for all sports
  useEffect(() => {
    let cancelled = false
    async function loadSportsStatus() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        const map: Record<string, boolean> = {}
        for (const s of sportsList) {
          map[s.slug] = s.in_season !== false
        }
        setInSeasonBySport(map)
      } catch {
        if (!cancelled) setInSeasonBySport({})
      }
    }
    if (isPremium) {
      loadSportsStatus()
    }
    return () => {
      cancelled = true
    }
  }, [isPremium])

  // Auto-select first available sport
  useEffect(() => {
    if (Object.keys(inSeasonBySport).length === 0) return
    const firstAvailable = SPORTS.find((s) => inSeasonBySport[s.id] !== false)?.id
    if (firstAvailable && firstAvailable !== selectedSport) setSelectedSport(firstAvailable)
  }, [inSeasonBySport, selectedSport])

  useEffect(() => {
    if (isPremium) {
      loadGames()
    } else {
      setLoading(false)
    }
  }, [selectedSport, isPremium])

  // Helper function to calculate implied probability from American odds
  function calculateImpliedProbability(price: string, providedImpliedProb?: number): number {
    // Use provided value if valid
    if (typeof providedImpliedProb === 'number' && !isNaN(providedImpliedProb) && providedImpliedProb > 0 && providedImpliedProb < 1) {
      return providedImpliedProb
    }
    
    // Calculate from American odds
    const cleaned = String(price || "").trim().replace("−", "-")
    const american = Number(cleaned.replace("+", ""))
    
    if (!isFinite(american) || american === 0) {
      return 0.5 // Default to 50% if can't parse
    }
    
    if (american < 0) {
      // Negative odds: -150 means 150/(150+100) = 0.6
      const odds = Math.abs(american)
      return odds / (odds + 100)
    } else {
      // Positive odds: +150 means 100/(150+100) = 0.4
      return 100 / (american + 100)
    }
  }

  async function loadGames() {
    try {
      setLoading(true)
      
      // Fetch games and probabilities in parallel
      const [gamesData, probabilitiesData] = await Promise.all([
        api.getGames(selectedSport),
        api.getHeatmapProbabilities(selectedSport).catch((err) => {
          console.warn("Failed to fetch heatmap probabilities, using fallback:", err)
          return []
        })
      ])
      
      setGames(gamesData)
      
      // Create a map of game_id -> probabilities for quick lookup
      const probMap = new Map<string, typeof probabilitiesData[0]>()
      for (const prob of probabilitiesData) {
        probMap.set(prob.game_id, prob)
      }
      
      // Transform games into heatmap data
      const cells: HeatmapCell[] = []
      
      for (const game of gamesData) {
        const gameProbs = probMap.get(game.id)
        
        for (const market of game.markets) {
          for (const odds of market.odds) {
            // Calculate implied probability (with fallback to calculation from price)
            const impliedProb = calculateImpliedProbability(odds.price, odds.implied_prob)
            
            if (!isFinite(impliedProb) || impliedProb <= 0 || impliedProb >= 1) {
              console.warn("Invalid implied probability for", game.id, market.market_type, odds.outcome, {
                price: odds.price,
                impliedProb
              })
              continue // Skip invalid entries
            }
            
            // Determine model probability based on market type
            let modelProb: number | null = null
            
            if (market.market_type === "h2h") {
              // H2H: Use home_win_prob or away_win_prob based on outcome
              if (gameProbs) {
                const outcomeLower = odds.outcome.toLowerCase()
                if (outcomeLower.includes(game.home_team.toLowerCase()) || outcomeLower === "home") {
                  modelProb = gameProbs.home_win_prob
                } else if (outcomeLower.includes(game.away_team.toLowerCase()) || outcomeLower === "away") {
                  modelProb = gameProbs.away_win_prob
                }
              }
            } else if (market.market_type === "spreads") {
              // Spreads: Use spread_confidence converted to probability (0-100 -> 0-1)
              if (gameProbs?.spread_confidence !== null && gameProbs?.spread_confidence !== undefined) {
                // Convert confidence (0-100) to probability (0.05-0.95)
                const confidence = gameProbs.spread_confidence
                modelProb = Math.max(0.05, Math.min(0.95, confidence / 100))
              }
            } else if (market.market_type === "totals") {
              // Totals: Use total_confidence converted to probability (0-100 -> 0-1)
              if (gameProbs?.total_confidence !== null && gameProbs?.total_confidence !== undefined) {
                // Convert confidence (0-100) to probability (0.05-0.95)
                const confidence = gameProbs.total_confidence
                modelProb = Math.max(0.05, Math.min(0.95, confidence / 100))
              }
            }
            
            // Fallback: If no model probability available, use implied probability
            if (modelProb === null || !isFinite(modelProb)) {
              modelProb = impliedProb
            }
            
            // Ensure modelProb is within valid range
            modelProb = Math.max(0.05, Math.min(0.95, modelProb))
            
            const edge = (modelProb - impliedProb) * 100
            
            // Validate all values are numbers
            if (!isFinite(modelProb) || !isFinite(edge)) {
              console.warn("Invalid probability values for", game.id, market.market_type, odds.outcome, {
                impliedProb,
                modelProb,
                edge,
                price: odds.price
              })
              continue // Skip invalid entries
            }
            
            // Determine if upset candidate
            const isUpset = odds.price.startsWith("+") && edge > 2
            
            cells.push({
              game_id: game.id,
              game: `${game.away_team} @ ${game.home_team}`,
              home_team: game.home_team,
              away_team: game.away_team,
              market_type: market.market_type,
              outcome: odds.outcome,
              odds: odds.price,
              book: market.book || "Unknown",
              implied_prob: impliedProb,
              model_prob: modelProb,
              edge: edge,
              is_upset: isUpset
            })
          }
        }
      }
      
      // Sort by edge (highest first)
      cells.sort((a, b) => b.edge - a.edge)
      setHeatmapData(cells)
    } catch (error) {
      console.error("Failed to load games:", error)
    } finally {
      setLoading(false)
    }
  }

  function toggleLeg(cell: HeatmapCell) {
    const legKey = `${cell.game_id}-${cell.market_type}-${cell.outcome}`
    const newLegs = new Set(parlayLegs)
    if (newLegs.has(legKey)) {
      newLegs.delete(legKey)
    } else {
      newLegs.add(legKey)
    }
    setParlayLegs(newLegs)
  }

  const filteredData = heatmapData.filter(cell => 
    selectedMarket === "all" || cell.market_type === selectedMarket
  )

  // Premium-only feature
  const displayedData = filteredData

  // Get unique games for the grid view
  const uniqueGames = Array.from(new Set(heatmapData.map(c => c.game_id)))
    .map(gameId => heatmapData.find(c => c.game_id === gameId)!)
    .filter(Boolean)

  // Show locked UI for non-premium users
  if (!isPremium) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
          <AnimatedBackground variant="intense" />
          <div className="flex-1 relative z-10 flex flex-col">
            <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
              <div className="container mx-auto px-2 sm:px-4 py-3 sm:py-4 md:py-5">
                <div className="mb-3 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                  <BalanceStrip compact />
                </div>
                <DashboardAccountCommandCenter />
              </div>
            </section>

            <section className="flex-1">
              <div className="container mx-auto px-2 sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <Flame className="h-8 w-8 text-emerald-400" />
                    <h1 className="text-3xl md:text-4xl font-black text-white">
                      Odds Heatmap
                    </h1>
                    <Lock className="h-6 w-6 text-gray-500" />
                  </div>
                  <p className="text-gray-400">
                    Visualize value edges across all games. Green = positive edge (model prob &gt; implied)
                  </p>
                </div>

                <div className="max-w-2xl mx-auto text-center py-20">
                  <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
                    <Lock className="h-10 w-10 text-emerald-400" />
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-4">
                    Premium Feature
                  </h2>
                  <p className="text-lg text-gray-400 mb-8">
                    The Odds Heatmap is available exclusively for Premium subscribers. Upgrade to unlock real-time model probabilities, edge calculations, and comprehensive odds analysis across all sportsbooks.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link href="/pricing">
                      <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold">
                        <Crown className="h-5 w-5 mr-2" />
                        Upgrade to Premium
                      </Button>
                    </Link>
                    <Link href="/app">
                      <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10">
                        Back to Dashboard
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </section>
          </div>
        </div>
        {isCreditUser && (
          <PremiumBlurOverlay
            title="Premium Page"
            message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Odds Heatmap."
          />
        )}
      </DashboardLayout>
    )
  }

  // Premium users see the full heatmap
  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
        <AnimatedBackground variant="intense" />
        <div className="flex-1 relative z-10 flex flex-col">
          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-3 sm:py-4 md:py-5">
              <div className="mb-3 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                <BalanceStrip compact />
              </div>
              <DashboardAccountCommandCenter />
            </div>
          </section>

          <section className="flex-1">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <Flame className="h-8 w-8 text-emerald-400" />
                    <h1 className="text-3xl md:text-4xl font-black text-white">
                      Odds Heatmap
                    </h1>
                  </div>
                  <p className="text-gray-400">
                    Visualize value edges across all games. Green = positive edge (model prob &gt; implied)
                  </p>
                </div>

                {/* Filters */}
                <div className="py-4 border-b border-white/5 bg-black/20 rounded-lg px-4">
            <div className="flex flex-wrap items-center gap-4">
              {/* Sport Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Sport:</span>
                {SPORTS.map((sport) => {
                  const isComingSoon = sportsUiPolicy.isComingSoon(sport.id)
                  const isDisabled = inSeasonBySport[sport.id] === false || isComingSoon
                  const disabledLabel = isComingSoon ? "Coming Soon" : "Not in season"

                  return (
                    <button
                      key={sport.id}
                      onClick={() => setSelectedSport(sport.id)}
                      disabled={isDisabled}
                      className={cn(
                        "px-3 py-1.5 rounded-full text-xs font-medium uppercase transition-all",
                        selectedSport === sport.id
                          ? "bg-emerald-500 text-black"
                          : isDisabled
                            ? "bg-white/5 text-gray-500 cursor-not-allowed opacity-50"
                            : "bg-white/5 text-gray-400 hover:bg-white/10"
                      )}
                      title={isDisabled ? disabledLabel : undefined}
                    >
                      {sport.label}
                      {isDisabled && (
                        <span className="ml-2 text-[10px] font-bold uppercase">{disabledLabel}</span>
                      )}
                    </button>
                  )
                })}
              </div>
              
              <div className="h-6 w-px bg-white/10" />
              
              {/* Market Filter */}
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-500" />
                {(["all", "h2h", "spreads", "totals"] as const).map((market) => (
                  <button
                    key={market}
                    onClick={() => setSelectedMarket(market)}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                      selectedMarket === market
                        ? "bg-white/20 text-white"
                        : "bg-white/5 text-gray-400 hover:bg-white/10"
                    )}
                  >
                    {market === "all" ? "All" : market === "h2h" ? "ML" : market === "spreads" ? "Spread" : "Total"}
                  </button>
                ))}
              </div>
              
              <div className="ml-auto flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadGames}
                  disabled={loading}
                  className="border-white/20"
                >
                  <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                  Refresh
                </Button>
              </div>
                </div>
              </div>

                {/* Top Value Plays Summary */}
                {displayedData.length > 0 && (
                  <div className="py-6 bg-black/20 border border-white/10 rounded-lg px-4">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-emerald-400" />
                      Top Value Plays
                    </h2>
                    
                    <div className="grid md:grid-cols-3 gap-4">
                      {displayedData.slice(0, 3).map((cell, index) => (
                        <div
                          key={index}
                          className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <div className="font-bold text-white">{cell.outcome}</div>
                              <div className="text-sm text-gray-400">{cell.game}</div>
                            </div>
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                              +{cell.edge.toFixed(1)}% edge
                            </Badge>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex flex-col gap-1">
                              <span className="text-gray-400">Odds: {cell.odds}</span>
                              <span className="text-xs text-gray-500">Book: {cell.book}</span>
                            </div>
                            <span className="text-emerald-400 font-medium">
                              {(cell.model_prob * 100).toFixed(0)}% model prob
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Legend */}
                <div className="py-4 bg-black/10 rounded-lg px-4">
                  <div className="flex items-center gap-6">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <Info className="h-4 w-4" />
                      <span>Edge Legend:</span>
                    </div>
                    <div className="flex items-center gap-4">
                      {[
                        { label: "+5%+", color: "bg-emerald-500" },
                        { label: "+3%", color: "bg-emerald-400" },
                        { label: "+1%", color: "bg-emerald-300" },
                        { label: "0%", color: "bg-gray-500" },
                        { label: "-2%", color: "bg-red-300" },
                        { label: "-5%", color: "bg-red-500" },
                      ].map((item) => (
                        <div key={item.label} className="flex items-center gap-1.5">
                          <div className={cn("w-4 h-4 rounded", item.color)} />
                          <span className="text-xs text-gray-400">{item.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Heatmap */}
                <div className="py-6">
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                <span className="ml-3 text-gray-400">Loading odds data...</span>
              </div>
            ) : displayedData.length === 0 ? (
              <div className="text-center py-20">
                <Flame className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No Data Available</h3>
                <p className="text-gray-400">Try selecting a different sport or market</p>
              </div>
            ) : (
              <div className="space-y-2">
                {/* Table Header */}
                <div className="grid grid-cols-12 gap-2 px-4 py-2 text-xs font-medium text-gray-500 border-b border-white/10">
                  <div className="col-span-3">Game</div>
                  <div className="col-span-2">Pick</div>
                  <div className="col-span-1 text-center">Odds</div>
                  <div className="col-span-1 text-center">Book</div>
                  <div className="col-span-2 text-center">Model Prob</div>
                  <div className="col-span-2 text-center">Edge</div>
                  <div className="col-span-1 text-center">Action</div>
                </div>
                
                {/* Rows */}
                {displayedData.map((cell, index) => {
                  const legKey = `${cell.game_id}-${cell.market_type}-${cell.outcome}`
                  const isSelected = parlayLegs.has(legKey)
                  
                  return (
                    <motion.div
                      key={legKey}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.02 }}
                      className={cn(
                        "grid grid-cols-12 gap-2 px-4 py-3 rounded-lg items-center transition-all",
                        isSelected ? "bg-emerald-500/10 border border-emerald-500/30" : "bg-white/[0.02] hover:bg-white/[0.04]"
                      )}
                    >
                      <div className="col-span-3">
                        <div className="text-sm font-medium text-white truncate">{cell.game}</div>
                        <div className="text-xs text-gray-500 capitalize">{cell.market_type === "h2h" ? "Moneyline" : cell.market_type}</div>
                      </div>
                      
                      <div className="col-span-2">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm text-white truncate">{cell.outcome}</span>
                          {cell.is_upset && (
                            <span className="text-purple-400 text-xs">🦍</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="col-span-1 text-center">
                        <span className="text-sm font-medium text-white">{cell.odds}</span>
                      </div>
                      
                      <div className="col-span-1 text-center">
                        <span className="text-xs text-gray-400 truncate block" title={cell.book}>
                          {cell.book}
                        </span>
                      </div>
                      
                      <div className="col-span-2 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-sm text-emerald-400">
                            {isFinite(cell.model_prob) ? (cell.model_prob * 100).toFixed(1) : "N/A"}%
                          </span>
                          <span className="text-xs text-gray-500">vs</span>
                          <span className="text-sm text-gray-400">
                            {isFinite(cell.implied_prob) ? (cell.implied_prob * 100).toFixed(1) : "N/A"}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="col-span-2 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className={cn("w-8 h-3 rounded", getEdgeColor(cell.edge))} />
                          <span className={cn("text-sm font-bold", getEdgeTextColor(cell.edge))}>
                            {isFinite(cell.edge) 
                              ? `${cell.edge > 0 ? "+" : ""}${cell.edge.toFixed(1)}%`
                              : "N/A"
                            }
                          </span>
                        </div>
                      </div>
                      
                      <div className="col-span-1 text-center">
                        <Button
                          size="sm"
                          variant={isSelected ? "default" : "outline"}
                          onClick={() => toggleLeg(cell)}
                          className={cn(
                            "text-xs w-full",
                            isSelected 
                              ? "bg-emerald-500 hover:bg-emerald-600 text-black" 
                              : "border-white/20 hover:bg-white/10"
                          )}
                        >
                          {isSelected ? <Check className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                        </Button>
                      </div>
                    </motion.div>
                  )
                })}
                
                  </div>
                )}
                </div>

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
                        <span className="font-semibold">Build Parlay</span>
                        <TrendingUp className="h-5 w-5" />
                      </div>
                    </Link>
                  </motion.div>
                )}
              </motion.div>
            </div>
          </section>
        </div>
      </div>
      {isCreditUser && !isPremium && (
        <PremiumBlurOverlay
          title="Premium Page"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Odds Heatmap."
        />
      )}
    </DashboardLayout>
  )
}




