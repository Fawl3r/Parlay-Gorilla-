"use client"

import { BestBet } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp } from "lucide-react"

interface BestBetsSectionProps {
  bestBets: BestBet[]
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

export function BestBetsSection({ bestBets, matchup }: BestBetsSectionProps) {
  if (!bestBets || bestBets.length === 0) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Top 3 Best Bets
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {bestBets.map((bet, index) => {
          const pickDisplay = replaceTeamPlaceholders(bet.pick, matchup)
          return (
            <div
              key={index}
              className="border rounded-lg p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline">{bet.bet_type}</Badge>
                    <span className="font-bold text-lg">{pickDisplay}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{bet.rationale}</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary">{Math.round(bet.confidence)}%</p>
                  <p className="text-xs text-muted-foreground">Confidence</p>
                </div>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

