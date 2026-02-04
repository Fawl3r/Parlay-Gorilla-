"use client"

import { useEffect, useRef, useState } from "react"
import { motion } from "framer-motion"
import { AlertCircle, Calendar, Copy, Crown, Info, Loader2, Lock, TrendingUp } from "lucide-react"

import { cn } from "@/lib/utils"
import { PaywallModal } from "@/components/paywall/PaywallModal"
import { getCopy } from "@/lib/content"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tooltip } from "@/components/ui/tooltip"

import {
  ACTION_COPY,
  TRY_THIS_LABEL,
  eligibleGamesSummary,
  fallbackStageLabel,
} from "@/lib/parlay/parlayUserCopy"
import {
  getCopyForReason,
  getActionLabel,
  getActionIdForReason,
  TRIPLE_DOWNGRADE_TOAST,
  TRIPLE_DOWNGRADE_BADGE,
  FALLBACK_BANNER,
  FALLBACK_TOOLTIP,
  FALLBACK_BANNER_BEGINNER,
  TRIPLE_LABEL_DEFAULT,
  TRIPLE_SUBTEXT_DEFAULT,
  TRIPLE_LABEL_BEGINNER,
  TRIPLE_SUBTEXT_BEGINNER,
  TRIPLE_TOOLTIP_BEGINNER,
  TRIPLE_TOOLTIP_DEFAULT,
  SUPPORT_ID_LABEL,
  SUPPORT_ID_TOOLTIP,
  AVAILABILITY_HINT,
  UPDATED_PICK_OPTIONS_TOAST,
  WHAT_HAPPENED_LABEL,
  WHAT_HAPPENED_PRIMARY,
  WHAT_HAPPENED_YOU_TRIED,
} from "@/lib/parlay/uxLanguageMap"
import { useBeginnerMode } from "@/lib/parlay/useBeginnerMode"
import { AiParlayResultCard } from "./results/AiParlayResultCard"
import { TripleParlayResult } from "./results/TripleParlayResult"
import { QuickStartPanel, getQuickStartSeenStored } from "./QuickStartPanel"
import { SPORT_COLORS, SPORT_OPTIONS, type BuilderMode, type SportOption } from "./types"
import { useParlayBuilderViewModel } from "./useParlayBuilderViewModel"
import { FirstParlayConfidenceModal, shouldShowFirstParlayModal } from "@/components/onboarding/FirstParlayConfidenceModal"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"
import { toast } from "sonner"
import { trackEvent, trackOnboardingQuickStartShown } from "@/lib/track-event"
import {
  recordParlaySuccess,
  getSuccessCount,
  isGraduationNudgeDismissed,
  setGraduationNudgeDismissed,
  GRADUATION_THRESHOLD_BUILDS,
} from "@/lib/parlay/successTracking"
import Link from "next/link"

function GraduationNudgeCard({
  successCount,
  onProfileClick,
  onDismiss,
  onShown,
}: {
  successCount: number
  onProfileClick: () => void
  onDismiss: () => void
  onShown: () => void
}) {
  const shownRef = useRef(false)
  useEffect(() => {
    if (!shownRef.current) {
      shownRef.current = true
      onShown()
    }
  }, [onShown])
  return (
    <Card className="border-primary/20 bg-primary/5">
      <CardContent className="py-3 px-4 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          Want more control? You can turn off Beginner Mode anytime to customize picks your way.
        </p>
        <div className="flex items-center gap-2">
          <Link
            href="/profile"
            className="text-sm font-medium text-primary hover:text-primary/80 underline decoration-dotted"
            onClick={onProfileClick}
          >
            Profile settings
          </Link>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-foreground"
            onClick={onDismiss}
          >
            Dismiss
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export function ParlayBuilder() {
  const { state, actions } = useParlayBuilderViewModel()
  const { nudgeInstallCta } = usePwaInstallNudge()
  const { isBeginnerMode } = useBeginnerMode()
  const [showFirstParlayModal, setShowFirstParlayModal] = useState(false)
  const [quickStartSeen, setQuickStartSeen] = useState(false)
  const [successCount, setSuccessCount] = useState(0)
  const [graduationNudgeDismissed, setGraduationNudgeDismissedState] = useState(false)
  const toastDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevParlayIdRef = useRef<string | null>(null)
  const quickStartShownFiredRef = useRef(false)

  useEffect(() => {
    setQuickStartSeen(getQuickStartSeenStored())
  }, [])

  useEffect(() => {
    setSuccessCount(getSuccessCount())
  }, [])

  useEffect(() => {
    setGraduationNudgeDismissedState(isGraduationNudgeDismissed())
  }, [])

  const {
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
    isSaving,
    generationProgress,
    availableWeeks,
    selectedWeek,
    currentWeek,
    loadingWeeks,
    user,
    isPremium,
    freeParlaysRemaining,
    mixSportsAllowed,
    entitlements,
    maxLegsFromEntitlements,
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
  } = state

  const {
    setNumLegs,
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
  } = actions
  const { lastQuickActionId } = state

  const primaryExclusionReasonRaw = insufficientCandidatesError?.top_exclusion_reasons?.[0]
  const primaryExclusionReason =
    primaryExclusionReasonRaw != null && typeof primaryExclusionReasonRaw === "object" && "reason" in primaryExclusionReasonRaw
      ? (primaryExclusionReasonRaw as { reason: string }).reason
      : null
  const reasonCopy = getCopyForReason(primaryExclusionReason, isBeginnerMode)

  async function copyDebugId() {
    if (!insufficientCandidatesError) return
    const text = `Debug ID: ${insufficientCandidatesError.debug_id ?? "—"} · Need ${insufficientCandidatesError.needed}, have ${insufficientCandidatesError.have}`
    try {
      await navigator.clipboard.writeText(text)
      toast.success("Copied to clipboard")
    } catch {
      toast.error("Could not copy")
    }
  }

  useEffect(() => {
    if (!parlay?.id) {
      prevParlayIdRef.current = null
      return
    }
    const parlayId = parlay.id
    if (prevParlayIdRef.current !== parlayId) {
      prevParlayIdRef.current = parlayId
      const { count, isFirstSuccess } = recordParlaySuccess()
      setSuccessCount(count)
      if (isFirstSuccess) {
        toast.success("Nice! You're all set. We'll keep doing the hard work for you.")
      }
    }
  }, [parlay, parlay?.id, isBeginnerMode])

  // Show first parlay modal when parlay is generated and it's the first time
  useEffect(() => {
    if (parlay && shouldShowFirstParlayModal()) {
      // Small delay to let the parlay render first
      const timer = setTimeout(() => {
        setShowFirstParlayModal(true)
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [parlay])

  // Smart install nudge: when user generates an AI pick, allow CTA to re-appear
  useEffect(() => {
    if (parlay) nudgeInstallCta()
  }, [parlay, nudgeInstallCta])

  const showQuickStart = isBeginnerMode && !quickStartSeen

  useEffect(() => {
    if (showQuickStart && !quickStartShownFiredRef.current) {
      quickStartShownFiredRef.current = true
      trackOnboardingQuickStartShown()
    }
  }, [showQuickStart])

  return (
    <>
      <div className="space-y-6" data-testid="ai-picks-page" data-page="ai-builder">
        {showQuickStart && (
          <QuickStartPanel
            visible={showQuickStart}
            onDismiss={() => setQuickStartSeen(true)}
            onSelectNfl={() => {
              setSelectedSports(["NFL"])
              setNumLegs(2)
              handleModeChange("single")
            }}
            onSelectNba={() => {
              setSelectedSports(["NBA" as SportOption])
              setNumLegs(2)
              handleModeChange("single")
            }}
            onSelectTriple={() => {
              handleModeChange("triple")
              setTripleModeEnabled(true)
              setNumLegs(3)
              setSelectedSports(["NFL"])
            }}
            onSelectAllSports={() => {
              setSelectedSports(["NFL", "NBA", "NHL", "MLB"] as SportOption[])
              setMixSports(true)
              setNumLegs(2)
              handleModeChange("single")
            }}
            tripleAvailable={strongEdges !== null && strongEdges >= 3}
            allSportsEntitled={!!mixSportsAllowed}
          />
        )}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>{getCopy("app.slipBuilder.header")}</CardTitle>
                <CardDescription>
                  {getCopy("app.slipBuilder.helper")}
                </CardDescription>
              </div>
              {/* Subscription Status Badge */}
              {user && (
                <div className="flex-shrink-0">
                  {isPremium ? (
                    <Badge
                      className="bg-primary text-primary-foreground border-0"
                    >
                      <Crown className="h-3 w-3 mr-1" />
                      Premium
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                      {freeParlaysRemaining > 0
                        ? `${freeParlaysRemaining} free parlay${freeParlaysRemaining > 1 ? "s" : ""} left this week`
                        : "Weekly limit reached"}
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
                  {
                    value: "triple",
                    label: isBeginnerMode ? TRIPLE_LABEL_BEGINNER : TRIPLE_LABEL_DEFAULT,
                    hint: isBeginnerMode ? TRIPLE_SUBTEXT_BEGINNER : TRIPLE_SUBTEXT_DEFAULT,
                  },
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => handleModeChange(option.value as BuilderMode)}
                    className={cn(
                      "rounded-md border-2 p-2.5 sm:p-3 text-left transition-colors min-h-[60px] sm:min-h-[auto]",
                      mode === option.value ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"
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
                    {!mixSportsAllowed && (
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
                      // Free users can select any single sport (can switch between them)
                      // Premium users can select multiple sports
                      const canSelect = mixSportsAllowed || selected || selectedSports.length === 0 || (!mixSportsAllowed && selectedSports.length === 1)
                      const legCount = candidateLegCounts[sport]
                      const hasLegs = legCount !== undefined && legCount > 0
                      
                      return (
                        <button
                          key={sport}
                          type="button"
                          onClick={() => toggleSport(sport)}
                          disabled={!canSelect}
                          className={cn(
                            "rounded-full border px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all min-h-[36px] sm:min-h-[auto] relative",
                            selected ? `${colors.bg} ${colors.text} ${colors.border} border-2` : "border-border text-muted-foreground hover:border-primary/50",
                            !canSelect && "opacity-50 cursor-not-allowed"
                          )}
                          title={
                            !canSelect
                              ? "Multi-sport parlays require Elite. Upgrade to unlock."
                              : legCount !== undefined && legCount > 0
                              ? "Enough games available to build parlays"
                              : legCount !== undefined
                              ? "Few or no games available for this sport right now"
                              : undefined
                          }
                        >
                          <span className="flex items-center gap-1.5">
                            {sport}
                            {legCount !== undefined && (
                              <span className={cn(
                                "text-[10px] px-1.5 py-0.5 rounded",
                                hasLegs ? "bg-emerald-500/20 text-emerald-400" : "bg-gray-500/20 text-gray-400"
                              )}>
                                {legCount}
                              </span>
                            )}
                          </span>
                          {!canSelect && !selected && (
                            <Lock className="absolute -top-1 -right-1 h-3 w-3 text-amber-400 bg-background rounded-full p-0.5" />
                          )}
                        </button>
                      )
                    })}
                  </div>

                  {/* Multi-sport restriction message */}
                  {!mixSportsAllowed && selectedSports.length === 1 && (
                    <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                      <p className="text-xs text-amber-300 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        <span>
                          Multi-sport parlays are a premium feature.{" "}
                          <a href="/premium" className="underline font-medium">
                            Upgrade to unlock
                          </a>
                        </span>
                      </p>
                    </div>
                  )}

                  {/* Mix Sports Toggle */}
                  {selectedSports.length > 1 && (
                    <div className="mt-3 flex items-center gap-3">
                      <button
                        type="button"
                        onClick={toggleMixSports}
                        disabled={!mixSportsAllowed}
                        className={cn(
                          "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                          mixSports && mixSportsAllowed ? "bg-primary" : "bg-muted",
                          !mixSportsAllowed && "opacity-50 cursor-not-allowed"
                        )}
                        title={!mixSportsAllowed ? "Multi-sport mixing requires Premium" : undefined}
                      >
                        <span
                          className={cn(
                            "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                            mixSports && mixSportsAllowed ? "translate-x-6" : "translate-x-1"
                          )}
                        />
                      </button>
                      <span className="text-sm text-muted-foreground">
                        Mix sports in parlay
                        {!mixSportsAllowed && (
                          <span className="ml-1 text-amber-400">
                            <Lock className="h-3 w-3 inline" />
                          </span>
                        )}
                        <span className="block text-xs">
                          {mixSports && mixSportsAllowed ? "Legs will be drawn from all selected sports" : "Single sport per parlay"}
                        </span>
                      </span>
                    </div>
                  )}

                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Selected: {selectedSports.join(", ")}
                      {mixSports && selectedSports.length > 1 && mixSportsAllowed && " (Mixed)"}
                    </p>
                    {selectedSports.length === 1 && (candidateLegCounts[selectedSports[0]] !== undefined || loadingLegCounts) && (
                      <div className="space-y-1">
                        <p className={cn(
                          "text-xs",
                          (candidateLegCounts[selectedSports[0]] ?? 0) > 0 ? "text-emerald-400" : "text-amber-400"
                        )}>
                          {loadingLegCounts
                            ? "Checking games..."
                            : eligibleGamesSummary({
                                uniqueGames: eligibilityUniqueGames ?? undefined,
                                legCount: candidateLegCounts[selectedSports[0]],
                                numLegsRequested: numLegs,
                                sport: selectedSports[0],
                                includePlayerProps,
                                beginnerMode: isBeginnerMode,
                              })}
                        </p>
                        {!loadingLegCounts && (candidateLegCounts[selectedSports[0]] ?? 0) > 0 && (candidateLegCounts[selectedSports[0]] ?? 0) <= 3 && (
                          <p className="text-[11px] text-muted-foreground">
                            {AVAILABILITY_HINT}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
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
                              (weekInfo.is_current || (currentWeek !== null && weekInfo.week === currentWeek)) && "ring-2 ring-emerald-500/30"
                            )}
                          >
                            {weekInfo.label}
                            {(weekInfo.is_current || (currentWeek !== null && weekInfo.week === currentWeek)) && (
                              <span className="ml-1 text-xs text-emerald-400">(Current)</span>
                            )}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No weeks available. Check back when the NFL season starts.</p>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">
                      Select which week's games to build your Gorilla Parlay from.
                      {selectedWeek && ` Building from Week ${selectedWeek} games.`}
                    </p>
                  </div>
                )}

                <div>
                  <label className="text-sm font-medium mb-2 block">Number of picks: {numLegs}</label>
                  <input
                    type="range"
                    min="1"
                    max={maxLegsFromEntitlements}
                    value={numLegs}
                    onChange={(e) => setNumLegs(Number(e.target.value))}
                    className="w-full accent-primary"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>1</span>
                    <span>{maxLegsFromEntitlements}</span>
                  </div>
                  {/* Triple · Confidence Mode: only when we find 3 strong picks */}
                  <div className="mt-3 space-y-1.5">
                    <p className="text-xs text-muted-foreground">
                      {isBeginnerMode ? TRIPLE_SUBTEXT_BEGINNER : TRIPLE_SUBTEXT_DEFAULT}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <button
                        type="button"
                        onClick={() => setTripleModeEnabled(true)}
                        disabled={strongEdges !== null && strongEdges < 3}
                        className={cn(
                          "rounded-md border-2 px-3 py-1.5 text-xs font-medium transition-colors",
                          tripleMode ? "border-primary bg-primary/10 text-primary-foreground" : "border-border hover:border-primary/50",
                          strongEdges !== null && strongEdges < 3 && "opacity-50 cursor-not-allowed"
                        )}
                        title={
                          strongEdges !== null && strongEdges < 3
                            ? (isBeginnerMode ? TRIPLE_TOOLTIP_BEGINNER : "We only show Triple when we find 3 strong picks. Try 2 picks or include more upcoming games.")
                            : undefined
                        }
                      >
                        {isBeginnerMode ? TRIPLE_LABEL_BEGINNER : TRIPLE_LABEL_DEFAULT}
                      </button>
                      {strongEdges !== null && strongEdges < 3 && (
                        <span className="text-xs text-muted-foreground">
                          Only a few strong picks right now
                        </span>
                      )}
                      {tripleMode && (
                        <Tooltip
                          content={isBeginnerMode ? TRIPLE_TOOLTIP_BEGINNER : TRIPLE_TOOLTIP_DEFAULT}
                          className="inline-flex"
                        />
                      )}
                    </div>
                    {strongEdges !== null && strongEdges < 3 && (
                      <p className="text-xs text-amber-200/90">
                        Use fewer picks or include all upcoming games.
                      </p>
                    )}
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
                          riskProfile === profile ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"
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

                {/* Player picks Toggle (Premium Only) */}
                <div className="border rounded-lg p-3 bg-muted/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <label className="text-sm font-medium">Include player picks</label>
                      {!isPremium && (
                        <Badge variant="outline" className="text-xs border-amber-500/50 text-amber-400">
                          <Lock className="h-3 w-3 mr-1" />
                          Premium
                        </Badge>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        if (!isPremium) {
                          // Open paywall for premium feature
                          return
                        }
                        setIncludePlayerProps(!includePlayerProps)
                      }}
                      disabled={!isPremium}
                      className={cn(
                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                        includePlayerProps && isPremium ? "bg-primary" : "bg-muted",
                        !isPremium && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <span
                        className={cn(
                          "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                          includePlayerProps && isPremium ? "translate-x-6" : "translate-x-1"
                        )}
                      />
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    {isPremium
                      ? "Include player picks from FanDuel and DraftKings in your parlay"
                      : "Player picks are a premium feature. Upgrade to unlock."}
                  </p>
                </div>
              </>
            ) : (
              <>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium">Sports to Mix</label>
                    {!mixSportsAllowed && (
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
                      const canSelect = mixSportsAllowed || selected || selectedSports.length === 0
                      return (
                        <button
                          key={sport}
                          type="button"
                          onClick={() => toggleSport(sport)}
                          disabled={!canSelect}
                          className={cn(
                            "rounded-full border px-3 sm:px-4 py-1.5 sm:py-2 text-xs sm:text-sm font-medium transition-all min-h-[36px] sm:min-h-[auto] relative",
                            selected ? `${colors.bg} ${colors.text} ${colors.border} border-2` : "border-border text-muted-foreground hover:border-primary/50",
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
                  {!mixSportsAllowed && (
                    <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                      <p className="text-xs text-amber-300 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        <span>
                          Confidence Mode with multiple sports is a premium feature.{" "}
                          <a href="/premium" className="underline font-medium">
                            Upgrade to unlock
                          </a>
                        </span>
                      </p>
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground mt-2">
                    Safe parlays use 3-6 picks, Balanced uses 7-12, and Degen pushes 13-20 picks. Mixing leagues keeps correlation
                    low and maximizes edge discovery.
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
                    Our AI analyzes thousands of games, calculates win probabilities, and optimizes your parlay selection.{" "}
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
                        className="h-full bg-gradient-to-r from-primary to-accent"
                        initial={{ width: 0 }}
                        animate={{ width: `${generationProgress.progress}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>

                    {/* Time Information */}
                    <div className="flex justify-between items-center text-xs text-muted-foreground">
                      <span>Elapsed: {Math.floor(generationProgress.elapsed)}s</span>
                      <span>Est. remaining: {Math.max(0, Math.ceil(generationProgress.estimated - generationProgress.elapsed))}s</span>
                      <span>{Math.floor(generationProgress.progress)}% complete</span>
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

            {!user && entitlements && !entitlements.is_authenticated && (
              <p className="text-sm text-amber-200/90 mb-2">
                Sign in to generate AI parlays.
              </p>
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
          <Card className="border-amber-500/40">
            <CardContent className="py-6 space-y-4">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-6 w-6 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-destructive">
                    {(insufficientCandidatesError || suggestError?.code === "insufficient_candidates")
                      ? reasonCopy.title
                      : "Something went wrong"}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    {(insufficientCandidatesError || suggestError?.code === "insufficient_candidates")
                      ? reasonCopy.body
                      : error}
                  </p>
                  {!isBeginnerMode && (insufficientCandidatesError || suggestError?.code === "insufficient_candidates") && (
                    <details className="mt-3 text-xs text-muted-foreground border-t border-border/50 pt-3">
                      <summary className="cursor-pointer hover:text-foreground/80 list-none font-medium text-foreground/90">
                        {WHAT_HAPPENED_LABEL}
                      </summary>
                      <div className="mt-2 space-y-2 pl-0">
                        <p>
                          <span className="font-medium text-foreground/80">{WHAT_HAPPENED_PRIMARY}</span>{" "}
                          {reasonCopy.title}. {reasonCopy.body}
                        </p>
                        {lastQuickActionId && (
                          <p>
                            <span className="font-medium text-foreground/80">{WHAT_HAPPENED_YOU_TRIED}</span>{" "}
                            {getActionLabel(lastQuickActionId)}
                          </p>
                        )}
                        {insufficientCandidatesError?.debug_id && (
                          <div className="flex items-center gap-2 flex-wrap">
                            <span>{SUPPORT_ID_LABEL} {insufficientCandidatesError.debug_id}</span>
                            <Tooltip content={SUPPORT_ID_TOOLTIP} className="inline-flex" />
                            <button
                              type="button"
                              onClick={copyDebugId}
                              className="inline-flex items-center justify-center rounded p-1 text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
                              title={SUPPORT_ID_TOOLTIP}
                              aria-label="Copy support ID"
                            >
                              <Copy className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    </details>
                  )}
                  {suggestError?.hint && !insufficientCandidatesError && suggestError?.code !== "insufficient_candidates" && (
                    <p className="text-sm text-muted-foreground mt-2 text-amber-200/90">{suggestError.hint}</p>
                  )}
                </div>
              </div>
              {(insufficientCandidatesError || suggestError?.code === "insufficient_candidates") && (() => {
                const clearError = () => {
                  setError(null)
                  setSuggestError(null)
                  setInsufficientCandidatesError(null)
                }
                const runActionById = (actionId: string) => {
                  if (actionId === "ml_only") setIncludePlayerProps(false)
                  else if (actionId === "all_upcoming") setSelectedWeek(null)
                  else if (actionId === "enable_props") setIncludePlayerProps(true)
                  else if (actionId === "lower_legs") setNumLegs(3)
                  else if (actionId === "single_sport") {
                    setSelectedSports([selectedSports[0]])
                    setMixSports(false)
                  }
                }
                const showUpdatedToast = () => {
                  if (toastDebounceRef.current) clearTimeout(toastDebounceRef.current)
                  toastDebounceRef.current = setTimeout(() => {
                    toast.success(UPDATED_PICK_OPTIONS_TOAST)
                    toastDebounceRef.current = null
                  }, 600)
                }
                if (isBeginnerMode) {
                  const actionId = getActionIdForReason(primaryExclusionReason, true)
                  return (
                    <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
                      <span className="text-xs text-muted-foreground w-full">{TRY_THIS_LABEL}</span>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          trackEvent("ai_picks_quick_action_clicked", {
                            action_id: actionId,
                            primary_reason: primaryExclusionReason ?? undefined,
                            debug_id: insufficientCandidatesError?.debug_id,
                          })
                          setLastQuickActionId(actionId)
                          runActionById(actionId)
                          clearError()
                          showUpdatedToast()
                        }}
                      >
                        {reasonCopy.action}
                      </Button>
                    </div>
                  )
                }
                const primaryReasonsForAllUpcoming = ["OUTSIDE_WEEK", "STATUS_NOT_UPCOMING"]
                const showMlOnly = includePlayerProps || primaryExclusionReason === "NO_ODDS"
                const actions: { id: keyof typeof ACTION_COPY; show: boolean; primaryWhen: string[]; onClick: () => void }[] = [
                  {
                    id: "ml_only",
                    show: showMlOnly,
                    primaryWhen: ["NO_ODDS"],
                    onClick: () => {
                      trackEvent("ai_picks_quick_action_clicked", {
                        action_id: "ml_only",
                        primary_reason: primaryExclusionReason ?? undefined,
                        debug_id: insufficientCandidatesError?.debug_id,
                      })
                      setLastQuickActionId("ml_only")
                      setIncludePlayerProps(false)
                      clearError()
                      showUpdatedToast()
                    },
                  },
                  {
                    id: "all_upcoming",
                    show: selectedWeek != null && selectedSports.includes("NFL"),
                    primaryWhen: primaryReasonsForAllUpcoming,
                    onClick: () => {
                      trackEvent("ai_picks_quick_action_clicked", {
                        action_id: "all_upcoming",
                        primary_reason: primaryExclusionReason ?? undefined,
                        debug_id: insufficientCandidatesError?.debug_id,
                      })
                      setLastQuickActionId("all_upcoming")
                      setSelectedWeek(null)
                      clearError()
                      showUpdatedToast()
                    },
                  },
                  {
                    id: "enable_props",
                    show: isPremium && !includePlayerProps,
                    primaryWhen: ["PLAYER_PROPS_DISABLED"],
                    onClick: () => {
                      trackEvent("ai_picks_quick_action_clicked", {
                        action_id: "enable_props",
                        primary_reason: primaryExclusionReason ?? undefined,
                        debug_id: insufficientCandidatesError?.debug_id,
                      })
                      setLastQuickActionId("enable_props")
                      setIncludePlayerProps(true)
                      clearError()
                      showUpdatedToast()
                    },
                  },
                  {
                    id: "lower_legs",
                    show: true,
                    primaryWhen: [],
                    onClick: () => {
                      trackEvent("ai_picks_quick_action_clicked", {
                        action_id: "lower_legs",
                        primary_reason: primaryExclusionReason ?? undefined,
                        debug_id: insufficientCandidatesError?.debug_id,
                      })
                      setLastQuickActionId("lower_legs")
                      setNumLegs(3)
                      clearError()
                      showUpdatedToast()
                    },
                  },
                  {
                    id: "single_sport",
                    show: selectedSports.length > 1,
                    primaryWhen: [],
                    onClick: () => {
                      trackEvent("ai_picks_quick_action_clicked", {
                        action_id: "single_sport",
                        primary_reason: primaryExclusionReason ?? undefined,
                        debug_id: insufficientCandidatesError?.debug_id,
                      })
                      setLastQuickActionId("single_sport")
                      setSelectedSports([selectedSports[0]])
                      setMixSports(false)
                      clearError()
                      showUpdatedToast()
                    },
                  },
                ]
                const visible = actions.filter((a) => a.show)
                const ordered = [...visible].sort((a, b) => {
                  if (!primaryExclusionReason) return 0
                  const aFirst = a.primaryWhen.includes(primaryExclusionReason)
                  const bFirst = b.primaryWhen.includes(primaryExclusionReason)
                  if (aFirst && !bFirst) return -1
                  if (!aFirst && bFirst) return 1
                  return 0
                })
                return (
                  <div className="flex flex-wrap gap-2 pt-2 border-t border-border/50">
                    <span className="text-xs text-muted-foreground w-full">{TRY_THIS_LABEL}</span>
                    {ordered.map((action) => (
                      <Button
                        key={action.id}
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={action.onClick}
                      >
                        {getActionLabel(action.id)}
                      </Button>
                    ))}
                  </div>
                )
              })()}
              {!isBeginnerMode && suggestError?.meta && typeof suggestError.meta === "object" && Object.keys(suggestError.meta).length > 0 && (
                <details className="text-xs text-muted-foreground pt-2">
                  <summary className="cursor-pointer hover:text-foreground/80">Debug details</summary>
                  <pre className="mt-2 p-2 bg-muted/50 rounded overflow-x-auto">
                    {JSON.stringify(suggestError.meta, null, 2)}
                  </pre>
                </details>
              )}
            </CardContent>
          </Card>
        )}

        {parlay && (
          <>
            {parlay.fallback_used && parlay.fallback_stage && (
              <Card className="border-primary/30 bg-primary/5">
                <CardContent className="py-3 px-4 flex items-center gap-2 flex-wrap">
                  <Info className="h-4 w-4 text-primary flex-shrink-0" />
                  <span className="text-sm text-muted-foreground">
                    {isBeginnerMode
                      ? FALLBACK_BANNER_BEGINNER
                      : `${FALLBACK_BANNER} ${fallbackStageLabel(parlay.fallback_stage)}`}
                  </span>
                  {!isBeginnerMode && (
                    <Tooltip content={FALLBACK_TOOLTIP} className="flex-shrink-0" />
                  )}
                </CardContent>
              </Card>
            )}
            {isBeginnerMode && successCount >= GRADUATION_THRESHOLD_BUILDS && !graduationNudgeDismissed && (
              <GraduationNudgeCard
                successCount={successCount}
                onProfileClick={() => {
                  trackEvent("beginner_graduation_nudge_clicked", { action: "profile" })
                }}
                onDismiss={() => {
                  trackEvent("beginner_graduation_nudge_clicked", { action: "dismiss" })
                  setGraduationNudgeDismissed()
                  setGraduationNudgeDismissedState(true)
                }}
                onShown={() => {
                  trackEvent("beginner_graduation_nudge_shown", { success_count: successCount })
                }}
              />
            )}
            {parlayDowngraded && (
              <Card className="border-amber-500/30 bg-amber-500/5">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className="border-amber-500/50 text-amber-400 text-xs">
                      {TRIPLE_DOWNGRADE_BADGE}
                    </Badge>
                  </div>
                  {!isBeginnerMode && parlayDowngradeExplain && (
                    <p className="text-xs text-muted-foreground mt-2">
                      We found 2 strong picks today. We skipped forcing a third.
                    </p>
                  )}
                  {!isBeginnerMode && (
                    <p className="text-xs text-muted-foreground mt-1">
                      Use fewer picks or include all upcoming games.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}
            <AiParlayResultCard parlay={parlay} onSave={handleSaveAiParlay} isSaving={isSaving} />
          </>
        )}
        {tripleParlay && <TripleParlayResult data={tripleParlay} />}
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
        premiumUpsellTrigger={paywallUpsellTrigger ?? undefined}
        premiumUpsellVariant={paywallUpsellVariant}
      />

      {/* First Parlay Confidence Modal */}
      <FirstParlayConfidenceModal
        open={showFirstParlayModal}
        onClose={() => setShowFirstParlayModal(false)}
        onDontShowAgain={() => setShowFirstParlayModal(false)}
      />
    </>
  )
}


