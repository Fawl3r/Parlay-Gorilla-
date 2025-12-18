"use client"

import { useEffect, useMemo, useState } from "react"
import { AnimatePresence } from "framer-motion"
import { Crown, Lock } from "lucide-react"

import { api } from "@/lib/api"
import type {
  CounterLegCandidate,
  CounterParlayMode,
  CustomParlayAnalysisResponse,
  CustomParlayLeg,
  GameResponse,
  ParlayCoverageResponse,
} from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { getPaywallError, isPaywallError, type PaywallError, useSubscription } from "@/lib/subscription-context"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"
import { toast } from "sonner"

import { GameCard } from "@/components/custom-parlay/GameCard"
import { CustomParlayAnalysisModal } from "@/components/custom-parlay/AnalysisModal"
import { CoveragePackModal } from "@/components/custom-parlay/CoveragePackModal"
import { ParlaySlip, MAX_CUSTOM_PARLAY_LEGS } from "@/components/custom-parlay/ParlaySlip"
import type { SelectedPick } from "@/components/custom-parlay/types"

const SPORTS = [
  { id: "nfl", name: "NFL", icon: "🏈" },
  { id: "nba", name: "NBA", icon: "🏀" },
  { id: "nhl", name: "NHL", icon: "🏒" },
  { id: "mlb", name: "MLB", icon: "⚾" },
  { id: "ncaaf", name: "NCAAF", icon: "🏈" },
  { id: "ncaab", name: "NCAAB", icon: "🏀" },
] as const

function clampInt(value: number, min: number, max: number) {
  if (!Number.isFinite(value)) return min
  return Math.max(min, Math.min(max, Math.trunc(value)))
}

export function CustomParlayBuilder() {
  const [selectedSport, setSelectedSport] = useState<(typeof SPORTS)[number]["id"]>(SPORTS[0].id)
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPicks, setSelectedPicks] = useState<SelectedPick[]>([])

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<CustomParlayAnalysisResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [savedParlayId, setSavedParlayId] = useState<string | null>(null)

  // Counter ticket state
  const [isGeneratingCounter, setIsGeneratingCounter] = useState(false)
  const [counterAnalysis, setCounterAnalysis] = useState<CustomParlayAnalysisResponse | null>(null)
  const [counterCandidates, setCounterCandidates] = useState<CounterLegCandidate[] | null>(null)
  const [counterMode, setCounterMode] = useState<CounterParlayMode>("best_edges")
  const [counterTargetLegs, setCounterTargetLegs] = useState(3)

  // Coverage pack state
  const [isGeneratingCoveragePack, setIsGeneratingCoveragePack] = useState(false)
  const [coveragePack, setCoveragePack] = useState<ParlayCoverageResponse | null>(null)
  const [isCoverageModalOpen, setIsCoverageModalOpen] = useState(false)
  const [coverageMaxTotalParlays, setCoverageMaxTotalParlays] = useState(20)
  const [coverageScenarioMax, setCoverageScenarioMax] = useState(10)
  const [coverageRoundRobinMax, setCoverageRoundRobinMax] = useState(10)
  const [coverageRoundRobinSize, setCoverageRoundRobinSize] = useState(3)

  // Subscription & Paywall
  const { user } = useAuth()
  const { canUseCustomBuilder, isPremium, refreshStatus } = useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("custom_builder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)

  // Keep target legs clamped to current slip size.
  useEffect(() => {
    const max = Math.max(1, Math.min(selectedPicks.length || 1, MAX_CUSTOM_PARLAY_LEGS))
    setCounterTargetLegs((prev) => clampInt(prev, 1, max))
    const rrSizeMax = Math.max(2, Math.min(selectedPicks.length || 2, MAX_CUSTOM_PARLAY_LEGS))
    setCoverageRoundRobinSize((prev) => clampInt(prev, 2, rrSizeMax))
    if (selectedPicks.length === 0) {
      setSavedParlayId(null)
    }
  }, [selectedPicks.length])

  // Fetch sports availability (in-season) and disable out-of-season sports.
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
    loadSportsStatus()
    return () => {
      cancelled = true
    }
  }, [])

  // If the selected sport becomes out-of-season, fall back to the first in-season option.
  useEffect(() => {
    if (!Object.keys(inSeasonBySport).length) return
    if (inSeasonBySport[selectedSport] !== false) return
    const firstAvailable = SPORTS.find((s) => inSeasonBySport[s.id] !== false)?.id
    if (firstAvailable && firstAvailable !== selectedSport) setSelectedSport(firstAvailable)
  }, [inSeasonBySport, selectedSport])

  // Fetch games when sport changes
  useEffect(() => {
    async function fetchGames() {
      setLoading(true)
      setError(null)
      try {
        const gamesData = await api.getGames(selectedSport)
        setGames(gamesData.filter((g) => g.markets.length > 0))
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
    setError(null)

    const existingIndex = selectedPicks.findIndex(
      (p) => p.game_id === pick.game_id && p.market_type === pick.market_type && p.pick === pick.pick
    )

    if (existingIndex >= 0) {
      setSelectedPicks((picks) => picks.filter((_, i) => i !== existingIndex))
      return
    }

    const hasSameGameMarket = selectedPicks.some((p) => p.game_id === pick.game_id && p.market_type === pick.market_type)
    const wouldIncreaseCount = !hasSameGameMarket
    if (wouldIncreaseCount && selectedPicks.length >= MAX_CUSTOM_PARLAY_LEGS) {
      setError(`Max ${MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove a leg to add another.`)
      return
    }

    setSelectedPicks((picks) => [...picks.filter((p) => !(p.game_id === pick.game_id && p.market_type === pick.market_type)), pick])
  }

  const handleRemovePick = (index: number) => {
    setError(null)
    setSelectedPicks((picks) => picks.filter((_, i) => i !== index))
  }

  const legsPayload = useMemo((): CustomParlayLeg[] => {
    return selectedPicks.map((pick) => {
      const leg: CustomParlayLeg = {
        game_id: pick.game_id,
        pick: pick.pick,
        market_type: pick.market_type,
      }
      if (pick.market_id) leg.market_id = pick.market_id
      if (pick.odds) leg.odds = pick.odds
      if (pick.point !== undefined && pick.point !== null) leg.point = pick.point
      return leg
    })
  }, [selectedPicks])

  const handleAnalyze = async () => {
    if (selectedPicks.length < 1) return
    if (selectedPicks.length > MAX_CUSTOM_PARLAY_LEGS) {
      setError(`Max ${MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove some legs and try again.`)
      return
    }

    setIsAnalyzing(true)
    setError(null)
    try {
      const result = await api.analyzeCustomParlay(legsPayload)
      setAnalysis(result)
      setIsModalOpen(true)
    } catch (err: any) {
      if (isPaywallError(err)) {
        const pwErr = getPaywallError(err)
        setPaywallError(pwErr)
        setPaywallReason("custom_builder_locked")
        setShowPaywall(true)
        return
      }
      console.error("Analysis failed:", err)
      setError(err.message || "Failed to analyze parlay. Please try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleSave = async (title?: string) => {
    if (selectedPicks.length < 1) return
    if (selectedPicks.length > MAX_CUSTOM_PARLAY_LEGS) {
      setError(`Max ${MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove some legs and try again.`)
      return
    }

    setIsSaving(true)
    setError(null)
    try {
      const saved = await api.saveCustomParlay({
        saved_parlay_id: savedParlayId || undefined,
        title: title || `Custom Parlay (${selectedPicks.length} legs)`,
        legs: legsPayload,
      })
      setSavedParlayId(saved.id)
      toast.success(
        saved.inscription_status === "queued"
          ? `Saved v${saved.version}! On-chain proof queued.`
          : `Saved v${saved.version}!`
      )
    } catch (err: any) {
      console.error("Save failed:", err)
      toast.error(err?.response?.data?.detail || err?.message || "Failed to save parlay")
    } finally {
      setIsSaving(false)
    }
  }

  const handleGenerateCounter = async () => {
    if (selectedPicks.length < 1) return
    if (selectedPicks.length > MAX_CUSTOM_PARLAY_LEGS) {
      setError(`Max ${MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove some legs and try again.`)
      return
    }

    setIsGeneratingCounter(true)
    setError(null)
    try {
      // Ensure we have an analysis to show side-by-side.
      if (!analysis) {
        const original = await api.analyzeCustomParlay(legsPayload)
        setAnalysis(original)
      }

      const target = clampInt(counterTargetLegs, 1, Math.min(selectedPicks.length, MAX_CUSTOM_PARLAY_LEGS))
      const counter = await api.buildCounterParlay({
        legs: legsPayload,
        target_legs: counterMode === "flip_all" ? undefined : target,
        mode: counterMode,
        min_edge: 0.0,
      })

      setCounterAnalysis(counter.counter_analysis)
      setCounterCandidates(counter.candidates)
      setIsModalOpen(true)
    } catch (err: any) {
      if (isPaywallError(err)) {
        const pwErr = getPaywallError(err)
        setPaywallError(pwErr)
        setPaywallReason("custom_builder_locked")
        setShowPaywall(true)
        return
      }
      console.error("Counter ticket failed:", err)
      setError(err.message || "Failed to build counter parlay. Please try again.")
    } finally {
      setIsGeneratingCounter(false)
    }
  }

  const handleGenerateCoveragePack = async () => {
    if (selectedPicks.length < 1) return
    if (selectedPicks.length > MAX_CUSTOM_PARLAY_LEGS) {
      setError(`Max ${MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove some legs and try again.`)
      return
    }

    setIsGeneratingCoveragePack(true)
    setError(null)
    try {
      const resp = await api.buildCoveragePack({
        legs: legsPayload,
        max_total_parlays: clampInt(coverageMaxTotalParlays, 1, 20),
        scenario_max: clampInt(coverageScenarioMax, 0, 20),
        round_robin_max: clampInt(coverageRoundRobinMax, 0, 20),
        round_robin_size: clampInt(coverageRoundRobinSize, 2, Math.max(2, Math.min(selectedPicks.length, MAX_CUSTOM_PARLAY_LEGS))),
      })
      setCoveragePack(resp)
      setIsCoverageModalOpen(true)
    } catch (err: any) {
      if (isPaywallError(err)) {
        const pwErr = getPaywallError(err)
        setPaywallError(pwErr)
        setPaywallReason("custom_builder_locked")
        setShowPaywall(true)
        return
      }
      console.error("Coverage pack failed:", err)
      setError(err.message || "Failed to build coverage pack. Please try again.")
    } finally {
      setIsGeneratingCoveragePack(false)
    }
  }

  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }

  if (!canUseCustomBuilder && user) {
    return (
      <>
        <div className="min-h-screen p-6 relative">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl border border-emerald-500/30 p-8 max-w-md text-center shadow-2xl">
              <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                <Lock className="h-8 w-8 text-emerald-400" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Premium Subscription Required</h2>
              <p className="text-gray-400 mb-6">
                The Custom Parlay Builder requires an active Gorilla Premium subscription. Credits cannot be used for this feature. Premium members get 15 custom parlays per day.
              </p>
              <button
                onClick={() => setShowPaywall(true)}
                className="w-full py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
              >
                <Crown className="h-5 w-5" />
                Unlock Premium
              </button>
            </div>
          </div>
          <div className="filter blur-sm pointer-events-none">
            <div className="text-center mb-8">
              <h1 className="text-4xl font-bold text-white mb-2">AI Parlay Builder 🦍</h1>
              <p className="text-white/60 max-w-2xl mx-auto">
                Select your picks and get AI-powered analysis with probability estimates and confidence scores
              </p>
            </div>
          </div>
        </div>

        <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
      </>
    )
  }

  return (
    <>
      <div className="min-h-screen p-6">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <h1 className="text-4xl font-bold text-white">AI Parlay Builder 🦍</h1>
            {isPremium && (
              <span className="bg-gradient-to-r from-emerald-500 to-green-500 text-black text-xs font-bold px-2 py-1 rounded-full">
                <Crown className="h-3 w-3 inline mr-1" />
                Premium
              </span>
            )}
          </div>
          <p className="text-white/60 max-w-2xl mx-auto">
            Select your picks and generate a counter ticket to spot upsets / value against your assumptions.
          </p>
        </div>

        <div className="flex justify-center gap-2 mb-8 flex-wrap">
          {SPORTS.map((sport) => (
            <button
              key={sport.id}
              onClick={() => setSelectedSport(sport.id)}
              disabled={inSeasonBySport[sport.id] === false}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                selectedSport === sport.id
                  ? "bg-[#00DD55] text-black"
                  : inSeasonBySport[sport.id] === false
                    ? "bg-white/5 text-white/30 cursor-not-allowed"
                    : "bg-white/10 text-white/70 hover:bg-[#00DD55]/20"
              }`}
              title={inSeasonBySport[sport.id] === false ? "Not in season" : undefined}
            >
              {sport.icon} {sport.name}
              {inSeasonBySport[sport.id] === false ? (
                <span className="ml-2 text-[10px] font-bold uppercase">Not in season</span>
              ) : null}
            </button>
          ))}
        </div>

        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <h2 className="text-xl font-bold text-white">{SPORTS.find((s) => s.id === selectedSport)?.name} Games</h2>

            {loading && (
              <div className="flex items-center justify-center py-12">
                <span className="text-4xl">🦍</span>
              </div>
            )}

            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">{error}</div>
            )}

            {!loading && !error && games.length === 0 && (
              <div className="text-center text-white/60 py-12">
                No games available for {SPORTS.find((s) => s.id === selectedSport)?.name}
              </div>
            )}

            {!loading &&
              games.map((game) => (
                <GameCard key={game.id} game={game} onSelectPick={handleSelectPick} selectedPicks={selectedPicks} />
              ))}
          </div>

          <div className="lg:col-span-1">
            <ParlaySlip
              picks={selectedPicks}
              onRemovePick={handleRemovePick}
              onAnalyze={handleAnalyze}
              isAnalyzing={isAnalyzing}
              onSave={handleSave}
              isSaving={isSaving}
              onGenerateCounter={handleGenerateCounter}
              isGeneratingCounter={isGeneratingCounter}
              counterMode={counterMode}
              onCounterModeChange={setCounterMode}
              counterTargetLegs={counterTargetLegs}
              onCounterTargetLegsChange={setCounterTargetLegs}
              onGenerateCoveragePack={handleGenerateCoveragePack}
              isGeneratingCoveragePack={isGeneratingCoveragePack}
              coverageMaxTotalParlays={coverageMaxTotalParlays}
              coverageScenarioMax={coverageScenarioMax}
              coverageRoundRobinMax={coverageRoundRobinMax}
              coverageRoundRobinSize={coverageRoundRobinSize}
              onCoverageMaxTotalParlaysChange={setCoverageMaxTotalParlays}
              onCoverageScenarioMaxChange={setCoverageScenarioMax}
              onCoverageRoundRobinMaxChange={setCoverageRoundRobinMax}
              onCoverageRoundRobinSizeChange={setCoverageRoundRobinSize}
            />
          </div>
        </div>

        <AnimatePresence>
          {isModalOpen && analysis && (
            <CustomParlayAnalysisModal
              analysis={analysis}
              counterAnalysis={counterAnalysis}
              counterCandidates={counterCandidates}
              onClose={() => setIsModalOpen(false)}
            />
          )}
        </AnimatePresence>

        <AnimatePresence>
          {isCoverageModalOpen && coveragePack && (
            <CoveragePackModal response={coveragePack} onClose={() => setIsCoverageModalOpen(false)} />
          )}
        </AnimatePresence>
      </div>

      <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
    </>
  )
}


