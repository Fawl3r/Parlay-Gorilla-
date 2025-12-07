"use client"

import { useEffect, useState, useRef } from "react"
import { api, GameResponse, NFLWeekInfo } from "@/lib/api"
import { Header } from "@/components/Header"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { GameCard } from "@/components/GameCard"
import { ParlayBuilder } from "@/components/ParlayBuilder"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"
import { Analytics } from "@/components/Analytics"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, AlertCircle, Target, Zap, BarChart3, Calendar } from "lucide-react"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { motion } from "framer-motion"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { GameCardSkeletonGrid } from "@/components/GameCardSkeleton"

type TabType = "games" | "custom-builder" | "ai-builder" | "analytics"

// Available sportsbooks
const SPORTSBOOKS = [
  { id: "fanduel", name: "FanDuel", logo: "🎰" },
  { id: "draftkings", name: "DraftKings", logo: "👑" },
  { id: "betmgm", name: "BetMGM", logo: "🦁" },
  { id: "caesars", name: "Caesars", logo: "🏛️" },
  { id: "pointsbet", name: "PointsBet", logo: "📍" },
  { id: "all", name: "All Books", logo: "📚" },
]

const SPORTS = [
  // Pro Sports
  { id: "nfl", name: "NFL", icon: "🏈", color: "from-green-500 to-emerald-600", category: "pro" },
  { id: "nba", name: "NBA", icon: "🏀", color: "from-orange-500 to-red-600", category: "pro" },
  { id: "nhl", name: "NHL", icon: "🏒", color: "from-blue-500 to-cyan-600", category: "pro" },
  { id: "mlb", name: "MLB", icon: "⚾", color: "from-red-500 to-pink-600", category: "pro" },
  // College Sports
  { id: "ncaaf", name: "CFB", icon: "🏈", color: "from-amber-500 to-yellow-600", category: "college" },
  { id: "ncaab", name: "CBB", icon: "🏀", color: "from-purple-600 to-indigo-700", category: "college" },
  // Soccer
  { id: "mls", name: "MLS", icon: "⚽", color: "from-sky-500 to-blue-600", category: "soccer" },
  { id: "epl", name: "EPL", icon: "⚽", color: "from-violet-600 to-purple-700", category: "soccer" },
  { id: "laliga", name: "La Liga", icon: "⚽", color: "from-rose-500 to-red-600", category: "soccer" },
  { id: "ucl", name: "UCL", icon: "⚽", color: "from-blue-600 to-indigo-700", category: "soccer" },
]

function AppContent() {
  const [games, setGames] = useState<GameResponse[]>([])
  const [filteredGames, setFilteredGames] = useState<GameResponse[]>([])
  const [selectedSportsbook, setSelectedSportsbook] = useState<string | null>(null)
  const [selectedSport, setSelectedSport] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabType>("games")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasLoadedGames, setHasLoadedGames] = useState(false)
  
  // Week selection for NFL
  const [availableWeeks, setAvailableWeeks] = useState<NFLWeekInfo[]>([])
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined)
  const [currentWeek, setCurrentWeek] = useState<number | null>(null)
  
  const mainRef = useRef<HTMLDivElement>(null)
  
  // Fetch NFL weeks on mount
  useEffect(() => {
    async function fetchWeeks() {
      try {
        const weeksData = await api.getNFLWeeks()
        setAvailableWeeks(weeksData.weeks.filter(w => w.is_available))
        setCurrentWeek(weeksData.current_week)
        // Default to current week
        if (weeksData.current_week) {
          setSelectedWeek(weeksData.current_week)
        }
      } catch (err) {
        console.error("Failed to fetch NFL weeks:", err)
      }
    }
    fetchWeeks()
  }, [])

  // Reset games when changing sport or sportsbook selection (only in games tab)
  useEffect(() => {
    if (activeTab === "games") {
      setGames([])
      setFilteredGames([])
      setHasLoadedGames(false)
      setError(null)
    }
  }, [selectedSport, selectedSportsbook, activeTab])

  const handleLoadGames = async () => {
    if (!selectedSport || !selectedSportsbook) return
    
    try {
      setLoading(true)
      setError(null)
      
      try {
        await api.healthCheck()
      } catch (healthErr) {
        setError('Backend server is not reachable. Make sure it is running on port 8000.')
        setLoading(false)
        return
      }
      
      // Pass week filter for NFL
      const weekFilter = selectedSport === "nfl" ? selectedWeek : undefined
      const data = await api.getGames(selectedSport, weekFilter)
      setGames(data)
      
      // Filter by sportsbook if not "all"
      if (selectedSportsbook === "all") {
        setFilteredGames(data)
      } else {
        const filtered = data.filter((game) =>
          game.markets.some((market) => market.book === selectedSportsbook)
        )
        setFilteredGames(filtered)
      }
      setHasLoadedGames(true)
    } catch (err: unknown) {
      console.error('Error fetching games:', err)
      const detail =
        typeof err === "object" && err !== null && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : null
      setError(detail || "Failed to fetch games. Please try again later.")
    } finally {
      setLoading(false)
    }
  }

  // Filter games when sportsbook changes (after games are loaded)
  useEffect(() => {
    if (hasLoadedGames && games.length > 0 && selectedSportsbook) {
      if (selectedSportsbook === "all") {
        setFilteredGames(games)
      } else {
        const filtered = games.filter((game) =>
          game.markets.some((market) => market.book === selectedSportsbook)
        )
        setFilteredGames(filtered)
      }
    }
  }, [selectedSportsbook, games, hasLoadedGames])
  
  const canLoadGames = selectedSport && selectedSportsbook

  const tabs = [
    { id: "games" as TabType, label: "Upcoming Games", icon: Calendar },
    { id: "custom-builder" as TabType, label: "Custom Builder", icon: Target },
    { id: "ai-builder" as TabType, label: "AI Builder", icon: Zap },
    { id: "analytics" as TabType, label: "Analytics", icon: BarChart3 },
  ]

  return (
    <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: '#0a0a0f' }}>
      {/* Enhanced Animated Background */}
      <AnimatedBackground variant="intense" />
      
      <Header />
      
      <main ref={mainRef} className="flex-1 relative overflow-hidden z-10">
        {/* Dashboard Header */}
        <section className="relative z-20 border-b border-border/50 bg-card/85 backdrop-blur-md shadow-lg">
          <div className="container mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-foreground mb-1">Gorilla Dashboard</h1>
                <p className="text-muted-foreground">Build parlays, view games, and track your performance</p>
              </div>
              <div className="flex items-center gap-4">
                <Link
                  href="/analysis"
                  className="px-4 py-2 text-sm font-medium text-foreground border border-border rounded-lg hover:border-primary/50 hover:text-primary transition-all bg-muted"
                >
                  Game Analysis
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Tab Navigation */}
        <section className="relative z-20 border-b border-border/50 bg-card/85 backdrop-blur-md">
          <div className="container mx-auto px-4">
            <div className="flex gap-2">
              {tabs.map((tab) => {
                const Icon = tab.icon
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`
                      flex items-center gap-2 px-6 py-3 text-sm font-medium transition-all relative
                      ${activeTab === tab.id
                        ? "text-primary"
                        : "text-muted-foreground hover:text-foreground"
                      }
                    `}
                  >
                    <Icon className="h-4 w-4" />
                    {tab.label}
                    {activeTab === tab.id && (
                      <motion.div
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-400"
                        layoutId="activeTab"
                        transition={{ type: "spring", stiffness: 500, damping: 30 }}
                      />
                    )}
                  </button>
                )
              })}
            </div>
          </div>
        </section>

        {/* Tab Content */}
        <section className="relative z-20 flex-1 py-8">
          <div className="container mx-auto px-4 relative">
            {/* Upcoming Games Tab */}
            {activeTab === "games" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8 max-w-6xl mx-auto"
              >
                {/* Selection Panel */}
                <Card className="border-2 border-border/50 bg-card/90 backdrop-blur-md shadow-xl overflow-hidden">
                  <CardContent className="p-6 space-y-8">
                    {/* Step 1: Select Sport */}
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 font-bold text-sm">
                          1
                        </div>
                        <h3 className="text-lg font-semibold text-foreground">Select Sport</h3>
                        {selectedSport && (
                          <span className="text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">
                            ✓ {SPORTS.find(s => s.id === selectedSport)?.name}
                          </span>
                        )}
                      </div>
                      
                      {/* Pro Sports */}
                      <div className="space-y-2">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Pro Sports</span>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {SPORTS.filter(s => s.category === "pro").map((sport) => (
                            <motion.button
                              key={sport.id}
                              onClick={() => setSelectedSport(sport.id)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              className={cn(
                                "relative p-4 rounded-xl border-2 transition-all duration-200 overflow-hidden group",
                                selectedSport === sport.id
                                  ? "border-primary bg-primary/10"
                                  : "border-border bg-muted hover:border-primary/50 hover:bg-muted/80"
                              )}
                            >
                              {selectedSport === sport.id && (
                                <div className={`absolute inset-0 bg-gradient-to-br ${sport.color} opacity-20 dark:opacity-15`} />
                              )}
                              <div className="relative z-10 flex flex-col items-center gap-2">
                                <span className="text-3xl">{sport.icon}</span>
                                <span className={cn(
                                  "font-bold text-sm",
                                  selectedSport === sport.id ? "text-primary" : "text-foreground"
                                )}>
                                  {sport.name}
                                </span>
                              </div>
                            </motion.button>
                          ))}
                        </div>
                      </div>
                      
                      {/* College Sports */}
                      <div className="space-y-2">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">College Sports</span>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {SPORTS.filter(s => s.category === "college").map((sport) => (
                            <motion.button
                              key={sport.id}
                              onClick={() => setSelectedSport(sport.id)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              className={cn(
                                "relative p-3 rounded-xl border-2 transition-all duration-200 overflow-hidden group",
                                selectedSport === sport.id
                                  ? "border-primary bg-primary/10"
                                  : "border-border bg-muted hover:border-primary/50 hover:bg-muted/80"
                              )}
                            >
                              {selectedSport === sport.id && (
                                <div className={`absolute inset-0 bg-gradient-to-br ${sport.color} opacity-20 dark:opacity-15`} />
                              )}
                              <div className="relative z-10 flex flex-col items-center gap-1">
                                <span className="text-2xl">{sport.icon}</span>
                                <span className={cn(
                                  "font-bold text-xs",
                                  selectedSport === sport.id ? "text-primary" : "text-foreground"
                                )}>
                                  {sport.name}
                                </span>
                              </div>
                            </motion.button>
                          ))}
                        </div>
                      </div>
                      
                      {/* Soccer */}
                      <div className="space-y-2">
                        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Soccer</span>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {SPORTS.filter(s => s.category === "soccer").map((sport) => (
                            <motion.button
                              key={sport.id}
                              onClick={() => setSelectedSport(sport.id)}
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              className={cn(
                                "relative p-3 rounded-xl border-2 transition-all duration-200 overflow-hidden group",
                                selectedSport === sport.id
                                  ? "border-primary bg-primary/10"
                                  : "border-border bg-muted hover:border-primary/50 hover:bg-muted/80"
                              )}
                            >
                              {selectedSport === sport.id && (
                                <div className={`absolute inset-0 bg-gradient-to-br ${sport.color} opacity-20 dark:opacity-15`} />
                              )}
                              <div className="relative z-10 flex flex-col items-center gap-1">
                                <span className="text-2xl">{sport.icon}</span>
                                <span className={cn(
                                  "font-bold text-xs",
                                  selectedSport === sport.id ? "text-primary" : "text-foreground"
                                )}>
                                  {sport.name}
                                </span>
                              </div>
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Step 1.5: Week Selector for NFL */}
                    {selectedSport === "nfl" && availableWeeks.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="space-y-4"
                      >
                        <div className="flex items-center gap-3">
                          <Calendar className="h-5 w-5 text-primary" />
                          <h4 className="text-sm font-medium text-foreground">Select Week</h4>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {availableWeeks.map((weekInfo) => (
                            <button
                              key={weekInfo.week}
                              onClick={() => setSelectedWeek(weekInfo.week)}
                              className={cn(
                                "px-3 py-1.5 text-sm font-medium rounded-lg transition-all",
                                selectedWeek === weekInfo.week
                                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/30"
                                  : "bg-muted text-foreground hover:bg-muted/80 border border-border",
                                weekInfo.is_current && selectedWeek !== weekInfo.week && "ring-1 ring-emerald-500/50"
                              )}
                            >
                              {weekInfo.label}
                              {weekInfo.is_current && <span className="ml-1 text-xs opacity-75">✓</span>}
                            </button>
                          ))}
                        </div>
                      </motion.div>
                    )}

                    {/* Divider */}
                    <div className="border-t border-border" />

                    {/* Step 2: Select Sportsbook */}
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <div className={cn(
                          "flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm",
                          selectedSport ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                        )}>
                          2
                        </div>
                        <h3 className={cn(
                          "text-lg font-semibold",
                          selectedSport ? "text-foreground" : "text-muted-foreground"
                        )}>
                          Select Sportsbook
                        </h3>
                        {selectedSportsbook && (
                          <span className="text-xs text-primary bg-primary/10 px-2 py-1 rounded-full">
                            ✓ {SPORTSBOOKS.find(s => s.id === selectedSportsbook)?.name}
                          </span>
                        )}
                      </div>
                      <div className={cn(
                        "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 transition-opacity",
                        selectedSport ? "opacity-100" : "opacity-50 pointer-events-none"
                      )}>
                        {SPORTSBOOKS.map((book) => (
                          <motion.button
                            key={book.id}
                            onClick={() => setSelectedSportsbook(book.id)}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            disabled={!selectedSport}
                            className={cn(
                              "p-3 rounded-xl border-2 transition-all duration-200",
                              selectedSportsbook === book.id
                                ? "border-emerald-500 bg-emerald-500/10"
                                : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
                            )}
                          >
                            <div className="flex flex-col items-center gap-1">
                              <span className="text-2xl">{book.logo}</span>
                              <span className={cn(
                                "font-medium text-xs",
                                selectedSportsbook === book.id ? "text-primary" : "text-muted-foreground"
                              )}>
                                {book.name}
                              </span>
                            </div>
                          </motion.button>
                        ))}
                      </div>
                    </div>

                    {/* Divider */}
                    <div className="border-t border-border" />

                    {/* Load Games Button */}
                    <div className="flex justify-center">
                      <motion.button
                        onClick={handleLoadGames}
                        disabled={!canLoadGames || loading}
                        whileHover={canLoadGames && !loading ? { scale: 1.02 } : {}}
                        whileTap={canLoadGames && !loading ? { scale: 0.98 } : {}}
                        className={cn(
                          "px-8 py-4 rounded-xl font-bold text-lg transition-all duration-200 flex items-center gap-3",
                          canLoadGames && !loading
                            ? "bg-gradient-to-r from-emerald-500 to-green-500 text-black shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50"
                            : "bg-muted text-muted-foreground cursor-not-allowed"
                        )}
                      >
                        {loading ? (
                          <>
                            <Loader2 className="h-5 w-5 animate-spin" />
                            Loading Games...
                          </>
                        ) : (
                          <>
                            <Zap className="h-5 w-5" />
                            Load {selectedSport?.toUpperCase() || ""} Games
                          </>
                        )}
                      </motion.button>
                    </div>

                    {/* Selection Summary */}
                    {canLoadGames && !hasLoadedGames && !loading && (
                      <p className="text-center text-sm text-muted-foreground">
                        Ready to load {selectedSport?.toUpperCase()} games from {SPORTSBOOKS.find(s => s.id === selectedSportsbook)?.name}
                        {selectedSport === "nfl" && selectedWeek && ` for Week ${selectedWeek}`}
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Loading State - Use Skeleton Grid for better UX */}
                {loading && (
                  <div>
                    <div className="flex items-center gap-2 mb-4 text-foreground">
                      <Loader2 className="h-5 w-5 animate-spin text-primary" />
                      <span>Loading {selectedSport?.toUpperCase()} games...</span>
                    </div>
                    <GameCardSkeletonGrid count={6} />
                  </div>
                )}

                {/* Error State */}
                {error && (
                  <Card className="bg-red-500/20 border-red-500/40 backdrop-blur-md shadow-lg">
                    <CardContent className="flex items-center justify-center py-12">
                      <AlertCircle className="h-8 w-8 text-red-400" />
                      <div className="ml-4">
                        <h3 className="font-semibold text-red-400">Error loading games</h3>
                        <p className="text-sm text-muted-foreground">{error}</p>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Games Grid */}
                {!loading && !error && hasLoadedGames && filteredGames.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    {/* Results Header */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{SPORTS.find(s => s.id === selectedSport)?.icon}</span>
                        <div>
                          <h3 className="text-xl font-bold text-foreground">
                            {selectedSport?.toUpperCase()} Games
                            {selectedSport === "nfl" && selectedWeek && ` - Week ${selectedWeek}`}
                          </h3>
                          <p className="text-sm text-gray-400">
                            {filteredGames.length} games from {SPORTSBOOKS.find(s => s.id === selectedSportsbook)?.name}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => {
                          setHasLoadedGames(false)
                          setGames([])
                          setFilteredGames([])
                        }}
                        className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground border border-border rounded-lg hover:border-primary/50 transition-all"
                      >
                        Change Selection
                      </button>
                    </div>
                    
                    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                      {filteredGames.map((game) => (
                        <GameCard
                          key={game.id}
                          game={game}
                          selectedSportsbook={selectedSportsbook || "all"}
                        />
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* Empty State - After Loading */}
                {!loading && !error && hasLoadedGames && filteredGames.length === 0 && (
                  <Card className="bg-card/90 border-border/50 backdrop-blur-md shadow-xl">
                    <CardContent className="flex flex-col items-center justify-center py-12">
                      <Target className="h-12 w-12 text-muted-foreground mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">No games found</h3>
                      <p className="text-sm text-muted-foreground text-center mb-4">
                        No {selectedSport?.toUpperCase()} games available from {SPORTSBOOKS.find(s => s.id === selectedSportsbook)?.name}
                      </p>
                      <button
                        onClick={() => {
                          setHasLoadedGames(false)
                          setGames([])
                          setFilteredGames([])
                        }}
                        className="px-4 py-2 text-sm font-medium text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/10 transition-all"
                      >
                        Try Different Selection
                      </button>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            )}

            {/* Custom Parlay Builder Tab */}
            {activeTab === "custom-builder" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-7xl mx-auto"
              >
                <CustomParlayBuilder />
              </motion.div>
            )}

            {/* AI Parlay Builder Tab */}
            {activeTab === "ai-builder" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-6xl mx-auto"
              >
                <ParlayBuilder />
              </motion.div>
            )}

            {/* Analytics Tab */}
            {activeTab === "analytics" && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-6xl mx-auto"
              >
                <Analytics />
              </motion.div>
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default function AppPage() {
  return (
    <ProtectedRoute>
      <AppContent />
    </ProtectedRoute>
  )
}
