"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, Target, DollarSign } from "lucide-react"

interface BestPick {
  pick: string
  matchup?: string
  odds?: string
  rationale?: string
  confidence?: number
  type?: string // ML, spread, total
}

interface SameGameParlaysProps {
  parlays: any[] | Record<string, any> | null | undefined
}

export function SameGameParlays({ parlays }: SameGameParlaysProps) {
  if (!parlays) return null

  // Extract unique best picks from all parlay data
  const bestPicks: BestPick[] = []
  const seenPicks = new Set<string>()

  // Process either array or object format
  const parlayList = Array.isArray(parlays) ? parlays : Object.values(parlays)

  for (const parlay of parlayList) {
    if (!parlay?.legs) continue
    
    for (const leg of parlay.legs) {
      const pickKey = `${leg.pick}-${leg.matchup || leg.game}`
      if (!seenPicks.has(pickKey) && leg.pick) {
        seenPicks.add(pickKey)
        
        // Determine pick type from the pick text
        let pickType = "pick"
        const pickLower = leg.pick.toLowerCase()
        if (pickLower.includes("ml") || pickLower.includes("moneyline") || pickLower.includes("win")) {
          pickType = "Moneyline"
        } else if (pickLower.includes("spread") || pickLower.includes("+") || pickLower.includes("-")) {
          pickType = "Spread"
        } else if (pickLower.includes("over") || pickLower.includes("under") || pickLower.includes("total")) {
          pickType = "Total"
        }

        bestPicks.push({
          pick: leg.pick,
          matchup: leg.matchup || leg.game,
          odds: leg.odds,
          rationale: leg.rationale,
          confidence: leg.confidence,
          type: pickType,
        })
      }
    }
  }

  // Sort by confidence (highest first) and take top picks
  const topPicks = bestPicks
    .sort((a, b) => (b.confidence || 0) - (a.confidence || 0))
    .slice(0, 5) // Show top 5 unique picks

  if (topPicks.length === 0) return null

  const getPickIcon = (type?: string) => {
    switch (type) {
      case "Moneyline":
        return <DollarSign className="h-4 w-4" />
      case "Spread":
        return <Target className="h-4 w-4" />
      case "Total":
        return <TrendingUp className="h-4 w-4" />
      default:
        return <TrendingUp className="h-4 w-4" />
    }
  }

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "bg-muted"
    if (confidence >= 70) return "bg-green-500/20 text-green-400 border-green-500/30"
    if (confidence >= 50) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
    return "bg-red-500/20 text-red-400 border-red-500/30"
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Top Picks for This Matchup</h2>
      <p className="text-muted-foreground text-sm">
        AI-recommended bets with the highest confidence for this game
      </p>
      
      <div className="grid gap-3">
        {topPicks.map((pick, index) => (
          <Card 
            key={index} 
            className="border-primary/20 hover:border-primary/40 transition-colors"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="p-2 rounded-lg bg-primary/10 text-primary">
                    {getPickIcon(pick.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-lg">{pick.pick}</span>
                      {pick.odds && (
                        <Badge variant="outline" className="text-primary border-primary/30">
                          {pick.odds}
                        </Badge>
                      )}
                    </div>
                    {pick.matchup && (
                      <p className="text-sm text-muted-foreground mt-1">
                        {pick.matchup}
                      </p>
                    )}
                    {pick.rationale && (
                      <p className="text-sm text-muted-foreground mt-2 italic">
                        {pick.rationale}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col items-end gap-1">
                  {pick.type && (
                    <Badge variant="secondary" className="text-xs">
                      {pick.type}
                    </Badge>
                  )}
                  {pick.confidence && (
                    <Badge className={`${getConfidenceColor(pick.confidence)} border`}>
                      {Math.round(pick.confidence)}% conf
                    </Badge>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
