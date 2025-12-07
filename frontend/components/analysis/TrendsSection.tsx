"use client"

import { TrendAnalysis } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

interface TrendsSectionProps {
  atsTrends: TrendAnalysis
  totalsTrends: TrendAnalysis
  matchup?: string
}

function extractTeamNames(matchup?: string): { homeTeam: string; awayTeam: string } | null {
  if (!matchup) return null
  
  const match = matchup.match(/^(.+?)\s+@\s+(.+)$/)
  if (!match) return null
  
  return {
    awayTeam: match[1].trim(),
    homeTeam: match[2].trim(),
  }
}

export function TrendsSection({ atsTrends, totalsTrends, matchup }: TrendsSectionProps) {
  const teams = extractTeamNames(matchup)
  const homeTeamLabel = teams?.homeTeam || "Home Team"
  const awayTeamLabel = teams?.awayTeam || "Away Team"
  
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>ATS Trends</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm font-semibold mb-1">{homeTeamLabel}</p>
            <p className="text-sm text-muted-foreground">{atsTrends.home_team_trend}</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1">{awayTeamLabel}</p>
            <p className="text-sm text-muted-foreground">{atsTrends.away_team_trend}</p>
          </div>
          <div className="pt-3 border-t">
            <p className="text-sm">{atsTrends.analysis}</p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Over/Under Trends</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-sm font-semibold mb-1">{homeTeamLabel}</p>
            <p className="text-sm text-muted-foreground">{totalsTrends.home_team_trend}</p>
          </div>
          <div>
            <p className="text-sm font-semibold mb-1">{awayTeamLabel}</p>
            <p className="text-sm text-muted-foreground">{totalsTrends.away_team_trend}</p>
          </div>
          <div className="pt-3 border-t">
            <p className="text-sm">{totalsTrends.analysis}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

