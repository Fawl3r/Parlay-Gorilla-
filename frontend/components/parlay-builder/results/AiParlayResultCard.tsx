"use client"

import { useEffect, useRef } from "react"

import type { ParlayResponse } from "@/lib/api"
import { cn } from "@/lib/utils"
import { getConfidenceTextClass, getMarketLabel, getPickLabel } from "@/lib/parlayFormatting"
import { BringIntoViewManager } from "@/lib/ui/BringIntoViewManager"

import { ConfidenceRing } from "@/components/ConfidenceRing"
import { ShareParlayButton } from "@/components/social/ShareParlayButton"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import type { SportOption } from "../types"
import { SPORT_COLORS } from "../types"

export function AiParlayResultCard({
  parlay,
  onSave,
  isSaving,
}: {
  parlay: ParlayResponse
  onSave: () => void
  isSaving: boolean
}) {
  const rootRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    BringIntoViewManager.bringIntoView(rootRef.current, { behavior: "smooth", block: "start" })
  }, [parlay.id])

  return (
    <div ref={rootRef} tabIndex={-1}>
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
              <Button variant="outline" size="sm" onClick={onSave} disabled={isSaving}>
                {isSaving ? "Saving..." : "Save Parlay"}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
          <div className="flex flex-col gap-4 sm:gap-6 lg:flex-row lg:items-start">
            <ConfidenceRing
              score={parlay.model_confidence !== undefined ? parlay.model_confidence * 100 : parlay.overall_confidence}
              label="Model Confidence"
              size={140}
            />
            <div className="flex-1">
              <p className="text-sm text-muted-foreground">AI Model Confidence</p>
              <p
                className={cn(
                  "text-3xl font-bold",
                  getConfidenceTextClass(
                    parlay.model_confidence !== undefined ? parlay.model_confidence * 100 : parlay.overall_confidence
                  )
                )}
              >
                {parlay.model_confidence !== undefined
                  ? (parlay.model_confidence * 100).toFixed(1)
                  : parlay.overall_confidence.toFixed(1)}
                %
              </p>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                <div className="bg-muted/50 rounded-lg p-2 text-center">
                  <p className="text-xs text-muted-foreground">Hit Prob</p>
                  <p className="font-semibold text-lg">{(parlay.parlay_hit_prob * 100).toFixed(1)}%</p>
                </div>

                {parlay.parlay_ev !== undefined && (
                  <div className={cn("rounded-lg p-2 text-center", parlay.parlay_ev > 0 ? "bg-green-500/20" : "bg-red-500/20")}>
                    <p className="text-xs text-muted-foreground">Expected Value</p>
                    <p className={cn("font-semibold text-lg", parlay.parlay_ev > 0 ? "text-green-400" : "text-red-400")}>
                      {parlay.parlay_ev > 0 ? "+" : ""}
                      {(parlay.parlay_ev * 100).toFixed(1)}%
                    </p>
                  </div>
                )}

                {parlay.upset_count !== undefined && parlay.upset_count > 0 && (
                  <div className="bg-purple-500/20 rounded-lg p-2 text-center">
                    <p className="text-xs text-muted-foreground">Upsets</p>
                    <p className="font-semibold text-lg text-purple-400">🦍 {parlay.upset_count}</p>
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
                    <span className={cn("text-xs font-medium px-2 py-0.5 rounded-full border", colors.bg, colors.text, colors.border)}>
                      {sport}
                    </span>
                    <span className="text-xs text-muted-foreground">{leg.game}</span>
                  </div>
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="font-semibold text-foreground">Pick: {getPickLabel(leg)}</p>
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
    </div>
  )
}


