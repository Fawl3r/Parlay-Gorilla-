"use client"

import { useEffect, useMemo, useRef, useState } from "react"

import { api } from "@/lib/api"
import type {
  CounterLegCandidate,
  CounterParlayMode,
  CustomParlayAnalysisResponse,
  CustomParlayLeg,
  GameResponse,
  ParlayCoverageResponse,
} from "@/lib/api"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"
import { useAuth } from "@/lib/auth-context"
import { getPaywallError, isPaywallError, type PaywallError, useSubscription } from "@/lib/subscription-context"
import type { PaywallReason } from "@/components/paywall/PaywallModal"
import { toast } from "sonner"
import { useInscriptionCelebration } from "@/components/inscriptions/InscriptionCelebrationProvider"
import { useInscriptionConfirmationWatcher } from "@/components/inscriptions/hooks/useInscriptionConfirmationWatcher"
import { SolscanUrlBuilder } from "@/lib/inscriptions/SolscanUrlBuilder"

import { MAX_CUSTOM_PARLAY_LEGS } from "@/components/custom-parlay/ParlaySlip"
import type { SelectedPick } from "@/components/custom-parlay/types"
import {
  CustomParlayPrefillResolver,
  type CustomParlayPrefillRequest,
} from "@/components/custom-parlay/prefill/CustomParlayPrefillResolver"
import { CustomParlayBuilderView } from "@/components/custom-parlay/CustomParlayBuilderView"

const SPORTS = [
  { id: "nfl", name: "NFL", icon: "🏈" },
  { id: "nba", name: "NBA", icon: "🏀" },
  { id: "nhl", name: "NHL", icon: "🏒" },
  { id: "mlb", name: "MLB", icon: "⚾" },
  { id: "ncaaf", name: "NCAAF", icon: "🏈" },
  { id: "ncaab", name: "NCAAB", icon: "🏀" },
  { id: "mls", name: "MLS", icon: "⚽" },
  { id: "epl", name: "EPL", icon: "⚽" },
  { id: "laliga", name: "La Liga", icon: "⚽" },
  { id: "ufc", name: "UFC", icon: "🥊" },
  { id: "boxing", name: "Boxing", icon: "🥊" },
] as const

function clampInt(value: number, min: number, max: number) {
  if (!Number.isFinite(value)) return min
  return Math.max(min, Math.min(max, Math.trunc(value)))
}

export function CustomParlayBuilder({ prefillRequest }: { prefillRequest?: CustomParlayPrefillRequest }) {
  const [selectedSport, setSelectedSport] = useState<string>(SPORTS[0].id)
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})
  const [games, setGames] = useState<GameResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedPicks, setSelectedPicks] = useState<SelectedPick[]>([])
  const prefillAppliedRef = useRef(false)

  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysis, setAnalysis] = useState<CustomParlayAnalysisResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [savedParlayId, setSavedParlayId] = useState<string | null>(null)
  const [verifyOnChain, setVerifyOnChain] = useState(false)

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
  const { canUseCustomBuilder, isPremium, isCreditUser, refreshStatus, customAiParlaysRemaining, customAiParlaysLimit, inscriptionCostUsd } =
    useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("custom_builder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)

  const { celebrateInscription } = useInscriptionCelebration()
  const { watchInscription } = useInscriptionConfirmationWatcher({
    onConfirmed: (item) => {
      const solscanUrl = item.solscan_url || (item.inscription_tx ? SolscanUrlBuilder.forTx(item.inscription_tx) : null)
      if (!solscanUrl) return
      celebrateInscription({
        savedParlayId: item.id,
        parlayTitle: item.title,
        solscanUrl,
        inscriptionTx: item.inscription_tx,
      })
    },
    onFailed: () => {
      toast.error("Verification failed (you can retry later)")
    },
  })

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
    const selectedIsComingSoon = sportsUiPolicy.isComingSoon(selectedSport)
    if (!Object.keys(inSeasonBySport).length && !selectedIsComingSoon) return

    if (!selectedIsComingSoon && inSeasonBySport[selectedSport] !== false) return

    const firstAvailable = SPORTS.find(
      (s) => !sportsUiPolicy.isComingSoon(s.id) && inSeasonBySport[s.id] !== false
    )?.id
    if (firstAvailable && firstAvailable !== selectedSport) setSelectedSport(firstAvailable)
  }, [inSeasonBySport, selectedSport])

  // If we were deep-linked from an analysis page, force the builder sport first.
  useEffect(() => {
    const requested = String(prefillRequest?.sport || "").toLowerCase().trim()
    if (!requested) return
    if (requested === selectedSport) return
    if (!SPORTS.some((s) => s.id === requested)) return
    if (sportsUiPolicy.isComingSoon(requested)) return
    setSelectedSport(requested)
  }, [prefillRequest?.sport, selectedSport])

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

  // Apply deep-link prefill (once) after games load.
  useEffect(() => {
    if (prefillAppliedRef.current) return
    if (loading) return

    const req = prefillRequest
    const requestedSport = String(req?.sport || "").toLowerCase().trim()
    if (!requestedSport || requestedSport !== selectedSport) return

    const gameId = String(req?.gameId || "").trim()
    if (!gameId) return

    const game = games.find((g) => String(g.id) === gameId)
    if (!game) return

    const resolved = CustomParlayPrefillResolver.resolve(game, {
      sport: requestedSport,
      gameId,
      marketType: req?.marketType,
      pick: req?.pick,
      point: req?.point,
    })

    if (!resolved) {
      toast.error("Couldn’t prefill that pick. Please select it manually.")
      prefillAppliedRef.current = true
      return
    }

    handleSelectPick(resolved)
    toast.success("Pick added to your slip")
    prefillAppliedRef.current = true
  }, [games, handleSelectPick, loading, prefillRequest, selectedSport])

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

      toast.success(`Saved v${saved.version}!`)

      if (verifyOnChain) {
        try {
          const updated = await api.queueInscription(saved.id)
          const status = (updated.inscription_status || "").toLowerCase()
          if (status === "queued") {
            toast.success("Verification queued")
            watchInscription(updated.id)
          } else if (status === "confirmed") {
            toast.success("Verification confirmed")
            const solscanUrl =
              updated.solscan_url || (updated.inscription_tx ? SolscanUrlBuilder.forTx(updated.inscription_tx) : null)
            if (solscanUrl) {
              celebrateInscription({
                savedParlayId: updated.id,
                parlayTitle: saved.title,
                solscanUrl,
                inscriptionTx: updated.inscription_tx,
              })
            }
          }
          else if (status === "failed") toast.error("Verification queue failed (you can retry later)")
          await refreshStatus()
        } catch (err: any) {
          if (isPaywallError(err)) {
            const pwErr = getPaywallError(err)
            setPaywallError(pwErr)
            if (pwErr?.error_code === "LOGIN_REQUIRED") {
              setPaywallReason("login_required")
            } else if (pwErr?.error_code === "PREMIUM_REQUIRED") {
              setPaywallReason("feature_premium_only")
            } else if ((pwErr?.feature || "").toLowerCase() === "inscriptions") {
              setPaywallReason("inscriptions_overage")
            } else {
              setPaywallReason("feature_premium_only")
            }
            setShowPaywall(true)
            return
          }
          toast.error(err?.response?.data?.detail || err?.message || "Failed to queue verification")
        }
      }
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

  return (
    <CustomParlayBuilderView
      userPresent={Boolean(user)}
      canUseCustomBuilder={canUseCustomBuilder}
      isCreditUser={isCreditUser}
      isPremium={isPremium}
      sports={SPORTS}
      selectedSport={selectedSport}
      inSeasonBySport={inSeasonBySport}
      onSelectSport={setSelectedSport}
      games={games}
      loading={loading}
      error={error}
      selectedPicks={selectedPicks}
      onSelectPick={handleSelectPick}
      onRemovePick={handleRemovePick}
      onAnalyze={handleAnalyze}
      isAnalyzing={isAnalyzing}
      onSave={handleSave}
      isSaving={isSaving}
      verifyOnChain={verifyOnChain}
      onVerifyOnChainChange={setVerifyOnChain}
      inscriptionCostUsd={inscriptionCostUsd}
      customAiRemaining={customAiParlaysRemaining}
      customAiLimit={customAiParlaysLimit}
      onGenerateCounter={handleGenerateCounter}
      isGeneratingCounter={isGeneratingCounter}
      counterMode={counterMode}
      onCounterModeChange={setCounterMode}
      counterTargetLegs={counterTargetLegs}
      onCounterTargetLegsChange={setCounterTargetLegs}
      onGenerateCoveragePack={handleGenerateCoveragePack}
      isGeneratingCoveragePack={isGeneratingCoveragePack}
      coveragePack={coveragePack}
      isCoverageModalOpen={isCoverageModalOpen}
      onCloseCoverageModal={() => setIsCoverageModalOpen(false)}
      coverageMaxTotalParlays={coverageMaxTotalParlays}
      coverageScenarioMax={coverageScenarioMax}
      coverageRoundRobinMax={coverageRoundRobinMax}
      coverageRoundRobinSize={coverageRoundRobinSize}
      onCoverageMaxTotalParlaysChange={setCoverageMaxTotalParlays}
      onCoverageScenarioMaxChange={setCoverageScenarioMax}
      onCoverageRoundRobinMaxChange={setCoverageRoundRobinMax}
      onCoverageRoundRobinSizeChange={setCoverageRoundRobinSize}
      analysis={analysis}
      counterAnalysis={counterAnalysis}
      counterCandidates={counterCandidates}
      isModalOpen={isModalOpen}
      onCloseModal={() => setIsModalOpen(false)}
      showPaywall={showPaywall}
      paywallReason={paywallReason}
      paywallError={paywallError}
      onOpenPaywall={() => setShowPaywall(true)}
      onClosePaywall={handlePaywallClose}
    />
  )
}


