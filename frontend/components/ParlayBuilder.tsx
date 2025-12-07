"use client"

import { useState, useEffect } from "react"
import { api, ParlayResponse, TripleParlayResponse, NFLWeekInfo } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle, TrendingUp, Calendar, Crown } from "lucide-react"
import { cn } from "@/lib/utils"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { TripleParlayDisplay } from "@/components/TripleParlayDisplay"
import { getPickLabel, getMarketLabel, getConfidenceTextClass } from "@/lib/parlayFormatting"
import { useSubscription, isPaywallError, getPaywallError, PaywallError } from "@/lib/subscription-context"
import { PaywallModal, PaywallReason } from "@/components/paywall/PaywallModal"
import { useAuth } from "@/lib/auth-context"

const SPORT_OPTIONS = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "MLS", "EPL"] as const
type BuilderMode = "single" | "triple"
type SportOption = (typeof SPORT_OPTIONS)[number]

// Sport badges with colors
const SPORT_COLORS: Record<SportOption, { bg: string; text: string; border: string }> = {
  NFL: { bg: "bg-green-500/20", text: "text-green-300", border: "border-green-500/50" },
  NBA: { bg: "bg-orange-500/20", text: "text-orange-300", border: "border-orange-500/50" },
  NHL: { bg: "bg-blue-500/20", text: "text-blue-300", border: "border-blue-500/50" },
  MLB: { bg: "bg-red-500/20", text: "text-red-300", border: "border-red-500/50" },
  NCAAF: { bg: "bg-amber-500/20", text: "text-amber-300", border: "border-amber-500/50" },
  NCAAB: { bg: "bg-purple-500/30 dark:bg-purple-500/40", text: "text-purple-200 dark:text-purple-300", border: "border-purple-400/60 dark:border-purple-400/70" },
  MLS: { bg: "bg-sky-500/20", text: "text-sky-300", border: "border-sky-500/50" },
  EPL: { bg: "bg-violet-500/30 dark:bg-violet-500/40", text: "text-violet-200 dark:text-violet-300", border: "border-violet-400/60 dark:border-violet-400/70" },
}

export function ParlayBuilder() {
  const [mode, setMode] = useState<BuilderMode>("single")
  const [numLegs, setNumLegs] = useState(5)
  const [riskProfile, setRiskProfile] = useState<"conservative" | "balanced" | "degen">("balanced")
  const [selectedSports, setSelectedSports] = useState<SportOption[]>(["NFL", "NBA", "NHL"])
  const [mixSports, setMixSports] = useState(true)
  const [loading, setLoading] = useState(false)
  const [parlay, setParlay] = useState<ParlayResponse | null>(null)
  const [tripleParlay, setTripleParlay] = useState<TripleParlayResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  // Week selection state
  const [availableWeeks, setAvailableWeeks] = useState<NFLWeekInfo[]>([])
  const [selectedWeek, setSelectedWeek] = useState<number | null>(null)
  const [currentWeek, setCurrentWeek] = useState<number | null>(null)
  const [loadingWeeks, setLoadingWeeks] = useState(true)
  
  // Subscription & Paywall state
  const { user } = useAuth()
  const { isPremium, freeParlaysRemaining, refreshStatus } = useSubscription()
  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("ai_parlay_limit_reached")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)

  // Fetch NFL weeks on mount
  useEffect(() => {
    async function fetchWeeks() {
      try {
        setLoadingWeeks(true)
        const weeksData = await api.getNFLWeeks()
        setAvailableWeeks(weeksData.weeks.filter(w => w.is_available))
        setCurrentWeek(weeksData.current_week)
        // Default to current week
        if (weeksData.current_week) {
          setSelectedWeek(weeksData.current_week)
        }
      } catch (err) {
        console.error("Failed to fetch NFL weeks:", err)
      } finally {
        setLoadingWeeks(false)
      }
    }
    fetchWeeks()
  }, [])

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
    if (isSelected && selectedSports.length === 1) {
      return
    }
    setSelectedSports((prev) =>
      isSelected ? prev.filter((item) => item !== sport) : [...prev, sport]
    )
  }

  const handleGenerate = async () => {
    try {
      setLoading(true)
      setError(null)

      if (mode === "triple") {
        if (!selectedSports.length) {
          setError("Select at least one sport to build triple parlays.")
          return
        }
        const result = await api.suggestTripleParlay({ sports: selectedSports })
        setTripleParlay(result)
        setParlay(null)
      } else {
        // Single parlay with optional mixed sports
        if (!selectedSports.length) {
          setError("Select at least one sport to build a parlay.")
          return
        }
        
        // Include week filter for NFL
        const hasNFL = selectedSports.includes("NFL")
        const weekFilter = hasNFL && selectedWeek ? selectedWeek : undefined
        
        const result = await api.suggestParlay({
          num_legs: numLegs,
          risk_profile: riskProfile,
          sports: selectedSports,
          mix_sports: mixSports && selectedSports.length > 1,
          week: weekFilter,
        })
        setParlay(result)
        setTripleParlay(null)
      }
    } catch (error: unknown) {
      console.error("Error generating parlay:", error)
      
      // Check if this is a paywall error (402)
      if (isPaywallError(error)) {
        const paywallErr = getPaywallError(error)
        setPaywallError(paywallErr)
        
        if (paywallErr?.error_code === 'FREE_LIMIT_REACHED') {
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
                  <Badge className="bg-gradient-to-r from-emerald-500 to-green-500 text-black border-0">
                    <Crown className="h-3 w-3 mr-1" />
                    Premium
                  </Badge>
                ) : (
                  <Badge variant="outline" className="border-amber-500/50 text-amber-400">
                    {freeParlaysRemaining > 0 
                      ? `${freeParlaysRemaining} free parlay left today`
                      : 'Daily limit reached'
                    }
                  </Badge>
                )}
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <label className="text-sm font-medium mb-2 block">Mode</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: "single", label: "Single Parlay", hint: "Manual controls" },
                { value: "triple", label: "Triple Parlays", hint: "Safe / Balanced / Degen" },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleModeChange(option.value as BuilderMode)}
                  className={cn(
                    "rounded-md border-2 p-3 text-left transition-colors",
                    mode === option.value
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  <div className="font-medium">{option.label}</div>
                  <div className="text-xs text-muted-foreground">{option.hint}</div>
                </button>
              ))}
            </div>
          </div>

          {mode === "single" ? (
            <>
              {/* Sports Selection for Single Mode */}
              <div>
                <label className="text-sm font-medium mb-2 block">Sports to Include</label>
                <div className="flex flex-wrap gap-2">
                  {SPORT_OPTIONS.map((sport) => {
                    const selected = selectedSports.includes(sport)
                    const colors = SPORT_COLORS[sport]
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        className={cn(
                          "rounded-full border px-4 py-1.5 text-sm font-medium transition-all",
                          selected
                            ? `${colors.bg} ${colors.text} ${colors.border} border-2`
                            : "border-border text-muted-foreground hover:border-primary/50"
                        )}
                      >
                        {sport}
                      </button>
                    )
                  })}
                </div>
                
                {/* Mix Sports Toggle */}
                {selectedSports.length > 1 && (
                  <div className="mt-3 flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => setMixSports(!mixSports)}
                      className={cn(
                        "relative inline-flex h-6 w-11 items-center rounded-full transition-colors",
                        mixSports ? "bg-primary" : "bg-muted"
                      )}
                    >
                      <span
                        className={cn(
                          "inline-block h-4 w-4 transform rounded-full bg-white transition-transform",
                          mixSports ? "translate-x-6" : "translate-x-1"
                        )}
                      />
                    </button>
                    <span className="text-sm text-muted-foreground">
                      Mix sports in parlay
                      <span className="block text-xs">
                        {mixSports ? "Legs will be drawn from all selected sports" : "Single sport per parlay"}
                      </span>
                    </span>
                  </div>
                )}
                
                <p className="text-xs text-muted-foreground mt-2">
                  Selected: {selectedSports.join(", ")}
                  {mixSports && selectedSports.length > 1 && " (Mixed)"}
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
                <div className="grid grid-cols-3 gap-2">
                  {(["conservative", "balanced", "degen"] as const).map((profile) => (
                    <button
                      key={profile}
                      type="button"
                      onClick={() => setRiskProfile(profile)}
                      className={cn(
                        "p-3 rounded-md border-2 transition-colors",
                        riskProfile === profile
                          ? "border-primary bg-primary/10"
                          : "border-border hover:border-primary/50"
                      )}
                    >
                      <div className="font-medium capitalize">{profile}</div>
                      <div className="text-xs text-muted-foreground mt-1">
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
                <label className="text-sm font-medium mb-2 block">Sports to Mix</label>
                <div className="flex flex-wrap gap-2">
                  {SPORT_OPTIONS.map((sport) => {
                    const selected = selectedSports.includes(sport)
                    const colors = SPORT_COLORS[sport]
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        className={cn(
                          "rounded-full border px-4 py-1.5 text-sm font-medium transition-all",
                          selected
                            ? `${colors.bg} ${colors.text} ${colors.border} border-2`
                            : "border-border text-muted-foreground hover:border-primary/50"
                        )}
                      >
                        {sport}
                      </button>
                    )
                  })}
                </div>
                <p className="text-xs text-muted-foreground mt-2">
                  Safe parlays use 3-6 legs, Balanced uses 7-12, and Degen pushes 13-20 legs. Mixing
                  leagues keeps correlation low and maximizes edge discovery.
                </p>
                <p className="text-xs font-medium mt-1">Selected: {selectedSports.join(", ")}</p>
              </div>
            </>
          )}

          <Button onClick={handleGenerate} disabled={loading} className="w-full">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Working...
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
          <CardHeader>
            <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <CardTitle>{parlay.num_legs}-Leg Parlay</CardTitle>
                <CardDescription className="capitalize">{parlay.risk_profile} profile</CardDescription>
              </div>
              <Badge variant="outline" className="text-xs">
                Hit Probability {(parlay.parlay_hit_prob * 100).toFixed(1)}%
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
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
    />
    </>
  )
}
