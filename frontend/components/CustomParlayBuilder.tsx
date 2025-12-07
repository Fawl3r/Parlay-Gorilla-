"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { api, GameResponse, CustomParlayLeg, CustomParlayAnalysisResponse } from "@/lib/api"
import { TeamLogo } from "./TeamLogo"
import { useSubscription, isPaywallError, getPaywallError, PaywallError } from "@/lib/subscription-context"
import { PaywallModal, PaywallReason } from "@/components/paywall/PaywallModal"
import { useAuth } from "@/lib/auth-context"
import { Crown, Lock } from "lucide-react"

// ============================================================================
// Types
// ============================================================================

interface SelectedPick extends CustomParlayLeg {
  gameDisplay: string
  pickDisplay: string
  homeTeam: string
  awayTeam: string
  sport: string
  oddsDisplay: string
}

// ============================================================================
// Sport Configuration
// ============================================================================

const SPORTS = [
  { id: "nfl", name: "NFL", icon: "🏈" },
  { id: "nba", name: "NBA", icon: "🏀" },
  { id: "nhl", name: "NHL", icon: "🏒" },
  { id: "mlb", name: "MLB", icon: "⚾" },
  { id: "ncaaf", name: "NCAAF", icon: "🏈" },
  { id: "ncaab", name: "NCAAB", icon: "🏀" },
]

// ============================================================================
// Helper Functions
// ============================================================================

function formatGameTime(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

function getConfidenceStyles(recommendation: string) {
  switch (recommendation) {
    case "strong":
      return "bg-green-500/20 text-green-400 border-green-500/50"
    case "moderate":
      return "bg-yellow-500/20 text-yellow-400 border-yellow-500/50"
    case "weak":
      return "bg-orange-500/20 text-orange-400 border-orange-500/50"
    case "avoid":
      return "bg-red-500/20 text-red-400 border-red-500/50"
    default:
      return "bg-gray-500/20 text-gray-400 border-gray-500/50"
  }
}

function getOverallStyles(recommendation: string) {
  switch (recommendation) {
    case "strong_play":
      return { bg: "from-green-600/30 to-green-900/30", border: "border-green-500", text: "text-green-400" }
    case "solid_play":
      return { bg: "from-yellow-600/30 to-yellow-900/30", border: "border-yellow-500", text: "text-yellow-400" }
    case "risky_play":
      return { bg: "from-orange-600/30 to-orange-900/30", border: "border-orange-500", text: "text-orange-400" }
    case "avoid":
      return { bg: "from-red-600/30 to-red-900/30", border: "border-red-500", text: "text-red-400" }
    default:
      return { bg: "from-gray-600/30 to-gray-900/30", border: "border-gray-500", text: "text-gray-400" }
  }
}

// ============================================================================
// Sub-Components
// ============================================================================

function GameCard({ 
  game, 
  onSelectPick,
  selectedPicks 
}: { 
  game: GameResponse
  onSelectPick: (pick: SelectedPick) => void
  selectedPicks: SelectedPick[]
}) {
  const [expanded, setExpanded] = useState(false)
  
  const isPickSelected = (gameId: string, marketType: string, pick: string) => {
    return selectedPicks.some(
      p => p.game_id === gameId && p.market_type === marketType && p.pick.toLowerCase() === pick.toLowerCase()
    )
  }
  
  // Find markets
  const moneylineMarket = game.markets.find(m => m.market_type === "h2h")
  const spreadsMarket = game.markets.find(m => m.market_type === "spreads")
  const totalsMarket = game.markets.find(m => m.market_type === "totals")
  
  const handlePickSelect = (marketType: string, pick: string, odds: string, point?: number) => {
    const pickDisplay = marketType === "h2h" 
      ? `${pick} ML`
      : marketType === "spreads"
      ? `${pick} ${point ? (point > 0 ? `+${point}` : point) : ""}`
      : `${pick.toUpperCase()} ${point || ""}`
    
    onSelectPick({
      game_id: game.id,
      pick,
      market_type: marketType as "h2h" | "spreads" | "totals",
      odds,
      point,
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
      {/* Game Header */}
      <div 
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <TeamLogo teamName={game.away_team} sport={game.sport} size="sm" />
              <span className="text-white font-medium">{game.away_team}</span>
            </div>
            <span className="text-white/40">@</span>
            <div className="flex items-center gap-2">
              <TeamLogo teamName={game.home_team} sport={game.sport} size="sm" />
              <span className="text-white font-medium">{game.home_team}</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-white/60 text-sm">{formatGameTime(game.start_time)}</span>
            <motion.span
              animate={{ rotate: expanded ? 180 : 0 }}
              className="text-white/40"
            >
              ▼
            </motion.span>
          </div>
        </div>
      </div>
      
      {/* Betting Options */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/10"
          >
            <div className="p-4 space-y-4">
              {/* Moneyline */}
              {moneylineMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Moneyline</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {moneylineMarket.odds.map((odd) => {
                      const isHome = odd.outcome.toLowerCase().includes("home") || 
                                    odd.outcome.toLowerCase().includes(game.home_team.toLowerCase())
                      const teamName = isHome ? game.home_team : game.away_team
                      const selected = isPickSelected(game.id, "h2h", teamName)
                      
                      return (
                        <button
                          key={odd.id}
                          onClick={() => handlePickSelect("h2h", teamName, odd.price)}
                          className={`p-3 rounded-lg border transition-all ${
                            selected
                              ? "bg-cyan-500/30 border-cyan-400 text-cyan-400"
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
              
              {/* Spreads */}
              {spreadsMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Spread</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {spreadsMarket.odds.map((odd, index) => {
                      const outcomeLower = odd.outcome.toLowerCase()
                      const homeTeamLower = game.home_team.toLowerCase()
                      const awayTeamLower = game.away_team.toLowerCase()
                      
                      // Check if outcome contains team name (outcome format: "Team Name +7.0" or "Team Name -7.0")
                      // Prefer team name match over "home"/"away" keywords for accuracy
                      const containsHomeTeam = outcomeLower.includes(homeTeamLower)
                      const containsAwayTeam = outcomeLower.includes(awayTeamLower)
                      const containsHomeKeyword = outcomeLower.includes("home")
                      const containsAwayKeyword = outcomeLower.includes("away")
                      
                      // Determine team based on outcome content
                      let teamName: string
                      let pickValue: string
                      
                      if (containsHomeTeam && !containsAwayTeam) {
                        // Explicitly matches home team name
                        teamName = game.home_team
                        pickValue = "home"
                      } else if (containsAwayTeam && !containsHomeTeam) {
                        // Explicitly matches away team name
                        teamName = game.away_team
                        pickValue = "away"
                      } else if (containsHomeKeyword && !containsAwayKeyword) {
                        // Falls back to "home" keyword
                        teamName = game.home_team
                        pickValue = "home"
                      } else if (containsAwayKeyword && !containsHomeKeyword) {
                        // Falls back to "away" keyword
                        teamName = game.away_team
                        pickValue = "away"
                      } else {
                        // Last resort: use index as tiebreaker (assume first is home, second is away)
                        // This prevents both showing the same team
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
                          onClick={() => handlePickSelect("spreads", pickValue, odd.price, point)}
                          className={`p-3 rounded-lg border transition-all ${
                            selected
                              ? "bg-cyan-500/30 border-cyan-400 text-cyan-400"
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
              
              {/* Totals */}
              {totalsMarket && (
                <div>
                  <h4 className="text-white/60 text-xs uppercase mb-2">Total</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {totalsMarket.odds.map((odd) => {
                      const isOver = odd.outcome.toLowerCase().includes("over")
                      const point = parseFloat(odd.outcome.match(/\d+\.?\d*/)?.[0] || "0")
                      const selected = isPickSelected(game.id, "totals", isOver ? "over" : "under")
                      
                      return (
                        <button
                          key={odd.id}
                          onClick={() => handlePickSelect("totals", isOver ? "over" : "under", odd.price, point)}
                          className={`p-3 rounded-lg border transition-all ${
                            selected
                              ? "bg-cyan-500/30 border-cyan-400 text-cyan-400"
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

function ParlaySlip({ 
  picks, 
  onRemovePick,
  onAnalyze,
  isAnalyzing 
}: { 
  picks: SelectedPick[]
  onRemovePick: (index: number) => void
  onAnalyze: () => void
  isAnalyzing: boolean
}) {
  return (
    <div className="bg-black/60 border border-white/10 rounded-xl p-4 sticky top-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-white font-bold text-lg">Your Parlay</h3>
        <span className="bg-cyan-500/20 text-cyan-400 px-2 py-1 rounded text-sm">
          {picks.length} leg{picks.length !== 1 ? "s" : ""}
        </span>
      </div>
      
      {picks.length === 0 ? (
        <div className="text-white/40 text-center py-8">
          <p>Select picks from the games below</p>
          <p className="text-sm mt-2">Minimum 2 legs required</p>
        </div>
      ) : (
        <div className="space-y-2 mb-4 max-h-[400px] overflow-y-auto">
          {picks.map((pick, index) => (
            <motion.div
              key={`${pick.game_id}-${pick.market_type}-${pick.pick}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white/5 border border-white/10 rounded-lg p-3 flex items-center justify-between"
            >
              <div className="flex-1">
                <div className="text-white/60 text-xs">{pick.gameDisplay}</div>
                <div className="text-white font-medium">{pick.pickDisplay}</div>
                <div className="text-cyan-400 text-sm">{pick.oddsDisplay}</div>
              </div>
              <button
                onClick={() => onRemovePick(index)}
                className="text-red-400 hover:text-red-300 p-1"
              >
                ✕
              </button>
            </motion.div>
          ))}
        </div>
      )}
      
      <button
        onClick={onAnalyze}
        disabled={picks.length < 2 || isAnalyzing}
        className={`w-full py-3 rounded-lg font-bold transition-all ${
          picks.length >= 2 && !isAnalyzing
            ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-400 hover:to-blue-500"
            : "bg-white/10 text-white/40 cursor-not-allowed"
        }`}
      >
        {isAnalyzing ? (
          <span className="flex items-center justify-center gap-2">
            <motion.span
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            >
              🦍
            </motion.span>
            Analyzing...
          </span>
        ) : (
          `Get AI Analysis${picks.length >= 2 ? "" : " (min 2 legs)"}`
        )}
      </button>
    </div>
  )
}

function AnalysisResults({ analysis, onClose }: { analysis: CustomParlayAnalysisResponse; onClose: () => void }) {
  const overallStyles = getOverallStyles(analysis.ai_recommendation)
  
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-gradient-to-br ${overallStyles.bg} border ${overallStyles.border} rounded-2xl p-6`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-white">Parlay Analysis</h2>
            <p className="text-white/60">{analysis.num_legs}-leg parlay</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/60 hover:text-white text-2xl"
          >
            ✕
          </button>
        </div>
        
        {/* Overall Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-black/40 rounded-lg p-4 text-center">
            <div className="text-white/60 text-sm">AI Probability</div>
            <div className={`text-2xl font-bold ${overallStyles.text}`}>
              {analysis.combined_ai_probability.toFixed(1)}%
            </div>
          </div>
          <div className="bg-black/40 rounded-lg p-4 text-center">
            <div className="text-white/60 text-sm">Confidence</div>
            <div className={`text-2xl font-bold ${overallStyles.text}`}>
              {analysis.overall_confidence.toFixed(0)}/100
            </div>
          </div>
          <div className="bg-black/40 rounded-lg p-4 text-center">
            <div className="text-white/60 text-sm">Parlay Odds</div>
            <div className="text-2xl font-bold text-white">{analysis.parlay_odds}</div>
          </div>
          <div className="bg-black/40 rounded-lg p-4 text-center">
            <div className="text-white/60 text-sm">Recommendation</div>
            <div className={`text-lg font-bold ${overallStyles.text} capitalize`}>
              {analysis.ai_recommendation.replace(/_/g, " ")}
            </div>
          </div>
        </div>
        
        {/* Leg Analysis */}
        <div className="mb-6">
          <h3 className="text-white font-bold mb-3">Leg Breakdown</h3>
          <div className="space-y-2">
            {analysis.legs.map((leg, i) => (
              <div
                key={i}
                className={`bg-black/30 rounded-lg p-4 border ${getConfidenceStyles(leg.recommendation)}`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-white/60 text-sm">{leg.game}</div>
                    <div className="text-white font-medium">{leg.pick_display}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-white font-bold">{leg.odds}</div>
                    <div className="text-sm">
                      <span className="text-white/60">AI: </span>
                      <span className={getConfidenceStyles(leg.recommendation).split(" ")[1]}>
                        {leg.ai_probability.toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex items-center gap-4 text-sm">
                  <span className="text-white/60">
                    Confidence: <span className="text-white">{leg.confidence.toFixed(0)}%</span>
                  </span>
                  <span className="text-white/60">
                    Edge: <span className={leg.edge >= 0 ? "text-green-400" : "text-red-400"}>
                      {leg.edge >= 0 ? "+" : ""}{leg.edge.toFixed(1)}%
                    </span>
                  </span>
                  <span className={`px-2 py-0.5 rounded text-xs uppercase ${getConfidenceStyles(leg.recommendation)}`}>
                    {leg.recommendation}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* AI Analysis */}
        <div className="space-y-4">
          <div className="bg-black/40 rounded-lg p-4">
            <h4 className="text-white font-bold mb-2 flex items-center gap-2">
              <span>🦍</span> Gorilla&apos;s Take
            </h4>
            <p className="text-white/80 leading-relaxed">{analysis.ai_summary}</p>
          </div>
          
          <div className="bg-black/40 rounded-lg p-4">
            <h4 className="text-white font-bold mb-2 flex items-center gap-2">
              <span>⚠️</span> Risk Notes
            </h4>
            <p className="text-white/80 leading-relaxed">{analysis.ai_risk_notes}</p>
          </div>
          
          {analysis.weak_legs.length > 0 && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <h4 className="text-red-400 font-bold mb-2">Legs of Concern</h4>
              <ul className="text-white/70 text-sm space-y-1">
                {analysis.weak_legs.map((leg, i) => (
                  <li key={i}>• {leg}</li>
                ))}
              </ul>
            </div>
          )}
          
          {analysis.strong_legs.length > 0 && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
              <h4 className="text-green-400 font-bold mb-2">Strong Picks</h4>
              <ul className="text-white/70 text-sm space-y-1">
                {analysis.strong_legs.map((leg, i) => (
                  <li key={i}>• {leg}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
        
        {/* Close Button */}
        <div className="mt-6 flex justify-center">
          <button
            onClick={onClose}
            className="px-8 py-3 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
          >
            Close Analysis
          </button>
        </div>
      </motion.div>
    </motion.div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function CustomParlayBuilder() {
  const [selectedSport, setSelectedSport] = useState(SPORTS[0].id)
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPicks, setSelectedPicks] = useState<SelectedPick[]>([])
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  
  // Subscription & Paywall
  const { user } = useAuth()
  const { canUseCustomBuilder, isPremium, refreshStatus } = useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("custom_builder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)
  const [analysis, setAnalysis] = useState<CustomParlayAnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Fetch games when sport changes
  useEffect(() => {
    async function fetchGames() {
      setLoading(true)
      setError(null)
      try {
        const gamesData = await api.getGames(selectedSport)
        setGames(gamesData.filter(g => g.markets.length > 0))
      } catch (err) {
        console.error("Failed to fetch games:", err)
        setError("Failed to load games. Please try again.")
      } finally {
        setLoading(false)
      }
    }
    fetchGames()
  }, [selectedSport])
  
  const handleSelectPick = (pick: SelectedPick) => {
    // Check if already selected - toggle off
    const existingIndex = selectedPicks.findIndex(
      p => p.game_id === pick.game_id && p.market_type === pick.market_type && p.pick === pick.pick
    )
    
    if (existingIndex >= 0) {
      setSelectedPicks(picks => picks.filter((_, i) => i !== existingIndex))
    } else {
      // Remove any existing pick for same game + market type
      setSelectedPicks(picks => [
        ...picks.filter(p => !(p.game_id === pick.game_id && p.market_type === pick.market_type)),
        pick
      ])
    }
  }
  
  const handleRemovePick = (index: number) => {
    setSelectedPicks(picks => picks.filter((_, i) => i !== index))
  }
  
  const handleAnalyze = async () => {
    if (selectedPicks.length < 2) return
    
    setIsAnalyzing(true)
    setError(null)
    
    try {
      const legs: CustomParlayLeg[] = selectedPicks.map(pick => {
        const leg: CustomParlayLeg = {
          game_id: pick.game_id,
          pick: pick.pick,
          market_type: pick.market_type,
        }
        
        // Only include optional fields if they have values
        if (pick.odds) {
          leg.odds = pick.odds
        }
        if (pick.point !== undefined && pick.point !== null) {
          leg.point = pick.point
        }
        
        return leg
      })
      
      console.log('Sending parlay legs:', JSON.stringify(legs, null, 2))
      const result = await api.analyzeCustomParlay(legs)
      setAnalysis(result)
    } catch (err: any) {
      // Check if this is a paywall error (402)
      if (isPaywallError(err)) {
        const paywallErr = getPaywallError(err)
        setPaywallError(paywallErr)
        setPaywallReason('custom_builder_locked')
        setShowPaywall(true)
        return
      }
      
      console.error("Analysis failed:", err)
      setError(err.message || "Failed to analyze parlay. Please try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }
  
  // Handle paywall close
  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }
  
  // Show locked state for non-premium users
  if (!canUseCustomBuilder && user) {
    return (
      <>
        <div className="min-h-screen p-6 relative">
          {/* Locked Overlay */}
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-10 flex items-center justify-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 p-8 max-w-md text-center shadow-2xl"
            >
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Premium Feature</h2>
              <p className="text-gray-400 mb-6">
                The Custom Parlay Builder is available to Gorilla Premium members.
                Build your own parlays with AI-powered analysis and validation.
              </p>
              <button
                onClick={() => setShowPaywall(true)}
                className="w-full py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
              >
                <Crown className="h-5 w-5" />
                Unlock Premium
              </button>
            </motion.div>
          </div>
          
          {/* Blurred content behind */}
          <div className="filter blur-sm pointer-events-none">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">
                AI Parlay Builder 🦍
              </h1>
              <p className="text-white/60 max-w-2xl mx-auto">
                Select your picks and get AI-powered analysis with probability estimates and confidence scores
              </p>
            </div>
          </div>
        </div>
        
        <PaywallModal
          isOpen={showPaywall}
          onClose={handlePaywallClose}
          reason={paywallReason}
          error={paywallError}
        />
      </>
    )
  }
  
  return (
    <>
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex items-center justify-center gap-2 mb-2">
          <h1 className="text-4xl font-bold text-white">
            AI Parlay Builder 🦍
          </h1>
          {isPremium && (
            <span className="bg-gradient-to-r from-emerald-500 to-green-500 text-black text-xs font-bold px-2 py-1 rounded-full">
              <Crown className="h-3 w-3 inline mr-1" />
              Premium
            </span>
          )}
        </div>
        <p className="text-white/60 max-w-2xl mx-auto">
          Select your picks and get AI-powered analysis with probability estimates and confidence scores
        </p>
      </div>
      
      {/* Sport Selector */}
      <div className="flex justify-center gap-2 mb-8 flex-wrap">
        {SPORTS.map(sport => (
          <button
            key={sport.id}
            onClick={() => setSelectedSport(sport.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-all ${
              selectedSport === sport.id
                ? "bg-cyan-500 text-white"
                : "bg-white/10 text-white/70 hover:bg-white/20"
            }`}
          >
            {sport.icon} {sport.name}
          </button>
        ))}
      </div>
      
      {/* Main Content */}
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Games List */}
        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-xl font-bold text-white">
            {SPORTS.find(s => s.id === selectedSport)?.name} Games
          </h2>
          
          {loading && (
            <div className="flex items-center justify-center py-12">
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="text-4xl"
              >
                🦍
              </motion.span>
            </div>
          )}
          
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
              {error}
            </div>
          )}
          
          {!loading && !error && games.length === 0 && (
            <div className="text-center text-white/60 py-12">
              No games available for {SPORTS.find(s => s.id === selectedSport)?.name}
            </div>
          )}
          
          {!loading && games.map(game => (
            <GameCard
              key={game.id}
              game={game}
              onSelectPick={handleSelectPick}
              selectedPicks={selectedPicks}
            />
          ))}
        </div>
        
        {/* Parlay Slip */}
        <div className="lg:col-span-1">
          <ParlaySlip
            picks={selectedPicks}
            onRemovePick={handleRemovePick}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
        </div>
      </div>
      
      {/* Analysis Modal */}
      <AnimatePresence>
        {analysis && (
          <AnalysisResults
            analysis={analysis}
            onClose={() => setAnalysis(null)}
          />
        )}
      </AnimatePresence>
    </div>
    
    {/* Paywall Modal */}
    <PaywallModal
      isOpen={showPaywall}
      onClose={handlePaywallClose}
      reason={paywallReason}
      error={paywallError}
    />
    </>
  )
}

