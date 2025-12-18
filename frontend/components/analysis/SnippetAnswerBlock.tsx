"use client"

/**
 * SnippetAnswerBlock - Optimized for Google Featured Snippets
 * 
 * This component displays the key answer at the top of the page
 * in a format that Google can easily extract for featured snippets.
 * 
 * Key features:
 * - Clear H2 question header
 * - Direct answer in first paragraph
 * - Structured data alignment
 * - Concise, fact-based format
 */

import { GameAnalysisResponse } from "@/lib/api"
import { parseMatchup } from "@/lib/team-assets"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp, TrendingDown, AlertCircle, Trophy, Target } from "lucide-react"

interface SnippetAnswerBlockProps {
  analysis: GameAnalysisResponse
}

// Parse matchup string like "Team A @ Team B" or "Team A vs Team B" to extract teams
function parseMatchupTeams(matchup: string): { home: string; away: string } {
  const parsed = parseMatchup(matchup)
  return {
    away: parsed.awayTeam || "Away Team",
    home: parsed.homeTeam || "Home Team",
  }
}

export function SnippetAnswerBlock({ analysis }: SnippetAnswerBlockProps) {
  const probs = analysis.analysis_content?.model_win_probability
  const { home: homeTeam, away: awayTeam } = parseMatchupTeams(analysis.matchup)
  const homeProb = probs?.home_win_prob || 0.5
  const awayProb = probs?.away_win_prob || 0.5
  
  const favoredTeam = homeProb > awayProb ? homeTeam : awayTeam
  const favoredProb = Math.max(homeProb, awayProb)
  const underdogTeam = homeProb > awayProb ? awayTeam : homeTeam
  const underdogProb = Math.min(homeProb, awayProb)
  
  const isClose = Math.abs(homeProb - awayProb) < 0.1
  const isUpset = underdogProb > 0.40  // Underdog has decent chance
  
  // Get AI confidence
  const aiConfidence = probs?.ai_confidence || 50
  
  // Get picks - use correct property names from GameAnalysisContent
  const spreadPick = analysis.analysis_content?.ai_spread_pick
  const totalPick = analysis.analysis_content?.ai_total_pick
  const bestBets = analysis.analysis_content?.best_bets
  const bestBet = bestBets?.[0]
  
  return (
    <section 
      className="mb-8" 
      aria-label="Quick Answer"
      itemScope 
      itemType="https://schema.org/Answer"
    >
      {/* Primary Answer Box - Optimized for Featured Snippet */}
      <Card className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 border-amber-200 dark:border-amber-800 p-6 mb-4">
        {/* Question Header (H2 for snippet targeting) */}
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-3">
          Who will win {analysis.matchup}?
        </h2>
        
        {/* Direct Answer (First paragraph - most likely to be featured) */}
        <p 
          className="text-lg text-gray-800 dark:text-gray-200 mb-4"
          itemProp="text"
        >
          <strong>{favoredTeam}</strong> is projected to win with a{" "}
          <strong className="text-amber-600 dark:text-amber-400">
            {(favoredProb * 100).toFixed(0)}% probability
          </strong>
          {isClose && " in what should be a close game"}.
          {underdogTeam} has a {(underdogProb * 100).toFixed(0)}% chance
          {isUpset && ", making this a potential upset opportunity"}.
        </p>
        
        {/* Confidence Badge */}
        <div className="flex items-center gap-2 mb-4">
          <Badge 
            variant={aiConfidence >= 70 ? "default" : aiConfidence >= 50 ? "secondary" : "outline"}
            className={
              aiConfidence >= 70 
                ? "bg-green-600" 
                : aiConfidence >= 50 
                  ? "bg-amber-500" 
                  : ""
            }
          >
            <Target className="w-3 h-3 mr-1" />
            Model Confidence: {aiConfidence}%
          </Badge>
          
          {isClose && (
            <Badge variant="outline" className="border-amber-500 text-amber-600">
              <AlertCircle className="w-3 h-3 mr-1" />
              Close Game
            </Badge>
          )}
          
          {isUpset && (
            <Badge variant="outline" className="border-purple-500 text-purple-600">
              <TrendingUp className="w-3 h-3 mr-1" />
              Upset Alert
            </Badge>
          )}
        </div>
      </Card>
      
      {/* Quick Picks Grid - Secondary snippet targets */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Spread Pick */}
        {spreadPick?.pick && (
          <Card className="p-4 border-l-4 border-l-blue-500">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
              Best Spread Bet
            </h3>
            <p className="text-blue-600 dark:text-blue-400 font-medium mb-1">
              {spreadPick.pick}
            </p>
            {spreadPick.confidence && (
              <Badge variant="outline" className="text-xs">
                {spreadPick.confidence} confidence
              </Badge>
            )}
          </Card>
        )}
        
        {/* Total Pick */}
        {totalPick?.pick && (
          <Card className="p-4 border-l-4 border-l-green-500">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
              Over/Under Pick
            </h3>
            <p className="text-green-600 dark:text-green-400 font-medium mb-1">
              {totalPick.pick}
            </p>
            {totalPick.confidence && (
              <Badge variant="outline" className="text-xs">
                {totalPick.confidence} confidence
              </Badge>
            )}
          </Card>
        )}
        
        {/* Best Bet */}
        {bestBet?.pick && (
          <Card className="p-4 border-l-4 border-l-amber-500">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-1 flex items-center gap-1">
              <Trophy className="w-4 h-4 text-amber-500" />
              Top Pick
            </h3>
            <p className="text-amber-600 dark:text-amber-400 font-medium mb-1">
              {bestBet.pick}
            </p>
            {bestBet.confidence && (
              <Badge variant="outline" className="text-xs">
                {bestBet.confidence} confidence
              </Badge>
            )}
          </Card>
        )}
      </div>
      
      {/* Win Probability Summary (H3 for secondary snippet) */}
      <Card className="mt-4 p-4">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
          {analysis.matchup} Win Probabilities
        </h3>
        
        <div className="flex items-center justify-between">
          {/* Away Team */}
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              {awayTeam}
            </p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(awayProb * 100).toFixed(0)}%
            </p>
          </div>
          
          {/* VS Divider */}
          <div className="text-gray-400 font-medium">vs</div>
          
          {/* Home Team */}
          <div className="text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
              {homeTeam}
              <span className="ml-1 text-xs text-amber-500">(Home)</span>
            </p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {(homeProb * 100).toFixed(0)}%
            </p>
          </div>
        </div>
        
        {/* Probability Bar */}
        <div className="mt-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
          <div 
            className="h-full bg-red-500 transition-all duration-500"
            style={{ width: `${awayProb * 100}%` }}
            title={`${awayTeam}: ${(awayProb * 100).toFixed(0)}%`}
          />
          <div 
            className="h-full bg-blue-500 transition-all duration-500"
            style={{ width: `${homeProb * 100}%` }}
            title={`${homeTeam}: ${(homeProb * 100).toFixed(0)}%`}
          />
        </div>
        
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Probabilities calculated by Parlay Gorilla AI using team stats, injuries, weather, and market data.
        </p>
      </Card>
    </section>
  )
}

export default SnippetAnswerBlock

