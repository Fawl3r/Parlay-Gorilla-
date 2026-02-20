"use client"

import { ParlayResponse, TripleParlayResponse } from "@/lib/api"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { getPickLabel, getMarketLabel } from "@/lib/parlayFormatting"
import { cn } from "@/lib/utils"

type SportOption = "NFL" | "NBA" | "NHL" | "MLB"

const SPORT_COLORS: Record<SportOption, { bg: string; text: string; border: string }> = {
  NFL: { bg: "bg-green-500/20", text: "text-green-400", border: "border-green-500/50" },
  NBA: { bg: "bg-orange-500/20", text: "text-orange-400", border: "border-orange-500/50" },
  NHL: { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/50" },
  MLB: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/50" },
}

const COLUMN_META = {
  safe: {
    title: "Safe Core",
    description: "3-6 legs • high confidence focus",
    accent: "from-emerald-500/20 via-emerald-500/10 to-transparent",
  },
  balanced: {
    title: "Balanced Edge",
    description: "7-12 legs • smart mix of value",
    accent: "from-sky-500/20 via-sky-500/10 to-transparent",
  },
  degen: {
    title: "Degen Lotto",
    description: "13-20 legs • moonshot upside",
    accent: "from-rose-500/20 via-rose-500/10 to-transparent",
  },
} as const

interface TripleParlayDisplayProps {
  data: TripleParlayResponse
}

export function TripleParlayDisplay({ data }: TripleParlayDisplayProps) {
  const groups: Array<{ key: "safe" | "balanced" | "degen"; parlay: ParlayResponse }> = [
    { key: "safe", parlay: data.safe },
    { key: "balanced", parlay: data.balanced },
    { key: "degen", parlay: data.degen },
  ]

  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
      {groups.map(({ key, parlay }) => {
        const column = COLUMN_META[key]
        const meta = data.metadata?.[key]
        return (
          <Card key={key} className="relative overflow-hidden transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg">
            <div className={`absolute inset-0 bg-gradient-to-b ${column.accent} pointer-events-none`} />
            <CardHeader className="relative">
              <CardTitle className="flex items-center justify-between">
                <span>{column.title}</span>
                <Badge variant="outline" className="text-xs">
                  {parlay.num_legs} legs • {meta?.sport || parlay.risk_profile}
                </Badge>
              </CardTitle>
              <CardDescription>{column.description}</CardDescription>
            </CardHeader>
            <CardContent className="relative space-y-4">
              <div className="flex items-center gap-4">
                <ConfidenceRing score={parlay.overall_confidence} size={90} />
                <div>
                  <div className="text-3xl font-bold">{(parlay.parlay_hit_prob * 100).toFixed(1)}%</div>
                  <p className="text-xs text-muted-foreground">Hit probability</p>
                  {meta?.highlight_leg && (
                    <p className="mt-2 text-xs text-muted-foreground">
                      Highlight: <span className="font-medium text-foreground">{meta.highlight_leg}</span>
                    </p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-semibold text-sm uppercase tracking-wide text-muted-foreground">Legs</h4>
                {parlay.legs.map((leg, index) => {
                  const sport = (leg.sport || "NFL") as SportOption
                  const colors = SPORT_COLORS[sport] || SPORT_COLORS.NFL
                  return (
                    <div key={`${leg.market_id}-${index}`} className="rounded-lg border bg-background/70 p-3 transition-transform duration-200 hover:-translate-y-1 hover:shadow-md">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn(
                          "text-xs font-medium px-1.5 py-0.5 rounded border",
                          colors.bg, colors.text, colors.border
                        )}>
                          {sport}
                        </span>
                        <span className="text-xs text-muted-foreground">{leg.game}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-primary">{getPickLabel(leg)}</p>
                          <p className="text-xs text-muted-foreground">
                            {getMarketLabel(leg.market_type)} • Odds {leg.odds}
                          </p>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {leg.confidence.toFixed(0)}% conf
                        </Badge>
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="border-t pt-3 space-y-3">
                <section>
                  <h5 className="text-sm font-semibold">AI Summary</h5>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">{parlay.ai_summary}</p>
                </section>
                <section className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
                  <h5 className="text-sm font-semibold text-amber-900 dark:text-amber-100">Risk Notes</h5>
                  <p className="text-sm text-muted-foreground whitespace-pre-line">{parlay.ai_risk_notes}</p>
                </section>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}

