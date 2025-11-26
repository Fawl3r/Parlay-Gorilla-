"use client"

import { useState } from "react"
import { api, ParlayResponse, TripleParlayResponse } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle, TrendingUp } from "lucide-react"
import { cn } from "@/lib/utils"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { TripleParlayDisplay } from "@/components/TripleParlayDisplay"
import { getPickLabel, getMarketLabel, getConfidenceTextClass } from "@/lib/parlayFormatting"

const SPORT_OPTIONS = ["NFL", "NBA", "NHL"] as const
type BuilderMode = "single" | "triple"
type SportOption = (typeof SPORT_OPTIONS)[number]

export function ParlayBuilder() {
  const [mode, setMode] = useState<BuilderMode>("single")
  const [numLegs, setNumLegs] = useState(5)
  const [riskProfile, setRiskProfile] = useState<"conservative" | "balanced" | "degen">("balanced")
  const [selectedSports, setSelectedSports] = useState<SportOption[]>(["NFL", "NBA", "NHL"])
  const [loading, setLoading] = useState(false)
  const [parlay, setParlay] = useState<ParlayResponse | null>(null)
  const [tripleParlay, setTripleParlay] = useState<TripleParlayResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

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
        const result = await api.suggestParlay({
          num_legs: numLegs,
          risk_profile: riskProfile,
        })
        setParlay(result)
        setTripleParlay(null)
      }
    } catch (error: unknown) {
      console.error("Error generating parlay:", error)
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

  const generateButtonLabel = mode === "triple" ? "Generate Triple Parlays" : "Generate Parlay"

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Build Your Parlays</CardTitle>
          <CardDescription>
            Switch between a single high-precision suggestion and the triple-parlay flight (Safe,
            Balanced, Degen) with live Confidence Rings and AI commentary.
          </CardDescription>
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
              <div>
                <label className="text-sm font-medium mb-2 block">Number of Legs: {numLegs}</label>
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={numLegs}
                  onChange={(e) => setNumLegs(Number(e.target.value))}
                  className="w-full"
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
                    return (
                      <button
                        key={sport}
                        type="button"
                        onClick={() => toggleSport(sport)}
                        className={cn(
                          "rounded-full border px-3 py-1 text-sm transition-colors",
                          selected
                            ? "border-primary bg-primary/10 text-primary"
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
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center">
              <ConfidenceRing score={parlay.overall_confidence} label="Confidence" size={140} />
              <div>
                <p className="text-sm text-muted-foreground">Overall Confidence</p>
                <p className={cn("text-3xl font-bold", getConfidenceTextClass(parlay.overall_confidence))}>
                  {parlay.overall_confidence.toFixed(1)}%
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Parlay hit probability {(parlay.parlay_hit_prob * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="font-semibold">Parlay Legs</h4>
              {parlay.legs.map((leg, index) => (
                <div key={`${leg.market_id}-${index}`} className="border rounded-lg p-3 bg-muted/30">
                  <div className="text-xs text-muted-foreground mb-1">{leg.game}</div>
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
              ))}
            </div>

            <div className="border-t pt-4 space-y-3">
              <section>
                <h4 className="font-semibold mb-1">AI Summary</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-line">{parlay.ai_summary}</p>
              </section>
              <section className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                <h4 className="font-semibold mb-1 text-amber-900 dark:text-amber-100">Risk Assessment</h4>
                <p className="text-sm text-muted-foreground whitespace-pre-line">{parlay.ai_risk_notes}</p>
              </section>
            </div>
          </CardContent>
        </Card>
      )}

      {tripleParlay && <TripleParlayDisplay data={tripleParlay} />}
    </div>
  )
}
