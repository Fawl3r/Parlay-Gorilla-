"use client"

import { useState, useEffect, useRef } from "react"
import { motion } from "framer-motion"
import { api, ParlayResponse, TripleParlayResponse, NFLWeekInfo } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle, TrendingUp, Calendar, Crown, Lock } from "lucide-react"
import { cn } from "@/lib/utils"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { TripleParlayDisplay } from "@/components/TripleParlayDisplay"
import { getPickLabel, getMarketLabel, getConfidenceTextClass } from "@/lib/parlayFormatting"
import { ShareParlayButton } from "@/components/social/ShareParlayButton"
import { useSubscription, isPaywallError, getPaywallError, PaywallError } from "@/lib/subscription-context"
import { PaywallModal, PaywallReason } from "@/components/paywall/PaywallModal"
import { useAuth } from "@/lib/auth-context"
import { toast } from "sonner"

const SPORT_OPTIONS = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "MLS", "EPL"] as const
type BuilderMode = "single" | "triple"
type SportOption = (typeof SPORT_OPTIONS)[number]

// Sport badges with a consistent landing-page neon palette (minimalistic UI).
const SPORT_COLORS: Record<SportOption, { bg: string; text: string; border: string }> = {
  NFL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NBA: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NHL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  MLB: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NCAAF: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NCAAB: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  MLS: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  EPL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
}

export function ParlayBuilder() {
  const [mode, setMode] = useState<BuilderMode>("single")
  const [numLegs, setNumLegs] = useState(5)
  const [riskProfile, setRiskProfile] = useState<"conservative" | "balanced" | "degen">("balanced")
  const [selectedSports, setSelectedSports] = useState<SportOption[]>(["NFL"])
  const [mixSports, setMixSports] = useState(false)
  const [loading, setLoading] = useState(false)
  const [parlay, setParlay] = useState<ParlayResponse | null>(null)
  const [tripleParlay, setTripleParlay] = useState<TripleParlayResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  
  // Progress tracking
  const [generationProgress, setGenerationProgress] = useState<{
    status: string
    progress: number
    elapsed: number
    estimated: number
  } | null>(null)
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
  const [paywallParlayType, setPaywallParlayType] = useState<'single' | 'multi'>('single')
  const [paywallPrices, setPaywallPrices] = useState<{ single?: number; multi?: number }>({})
  

  // Fetch NFL weeks on mount and refresh periodically
  useEffect(() => {
    async function fetchWeeks() {
      try {
        setLoadingWeeks(true)
        const weeksData = await api.getNFLWeeks()
        // Only show available weeks (current and future, not past)
        const available = weeksData.weeks.filter(w => w.is_available)
        setAvailableWeeks(available)
        setCurrentWeek(weeksData.current_week)
        // Default to current week if available, otherwise first available week
        if (weeksData.current_week) {
          const currentWeekInfo = available.find(w => w.week === weeksData.current_week)
          if (currentWeekInfo) {
            setSelectedWeek(weeksData.current_week)
          } else if (available.length > 0) {
            // If current week not available (past), use first available (next week)
            setSelectedWeek(available[0].week)
          }
        } else if (available.length > 0) {
          setSelectedWeek(available[0].week)
        }
      } catch (err) {
        console.error("Failed to fetch NFL weeks:", err)
      } finally {
        setLoadingWeeks(false)
      }
    }
    fetchWeeks()
    // Refresh every hour to catch week transitions
    const interval = setInterval(fetchWeeks, 60 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  // Enforce single sport selection for free users
  useEffect(() => {
    if (!canUseMultiSport) {
      // If user doesn't have multi-sport access, ensure only one sport is selected
      setSelectedSports(prev => {
        if (prev.length > 1) {
          return [prev[0]]
        }
        return prev
      })
      // Disable mix sports toggle for free users
      setMixSports(prev => {
        if (prev) {
          return false
        }
        return prev
      })
    }
  }, [canUseMultiSport])

  const handleModeChange = (nextMode: BuilderMode) => {
    if (mode === nextMode) {
      return
    }
    setMode(nextMode)
    setError(null)
    setParlay(null)
    setTripleParlay(null)
  }

  const toggleSport = (sport: SportOption) => {
    const isSelected = selectedSports.includes(sport)
    
    // Prevent deselecting if it's the only sport
    if (isSelected && selectedSports.length === 1) {
      return
    }
    
    // If user doesn't have multi-sport access, prevent selecting multiple sports
    if (!isSelected && !canUseMultiSport && selectedSports.length >= 1) {
      // Show paywall for multi-sport feature
      setPaywallReason('feature_premium_only')
      setPaywallError({
        error_code: 'PREMIUM_REQUIRED',
        message: 'Multi-sport parlays are a premium feature. Upgrade to unlock this feature!',
        remaining_today: 0,
        feature: 'multi_sport',
        upgrade_url: '/premium',
      })
      setShowPaywall(true)
      return
    }
    
    setSelectedSports((prev) =>
      isSelected ? prev.filter((item) => item !== sport) : [...prev, sport]
    )
    
    // If user doesn't have multi-sport access and now has multiple sports selected, reset to single sport
    if (!canUseMultiSport && !isSelected && selectedSports.length >= 1) {
      // This shouldn't happen due to the check above, but as a safety measure
      setSelectedSports([sport])
      setMixSports(false)
    }
  }

  // Calculate estimated generation time based on complexity
  const getEstimatedTime = (): number => {
    if (mode === "triple") {
      return 90 // Triple parlays take longer (3 parlays)
    }
    
    const baseTime = 15 // Base time in seconds
    const legMultiplier = numLegs * 1.5 // 1.5 seconds per leg
    const sportMultiplier = selectedSports.length > 1 ? 20 : 0 // Extra time for mixed sports
    const riskMultiplier = riskProfile === "degen" ? 15 : riskProfile === "balanced" ? 8 : 0
    
    return Math.ceil(baseTime + legMultiplier + sportMultiplier + riskMultiplier)
  }

  // Progress tracking effect
  useEffect(() => {
    if (!loading || !startTime) {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      return
    }

    const estimated = getEstimatedTime()
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
      
      // Update status message based on progress
      const newMessageIndex = Math.min(
        Math.floor((progress / 100) * statusMessages.length),
        statusMessages.length - 1
      )
      if (newMessageIndex !== messageIndex) {
        messageIndex = newMessageIndex
      }

      setGenerationProgress({
        status: statusMessages[messageIndex],
        progress,
        elapsed,
        estimated,
      })
    }

    // Update every 500ms
    progressIntervalRef.current = setInterval(updateProgress, 500)
    updateProgress() // Initial update

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
    }
  }, [loading, startTime, mode, numLegs, selectedSports.length, riskProfile])

  const handleGenerate = async () => {
    try {
      setLoading(true)
      setError(null)
      setGenerationProgress(null)
      setStartTime(Date.now())

      // Check multi-sport restrictions before generating
      const isMultiSportRequest = (mixSports && selectedSports.length > 1) || (mode === "triple" && selectedSports.length > 1)
      if (isMultiSportRequest && !canUseMultiSport) {
        setPaywallReason('feature_premium_only')
        setPaywallError({
          error_code: 'PREMIUM_REQUIRED',
          message: 'Multi-sport parlays are a premium feature. Upgrade to unlock this feature!',
          remaining_today: 0,
          feature: 'multi_sport',
          upgrade_url: '/premium',
        })
        setShowPaywall(true)
        setLoading(false)
        setStartTime(null)
        return
      }

      if (mode === "triple") {
        if (!selectedSports.length) {
          setError("Select at least one sport to build triple parlays.")
          setLoading(false)
          setStartTime(null)
          return
        }
        const result = await api.suggestTripleParlay({ sports: selectedSports })
        setTripleParlay(result)
        setParlay(null)
      } else {
        // Single parlay with optional mixed sports
        if (!selectedSports.length) {
          setError("Select at least one sport to build a parlay.")
          setLoading(false)
          setStartTime(null)
          return
        }
        
        // Include week filter for NFL
        const hasNFL = selectedSports.includes("NFL")
        const weekFilter = hasNFL && selectedWeek ? selectedWeek : undefined
        
        const result = await api.suggestParlay({
          num_legs: numLegs,
          risk_profile: riskProfile,
          sports: selectedSports,
          mix_sports: mixSports && selectedSports.length > 1 && canUseMultiSport,
          week: weekFilter,
        })
        setParlay(result)
        setTripleParlay(null)
      }
      
      // Set progress to 100% on completion
      setGenerationProgress(prev => prev ? { ...prev, progress: 100, status: "Complete!" } : null)
    } catch (error: unknown) {
      console.error("Error generating parlay:", error)
      
      // Check if this is a timeout error
      if (
        (error as any)?.isTimeout ||
        (error as any)?.code === 'ECONNABORTED' ||
        (error as any)?.code === 'TIMEOUT' ||
        (error instanceof Error && error.message?.includes('timeout'))
      ) {
        setError(
          "Parlay generation timed out. This can happen when the system is processing many requests. " +
          "Please try again in a moment, or try with fewer legs or a different risk profile."
        )
        setParlay(null)
        setTripleParlay(null)
        return
      }
      
      // Check if this is a paywall error (402)
      if (isPaywallError(error)) {
        const paywallErr = getPaywallError(error)
        setPaywallError(paywallErr)
        
        // Determine parlay type from current selection
        const isMultiSport = mixSports && selectedSports.length > 1
        setPaywallParlayType(isMultiSport ? 'multi' : 'single')
        
        // Extract pricing if provided by backend
        if (paywallErr?.single_price || paywallErr?.multi_price) {
          setPaywallPrices({
            single: paywallErr.single_price,
            multi: paywallErr.multi_price,
          })
        }
        
        if (paywallErr?.error_code === 'PAY_PER_USE_REQUIRED') {
          setPaywallReason('pay_per_use_required')
        } else if (paywallErr?.error_code === 'FREE_LIMIT_REACHED') {
          setPaywallReason('ai_parlay_limit_reached')
        } else if (paywallErr?.error_code === 'PREMIUM_REQUIRED') {
          setPaywallReason('feature_premium_only')
        } else if (paywallErr?.error_code === 'LOGIN_REQUIRED') {
          setPaywallReason('login_required')
        }
        
        setShowPaywall(true)
        setParlay(null)
        setTripleParlay(null)
        return
      }
      
      const detail =
        typeof error === "object" && error !== null && "response" in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined
      const message = detail || (error instanceof Error ? error.message : "Failed to generate parlay")
      setError(`Error: ${message}`)
      setParlay(null)
      setTripleParlay(null)
    } finally {
      setLoading(false)
      setStartTime(null)
      // Clear progress after a short delay to show completion
      setTimeout(() => {
        setGenerationProgress(null)
      }, 1000)
    }
  }

  const handleSaveAiParlay = async () => {
    if (!parlay) return
    setIsSaving(true)
    try {
      const saved = await api.saveAiParlay({
        title: `AI Parlay (${parlay.num_legs} legs)`,
        legs: parlay.legs,
      })
      toast.success(`Saved parlay (${saved.parlay_type})`)
    } catch (err: any) {
      console.error("Failed to save AI parlay:", err)
      toast.error(err?.response?.data?.detail || err?.message || "Failed to save parlay")
    } finally {
      setIsSaving(false)
    }
  }
  
  // Handle paywall close and refresh status
  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus() // Refresh subscription status in case user upgraded
  }

  const generateButtonLabel = mode === "triple" ? "Generate Triple Parlays" : "Generate Parlay"

  return (
    <>
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle>AI Parlay Builder</CardTitle>
              <CardDescription>
                Switch between a single high-precision suggestion and the triple-parlay flight (Safe,
                Balanced, Degen) with live Confidence Rings and AI commentary.
              </CardDescription>
            </div>
            {/* Subscription Status Badge */}
            {user && (
              <div className="flex-shrink-0">
                {isPremium ? (
                  <Badge 
                    className="bg-[#00DD55] text-black border-0"
                    style={{
                      boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                    }}
                  >
                    <Crown className="h-3 w-3 mr-1" />
                    Premium
                  </Badge>
                ) : (
                  <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                    {freeParlaysRemaining > 0 
                      ? `${freeParlaysRemaining} free parlay${freeParlaysRemaining > 1 ? 's' : ''} left today`
                      : 'Daily limit reached'
                    }
                  </Badge>
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
          <div>
            <label className="text-sm font-medium mb-2 block">Mode</label>
            <div className="grid grid-cols-2 gap-2 sm:gap-3">
              {[
                { value: "single", label: "Single Parlay", hint: "Manual controls" },
                { value: "triple", label: "Triple Parlays", hint: "Safe / Balanced / Degen" },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleModeChange(option.value as BuilderMode)}
                  className={cn(
                    "rounded-md border-2 p-2.5 sm:p-3 text-left transition-colors min-h-[60px] sm:min-h-[auto]",
                    mode === option.value
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  <div className="font-medium text-sm sm:text-base">{option.label}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">{option.hint}</div>
                </button>
              ))}
            </div>
          </div>

          {mode === "single" ? (
            <>
              {/* Sports Selection for Single Mode */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Sports to Include</label>
                  {!canUseMultiSport && (
                    <Badge variant="outline" className="text-xs border-amber-500/50 text-amber-400">
                      <Lock className="h-3 w-3 mr-1" />
                      Single sport only
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {SPORT_OPTIONS.map((sport) => {
                    const selected = selectedSports.includes(sport)
                    const colors = SPORT_COLORS[sport]
                    const canSelect = canUseMultiSport || selected || selectedSports.length === 0
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        disabled={!canSelect}
                        className={cn(
                          "rounded-full border px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all min-h-[36px] sm:min-h-[auto] relative",
                          selected
                            ? `${colors.bg} ${colors.text} ${colors.border} border-2`
                            : "border-border text-muted-foreground hover:border-primary/50",
                          !canSelect && "opacity-50 cursor-not-allowed"
                        )}
                        title={!canSelect ? "Multi-sport parlays require Premium. Upgrade to unlock!" : undefined}
                      >
                        {sport}
                        {!canSelect && !selected && (
                          <Lock className="absolute -top-1 -right-1 h-3 w-3 text-amber-400 bg-background rounded-full p-0.5" />
                        )}
                      </button>
                    )
                  })}
                </div>
                
                {/* Multi-sport restriction message */}
                {!canUseMultiSport && selectedSports.length === 1 && (
                  <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <p className="text-xs text-amber-300 flex items-center gap-1">
                      <Lock className="h-3 w-3" />
                      <span>Multi-sport parlays are a premium feature. <a href="/premium" className="underline font-medium">Upgrade to unlock</a></span>
                    </p>
                  </div>
                )}
                
                {/* Mix Sports Toggle */}
                {selectedSports.length > 1 && (
                  <div className="mt-3 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => {
                        if (!canUseMultiSport) {
                          setPaywallReason('feature_premium_only')
                          setPaywallError({
                            error_code: 'PREMIUM_REQUIRED',
                            message: 'Multi-sport parlays are a premium feature. Upgrade to unlock this feature!',
                            remaining_today: 0,
                            feature: 'multi_sport',
                            upgrade_url: '/premium',
                          })
                          setShowPaywall(true)
                          return
                        }
                        setMixSports(!mixSports)
                      }}
                      disabled={!canUseMultiSport}
                      className={cn(
                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                        mixSports && canUseMultiSport ? "bg-primary" : "bg-muted",
                        !canUseMultiSport && "opacity-50 cursor-not-allowed"
                      )}
                      title={!canUseMultiSport ? "Multi-sport mixing requires Premium" : undefined}
                    >
                      <span
                        className={cn(
                          "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                          mixSports && canUseMultiSport ? "translate-x-6" : "translate-x-1"
                        )}
                      />
                    </button>
                    <span className="text-sm text-muted-foreground">
                      Mix sports in parlay
                      {!canUseMultiSport && (
                        <span className="ml-1 text-amber-400">
                          <Lock className="h-3 w-3 inline" />
                        </span>
                      )}
                      <span className="block text-xs">
                        {mixSports && canUseMultiSport ? "Legs will be drawn from all selected sports" : "Single sport per parlay"}
                      </span>
                    </span>
                  </div>
                )}
                
                <p className="text-xs text-muted-foreground mt-2">
                  Selected: {selectedSports.join(", ")}
                  {mixSports && selectedSports.length > 1 && canUseMultiSport && " (Mixed)"}
                </p>
              </div>

              {/* Week Selection for NFL */}
              {selectedSports.includes("NFL") && (
                <div>
                  <label className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    NFL Week
                  </label>
                  {loadingWeeks ? (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading weeks...
                    </div>
                  ) : availableWeeks.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {availableWeeks.map((weekInfo) => (
                        <button
                          key={weekInfo.week}
                          type="button"
                          onClick={() => setSelectedWeek(weekInfo.week)}
                          className={cn(
                            "rounded-lg border px-3 py-2 text-sm font-medium transition-all",
                            selectedWeek === weekInfo.week
                              ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                              : "border-border text-muted-foreground hover:border-emerald-500/50",
                            weekInfo.is_current && "ring-2 ring-emerald-500/30"
                          )}
                        >
                          {weekInfo.label}
                          {weekInfo.is_current && (
                            <span className="ml-1 text-xs text-emerald-400">(Current)</span>
                          )}
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No weeks available. Check back when the NFL season starts.
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-2">
                    Select which week's games to build your AI parlay from.
                    {selectedWeek && ` Building from Week ${selectedWeek} games.`}
                  </p>
                </div>
              )}

              <div>
                <label className="text-sm font-medium mb-2 block">Number of Legs: {numLegs}</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={numLegs}
                  onChange={(e) => setNumLegs(Number(e.target.value))}
                  className="w-full accent-primary"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-1">
                  <span>1</span>
                  <span>20</span>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">Risk Profile</label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {(["conservative", "balanced", "degen"] as const).map((profile) => (
                    <button
                      key={profile}
                      type="button"
                      onClick={() => setRiskProfile(profile)}
                      className={cn(
                        "p-2.5 sm:p-3 rounded-md border-2 transition-colors min-h-[60px] sm:min-h-[auto]",
                        riskProfile === profile
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      )}
                    >
                      <div className="font-medium capitalize text-sm sm:text-base">{profile}</div>
                      <div className="text-xs text-muted-foreground mt-0.5 sm:mt-1">
                        {profile === "conservative" && "High confidence only"}
                        {profile === "balanced" && "Mix of picks"}
                        {profile === "degen" && "Higher risk, higher reward"}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium">Sports to Mix</label>
                  {!canUseMultiSport && (
                    <Badge variant="outline" className="text-xs border-amber-500/50 text-amber-400">
                      <Lock className="h-3 w-3 mr-1" />
                      Premium only
                    </Badge>
                  )}
                </div>
                <div className="flex flex-wrap gap-2">
                  {SPORT_OPTIONS.map((sport) => {
                    const selected = selectedSports.includes(sport)
                    const colors = SPORT_COLORS[sport]
                    const canSelect = canUseMultiSport || selected || selectedSports.length === 0
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        disabled={!canSelect}
                        className={cn(
                          "rounded-full border px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all min-h-[36px] sm:min-h-[auto] relative",
                          selected
                            ? `${colors.bg} ${colors.text} ${colors.border} border-2`
                            : "border-border text-muted-foreground hover:border-primary/50",
                          !canSelect && "opacity-50 cursor-not-allowed"
                        )}
                        title={!canSelect ? "Multi-sport parlays require Premium. Upgrade to unlock!" : undefined}
                      >
                        {sport}
                        {!canSelect && !selected && (
                          <Lock className="absolute -top-1 -right-1 h-3 w-3 text-amber-400 bg-background rounded-full p-0.5" />
                        )}
                      </button>
                    )
                  })}
                </div>
                
                {/* Multi-sport restriction message */}
                {!canUseMultiSport && (
                  <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                    <p className="text-xs text-amber-300 flex items-center gap-1">
                      <Lock className="h-3 w-3" />
                      <span>Triple parlay multi-sport mixing is a premium feature. <a href="/premium" className="underline font-medium">Upgrade to unlock</a></span>
                    </p>
                  </div>
                )}
                
                <p className="text-xs text-muted-foreground mt-2">
                  Safe parlays use 3-6 legs, Balanced uses 7-12, and Degen pushes 13-20 legs. Mixing
                  leagues keeps correlation low and maximizes edge discovery.
                </p>
                <p className="text-xs font-medium mt-1">Selected: {selectedSports.join(", ")}</p>
              </div>
            </>
          )}

          {/* Generation Time Warning */}
          {!loading && (
            <div className="mb-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <p className="text-xs text-amber-200 flex items-start gap-2">
                <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                <span>
                  <strong>⏱️ Generation Time:</strong> This process typically takes <strong>30 seconds to 5 minutes depending on traffic</strong>. 
                  Our AI analyzes thousands of games, calculates win probabilities, and optimizes your parlay selection. 
                  <strong className="block mt-1">Please do not close this page during generation.</strong>
                  <span className="block mt-1 text-amber-300/80">This will improve in future updates.</span>
                </span>
              </p>
            </div>
          )}

          {/* Progress Display */}
          {loading && generationProgress && (
            <Card className="mb-4 border-primary/30 bg-card/80">
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Status Message */}
                  <div className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                    <p className="text-sm font-medium text-foreground">{generationProgress.status}</p>
                  </div>
                  
                  {/* Progress Bar */}
                  <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary to-[#39ff14]"
                      initial={{ width: 0 }}
                      animate={{ width: `${generationProgress.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  
                  {/* Time Information */}
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>
                      Elapsed: {Math.floor(generationProgress.elapsed)}s
                    </span>
                    <span>
                      Est. remaining: {Math.max(0, Math.ceil(generationProgress.estimated - generationProgress.elapsed))}s
                    </span>
                    <span>
                      {Math.floor(generationProgress.progress)}% complete
                    </span>
                  </div>
                  
                  {/* Timeout Warning */}
                  {generationProgress.elapsed > 120 && generationProgress.elapsed < 150 && (
                    <div className="p-2 bg-amber-500/10 border border-amber-500/30 rounded text-xs text-amber-200">
                      ⚠️ Generation is taking longer than usual. This is normal for complex parlays. Please continue waiting...
                    </div>
                  )}
                  {generationProgress.elapsed >= 150 && (
                    <div className="p-2 bg-orange-500/10 border border-orange-500/30 rounded text-xs text-orange-200">
                      ⏳ Still processing... Complex parlays can take up to 3 minutes. We're working on it!
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          <Button onClick={handleGenerate} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating Parlay...
              </>
            ) : (
              <>
                <TrendingUp className="mr-2 h-4 w-4" />
                {generateButtonLabel}
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card>
          <CardContent className="flex items-center justify-center gap-3 py-6">
            <AlertCircle className="h-6 w-6 text-destructive" />
            <div>
              <h3 className="font-semibold text-destructive">Something went wrong</h3>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {parlay && (
        <Card>
          <CardHeader className="p-4 sm:p-6">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <CardTitle className="text-lg sm:text-xl">{parlay.num_legs}-Leg Parlay</CardTitle>
                <CardDescription className="capitalize text-xs sm:text-sm">{parlay.risk_profile} profile</CardDescription>
              </div>
              <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  Hit Probability {(parlay.parlay_hit_prob * 100).toFixed(1)}%
                </Badge>
                <ShareParlayButton parlayId={parlay.id} />
                <Button variant="outline" size="sm" onClick={handleSaveAiParlay} disabled={isSaving}>
                  {isSaving ? "Saving..." : "Save Parlay"}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
            <div className="flex flex-col gap-4 sm:gap-6 lg:flex-row lg:items-start">
              {/* Model Confidence Ring - uses model_confidence if available */}
              <ConfidenceRing 
                score={parlay.model_confidence !== undefined 
                  ? parlay.model_confidence * 100 
                  : parlay.overall_confidence
                } 
                label="Model Confidence" 
                size={140} 
              />
              <div className="flex-1">
                <p className="text-sm text-muted-foreground">AI Model Confidence</p>
                <p className={cn("text-3xl font-bold", getConfidenceTextClass(
                  parlay.model_confidence !== undefined 
                    ? parlay.model_confidence * 100 
                    : parlay.overall_confidence
                ))}>
                  {parlay.model_confidence !== undefined 
                    ? (parlay.model_confidence * 100).toFixed(1)
                    : parlay.overall_confidence.toFixed(1)}%
                </p>
                
                {/* Key Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                  <div className="bg-muted/50 rounded-lg p-2 text-center">
                    <p className="text-xs text-muted-foreground">Hit Prob</p>
                    <p className="font-semibold text-lg">{(parlay.parlay_hit_prob * 100).toFixed(1)}%</p>
                  </div>
                  
                  {parlay.parlay_ev !== undefined && (
                    <div className={cn(
                      "rounded-lg p-2 text-center",
                      parlay.parlay_ev > 0 ? "bg-green-500/20" : "bg-red-500/20"
                    )}>
                      <p className="text-xs text-muted-foreground">Expected Value</p>
                      <p className={cn(
                        "font-semibold text-lg",
                        parlay.parlay_ev > 0 ? "text-green-400" : "text-red-400"
                      )}>
                        {parlay.parlay_ev > 0 ? '+' : ''}{(parlay.parlay_ev * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                  
                  {parlay.upset_count !== undefined && parlay.upset_count > 0 && (
                    <div className="bg-purple-500/20 rounded-lg p-2 text-center">
                      <p className="text-xs text-muted-foreground">Upsets</p>
                      <p className="font-semibold text-lg text-purple-400">
                        🦍 {parlay.upset_count}
                      </p>
                    </div>
                  )}
                  
                  {parlay.model_version && (
                    <div className="bg-muted/50 rounded-lg p-2 text-center">
                      <p className="text-xs text-muted-foreground">Model</p>
                      <p className="font-semibold text-sm">{parlay.model_version}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold">Parlay Legs</h4>
              {parlay.legs.map((leg, index) => {
                const sport = (leg.sport || "NFL") as SportOption
                const colors = SPORT_COLORS[sport] || SPORT_COLORS.NFL
                return (
                  <div key={`${leg.market_id}-${index}`} className="border rounded-lg p-3 bg-muted/30">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn(
                        "text-xs font-medium px-2 py-0.5 rounded-full border",
                        colors.bg, colors.text, colors.border
                      )}>
                        {sport}
                      </span>
                      <span className="text-xs text-muted-foreground">{leg.game}</span>
                    </div>
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-semibold text-primary">Pick: {getPickLabel(leg)}</p>
                        <p className="text-xs text-muted-foreground">
                          {getMarketLabel(leg.market_type)} • Odds {leg.odds}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <Badge variant="outline" className="text-xs">
                            Win Prob {(leg.probability * 100).toFixed(1)}%
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            Confidence {leg.confidence.toFixed(0)}%
                          </Badge>
                        </div>
                      </div>
                      <div className={cn("font-bold text-lg", getConfidenceTextClass(leg.confidence))}>
                        {leg.confidence.toFixed(0)}%
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>

            <div className="border-t pt-4 space-y-3">
              <section>
                <h4 className="font-semibold mb-1 text-foreground">AI Summary</h4>
                <p className="text-sm text-foreground/90 whitespace-pre-line">{parlay.ai_summary}</p>
              </section>
              <section className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                <h4 className="font-semibold mb-1 text-amber-100">Risk Assessment</h4>
                <p className="text-sm text-foreground/90 whitespace-pre-line">{parlay.ai_risk_notes}</p>
              </section>
            </div>
          </CardContent>
        </Card>
      )}

      {tripleParlay && <TripleParlayDisplay data={tripleParlay} />}
    </div>
    
    {/* Paywall Modal */}
    <PaywallModal
      isOpen={showPaywall}
      onClose={handlePaywallClose}
      reason={paywallReason}
      error={paywallError}
      parlayType={paywallParlayType}
      singlePrice={paywallPrices.single}
      multiPrice={paywallPrices.multi}
    />
    </>
  )
}
