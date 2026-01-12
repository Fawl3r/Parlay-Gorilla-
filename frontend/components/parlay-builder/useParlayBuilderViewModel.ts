"use client"

import { useEffect, useRef, useState } from "react"
import { toast } from "sonner"

import { api, type NFLWeekInfo, type ParlayResponse, type TripleParlayResponse } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { getPaywallError, isPaywallError, useSubscription, type PaywallError } from "@/lib/subscription-context"
import { getCopy } from "@/lib/content"

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

export function useParlayBuilderViewModel() {
  const [mode, setMode] = useState<BuilderMode>("single")
  const [numLegs, setNumLegs] = useState(5)
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("balanced")
  const [selectedSports, setSelectedSports] = useState<SportOption[]>(["NFL"])
  const [mixSports, setMixSports] = useState(false)
  const [loading, setLoading] = useState(false)
  const [parlay, setParlay] = useState<ParlayResponse | null>(null)
  const [candidateLegCounts, setCandidateLegCounts] = useState<Record<string, number>>({})
  const [loadingLegCounts, setLoadingLegCounts] = useState(false)
  const [tripleParlay, setTripleParlay] = useState<TripleParlayResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

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

  // Enforce single sport selection for free users (but allow switching between sports)
  useEffect(() => {
    if (canUseMultiSport) return

    // Free users can only have one sport selected, but can switch between sports
    if (selectedSports.length > 1) {
      setSelectedSports([selectedSports[0]])
    }
    setMixSports(false)
  }, [canUseMultiSport, selectedSports.length])

  // Fetch candidate leg counts for selected sport
  useEffect(() => {
    if (selectedSports.length === 0) return

    let cancelled = false
    const sport = selectedSports[0]

    async function fetchLegCount() {
      try {
        setLoadingLegCounts(true)
        const { api } = await import('@/lib/api')
        const result = await api.parlay.getCandidateLegsCount(sport, selectedWeek || undefined)
        if (!cancelled) {
          setCandidateLegCounts((prev) => ({
            ...prev,
            [sport]: result.candidate_legs_count,
          }))
        }
      } catch (err) {
        console.error('Failed to fetch candidate leg count:', err)
      } finally {
        if (!cancelled) setLoadingLegCounts(false)
      }
    }

    fetchLegCount()
    return () => {
      cancelled = true
    }
  }, [selectedSports, selectedWeek])

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
      "Filtering candidate legs...",
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
  }

  const openPaywall = (nextReason: PaywallReason, nextError: PaywallError | null) => {
    setPaywallReason(nextReason)
    setPaywallError(nextError)
    setShowPaywall(true)
  }

  const toggleSport = (sport: SportOption) => {
    const isSelected = selectedSports.includes(sport)

    // If user doesn't have multi-sport access, allow switching between single sports
    if (!canUseMultiSport) {
      // Free users can switch to any single sport
      setSelectedSports([sport])
      setMixSports(false)
      return
    }

    // Premium users can select multiple sports
    // Prevent deselecting if it's the only sport
    if (isSelected && selectedSports.length === 1) return

    // If user doesn't have multi-sport access, prevent selecting multiple sports
    if (!isSelected && !canUseMultiSport && selectedSports.length >= 1) {
      openPaywall("feature_premium_only", resolveMultiSportPaywallError())
      return
    }

    setSelectedSports((prev) => (isSelected ? prev.filter((item) => item !== sport) : [...prev, sport]))

    if (!canUseMultiSport && !isSelected && selectedSports.length >= 1) {
      setSelectedSports([sport])
      setMixSports(false)
    }
  }

  const toggleMixSports = () => {
    if (!canUseMultiSport) {
      openPaywall("feature_premium_only", resolveMultiSportPaywallError())
      return
    }

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
      setGenerationProgress(null)
      setStartTime(Date.now())

      const isMultiSportRequest =
        (mixSports && selectedSports.length > 1) || (mode === "triple" && selectedSports.length > 1)

      if (isMultiSportRequest && !canUseMultiSport) {
        openPaywall("feature_premium_only", resolveMultiSportPaywallError())
        setLoading(false)
        setStartTime(null)
        return
      }

      if (!selectedSports.length) {
        setError(mode === "triple" ? "Select at least one sport to build triple parlays." : "Select at least one sport to build a parlay.")
        setLoading(false)
        setStartTime(null)
        return
      }

      if (mode === "triple") {
        const result = await api.suggestTripleParlay({ sports: selectedSports })
        setTripleParlay(result)
        setParlay(null)
      } else {
        const hasNFL = selectedSports.includes("NFL")
        const weekFilter = hasNFL && selectedWeek ? selectedWeek : undefined

        const result = await api.suggestParlay({
          num_legs: numLegs,
          risk_profile: riskProfile,
          sports: selectedSports,
          mix_sports: mixSports && selectedSports.length > 1 && canUseMultiSport,
          week: weekFilter,
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
      }

      setGenerationProgress((prev) => (prev ? { ...prev, progress: 100, status: "Complete!" } : null))
    } catch (err: unknown) {
      console.error("Error generating parlay:", err)

      if (isTimeoutError(err)) {
        setError(
          "Parlay generation timed out. This can happen when the system is processing many requests. " +
            "Please try again in a moment, or try with fewer legs or a different risk profile."
        )
        setParlay(null)
        setTripleParlay(null)
        return
      }

      if (isPaywallError(err)) {
        applyPaywallFromError(err)
        return
      }

      const rawDetail =
        typeof err === "object" && err !== null && "response" in err ? (err as any).response?.data?.detail : undefined
      const detail = formatApiErrorDetail(rawDetail)
      const message = detail || (err instanceof Error ? err.message : "Failed to generate parlay")
      setError(`Error: ${message}`)
      setParlay(null)
      setTripleParlay(null)
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
      loading,
      parlay,
      tripleParlay,
      error,
      isSaving,
      generationProgress,
      availableWeeks,
      selectedWeek,
      currentWeek,
      loadingWeeks,
      user,
      isPremium,
      freeParlaysRemaining,
      canUseMultiSport,
      showPaywall,
      paywallReason,
      paywallError,
      paywallParlayType,
      paywallPrices,
      generateButtonLabel,
      candidateLegCounts,
      loadingLegCounts,
    },
    actions: {
      setNumLegs,
      setRiskProfile,
      setSelectedWeek,
      handleModeChange,
      toggleSport,
      toggleMixSports,
      handleGenerate,
      handleSaveAiParlay,
      handlePaywallClose,
    },
  }
}


