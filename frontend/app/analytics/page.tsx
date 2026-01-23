"use client"

import { useEffect, useState, useMemo } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Loader2,
  BarChart3,
  TrendingUp,
  Target,
  Info,
  Star,
  Zap,
  Flame,
  Lock,
  Filter,
  Calendar,
  ArrowUpDown,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { api, type AnalyticsResponse, type AnalyticsGameResponse } from "@/lib/api"
import { sportsUiPolicy, type SportsListItem } from "@/lib/sports/SportsUiPolicy"

type MarketType = "moneyline" | "spread" | "totals"
type SortOption = "traffic" | "confidence" | "time"

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <AnalyticsContent />
    </ProtectedRoute>
  )
}

function AnalyticsContent() {
  const [data, setData] = useState<AnalyticsResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedSport, setSelectedSport] = useState<string | undefined>(undefined)
  const [marketType, setMarketType] = useState<MarketType>("moneyline")
  const [sortBy, setSortBy] = useState<SortOption>("traffic")
  const [filterHighConfidence, setFilterHighConfidence] = useState(false)
  const [filterFullAnalysis, setFilterFullAnalysis] = useState(false)
  const [filterTrending, setFilterTrending] = useState(false)
  const [availableSports, setAvailableSports] = useState<SportsListItem[]>([])

  // Load available sports
  useEffect(() => {
    let cancelled = false
    async function loadSports() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        const visibleSports = sportsUiPolicy.filterVisible(sportsList)
        setAvailableSports(visibleSports)
      } catch (err) {
        console.error("Failed to load sports list:", err)
        if (!cancelled) setAvailableSports([])
      }
    }
    loadSports()
    return () => {
      cancelled = true
    }
  }, [])

  // Load analytics data
  useEffect(() => {
    let cancelled = false
    async function loadData() {
      try {
        setLoading(true)
        setError(null)
        const response = await api.getAnalyticsGames(selectedSport, marketType)
        if (cancelled) return
        setData(response)
      } catch (err) {
        console.error("Failed to load analytics:", err)
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load analytics")
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadData()
    return () => {
      cancelled = true
    }
  }, [selectedSport, marketType])

  // Filter and sort games
  const filteredAndSortedGames = useMemo(() => {
    if (!data) return []

    let games = [...data.games]

    // Apply filters
    if (filterHighConfidence) {
      games = games.filter((game) => {
        if (marketType === "moneyline") {
          return (game.home_win_prob && game.home_win_prob >= 0.7) || (game.away_win_prob && game.away_win_prob >= 0.7)
        } else if (marketType === "spread") {
          return game.spread_confidence !== null && game.spread_confidence >= 70
        } else if (marketType === "totals") {
          return game.total_confidence !== null && game.total_confidence >= 70
        }
        return false
      })
    }

    if (filterFullAnalysis) {
      games = games.filter((game) => game.has_cached_analysis)
    }

    if (filterTrending) {
      games = games.filter((game) => game.is_trending)
    }

    // Apply sorting
    games.sort((a, b) => {
      if (sortBy === "traffic") {
        return b.traffic_score - a.traffic_score
      } else if (sortBy === "confidence") {
        if (marketType === "moneyline") {
          const aMax = Math.max(a.home_win_prob || 0, a.away_win_prob || 0)
          const bMax = Math.max(b.home_win_prob || 0, b.away_win_prob || 0)
          return bMax - aMax
        } else if (marketType === "spread") {
          return (b.spread_confidence || 0) - (a.spread_confidence || 0)
        } else {
          return (b.total_confidence || 0) - (a.total_confidence || 0)
        }
      } else {
        // Sort by time
        return new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
      }
    })

    return games
  }, [data, marketType, sortBy, filterHighConfidence, filterFullAnalysis, filterTrending])

  // Get market score for display
  function getMarketScore(game: AnalyticsGameResponse): { value: number; label: string; isProbability: boolean } {
    if (marketType === "moneyline") {
      const homeProb = game.home_win_prob || 0.5
      const awayProb = game.away_win_prob || 0.5
      const maxProb = Math.max(homeProb, awayProb)
      return {
        value: maxProb,
        label: `${(maxProb * 100).toFixed(1)}%`,
        isProbability: true,
      }
    } else if (marketType === "spread") {
      const conf = game.spread_confidence || 0
      return {
        value: conf,
        label: `${conf.toFixed(0)}`,
        isProbability: false,
      }
    } else {
      const conf = game.total_confidence || 0
      return {
        value: conf,
        label: `${conf.toFixed(0)}`,
        isProbability: false,
      }
    }
  }

  // Get color for market score
  function getMarketScoreColor(value: number, isProbability: boolean): string {
    if (isProbability) {
      if (value >= 0.9) return "text-red-400"
      if (value >= 0.7) return "text-orange-400"
      if (value >= 0.55) return "text-yellow-400"
      return "text-gray-400"
    } else {
      // Confidence score
      if (value >= 80) return "text-emerald-400"
      if (value >= 60) return "text-yellow-400"
      return "text-red-400"
    }
  }

  // Get badge color
  function getBadgeColor(value: number, isProbability: boolean): string {
    if (isProbability) {
      if (value >= 0.9) return "bg-red-500/20 border-red-500/30"
      if (value >= 0.7) return "bg-orange-500/20 border-orange-500/30"
      if (value >= 0.55) return "bg-yellow-500/20 border-yellow-500/30"
      return "bg-gray-500/20 border-gray-500/30"
    } else {
      if (value >= 80) return "bg-emerald-500/20 border-emerald-500/30"
      if (value >= 60) return "bg-yellow-500/20 border-yellow-500/30"
      return "bg-red-500/20 border-red-500/30"
    }
  }

  return (
    <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
      <AnimatedBackground variant="intense" />
      <div className="flex-1 relative z-10 flex flex-col">
        <section className="flex-1">
            <div className="container mx-auto px-2 sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Header */}
                <div className="mb-8">
                  <h1 className="text-3xl md:text-4xl font-black text-white mb-2 flex items-center gap-2">
                    <BarChart3 className="h-8 w-8 text-emerald-400" />
                    Analytics
                  </h1>
                  <p className="text-gray-400">Model probabilities, confidence scores, and game insights</p>
                </div>

                {/* Analytics Hero Snapshot */}
                {data && (
                  <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-xs text-gray-500 mb-1">Games Tracked Today</div>
                          <div className="text-2xl font-bold text-white">{data.snapshot.games_tracked_today}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">Model Accuracy</div>
                          <div className="text-2xl font-bold text-white">
                            {data.snapshot.model_accuracy_last_100 !== null
                              ? `${data.snapshot.model_accuracy_last_100.toFixed(0)}%`
                              : "N/A"}
                          </div>
                          <div className="text-xs text-gray-500">(Last 100 Games)</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">High-Confidence Games</div>
                          <div className="text-2xl font-bold text-emerald-400">{data.snapshot.high_confidence_games}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-500 mb-1">Trending Matchup</div>
                          <div className="text-lg font-semibold text-white truncate">
                            {data.snapshot.trending_matchup || "N/A"}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Market Type Toggle */}
                <div className="flex items-center gap-2 p-4 bg-black/20 rounded-lg border border-white/10">
                  <span className="text-xs text-gray-500 mr-2">Market Type:</span>
                  {(["moneyline", "spread", "totals"] as MarketType[]).map((type) => (
                    <button
                      key={type}
                      onClick={() => setMarketType(type)}
                      className={cn(
                        "px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize",
                        marketType === type
                          ? "bg-emerald-500 text-black"
                          : "bg-white/5 text-gray-400 hover:bg-white/10"
                      )}
                    >
                      {type === "moneyline" ? "Moneyline (Win Probabilities)" : type === "spread" ? "Spread (Confidence)" : "Totals (Confidence)"}
                    </button>
                  ))}
                </div>

                {/* Filters and Sorting */}
                <div className="flex flex-wrap items-center gap-4 p-4 bg-black/20 rounded-lg border border-white/10">
                  {/* Sport Filter */}
                  <div className="flex items-center gap-2">
                    <Filter className="h-4 w-4 text-gray-500" />
                    <span className="text-xs text-gray-500">Sport:</span>
                    <button
                      onClick={() => setSelectedSport(undefined)}
                      className={cn(
                        "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                        selectedSport === undefined
                          ? "bg-emerald-500 text-black"
                          : "bg-white/5 text-gray-400 hover:bg-white/10"
                      )}
                    >
                      All
                    </button>
                    {availableSports.map((sport) => {
                      const availability = sportsUiPolicy.resolveAvailability(sport)
                      const isDisabled = !availability.isAvailable
                      return (
                        <button
                          key={sport.slug}
                          onClick={() => !isDisabled && setSelectedSport(sport.slug)}
                          disabled={isDisabled}
                          className={cn(
                            "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors uppercase",
                            selectedSport === sport.slug
                              ? "bg-emerald-500 text-black"
                              : isDisabled
                                ? "bg-white/5 text-gray-500 cursor-not-allowed opacity-50"
                                : "bg-white/5 text-gray-400 hover:bg-white/10"
                          )}
                        >
                          {sport.slug}
                        </button>
                      )
                    })}
                  </div>

                  <div className="h-6 w-px bg-white/10" />

                  {/* Sort */}
                  <div className="flex items-center gap-2">
                    <ArrowUpDown className="h-4 w-4 text-gray-500" />
                    <span className="text-xs text-gray-500">Sort:</span>
                    {(["traffic", "confidence", "time"] as SortOption[]).map((option) => (
                      <button
                        key={option}
                        onClick={() => setSortBy(option)}
                        className={cn(
                          "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize",
                          sortBy === option
                            ? "bg-white/20 text-white"
                            : "bg-white/5 text-gray-400 hover:bg-white/10"
                        )}
                      >
                        {option === "traffic" ? "Most Popular" : option === "confidence" ? "Highest Confidence" : "Soonest"}
                      </button>
                    ))}
                  </div>

                  <div className="h-6 w-px bg-white/10" />

                  {/* Filters */}
                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filterHighConfidence}
                        onChange={(e) => setFilterHighConfidence(e.target.checked)}
                        className="rounded border-white/20"
                      />
                      High Confidence Only
                    </label>
                    <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filterFullAnalysis}
                        onChange={(e) => setFilterFullAnalysis(e.target.checked)}
                        className="rounded border-white/20"
                      />
                      Full Analysis Only
                    </label>
                    <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filterTrending}
                        onChange={(e) => setFilterTrending(e.target.checked)}
                        className="rounded border-white/20"
                      />
                      Trending Only
                    </label>
                  </div>
                </div>

                {/* Analytics Heatmap */}
                {loading ? (
                  <div className="flex justify-center items-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                    <span className="ml-3 text-gray-400">Loading analytics...</span>
                  </div>
                ) : error ? (
                  <Card className="bg-red-500/10 border-red-500/30">
                    <CardContent className="p-6 text-center">
                      <div className="text-red-400 font-semibold mb-2">Error loading analytics</div>
                      <div className="text-sm text-gray-400">{error}</div>
                    </CardContent>
                  </Card>
                ) : filteredAndSortedGames.length === 0 ? (
                  <Card className="bg-white/5 border-white/10">
                    <CardContent className="p-12 text-center">
                      <Target className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                      <div className="text-white font-semibold mb-2">No games found</div>
                      <div className="text-sm text-gray-400">Try adjusting your filters</div>
                    </CardContent>
                  </Card>
                ) : (
                  <div className="space-y-2">
                    {/* Table Header */}
                    <div className="grid grid-cols-12 gap-2 px-4 py-3 text-xs font-medium text-gray-500 border-b border-white/10 bg-black/20 rounded-t-lg">
                      <div className="col-span-3">Teams</div>
                      <div className="col-span-2 text-center">
                        {marketType === "moneyline" ? "Win Probability" : "Confidence Score"}
                      </div>
                      <div className="col-span-2">Badges</div>
                      <div className="col-span-2">Sport</div>
                      <div className="col-span-2">Time</div>
                      <div className="col-span-1">Action</div>
                    </div>

                    {/* Rows */}
                    {filteredAndSortedGames.map((game, index) => {
                      const marketScore = getMarketScore(game)
                      const isHighConfidence =
                        (marketType === "moneyline" && (marketScore.value >= 0.7 || marketScore.value <= 0.3)) ||
                        (marketType !== "moneyline" && marketScore.value >= 70)

                      return (
                        <motion.div
                          key={game.game_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.02 }}
                          className="grid grid-cols-12 gap-2 px-4 py-3 rounded-lg items-center bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                        >
                          {/* Teams */}
                          <div className="col-span-3">
                            <div className="text-sm font-semibold text-white">{game.matchup}</div>
                            <div className="text-xs text-gray-500">{game.sport.toUpperCase()}</div>
                          </div>

                          {/* Market Score */}
                          <div className="col-span-2 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <div className={cn("text-lg font-bold", getMarketScoreColor(marketScore.value, marketScore.isProbability))}>
                                {marketScore.label}
                                {!marketScore.isProbability && <span className="text-xs ml-1">/100</span>}
                              </div>
                              <Info
                                className="h-3 w-3 text-gray-500 cursor-help"
                                title={marketScore.isProbability
                                  ? "Model-estimated chance of winning the game"
                                  : "How confident the model is in this pick — not a true probability"}
                              />
                            </div>
                            {isHighConfidence && (
                              <div className="text-xs text-emerald-400 mt-1">High Confidence</div>
                            )}
                          </div>

                          {/* Badges */}
                          <div className="col-span-2 flex items-center gap-1.5 flex-wrap">
                            {game.has_cached_analysis && (
                              <Badge
                                className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30 text-xs"
                                title="Cached deep model analysis"
                              >
                                <Star className="h-3 w-3 mr-1" />
                                Full Analysis
                              </Badge>
                            )}
                            {!game.has_cached_analysis && (
                              <Badge
                                className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30 text-xs"
                                title="Fast approximation used when deep analysis isn't cached yet"
                              >
                                <Zap className="h-3 w-3 mr-1" />
                                Quick Model
                              </Badge>
                            )}
                            {game.is_trending && (
                              <Badge
                                className="bg-orange-500/20 text-orange-300 border-orange-500/30 text-xs"
                                title="High user traffic / interest"
                              >
                                <Flame className="h-3 w-3 mr-1" />
                                Trending
                              </Badge>
                            )}
                          </div>

                          {/* Sport */}
                          <div className="col-span-2 text-sm text-gray-400">{game.sport.toUpperCase()}</div>

                          {/* Time */}
                          <div className="col-span-2 text-xs text-gray-500">
                            {new Date(game.start_time).toLocaleDateString()} {new Date(game.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </div>

                          {/* Action */}
                          <div className="col-span-1">
                            {game.slug ? (
                              <Link href={`/analysis/${game.sport.toLowerCase()}/${game.slug}`}>
                                <Button size="sm" variant="outline" className="border-white/20 hover:bg-white/10 text-xs">
                                  View
                                </Button>
                              </Link>
                            ) : (
                              <Button size="sm" variant="outline" className="border-white/20 hover:bg-white/10 text-xs" disabled>
                                Generate
                              </Button>
                            )}
                          </div>
                        </motion.div>
                      )
                    })}
                  </div>
                )}

              </motion.div>
            </div>
          </section>
        </div>
      </div>
  )
}
