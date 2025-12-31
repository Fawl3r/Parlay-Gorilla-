"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useSubscription } from "@/lib/subscription-context"
import { api, GameResponse } from "@/lib/api"
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
  Info
} from "lucide-react"
import { cn } from "@/lib/utils"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"

interface HeatmapCell {
  game_id: string
  game: string
  home_team: string
  away_team: string
  market_type: string
  outcome: string
  odds: string
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

  const sports = ["nfl", "nba", "nhl", "mlb"]

  useEffect(() => {
    loadGames()
  }, [selectedSport])

  async function loadGames() {
    try {
      setLoading(true)
      const gamesData = await api.getGames(selectedSport)
      setGames(gamesData)
      
      // Transform games into heatmap data
      const cells: HeatmapCell[] = []
      
      for (const game of gamesData) {
        for (const market of game.markets) {
          for (const odds of market.odds) {
            // Calculate mock model probability and edge
            // In production, these come from the backend
            const impliedProb = odds.implied_prob
            const modelBoost = (Math.random() - 0.4) * 0.15 // -6% to +9% edge
            const modelProb = Math.max(0.05, Math.min(0.95, impliedProb + modelBoost))
            const edge = (modelProb - impliedProb) * 100
            
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

  // Free users only see top 10 rows
  const displayedData = isPremium ? filteredData : filteredData.slice(0, 10)
  const hasMoreLocked = !isPremium && filteredData.length > 10

  // Get unique games for the grid view
  const uniqueGames = Array.from(new Set(heatmapData.map(c => c.game_id)))
    .map(gameId => heatmapData.find(c => c.game_id === gameId)!)
    .filter(Boolean)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Header Section */}
        <section className="relative py-12 border-b border-white/10 bg-black/40 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Flame className="h-6 w-6 text-orange-400" />
                  <h1 className="text-3xl md:text-4xl font-black text-white">
                    Odds Heatmap
                  </h1>
                </div>
                <p className="text-gray-400">
                  Visualize value edges across all games. Green = positive edge (model prob &gt; implied)
                </p>
              </div>
              
              {!isPremium && (
                <Link href="/premium">
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 cursor-pointer hover:bg-emerald-500/30">
                    <Crown className="h-3 w-3 mr-1" />
                    Upgrade for Full Access
                  </Badge>
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Filters */}
        <section className="py-4 border-b border-white/5 bg-black/20">
          <div className="container mx-auto px-4">
            <div className="flex flex-wrap items-center gap-4">
              {/* Sport Selector */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Sport:</span>
                {sports.map((sport) => (
                  <button
                    key={sport}
                    onClick={() => setSelectedSport(sport)}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium uppercase transition-all",
                      selectedSport === sport
                        ? "bg-emerald-500 text-black"
                        : "bg-white/5 text-gray-400 hover:bg-white/10"
                    )}
                  >
                    {sport}
                  </button>
                ))}
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
        </section>

        {/* Legend */}
        <section className="py-4 bg-black/10">
          <div className="container mx-auto px-4">
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
        </section>

        {/* Heatmap */}
        <section className="py-8">
          <div className="container mx-auto px-4">
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
                  <div className="col-span-2 text-center">Model Prob</div>
                  <div className="col-span-2 text-center">Edge</div>
                  <div className="col-span-2 text-center">Action</div>
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
                      
                      <div className="col-span-2 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-sm text-emerald-400">{(cell.model_prob * 100).toFixed(1)}%</span>
                          <span className="text-xs text-gray-500">vs</span>
                          <span className="text-sm text-gray-400">{(cell.implied_prob * 100).toFixed(1)}%</span>
                        </div>
                      </div>
                      
                      <div className="col-span-2 text-center">
                        <div className="flex items-center justify-center gap-2">
                          <div className={cn("w-8 h-3 rounded", getEdgeColor(cell.edge))} />
                          <span className={cn("text-sm font-bold", getEdgeTextColor(cell.edge))}>
                            {cell.edge > 0 ? "+" : ""}{cell.edge.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      
                      <div className="col-span-2 text-center">
                        <Button
                          size="sm"
                          variant={isSelected ? "default" : "outline"}
                          onClick={() => toggleLeg(cell)}
                          className={cn(
                            "text-xs",
                            isSelected 
                              ? "bg-emerald-500 hover:bg-emerald-600 text-black" 
                              : "border-white/20"
                          )}
                        >
                          <Plus className={cn("h-3 w-3 mr-1", isSelected && "rotate-45")} />
                          {isSelected ? "Added" : "Add"}
                        </Button>
                      </div>
                    </motion.div>
                  )
                })}
                
                {/* Locked Content for Free Users */}
                {hasMoreLocked && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="relative mt-4"
                  >
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/90 z-10" />
                    <div className="p-8 bg-white/[0.02] border border-white/10 rounded-xl text-center relative z-20">
                      <Lock className="h-10 w-10 text-gray-500 mx-auto mb-4" />
                      <h3 className="text-xl font-bold text-white mb-2">
                        {filteredData.length - 10} More Value Plays
                      </h3>
                      <p className="text-gray-400 mb-6">
                        Upgrade to Premium to see all value opportunities
                      </p>
                      <Link href="/premium">
                        <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                          <Crown className="h-4 w-4 mr-2" />
                          Unlock Full Heatmap
                        </Button>
                      </Link>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Top Value Plays Summary */}
        {displayedData.length > 0 && (
          <section className="py-8 bg-black/20 border-t border-white/10">
            <div className="container mx-auto px-4">
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
                      <span className="text-gray-400">Odds: {cell.odds}</span>
                      <span className="text-emerald-400 font-medium">
                        {(cell.model_prob * 100).toFixed(0)}% model prob
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

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
      </main>
      
      <Footer />
      {isCreditUser && !isPremium && (
        <PremiumBlurOverlay
          title="Premium Page"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Odds Heatmap."
        />
      )}
    </div>
  )
}




