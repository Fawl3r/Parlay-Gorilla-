"use client"

import { SpreadPick, TotalPick, ModelWinProbability } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface KeyNumbersBarProps {
  spreadPick: SpreadPick
  totalPick: TotalPick
  winProbability: ModelWinProbability
  matchup?: string
}

function replaceTeamPlaceholders(text: string, matchup?: string): string {
  if (!matchup || !text) return text
  
  // Extract team names from matchup: "Away Team @ Home Team"
  const match = matchup.match(/^(.+?)\s+@\s+(.+)$/)
  if (!match) return text
  
  const [, awayTeam, homeTeam] = match
  
  // Replace "Home Team" and "Away Team" with actual team names
  let result = text
  result = result.replace(/Home Team/gi, homeTeam.trim())
  result = result.replace(/Away Team/gi, awayTeam.trim())
  
  return result
}

/**
 * Get confidence badge styling based on score
 */
function getConfidenceBadgeStyle(confidence: number): { variant: "default" | "secondary" | "destructive" | "outline", className: string } {
  if (confidence >= 70) {
    return { variant: "default", className: "bg-green-600 hover:bg-green-700 text-white" }
  } else if (confidence >= 50) {
    return { variant: "secondary", className: "bg-yellow-600 hover:bg-yellow-700 text-white" }
  } else if (confidence >= 30) {
    return { variant: "outline", className: "border-orange-500 text-orange-500" }
  }
  return { variant: "destructive", className: "" }
}

export function KeyNumbersBar({ spreadPick, totalPick, winProbability, matchup }: KeyNumbersBarProps) {
  const spreadDisplay = replaceTeamPlaceholders(spreadPick.pick, matchup)
  const totalDisplay = replaceTeamPlaceholders(totalPick.pick, matchup)
  
  // Use the new ai_confidence field if available, otherwise fall back to calculated value
  const aiConfidence = winProbability.ai_confidence ?? 
    Math.round(Math.max(winProbability.home_win_prob, winProbability.away_win_prob) * 100)
  
  const confidenceStyle = getConfidenceBadgeStyle(aiConfidence)
  
  return (
    <Card className="border-primary/30">
      <CardContent className="p-4">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Spread Pick</p>
            <p className="font-bold text-lg">{spreadDisplay}</p>
            <Badge variant="outline" className="mt-1">
              {Math.round(spreadPick.confidence)}% confidence
            </Badge>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Total Pick</p>
            <p className="font-bold text-lg">{totalDisplay}</p>
            <Badge variant="outline" className="mt-1">
              {Math.round(totalPick.confidence)}% confidence
            </Badge>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Home Win Prob</p>
            <p className="font-bold text-lg">{Math.round(winProbability.home_win_prob * 100)}%</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Away Win Prob</p>
            <p className="font-bold text-lg">{Math.round(winProbability.away_win_prob * 100)}%</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground mb-1">Model Confidence</p>
            <p className="font-bold text-lg">{Math.round(aiConfidence)}%</p>
            <Badge variant={confidenceStyle.variant} className={`mt-1 ${confidenceStyle.className}`}>
              {winProbability.calculation_method || "model"}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

