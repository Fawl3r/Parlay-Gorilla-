"use client"

import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { api, type EntitlementsResponse, type InsufficientCandidatesError, type NFLWeekInfo, type ParlayResponse, type ParlaySuggestError, type TripleParlayResponse } from "@/lib/api"
import {
  trackEvent,
  trackAiPicksGenerateAttempt,
  trackAiPicksGenerateSuccess,
  trackActivationSuccess,
  type PremiumUpsellTrigger,
  type PremiumUpsellVariant,
} from "@/lib/track-event"
import { useAuth } from "@/lib/auth-context"
import { useBeginnerMode } from "@/lib/parlay/useBeginnerMode"
import { getQuickStartSeenStored } from "./QuickStartPanel"
import { getPaywallError, isPaywallError, useSubscription, type PaywallError } from "@/lib/subscription-context"
import { getCopy } from "@/lib/content"
import { TRIPLE_DOWNGRADE_TOAST } from "@/lib/parlay/uxLanguageMap"

import type { BuilderMode, RiskProfile, SportOption } from "./types"
import type { PaywallReason } from "@/components/paywall/PaywallModal"

type ParlayBuilderProgress = {
  status: string
  progress: number
  elapsed: number
  estimated: number
}

type PaywallParlayType = "single" | "multi"

function resolveMultiSportPaywallError(): PaywallError {
  return {
    error_code: "PREMIUM_REQUIRED",
    message: "Multi-sport parlays are a premium feature. Upgrade to unlock this feature!",
    remaining_today: 0,
    feature: "multi_sport",
    upgrade_url: "/premium",
  }
}

function isTimeoutError(error: unknown) {
  const anyErr = error as any
  return (
    anyErr?.isTimeout ||
    anyErr?.code === "ECONNABORTED" ||
    anyErr?.code === "TIMEOUT" ||
    (error instanceof Error && error.message?.includes("timeout"))
  )
}

function formatApiErrorDetail(detail: unknown): string | null {
  if (detail === null || detail === undefined) return null
  if (typeof detail === "string") return detail

  // FastAPI validation errors: [{ loc: [...], msg: "...", type: "..." }, ...]
  if (Array.isArray(detail)) {
    const parts = detail
      .map((err: any) => {
        const loc = Array.isArray(err?.loc) ? err.loc.filter((p: any) => p !== "body").join(".") : ""
        const msg = String(err?.msg || err?.message || "Invalid value")
        return loc ? `${loc}: ${msg}` : msg
      })
      .filter(Boolean)
    return parts.length ? parts.join("; ") : null
  }

  if (typeof detail === "object") {
    const anyDetail = detail as any
    if (typeof anyDetail?.detail === "string") return anyDetail.detail
    if (typeof anyDetail?.message === "string") return anyDetail.message
    try {
      return JSON.stringify(detail)
    } catch {
      return String(detail)
    }
  }

  return String(detail)
}

function getEstimatedTimeSeconds(params: {
  mode: BuilderMode
  numLegs: number
  selectedSportsCount: number
  riskProfile: RiskProfile
}) {
  if (params.mode === "triple") return 90

  const baseTime = 15
  const legMultiplier = params.numLegs * 1.5
  const sportMultiplier = params.selectedSportsCount > 1 ? 20 : 0
  const riskMultiplier = params.riskProfile === "degen" ? 15 : params.riskProfile === "balanced" ? 8 : 0
  return Math.ceil(baseTime + legMultiplier + sportMultiplier + riskMultiplier)
}

const SESSION_KEY_ACTIVATION_FIRED = "pg_activation_success_fired"

export function useParlayBuilderViewModel() {
  const { isBeginnerMode } = useBeginnerMode()
  const [mode, setMode] = useState<BuilderMode>("single")
  const [numLegs, setNumLegs] = useState(5)
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("balanced")
  const [selectedSports, setSelectedSports] = useState<SportOption[]>(["NFL"])
  const [mixSports, setMixSports] = useState(false)
  const [mixSportsManuallySet, setMixSportsManuallySet] = useState(false)
  const [entitlements, setEntitlements] = useState<EntitlementsResponse | null>(null)
  const [includePlayerProps, setIncludePlayerProps] = useState(false)
  const [loading, setLoading] = useState(false)
  const [parlay, setParlay] = useState<ParlayResponse | null>(null)
  const [candidateLegCounts, setCandidateLegCounts] = useState<Record<string, number>>({})
  const [eligibilityReasons, setEligibilityReasons] = useState<string[]>([])
  const [eligibilityUniqueGames, setEligibilityUniqueGames] = useState<number | null>(null)
  const [insufficientCandidatesError, setInsufficientCandidatesError] = useState<InsufficientCandidatesError | null>(null)
  const [loadingLegCounts, setLoadingLegCounts] = useState(false)
  const [tripleParlay, setTripleParlay] = useState<TripleParlayResponse | null>(null)
  const [tripleMode, setTripleMode] = useState(false) // Triple (3 picks) high-confidence only
  const [strongEdges, setStrongEdges] = useState<number | null>(null) // from preflight when tripleMode
  const [parlayDowngraded, setParlayDowngraded] = useState(false) // last response was downgraded (Triple -> 2 legs)
  const [parlayDowngradeExplain, setParlayDowngradeExplain] = useState<string | null>(null)
  const [parlayDowngradeHaveStrong, setParlayDowngradeHaveStrong] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [suggestError, setSuggestError] = useState<ParlaySuggestError | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [lastQuickActionId, setLastQuickActionId] = useState<string | null>(null)

  // Progress tracking
  const [generationProgress, setGenerationProgress] = useState<ParlayBuilderProgress | null>(null)
  const [startTime, setStartTime] = useState<number | null>(null)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Week selection state
  const [availableWeeks, setAvailableWeeks] = useState<NFLWeekInfo[]>([])
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null)
  const [currentWeek, setCurrentWeek] = useState<number | null>(null)
  const [loadingWeeks, setLoadingWeeks] = useState(true)

  // Subscription & Paywall state
  const { user } = useAuth()
  const { isPremium, freeParlaysRemaining, refreshStatus, canUseMultiSport } = useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("ai_parlay_limit_reached")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)
  const [paywallParlayType, setPaywallParlayType] = useState<PaywallParlayType>("single")
  const [paywallPrices, setPaywallPrices] = useState<{ single?: number; multi?: number }>({})
  const [paywallUpsellTrigger, setPaywallUpsellTrigger] = useState<PremiumUpsellTrigger | null>(null)
  const [paywallUpsellVariant, setPaywallUpsellVariant] = useState<PremiumUpsellVariant>("A")

  // Server entitlements (single source of truth for mix_sports, max_legs)
  useEffect(() => {
    let cancelled = false
    api.getEntitlements().then((data) => {
      if (!cancelled) setEntitlements(data)
    }).catch((err) => {
      if (!cancelled) console.error("Failed to fetch entitlements:", err)
    })
    return () => { cancelled = true }
  }, [user?.id])

  // Auto mix sports: when 2+ sports selected and not manually overridden, turn on mix
  useEffect(() => {
    if (mixSportsManuallySet) return
    const shouldMix = selectedSports.length >= 2
    setMixSports(shouldMix)
  }, [mixSportsManuallySet, selectedSports.length])

  // Cap numLegs by server max_legs when entitlements load
  const maxLegsFromEntitlements = entitlements?.features?.max_legs ?? 20
  const mixSportsAllowed = entitlements ? entitlements.features.mix_sports : canUseMultiSport
  useEffect(() => {
    if (entitlements == null) return
    const maxLegs = entitlements.features.max_legs
    setNumLegs((prev) => (prev > maxLegs ? maxLegs : prev))
  }, [entitlements?.features?.max_legs])

  // Fetch NFL weeks on mount and refresh periodically
  useEffect(() => {
    let cancelled = false

    async function fetchWeeks() {
      try {
        setLoadingWeeks(true)
        const weeksData = await api.getNFLWeeks()
        if (cancelled) return

        // Only show available weeks (current and future, not past)
        const available = weeksData.weeks.filter((w) => w.is_available)
        setAvailableWeeks(available)
        setCurrentWeek(weeksData.current_week)

        // Default to current week if available, otherwise first available week
        if (weeksData.current_week) {
          const currentWeekInfo = available.find((w) => w.week === weeksData.current_week)
          if (currentWeekInfo) {
            setSelectedWeek(weeksData.current_week)
          } else if (available.length > 0) {
            setSelectedWeek(available[0].week)
          }
        } else if (available.length > 0) {
          setSelectedWeek(available[0].week)
        }
      } catch (err) {
        console.error("Failed to fetch NFL weeks:", err)
      } finally {
        if (!cancelled) setLoadingWeeks(false)
      }
    }

    fetchWeeks()
    const interval = setInterval(fetchWeeks, 60 * 60 * 1000)
    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [])

  // Enforce single sport when mix_sports not allowed (server entitlements or subscription fallback)
  useEffect(() => {
    if (mixSportsAllowed) return
    if (selectedSports.length > 1) {
      setSelectedSports([selectedSports[0]])
    }
    setMixSports(false)
    setMixSportsManuallySet(false)
  }, [mixSportsAllowed, selectedSports.length])

  // Track Triple availability for analytics (triple_available when strongEdges >= 3, triple_disabled when < 3)
  useEffect(() => {
    if (!tripleMode || strongEdges === null) return
    if (strongEdges >= 3) {
      trackEvent("triple_available", { have_strong: strongEdges, have_eligible: candidateLegCounts[selectedSports[0]] })
    } else {
      trackEvent("triple_disabled", { have_strong: strongEdges, have_eligible: candidateLegCounts[selectedSports[0]] })
    }
  }, [tripleMode, strongEdges, selectedSports, candidateLegCounts])

  // Fetch candidate leg counts for selected sport; when tripleMode also get strong_edges
  useEffect(() => {
    if (selectedSports.length === 0) return

    let cancelled = false
    const sport = selectedSports[0]
    const weekFilter = sport === "NFL" && selectedWeek ? selectedWeek : undefined
    const legsToFetch = tripleMode ? 3 : numLegs

    async function fetchLegCount() {
      try {
        setLoadingLegCounts(true)
        const { api } = await import('@/lib/api')
        const result = await api.getCandidateLegsCount(
          sport,
          weekFilter ?? undefined,
          legsToFetch,
          includePlayerProps && isPremium ? true : undefined,
          tripleMode ? 'TRIPLE' : undefined
        )
        if (!cancelled) {
          setCandidateLegCounts((prev) => ({ ...prev, [sport]: result.candidate_legs_count }))
          setEligibilityReasons(result.top_exclusion_reasons ?? [])
          setEligibilityUniqueGames(result.unique_games ?? null)
          if (tripleMode && result.strong_edges !== undefined) {
            setStrongEdges(result.strong_edges)
          } else if (!tripleMode) {
            setStrongEdges(null)
          }
        }
      } catch (err) {
        console.error('Failed to fetch candidate leg count:', err)
        if (!cancelled) setEligibilityReasons([])
        if (!cancelled && tripleMode) setStrongEdges(null)
      } finally {
        if (!cancelled) setLoadingLegCounts(false)
      }
    }

    fetchLegCount()
    return () => { cancelled = true }
  }, [selectedSports, selectedWeek, numLegs, includePlayerProps, isPremium, tripleMode])

  // Progress tracking effect
  useEffect(() => {
    if (!loading || !startTime) {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      return
    }

    const estimated = getEstimatedTimeSeconds({
      mode,
      numLegs,
      selectedSportsCount: selectedSports.length,
      riskProfile,
    })

    const statusMessages = [
      "Analyzing available games...",
      "Calculating win probabilities...",
      "Finding your best picks...",
      "Optimizing parlay selection...",
      "Generating AI explanations...",
      "Finalizing parlay...",
    ]

    let messageIndex = 0
    const updateProgress = () => {
      const elapsed = (Date.now() - startTime) / 1000
      const progress = Math.min(95, (elapsed / estimated) * 100)

      const newMessageIndex = Math.min(Math.floor((progress / 100) * statusMessages.length), statusMessages.length - 1)
      if (newMessageIndex !== messageIndex) messageIndex = newMessageIndex

      setGenerationProgress({
        status: statusMessages[messageIndex],
        progress,
        elapsed,
        estimated,
      })
    }

    progressIntervalRef.current = setInterval(updateProgress, 500)
    updateProgress()

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
    }
  }, [loading, startTime, mode, numLegs, selectedSports.length, riskProfile])

  const handleModeChange = (nextMode: BuilderMode) => {
    if (mode === nextMode) return
    setMode(nextMode)
    setError(null)
    setParlay(null)
    setTripleParlay(null)
    setParlayDowngraded(false)
  }

  const setTripleModeEnabled = (enabled: boolean) => {
    setTripleMode(enabled)
    if (enabled) {
      setNumLegs(3)
      trackEvent('triple_selected', { requested_markets: 'parlay', sports_mode: selectedSports.length > 1 ? 'mixed' : 'single' })
    } else {
      setParlayDowngraded(false)
      setParlayDowngradeExplain(null)
      setParlayDowngradeHaveStrong(null)
    }
  }

  const openPaywall = (nextReason: PaywallReason, nextError: PaywallError | null, upsellContext?: { trigger: PremiumUpsellTrigger; variant: PremiumUpsellVariant }) => {
    setPaywallReason(nextReason)
    setPaywallError(nextError)
    if (nextReason === "feature_premium_only" && upsellContext) {
      setPaywallUpsellTrigger(upsellContext.trigger)
      setPaywallUpsellVariant(upsellContext.variant)
    } else {
      setPaywallUpsellTrigger(null)
    }
    setShowPaywall(true)
  }

  const toggleSport = (sport: SportOption) => {
    const isSelected = selectedSports.includes(sport)

    // If user doesn't have multi-sport access, allow switching between single sports
    if (!mixSportsAllowed) {
      // Free users can switch to any single sport
      setSelectedSports([sport])
      setMixSports(false)
      return
    }

    // Premium users can select multiple sports
    // Prevent deselecting if it's the only sport
    if (isSelected && selectedSports.length === 1) return

    // If user doesn't have multi-sport access, prevent selecting multiple sports
    if (!isSelected && !mixSportsAllowed && selectedSports.length >= 1) {
      openPaywall("feature_premium_only", resolveMultiSportPaywallError(), { trigger: "mixed_sports_locked", variant: "A" })
      return
    }

    setSelectedSports((prev) => (isSelected ? prev.filter((item) => item !== sport) : [...prev, sport]))

    if (!mixSportsAllowed && !isSelected && selectedSports.length >= 1) {
      setSelectedSports([sport])
      setMixSports(false)
    }
  }

  const toggleMixSports = () => {
    if (!mixSportsAllowed) {
      openPaywall("feature_premium_only", resolveMultiSportPaywallError(), { trigger: "mixed_sports_locked", variant: "A" })
      return
    }
    setMixSportsManuallySet(true)
    setMixSports((prev) => !prev)
  }

  const clearProgressSoon = () => {
    setTimeout(() => {
      setGenerationProgress(null)
    }, 1000)
  }

  const applyPaywallFromError = (err: unknown) => {
    const pwErr = getPaywallError(err)
    setPaywallError(pwErr)

    const isMultiSport = mixSports && selectedSports.length > 1
    setPaywallParlayType(isMultiSport ? "multi" : "single")

    if (pwErr?.single_price || pwErr?.multi_price) {
      setPaywallPrices({ single: pwErr.single_price, multi: pwErr.multi_price })
    }

    if (pwErr?.error_code === "PAY_PER_USE_REQUIRED") {
      setPaywallReason("pay_per_use_required")
    } else if (pwErr?.error_code === "FREE_LIMIT_REACHED") {
      setPaywallReason("ai_parlay_limit_reached")
    } else if (pwErr?.error_code === "PREMIUM_REQUIRED") {
      setPaywallReason("feature_premium_only")
      setPaywallUpsellTrigger("mixed_sports_locked")
      setPaywallUpsellVariant("A")
    } else if (pwErr?.error_code === "LOGIN_REQUIRED") {
      setPaywallReason("login_required")
    }

    setShowPaywall(true)
    setParlay(null)
    setTripleParlay(null)
  }

  const handleGenerate = async () => {
    try {
      setLoading(true)
      setError(null)
      setSuggestError(null)
      setGenerationProgress(null)
      setStartTime(Date.now())

      const isMultiSportRequest =
        (mixSports && selectedSports.length > 1) || (mode === "triple" && selectedSports.length > 1)

      if (isMultiSportRequest && !mixSportsAllowed) {
        openPaywall("feature_premium_only", resolveMultiSportPaywallError())
        setLoading(false)
        setStartTime(null)
        return
      }

      if (!selectedSports.length) {
        setError("Select at least one sport to get started.")
        setLoading(false)
        setStartTime(null)
        return
      }

      const requestMode = mode === "triple" ? "TRIPLE" : numLegs === 2 ? "DOUBLE" : "SINGLE"
      const numPicks = mode === "triple" ? 3 : numLegs
      trackAiPicksGenerateAttempt({
        beginner_mode: isBeginnerMode,
        request_mode: requestMode,
        num_picks: numPicks,
        selected_sports: selectedSports.slice(),
      })

      if (mode === "triple") {
        const result = await api.suggestTripleParlay({ sports: selectedSports })
        setTripleParlay(result)
        setParlay(null)
        const timeToSuccessMs = startTime != null ? Date.now() - startTime : 0
        trackAiPicksGenerateSuccess({
          beginner_mode: isBeginnerMode,
          request_mode: "TRIPLE",
          num_picks: 3,
          fallback_used: false,
          downgraded: false,
          time_to_success_ms: timeToSuccessMs,
        })
        try {
          if (typeof window !== "undefined" && sessionStorage.getItem(SESSION_KEY_ACTIVATION_FIRED) !== "1") {
            sessionStorage.setItem(SESSION_KEY_ACTIVATION_FIRED, "1")
            trackActivationSuccess({
              beginner_mode: isBeginnerMode,
              used_quick_start: getQuickStartSeenStored(),
              request_mode: "TRIPLE",
              time_to_first_success_ms: timeToSuccessMs,
            })
          }
        } catch {
          // ignore
        }
      } else {
        const hasNFL = selectedSports.includes("NFL")
        const weekFilter = hasNFL && selectedWeek ? selectedWeek : undefined

        const result = await api.suggestParlay({
          num_legs: tripleMode ? 3 : numLegs,
          risk_profile: riskProfile,
          request_mode: tripleMode ? 'TRIPLE' : undefined,
          sports: selectedSports,
          mix_sports: mixSports && selectedSports.length > 1 && mixSportsAllowed,
          week: weekFilter,
          include_player_props: includePlayerProps && isPremium,
        })
        if (!result?.legs?.length || result.num_legs <= 0) {
          setError(
            "Parlay generation returned no picks. Please try again in a moment or choose different sport(s)."
          )
          setParlay(null)
          setTripleParlay(null)
          return
        }
        setParlay(result)
        setTripleParlay(null)
        setInsufficientCandidatesError(null)
        setParlayDowngraded(!!result.downgraded)
        const timeToSuccessMs = startTime != null ? Date.now() - startTime : 0
        trackAiPicksGenerateSuccess({
          beginner_mode: isBeginnerMode,
          request_mode: requestMode,
          num_picks: result.num_legs ?? numLegs,
          fallback_used: !!result.fallback_used,
          downgraded: !!result.downgraded,
          time_to_success_ms: timeToSuccessMs,
        })
        try {
          if (typeof window !== "undefined" && sessionStorage.getItem(SESSION_KEY_ACTIVATION_FIRED) !== "1") {
            sessionStorage.setItem(SESSION_KEY_ACTIVATION_FIRED, "1")
            trackActivationSuccess({
              beginner_mode: isBeginnerMode,
              used_quick_start: getQuickStartSeenStored(),
              request_mode: requestMode === "DOUBLE" ? "SINGLE" : requestMode,
              time_to_first_success_ms: timeToSuccessMs,
            })
          }
        } catch {
          // ignore
        }
        if (lastQuickActionId) {
          trackEvent("ai_picks_quick_action_result", {
            action_id: lastQuickActionId,
            debug_id: (result as any)?.debug_id ?? undefined,
            result: "success",
          })
          setLastQuickActionId(null)
        }
        setParlayDowngradeExplain(result.explain?.short_reason ?? null)
        setParlayDowngradeHaveStrong(result.downgrade_summary?.have_strong ?? null)
        if (result.downgraded) {
          toast.info(TRIPLE_DOWNGRADE_TOAST)
        }
        if (result.fallback_used && result.fallback_stage) {
          trackEvent("ai_picks_fallback_used", { fallback_stage: result.fallback_stage })
        }
        if (tripleMode && result.downgraded) {
          trackEvent("triple_downgraded_to_double", {
            have_eligible: result.downgrade_summary?.have_eligible,
            have_strong: result.downgrade_summary?.have_strong,
            debug_id: (result as any).debug_id,
          })
        }
        if (tripleMode && result.mode_returned === "TRIPLE" && !result.downgraded) {
          trackEvent("triple_generated", {
            have_eligible: result.downgrade_summary?.have_eligible,
            have_strong: 3,
          })
        }
      }

      setGenerationProgress((prev) => (prev ? { ...prev, progress: 100, status: "Complete!" } : null))
    } catch (err: unknown) {
      console.error("Error generating parlay:", err)

      if (isTimeoutError(err)) {
        setError(
          "Parlay generation timed out. This can happen when the system is processing many requests. " +
            "Please try again in a moment, or try with fewer picks or a different risk profile."
        )
        setParlay(null)
        setTripleParlay(null)
        return
      }

      if (isPaywallError(err)) {
        applyPaywallFromError(err)
        return
      }

      // 409 with InsufficientCandidatesError (needed, have, top_exclusion_reasons, debug_id)
      const insufficient = (err as any)?.insufficientCandidatesError as InsufficientCandidatesError | undefined
      if (insufficient) {
        setInsufficientCandidatesError(insufficient)
        setSuggestError({ code: "insufficient_candidates", message: insufficient.message, hint: insufficient.hint ?? undefined, meta: insufficient.meta ?? undefined })
        setError(insufficient.message)
        setParlay(null)
        setTripleParlay(null)
        setParlayDowngraded(false)
        trackEvent("ai_picks_generate_fail", { debug_id: insufficient.debug_id, needed: insufficient.needed, have: insufficient.have })
        const firstReason = insufficient.top_exclusion_reasons?.[0]
        const reason = typeof firstReason === "object" && firstReason !== null && "reason" in firstReason
          ? (firstReason as { reason: string; count?: number }).reason
          : "insufficient_candidates"
        const count = typeof firstReason === "object" && firstReason !== null && "count" in firstReason
          ? (firstReason as { reason: string; count?: number }).count
          : undefined
        trackEvent("ai_picks_generate_fail_reason", {
          reason,
          ...(count !== undefined && { count }),
          debug_id: insufficient.debug_id,
        })
        if (lastQuickActionId) {
          trackEvent("ai_picks_quick_action_result", {
            action_id: lastQuickActionId,
            debug_id: insufficient.debug_id,
            result: "fail",
            fail_reason: reason,
          })
          setLastQuickActionId(null)
        }
        if (tripleMode) {
          trackEvent("triple_failed_no_legs", {
            have_eligible: insufficient.have,
            have_strong: (insufficient.meta as any)?.strong_edges,
            debug_id: insufficient.debug_id,
          })
        }
        return
      }

      // 401/402/403/422 with typed ParlaySuggestError
      const typedSuggest = (err as any)?.parlaySuggestError as ParlaySuggestError | undefined
      if (typedSuggest) {
        setInsufficientCandidatesError(null)
        setSuggestError(typedSuggest)
        setError(typedSuggest.message)
        setParlay(null)
        setTripleParlay(null)
        if (typedSuggest.code === "insufficient_candidates") {
          trackEvent("ai_picks_generate_fail", { reason: "legacy_422" })
          trackEvent("ai_picks_generate_fail_reason", { reason: typedSuggest.code })
        }
        if (typedSuggest.code === "login_required") {
          setPaywallReason("login_required")
          setPaywallError({ error_code: "LOGIN_REQUIRED", message: typedSuggest.message, remaining_today: 0, feature: "ai_parlay", upgrade_url: "/login" })
          setShowPaywall(true)
        } else if (typedSuggest.code === "premium_required") {
          setPaywallReason("feature_premium_only")
          setPaywallError({ error_code: "PREMIUM_REQUIRED", message: typedSuggest.message, remaining_today: 0, feature: "mix_sports", upgrade_url: "/premium" })
          setShowPaywall(true)
        } else if (typedSuggest.code === "credits_required") {
          setPaywallReason("pay_per_use_required")
          setPaywallError({ error_code: "PAY_PER_USE_REQUIRED", message: typedSuggest.message, remaining_today: 0, feature: "ai_parlay", upgrade_url: "/billing" })
          setShowPaywall(true)
        }
        return
      }

      const rawDetail =
        typeof err === "object" && err !== null && "response" in err ? (err as any).response?.data?.detail : undefined
      const statusCode = typeof err === "object" && err !== null && "response" in err ? (err as any).response?.status : undefined
      const detail = formatApiErrorDetail(rawDetail)
      
      setSuggestError(null)
      setInsufficientCandidatesError(null)
      // Handle 503 errors (service unavailable - not enough games)
      if (statusCode === 503) {
        const errorMessage = detail || "Not enough games available. Try again later or select a different sport/week."
        setError(errorMessage)
      } else {
        const message = detail || (err instanceof Error ? err.message : "Failed to generate parlay")
        setError(`Error: ${message}`)
      }
      
      setParlay(null)
      setTripleParlay(null)
      if (lastQuickActionId) {
        trackEvent("ai_picks_quick_action_result", {
          action_id: lastQuickActionId,
          debug_id: undefined,
          result: "fail",
          fail_reason: "error",
        })
        setLastQuickActionId(null)
      }
    } finally {
      setLoading(false)
      setStartTime(null)
      clearProgressSoon()
    }
  }

  const handleSaveAiParlay = async () => {
    if (!parlay) return

    setIsSaving(true)
    try {
      const saved = await api.saveAiParlay({
        title: `Gorilla Parlay (${parlay.num_legs} legs)`,
        legs: parlay.legs,
      })
      toast.success(getCopy("notifications.success.slipSaved"))
    } catch (err: any) {
      console.error("Failed to save Gorilla Parlay:", err)
      toast.error(err?.response?.data?.detail || err?.message || getCopy("notifications.error.saveFailed"))
    } finally {
      setIsSaving(false)
    }
  }

  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }

  const generateButtonLabel = mode === "triple" ? "Generate Triple Parlays" : "Generate Parlay"

  return {
    state: {
      // UI state
      mode,
      numLegs,
      riskProfile,
      selectedSports,
      mixSports,
      includePlayerProps,
      loading,
      parlay,
      tripleParlay,
      error,
      suggestError,
      entitlements,
      mixSportsAllowed,
      maxLegsFromEntitlements,
      isSaving,
      generationProgress,
      availableWeeks,
      selectedWeek,
      currentWeek,
      loadingWeeks,
      user,
      isPremium,
      freeParlaysRemaining,
      showPaywall,
      paywallReason,
      paywallError,
      paywallParlayType,
      paywallPrices,
      paywallUpsellTrigger,
      paywallUpsellVariant,
      generateButtonLabel,
      candidateLegCounts,
      eligibilityReasons,
      eligibilityUniqueGames,
      insufficientCandidatesError,
      loadingLegCounts,
      tripleMode,
      strongEdges,
      parlayDowngraded,
      parlayDowngradeExplain,
      parlayDowngradeHaveStrong,
      lastQuickActionId,
    },
    actions: {
      setNumLegs: (value: number) => {
        setNumLegs(value)
        if (value !== 3) setTripleMode(false)
      },
      setRiskProfile,
      setSelectedWeek,
      setSelectedSports,
      setMixSports,
      setIncludePlayerProps,
      setError,
      setSuggestError,
      setInsufficientCandidatesError,
      setLastQuickActionId,
      handleModeChange,
      setTripleModeEnabled,
      toggleSport,
      toggleMixSports,
      handleGenerate,
      handleSaveAiParlay,
      handlePaywallClose,
    },
  }
}


