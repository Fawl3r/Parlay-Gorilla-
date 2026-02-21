"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { useSubscription } from "@/lib/subscription-context"
import { api, GameResponse } from "@/lib/api"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"
import { ToolShell } from "@/components/tools/ToolShell"
import { GorillaBotToolPanel } from "@/components/gorilla-bot/GorillaBotToolPanel"
import { dispatchGorillaBotOpen } from "@/lib/gorilla-bot/events"
import { ToolChatPromptBuilder } from "@/lib/gorilla-bot/ToolChatPromptBuilder"
import {
  Loader2,
  Plus,
  Crown,
  Lock,
  TrendingUp,
  RefreshCw,
  Check,
  MessageCircle,
} from "lucide-react"
import { cn } from "@/lib/utils"

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

const toolChatPrompts = new ToolChatPromptBuilder()

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

/**
 * Shared heatmap content: upgrade CTA when !isPremium, full heatmap when isPremium.
 * No layout (DashboardLayout/stripe). Use in app tab or standalone page.
 */
export function OddsHeatmapView() {
  const { isPremium } = useSubscription()
  const [games, setGames] = useState<GameResponse[]>([])
  const [heatmapData, setHeatmapData] = useState<HeatmapCell[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedSport, setSelectedSport] = useState("nfl")
  const [selectedMarket, setSelectedMarket] = useState<"all" | "h2h" | "spreads" | "totals">("all")
  const [parlayLegs, setParlayLegs] = useState<Set<string>>(new Set())
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})
  const [heatmapError, setHeatmapError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadSportsStatus() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        const map: Record<string, boolean> = {}
        for (const s of sportsList) {
          const key = (s.slug || "").toLowerCase()
          map[key] = typeof s.is_enabled === "boolean" ? s.is_enabled : (s.in_season !== false)
        }
        setInSeasonBySport(map)
      } catch {
        if (!cancelled) setInSeasonBySport({})
      }
    }
    if (isPremium) loadSportsStatus()
    return () => { cancelled = true }
  }, [isPremium])

  useEffect(() => {
    if (Object.keys(inSeasonBySport).length === 0) return
    const currentValid =
      inSeasonBySport[selectedSport.toLowerCase()] !== false &&
      !sportsUiPolicy.isComingSoon(selectedSport)
    if (currentValid) return
    const firstAvailable = SPORTS.find(
      (s) =>
        inSeasonBySport[(s.id || "").toLowerCase()] !== false &&
        !sportsUiPolicy.isComingSoon(s.id)
    )?.id
    if (firstAvailable) setSelectedSport(firstAvailable)
  }, [inSeasonBySport, selectedSport])

  function calculateImpliedProbability(price: string, providedImpliedProb?: number): number {
    if (typeof providedImpliedProb === "number" && !isNaN(providedImpliedProb) && providedImpliedProb > 0 && providedImpliedProb < 1)
      return providedImpliedProb
    const cleaned = String(price || "").trim().replace("−", "-")
    const american = Number(cleaned.replace("+", ""))
    if (!isFinite(american) || american === 0) return 0.5
    if (american < 0) return Math.abs(american) / (Math.abs(american) + 100)
    return 100 / (american + 100)
  }

  async function loadGames(forceRefresh = false) {
    setHeatmapError(null)
    setLoading(true)
    try {
      const [gamesData, probabilitiesData] = await Promise.all([
        api.getGames(selectedSport, undefined, forceRefresh),
        api.getHeatmapProbabilities(selectedSport).catch((err) => {
          setHeatmapError(err?.message ?? "Failed to load probabilities")
          return []
        }),
      ])
      const gamesList = gamesData.games ?? []
      setGames(gamesList)
      const probMap = new Map<string, (typeof probabilitiesData)[0]>()
      for (const prob of probabilitiesData) probMap.set(prob.game_id, prob)
      const cells: HeatmapCell[] = []
      for (const game of gamesList) {
        const gameProbs = probMap.get(game.id)
        const markets = game.markets ?? []
        for (const market of markets) {
          const oddsList = market.odds ?? []
          for (const odds of oddsList) {
            const impliedProb = calculateImpliedProbability(odds.price, odds.implied_prob)
            if (!isFinite(impliedProb) || impliedProb <= 0 || impliedProb >= 1) continue
            let modelProb: number | null = null
            if (market.market_type === "h2h" && gameProbs) {
              const o = (odds.outcome ?? "").toLowerCase()
              if (o.includes(game.home_team.toLowerCase()) || o === "home") modelProb = gameProbs.home_win_prob
              else if (o.includes(game.away_team.toLowerCase()) || o === "away") modelProb = gameProbs.away_win_prob
            } else if (market.market_type === "spreads" && gameProbs?.spread_confidence != null)
              modelProb = Math.max(0.05, Math.min(0.95, gameProbs.spread_confidence / 100))
            else if (market.market_type === "totals" && gameProbs?.total_confidence != null)
              modelProb = Math.max(0.05, Math.min(0.95, gameProbs.total_confidence / 100))
            if (modelProb === null || !isFinite(modelProb)) modelProb = impliedProb
            modelProb = Math.max(0.05, Math.min(0.95, modelProb))
            const edge = (modelProb - impliedProb) * 100
            if (!isFinite(edge)) continue
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
              edge,
              is_upset: isUpset,
            })
          }
        }
      }
      cells.sort((a, b) => b.edge - a.edge)
      setHeatmapData(cells)
    } catch (e) {
      console.error("Failed to load games:", e)
      setHeatmapError(e instanceof Error ? e.message : "Failed to load odds")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (isPremium) loadGames()
    else setLoading(false)
  }, [selectedSport, isPremium])

  function toggleLeg(cell: HeatmapCell) {
    const legKey = `${cell.game_id}-${cell.market_type}-${cell.outcome}`
    const next = new Set(parlayLegs)
    if (next.has(legKey)) next.delete(legKey)
    else next.add(legKey)
    setParlayLegs(next)
  }

  const displayedData = heatmapData.filter((c) => selectedMarket === "all" || c.market_type === selectedMarket)

  if (!isPremium) {
    return (
      <div className="w-full py-6">
        <div className="max-w-2xl mx-auto text-center py-20">
          <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mx-auto mb-6">
            <Lock className="h-10 w-10 text-emerald-400" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">Premium Feature</h2>
          <p className="text-lg text-gray-400 mb-8">
            The Odds Heatmap is available exclusively for Premium subscribers. Upgrade to unlock real-time model probabilities, edge calculations, and comprehensive odds analysis across all sportsbooks.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/pricing">
              <Button size="lg" className="bg-emerald-500 hover:bg-emerald-600 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] text-black font-bold transition-all duration-200">
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
    )
  }

  const heatmapPills = [
    { label: "Sport", value: SPORTS.find((s) => s.id === selectedSport)?.label ?? selectedSport.toUpperCase() },
    { label: "Market", value: selectedMarket === "all" ? "All" : selectedMarket === "h2h" ? "ML" : selectedMarket === "spreads" ? "Spread" : "Total" },
  ]

  const leftPanel = (
    <div className="space-y-4">
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-white">Sport</h3>
        <div className="flex flex-wrap gap-2">
          {SPORTS.map((sport) => {
            const isDisabled = inSeasonBySport[(sport.id || "").toLowerCase()] === false || sportsUiPolicy.isComingSoon(sport.id)
            return (
              <button
                key={sport.id}
                onClick={() => !isDisabled && setSelectedSport(sport.id)}
                disabled={isDisabled}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-medium uppercase transition-all duration-150 hover:scale-[1.02]",
                  selectedSport === sport.id ? "ring-2 ring-green-500/40 bg-emerald-500 text-black" : "bg-white/5 text-gray-400 hover:bg-white/10",
                  isDisabled && "opacity-50 cursor-not-allowed"
                )}
              >
                {sport.label}
              </button>
            )
          })}
        </div>
        <h3 className="text-sm font-semibold text-white pt-2">Market</h3>
        <div className="flex flex-wrap gap-2">
          {(["all", "h2h", "spreads", "totals"] as const).map((market) => (
            <button
              key={market}
              onClick={() => setSelectedMarket(market)}
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-150",
                selectedMarket === market ? "bg-white/20 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"
              )}
            >
              {market === "all" ? "All" : market === "h2h" ? "ML" : market === "spreads" ? "Spread" : "Total"}
            </button>
          ))}
        </div>
        <Button variant="outline" size="sm" onClick={() => loadGames(true)} disabled={loading} className="w-full border-white/20 hover:shadow-[0_0_20px_rgba(34,197,94,0.2)]">
          <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
          Force Refresh
        </Button>
      </div>
      <div>
        <h3 className="text-sm font-semibold text-white mb-2">Edge legend</h3>
        <div className="flex flex-wrap gap-3 text-xs text-gray-400">
          {[
            { label: "+5%+", color: "bg-emerald-500" },
            { label: "+3%", color: "bg-emerald-400" },
            { label: "0%", color: "bg-gray-500" },
            { label: "-5%", color: "bg-red-500" },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className={cn("w-4 h-4 rounded", item.color)} />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  const isEmpty =
    !loading &&
    (games.length === 0 ||
      games.every((g) => !(g.markets?.length)) ||
      heatmapData.length === 0)
  const showEmptyState = isEmpty && !heatmapError
  const showErrorState = Boolean(heatmapError)

  const heatmapTable = (
    <div className="overflow-x-auto">
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          <span className="ml-3 text-gray-400">Loading odds data...</span>
        </div>
      ) : showErrorState ? (
        <div className="text-center py-20">
          <div className="mb-4 rounded-lg bg-red-500/15 border border-red-500/30 p-4 text-red-200 text-sm max-w-md mx-auto">
            {heatmapError}
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            <Button variant="outline" size="sm" onClick={() => loadGames(false)} className="border-white/20">
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
            <Button variant="outline" size="sm" onClick={() => loadGames(true)} className="border-white/20">
              <RefreshCw className="h-4 w-4 mr-2" />
              Force Refresh
            </Button>
          </div>
        </div>
      ) : showEmptyState ? (
        <div className="text-center py-20">
          <p className="text-white/60 mb-4">No odds available yet for this sport.</p>
          <p className="text-sm text-gray-500 mb-4">Try another sport or force refresh to fetch the latest games and markets.</p>
          <Button variant="outline" size="sm" onClick={() => loadGames(true)} className="border-white/20">
            <RefreshCw className="h-4 w-4 mr-2" />
            Force Refresh
          </Button>
        </div>
      ) : displayedData.length === 0 ? (
        <div className="text-center py-20 text-white/60">No data for this sport/market. Try another filter or Force Refresh.</div>
      ) : (
        <div className="space-y-2 min-w-[600px]">
          <div className="grid grid-cols-12 gap-2 px-2 py-2 text-xs font-medium text-gray-500 border-b border-white/10">
            <div className="col-span-3">Game</div>
            <div className="col-span-2">Pick</div>
            <div className="col-span-1 text-center">Odds</div>
            <div className="col-span-1 text-center">Book</div>
            <div className="col-span-2 text-center">Model Prob</div>
            <div className="col-span-2 text-center">Edge</div>
            <div className="col-span-1 text-center">Action</div>
          </div>
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
                  "grid grid-cols-12 gap-2 px-2 py-3 rounded-lg items-center transition-all",
                  isSelected ? "bg-emerald-500/10 border border-emerald-500/30 ring-1 ring-green-500/30" : "bg-white/[0.02] hover:bg-white/[0.04]"
                )}
              >
                <div className="col-span-3">
                  <div className="text-sm font-medium text-white truncate">{cell.game}</div>
                  <div className="text-xs text-gray-500 capitalize">{cell.market_type === "h2h" ? "Moneyline" : cell.market_type}</div>
                </div>
                <div className="col-span-2 flex items-center gap-1.5">
                  <span className="text-sm text-white truncate">{cell.outcome}</span>
                  {cell.is_upset && <span className="text-purple-400 text-xs">🦍</span>}
                </div>
                <div className="col-span-1 text-center text-sm text-white">{cell.odds}</div>
                <div className="col-span-1 text-center text-xs text-gray-400 truncate" title={cell.book}>{cell.book}</div>
                <div className="col-span-2 text-center text-sm text-emerald-400">{isFinite(cell.model_prob) ? (cell.model_prob * 100).toFixed(1) : "N/A"}%</div>
                <div className="col-span-2 text-center flex items-center justify-center gap-2">
                  <div className={cn("w-8 h-3 rounded", getEdgeColor(cell.edge))} />
                  <span className={cn("text-sm font-bold", getEdgeTextColor(cell.edge))}>
                    {isFinite(cell.edge) ? `${cell.edge > 0 ? "+" : ""}${cell.edge.toFixed(1)}%` : "N/A"}
                  </span>
                </div>
                <div className="col-span-1 text-center">
                  <Button size="sm" variant={isSelected ? "default" : "outline"} onClick={() => toggleLeg(cell)} className={cn("text-xs w-full", isSelected ? "bg-emerald-500 hover:shadow-[0_0_20px_rgba(34,197,94,0.3)] text-black" : "border-white/20")}>
                    {isSelected ? <Check className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                  </Button>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )

  const botQuestions = [
    "How do I read the Odds Heatmap?",
    "What does edge % mean and what can make it misleading?",
    "What’s the difference between implied prob and model prob?",
    "What does the 🦍 icon mean in this table?",
  ]

  const askAboutHeatmap = () => {
    const topCells = displayedData.slice(0, 6)
    dispatchGorillaBotOpen({
      prefill: toolChatPrompts.buildHeatmapOverviewPrefill({
        sport: selectedSport,
        market: selectedMarket,
        topCells,
      }),
    })
  }

  const rightContent = (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      <div className="lg:col-span-8 min-w-0">
        <div className="flex justify-end pb-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={askAboutHeatmap}
            className="border-white/20 bg-white/5 text-white/90 hover:bg-white/10"
          >
            <MessageCircle className="h-4 w-4 mr-2" />
            Ask about this heatmap
          </Button>
        </div>
        {heatmapTable}
      </div>
      <div className="lg:col-span-4 min-w-0 lg:sticky lg:top-0 lg:self-start">
        <GorillaBotToolPanel
          title="Odds Heatmap Assistant"
          subtitle="Ask about edges, probabilities, and what to double-check."
          suggestedQuestions={botQuestions}
        />
      </div>
    </div>
  )

  return (
    <>
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="overflow-x-hidden">
        <ToolShell
          title="Odds Heatmap"
          subtitle="Visualize value edges. Green = positive edge (model prob &gt; implied)."
          pills={heatmapPills}
          left={leftPanel}
          right={rightContent}
          stickyRight
        />
      </motion.div>
      {parlayLegs.size > 0 && (
        <motion.div initial={{ opacity: 0, y: 100 }} animate={{ opacity: 1, y: 0 }} className="fixed bottom-6 right-6 z-50">
          <Link href="/app?tab=custom-builder">
            <div className="flex items-center gap-3 px-5 py-3 rounded-full bg-emerald-500 text-black shadow-lg shadow-emerald-500/30 hover:shadow-[0_0_20px_rgba(34,197,94,0.4)] transition-all duration-200">
              <div className="w-7 h-7 rounded-full bg-black/20 flex items-center justify-center text-sm font-bold">{parlayLegs.size}</div>
              <span className="font-semibold">Build Parlay</span>
              <TrendingUp className="h-5 w-5" />
            </div>
          </Link>
        </motion.div>
      )}
    </>
  )
}
