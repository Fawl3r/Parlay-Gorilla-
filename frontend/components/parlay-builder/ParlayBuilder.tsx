"use client"

import { motion } from "framer-motion"
import { AlertCircle, Calendar, Crown, Loader2, Lock, TrendingUp } from "lucide-react"

import { cn } from "@/lib/utils"
import { PaywallModal } from "@/components/paywall/PaywallModal"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import { AiParlayResultCard } from "./results/AiParlayResultCard"
import { TripleParlayResult } from "./results/TripleParlayResult"
import { SPORT_COLORS, SPORT_OPTIONS, type BuilderMode } from "./types"
import { useParlayBuilderViewModel } from "./useParlayBuilderViewModel"

export function ParlayBuilder() {
  const { state, actions } = useParlayBuilderViewModel()

  const {
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
  } = state

  const {
    setNumLegs,
    setRiskProfile,
    setSelectedWeek,
    handleModeChange,
    toggleSport,
    toggleMixSports,
    handleGenerate,
    handleSaveAiParlay,
    handlePaywallClose,
  } = actions

  return (
    <>
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>🦍 Gorilla Parlay Builder 🦍</CardTitle>
                <CardDescription>
                  Switch between a single high-precision suggestion and the triple-parlay flight (Safe, Balanced, Degen) with
                  live Confidence Rings and AI commentary.
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
                        ? `${freeParlaysRemaining} free parlay${freeParlaysRemaining > 1 ? "s" : ""} left today`
                        : "Daily limit reached"}
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
                      // Free users can select any single sport (can switch between them)
                      // Premium users can select multiple sports
                      const canSelect = canUseMultiSport || selected || selectedSports.length === 0 || (!canUseMultiSport && selectedSports.length === 1)
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
                              ? "Multi-sport parlays require Premium. Upgrade to unlock!"
                              : legCount !== undefined
                              ? `${legCount} candidate legs available`
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
                  {!canUseMultiSport && selectedSports.length === 1 && (
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

                  <div className="mt-2 space-y-1">
                    <p className="text-xs text-muted-foreground">
                      Selected: {selectedSports.join(", ")}
                      {mixSports && selectedSports.length > 1 && canUseMultiSport && " (Mixed)"}
                    </p>
                    {selectedSports.length === 1 && candidateLegCounts[selectedSports[0]] !== undefined && (
                      <p className={cn(
                        "text-xs",
                        candidateLegCounts[selectedSports[0]] > 0
                          ? "text-emerald-400"
                          : "text-amber-400"
                      )}>
                        {candidateLegCounts[selectedSports[0]] > 0
                          ? `${candidateLegCounts[selectedSports[0]]} candidate legs available for ${selectedSports[0]}`
                          : `No candidate legs available for ${selectedSports[0]}. Try a different sport or week.`}
                      </p>
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
                  {!canUseMultiSport && (
                    <div className="mt-2 p-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                      <p className="text-xs text-amber-300 flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        <span>
                          Triple parlay multi-sport mixing is a premium feature.{" "}
                          <a href="/premium" className="underline font-medium">
                            Upgrade to unlock
                          </a>
                        </span>
                      </p>
                    </div>
                  )}

                  <p className="text-xs text-muted-foreground mt-2">
                    Safe parlays use 3-6 legs, Balanced uses 7-12, and Degen pushes 13-20 legs. Mixing leagues keeps correlation
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

        {parlay && <AiParlayResultCard parlay={parlay} onSave={handleSaveAiParlay} isSaving={isSaving} />}
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
      />
    </>
  )
}


