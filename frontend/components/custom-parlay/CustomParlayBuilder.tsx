"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"

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
import { getCopy } from "@/lib/content"
import {
  loadSlip,
  saveSlip,
  clearSlip as clearPersistedSlip,
  filterValidPicks,
} from "@/lib/custom-parlay/customBuilderPersistence"
import {
  buildTemplateSlip,
  getRequiredCount,
  type TemplateId,
} from "@/lib/custom-parlay/templateEngine"
import {
  trackCustomBuilderOpened,
  trackCustomBuilderPickAdded,
  trackCustomBuilderPickRemoved,
  trackCustomBuilderAnalyzeClicked,
  trackCustomBuilderAnalyzeSuccess,
  trackCustomBuilderAnalyzeFail,
  trackCustomBuilderSaveClicked,
  trackCustomBuilderSaveSuccess,
  trackCustomBuilderSaveFail,
  trackCustomBuilderPaywallShown,
  trackCustomBuilderUpgradeClicked,
  trackCustomBuilderClearSlip,
  trackCustomBuilderTemplateClicked,
  trackCustomBuilderTemplatePartial,
  trackCustomBuilderTemplateApplied,
  trackCustomBuilderTemplateFollowthroughShown,
} from "@/lib/track-event"
import { useBeginnerMode } from "@/lib/parlay/useBeginnerMode"

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

  const { isBeginnerMode } = useBeginnerMode()

  // Subscription & Paywall
  const { user } = useAuth()
  const { status, canUseCustomBuilder, isPremium, isCreditUser, refreshStatus } = useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("custom_builder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)
  const [creditsOverlayDismissed, setCreditsOverlayDismissed] = useState(false)
  const [templateFollowThroughTrigger, setTemplateFollowThroughTrigger] = useState(false)

  const builderAccessSummary = useMemo(() => {
    const tier = (status?.tier ?? "unknown") as "free" | "premium" | "unknown"
    const freeRemaining = status?.balances?.free_parlays_remaining ?? null
    const premiumRemaining = status?.balances?.premium_custom_builder_remaining ?? null
    const credits = status?.balances?.credit_balance ?? status?.credit_balance ?? 0
    return {
      builderTier: tier,
      freeCustomRemaining: freeRemaining,
      premiumCustomRemaining: premiumRemaining,
      creditsRemaining: credits,
    }
  }, [status])

  const openedFiredRef = useRef(false)
  const paywallShownFiredRef = useRef(false)
  const blockedOverlayShownFiredRef = useRef(false)

  const handleOpenPaywall = useCallback(() => {
    trackCustomBuilderUpgradeClicked({ source: "custom_builder_overlay" })
    setShowPaywall(true)
  }, [])

  const handleDismissCreditsOverlay = useCallback(() => {
    setCreditsOverlayDismissed(true)
  }, [])

  const userId = user?.id ?? null
  const restoredForUserIdRef = useRef<string | null | undefined>(undefined)

  // Restore slip from persistence once per userId (after user is known).
  useEffect(() => {
    if (restoredForUserIdRef.current === userId) return
    restoredForUserIdRef.current = userId
    const restored = loadSlip(userId)
    if (!restored) return
    if (restored.selectedSport && !sportsUiPolicy.isComingSoon(restored.selectedSport)) {
      setSelectedSport(restored.selectedSport)
    }
    const picks = (restored.picks ?? []).slice(0, MAX_CUSTOM_PARLAY_LEGS)
    if (picks.length > 0) setSelectedPicks(picks)
  }, [userId])

  // Fire custom_builder_opened once on mount.
  useEffect(() => {
    if (openedFiredRef.current) return
    openedFiredRef.current = true
    const credits = status?.balances?.credit_balance ?? status?.credit_balance ?? 0
    trackCustomBuilderOpened({
      sport: selectedSport,
      is_premium: isPremium,
      credits: typeof credits === "number" ? credits : 0,
    })
  }, [selectedSport, isPremium, status])

  // Debounced save slip (250ms).
  const saveSlipDebounced = useRef<ReturnType<typeof setTimeout> | null>(null)
  useEffect(() => {
    if (saveSlipDebounced.current) clearTimeout(saveSlipDebounced.current)
    saveSlipDebounced.current = setTimeout(() => {
      saveSlipDebounced.current = null
      saveSlip(userId, {
        v: 1,
        savedAt: Date.now(),
        selectedSport,
        picks: selectedPicks,
      })
    }, 250)
    return () => {
      if (saveSlipDebounced.current) clearTimeout(saveSlipDebounced.current)
    }
  }, [userId, selectedSport, selectedPicks])

  // When games load, re-filter picks and drop invalid.
  useEffect(() => {
    if (games.length === 0 || selectedPicks.length === 0) return
    const valid = filterValidPicks(selectedPicks, games)
    if (valid.length !== selectedPicks.length) {
      setSelectedPicks(valid)
    }
  }, [games])

  const blockedNoCredits = Boolean(user) && !canUseCustomBuilder && (builderAccessSummary.creditsRemaining ?? 0) <= 0
  const tier = builderAccessSummary.builderTier
  useEffect(() => {
    if (blockedNoCredits && !blockedOverlayShownFiredRef.current) {
      blockedOverlayShownFiredRef.current = true
      trackCustomBuilderPaywallShown({
        reason: tier === "free" ? "weekly_limit" : "premium_required",
        tier,
      })
    }
    if (!blockedNoCredits) blockedOverlayShownFiredRef.current = false
  }, [blockedNoCredits, tier])

  useEffect(() => {
    if (showPaywall && !paywallShownFiredRef.current) {
      paywallShownFiredRef.current = true
      const code = paywallError?.error_code
      const reason =
        code === "FREE_LIMIT_REACHED"
          ? "weekly_limit"
          : code === "PAY_PER_USE_REQUIRED"
            ? "credits_needed"
            : code === "PREMIUM_REQUIRED"
              ? "premium_required"
              : "unknown"
      trackCustomBuilderPaywallShown({ reason, tier })
    }
    if (!showPaywall) paywallShownFiredRef.current = false
  }, [showPaywall, paywallError?.error_code, tier])

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
      trackCustomBuilderPickRemoved({ sport: selectedSport, market_type: pick.market_type, is_premium: isPremium })
      return
    }

    const hasSameGameMarket = selectedPicks.some((p) => p.game_id === pick.game_id && p.market_type === pick.market_type)
    const wouldIncreaseCount = !hasSameGameMarket
    if (wouldIncreaseCount && selectedPicks.length >= MAX_CUSTOM_PARLAY_LEGS) {
      setError(`You can analyze up to ${MAX_CUSTOM_PARLAY_LEGS} picks at once. Remove a pick to add another.`)
      return
    }

    setSelectedPicks((picks) => [...picks.filter((p) => !(p.game_id === pick.game_id && p.market_type === pick.market_type)), pick])
    trackCustomBuilderPickAdded({ sport: selectedSport, market_type: pick.market_type, is_premium: isPremium })
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
      toast.error(getCopy("states.errors.loadFailed"))
      prefillAppliedRef.current = true
      return
    }

    handleSelectPick(resolved)
    toast.success(getCopy("notifications.success.checkComplete"))
    prefillAppliedRef.current = true
  }, [games, handleSelectPick, loading, prefillRequest, selectedSport])

  const handleRemovePick = (index: number) => {
    setError(null)
    const pick = selectedPicks[index]
    if (pick) trackCustomBuilderPickRemoved({ sport: selectedSport, market_type: pick.market_type, is_premium: isPremium })
    setSelectedPicks((picks) => picks.filter((_, i) => i !== index))
  }

  const handleClearSlip = useCallback(() => {
    setSelectedPicks([])
    setAnalysis(null)
    setCounterAnalysis(null)
    setCounterCandidates(null)
    setCoveragePack(null)
    setSavedParlayId(null)
    setError(null)
    clearPersistedSlip(userId)
    toast.success("Cleared. Start fresh anytime.")
    trackCustomBuilderClearSlip({ sport: selectedSport, pick_count: selectedPicks.length })
  }, [userId, selectedSport, selectedPicks.length])

  const handleApplyTemplate = useCallback(
    (templateId: TemplateId) => {
      const credits = builderAccessSummary.creditsRemaining ?? 0
      trackCustomBuilderTemplateClicked({
        template_id: templateId,
        sport: selectedSport,
        is_premium: isPremium,
        credits: typeof credits === "number" ? credits : 0,
      })
      const picks = buildTemplateSlip(templateId, games, {
        maxPicks: MAX_CUSTOM_PARLAY_LEGS,
        selectedSport,
      })
      const needed = getRequiredCount(templateId)
      const isPartial = picks.length < needed
      if (isPartial) {
        const msg =
          isBeginnerMode
            ? "Not enough games yet. Try again later."
            : "Not enough posted games for that template. Try all upcoming or fewer picks."
        if (picks.length > 0) {
          toast.info(msg, {
            action: {
              label: "Analyze what I've got",
              onClick: () => {
                handleAnalyze()
              },
            },
          })
        } else {
          toast.info(msg, {
            action: {
              label: "Include all upcoming",
              onClick: () => {
                if (typeof window !== "undefined") {
                  window.location.hash = "games"
                  document.querySelector("[data-custom-builder-games]")?.scrollIntoView?.({ behavior: "smooth" })
                }
              },
            },
          })
        }
        trackCustomBuilderTemplatePartial({
          template_id: templateId,
          found: picks.length,
          needed,
        })
      }
      setSelectedPicks(picks)
      setError(null)
      if (picks.length > 0) {
        trackCustomBuilderTemplateApplied({
          template_id: templateId,
          pick_count: picks.length,
          sport: selectedSport,
          is_premium: isPremium,
        })
        setTemplateFollowThroughTrigger(true)
        setTimeout(() => setTemplateFollowThroughTrigger(false), 1500)
      }
    },
    [games, selectedSport, isPremium, builderAccessSummary.creditsRemaining, isBeginnerMode]
  )

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
      setError(`You can analyze up to ${MAX_CUSTOM_PARLAY_LEGS} picks at once. Remove some picks and try again.`)
      return
    }

    const hasPlayerProps = selectedPicks.some((p) => p.market_type === "player_props")
    trackCustomBuilderAnalyzeClicked({
      sport: selectedSport,
      pick_count: selectedPicks.length,
      has_player_props: hasPlayerProps,
      is_premium: isPremium,
    })

    setIsAnalyzing(true)
    setError(null)
    try {
      const result = await api.analyzeCustomParlay(legsPayload)
      setAnalysis(result)
      setIsModalOpen(true)
      trackCustomBuilderAnalyzeSuccess({
        sport: selectedSport,
        pick_count: selectedPicks.length,
        has_player_props: hasPlayerProps,
        is_premium: isPremium,
        verification_created: Boolean(result?.verification?.id),
      })
    } catch (err: any) {
      if (isPaywallError(err)) {
        const pwErr = getPaywallError(err)
        setPaywallError(pwErr)
        setPaywallReason("custom_builder_locked")
        setShowPaywall(true)
        trackCustomBuilderAnalyzeFail({
          sport: selectedSport,
          pick_count: selectedPicks.length,
          is_premium: isPremium,
          reason: "paywall",
          error_code: pwErr?.error_code,
        })
        return
      }
      const is422 = err?.response?.status === 422
      trackCustomBuilderAnalyzeFail({
        sport: selectedSport,
        pick_count: selectedPicks.length,
        is_premium: isPremium,
        reason: is422 ? "validation" : "unknown",
        error_code: err?.response?.data?.detail,
      })
      console.error("Analysis failed:", err)
      setError(err.message || "Failed to analyze parlay. Please try again.")
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleSave = async (title?: string) => {
    if (selectedPicks.length < 1) return
    if (selectedPicks.length > MAX_CUSTOM_PARLAY_LEGS) {
      setError(`You can analyze up to ${MAX_CUSTOM_PARLAY_LEGS} picks at once. Remove some picks and try again.`)
      return
    }

    trackCustomBuilderSaveClicked({
      sport: selectedSport,
      pick_count: selectedPicks.length,
      is_premium: isPremium,
    })

    setIsSaving(true)
    setError(null)
    try {
      const saved = await api.saveCustomParlay({
        saved_parlay_id: savedParlayId || undefined,
        title: title || `Custom Parlay (${selectedPicks.length} picks)`,
        legs: legsPayload,
      })
      setSavedParlayId(saved.id)
      trackCustomBuilderSaveSuccess({
        sport: selectedSport,
        pick_count: selectedPicks.length,
        is_premium: isPremium,
      })
      toast.success(`Saved v${saved.version}!`)
    } catch (err: any) {
      trackCustomBuilderSaveFail({
        sport: selectedSport,
        pick_count: selectedPicks.length,
        is_premium: isPremium,
      })
      console.error("Save failed:", err)
      toast.error(err?.response?.data?.detail || err?.message || "Failed to save parlay")
    } finally {
      setIsSaving(false)
    }
  }

  const handleGenerateCounter = async () => {
    // Temporarily disabled - feature under maintenance
    setError("Counter / Upset Ticket feature is temporarily disabled for maintenance. Please check back soon.")
    return
  }

  const handleGenerateCoveragePack = async () => {
    // Temporarily disabled - feature under maintenance
    setError("Upset Possibilities / Coverage Pack feature is temporarily disabled for maintenance. Please check back soon.")
    return
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
      builderAccessSummary={builderAccessSummary}
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
      onClearSlip={handleClearSlip}
      onApplyTemplate={handleApplyTemplate}
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
      onOpenPaywall={handleOpenPaywall}
      onClosePaywall={handlePaywallClose}
      creditsOverlayDismissed={creditsOverlayDismissed}
      onDismissCreditsOverlay={handleDismissCreditsOverlay}
      templateFollowThroughTrigger={templateFollowThroughTrigger}
      isBeginnerMode={isBeginnerMode}
      onFollowThroughShown={trackCustomBuilderTemplateFollowthroughShown}
    />
  )
}


