"use client"

import { ModelWinProbability } from "@/lib/api"
import { getMatchupTeams, parseMatchup } from "@/lib/team-assets"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import Image from "next/image"
import { Calendar, Clock, MapPin } from "lucide-react"

interface MatchupHeroProps {
  matchup: string
  league: string
  gameTime: string
  confidence: ModelWinProbability
}

export function MatchupHero({ matchup, league, gameTime, confidence }: MatchupHeroProps) {
  const maxConfidence = Math.max(confidence.home_win_prob, confidence.away_win_prob)
  const confidenceScore = Math.round(maxConfidence * 100)
  
  const { awayTeam, homeTeam } = getMatchupTeams(matchup, league)
  const { awayTeam: awayTeamName, homeTeam: homeTeamName } = parseMatchup(matchup)
  
  const gameDate = new Date(gameTime)
  const formattedDate = gameDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })
  const formattedTime = gameDate.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  })

  return (
    <div className="relative overflow-hidden rounded-2xl border border-gray-300 dark:border-white/10 bg-gradient-to-br from-gray-200 via-gray-100 to-gray-200 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Background gradient based on team colors */}
      <div 
        className="absolute inset-0 opacity-20"
        style={{
          background: `linear-gradient(135deg, ${awayTeam?.primaryColor || '#10b981'}40 0%, transparent 50%, ${homeTeam?.primaryColor || '#10b981'}40 100%)`,
        }}
      />
      
      {/* Grid pattern overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03] dark:opacity-5"
        style={{
          backgroundImage: 'url("data:image/svg+xml,%3Csvg width="40" height="40" viewBox="0 0 40 40" xmlns="http://www.w3.org/2000/svg"%3E%3Cg fill="%23000000" fill-opacity="1"%3E%3Cpath d="M0 0h40v40H0V0zm1 1h38v38H1V1z"/%3E%3C/g%3E%3C/svg%3E")',
        }}
      />
      
      <div className="relative p-6 md:p-8">
        {/* League Badge */}
        <div className="flex justify-center mb-4">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-sm font-bold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-pulse"></span>
            {league} Game Analysis
          </span>
        </div>
        
        {/* Main Matchup Section */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-6 md:gap-10 py-6">
          {/* Away Team */}
          <div className="flex flex-col items-center text-center group">
            <div 
              className="relative w-28 h-28 md:w-36 md:h-36 rounded-2xl bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 p-4 mb-3 transition-transform group-hover:scale-105"
              style={{
                boxShadow: `0 10px 40px ${awayTeam?.primaryColor || '#10b981'}30`,
              }}
            >
              {awayTeam?.logo ? (
                <Image
                  src={awayTeam.logo}
                  alt={awayTeam.name}
                  fill
                  className="object-contain p-3"
                  unoptimized
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-4xl font-bold text-gray-400 dark:text-white/50">
                  {awayTeamName.substring(0, 3).toUpperCase()}
                </div>
              )}
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-1">
              {awayTeam?.name || awayTeamName}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Away</span>
              <span 
                className="px-2 py-0.5 rounded text-xs font-bold"
                style={{ 
                  backgroundColor: `${awayTeam?.primaryColor || '#10b981'}30`,
                  color: awayTeam?.primaryColor || '#10b981',
                }}
              >
                {Math.round(confidence.away_win_prob * 100)}%
              </span>
            </div>
          </div>
          
          {/* VS Divider */}
          <div className="flex flex-col items-center gap-2">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 border border-emerald-500/30 flex items-center justify-center">
              <span className="text-xl font-black text-gray-800 dark:text-white">@</span>
            </div>
            <span className="text-xs text-gray-500 uppercase tracking-widest">vs</span>
          </div>
          
          {/* Home Team */}
          <div className="flex flex-col items-center text-center group">
            <div 
              className="relative w-28 h-28 md:w-36 md:h-36 rounded-2xl bg-white dark:bg-white/5 border border-gray-200 dark:border-white/10 p-4 mb-3 transition-transform group-hover:scale-105"
              style={{
                boxShadow: `0 10px 40px ${homeTeam?.primaryColor || '#10b981'}30`,
              }}
            >
              {homeTeam?.logo ? (
                <Image
                  src={homeTeam.logo}
                  alt={homeTeam.name}
                  fill
                  className="object-contain p-3"
                  unoptimized
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-4xl font-bold text-gray-400 dark:text-white/50">
                  {homeTeamName.substring(0, 3).toUpperCase()}
                </div>
              )}
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-white mb-1">
              {homeTeam?.name || homeTeamName}
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Home</span>
              <span 
                className="px-2 py-0.5 rounded text-xs font-bold"
                style={{ 
                  backgroundColor: `${homeTeam?.primaryColor || '#10b981'}30`,
                  color: homeTeam?.primaryColor || '#10b981',
                }}
              >
                {Math.round(confidence.home_win_prob * 100)}%
              </span>
            </div>
          </div>
        </div>
        
        {/* Game Info Bar */}
        <div className="flex flex-wrap justify-center gap-4 md:gap-6 py-4 border-t border-gray-300 dark:border-white/10">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <Calendar className="w-4 h-4" />
            <span className="text-sm">{formattedDate}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <Clock className="w-4 h-4" />
            <span className="text-sm">{formattedTime}</span>
          </div>
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <MapPin className="w-4 h-4" />
            <span className="text-sm">{homeTeam?.name || homeTeamName} Stadium</span>
          </div>
        </div>
        
        {/* Confidence Section */}
        <div className="flex justify-center pt-4">
          <div className="flex items-center gap-6 px-6 py-3 rounded-xl bg-gray-200 dark:bg-white/5 border border-gray-300 dark:border-white/10">
            <ConfidenceRing score={confidenceScore} label="AI Confidence" size={100} />
            <div className="text-left">
              <p className="text-sm font-semibold text-gray-900 dark:text-white">Model Win Probability</p>
              <p className="text-2xl font-bold text-emerald-700 dark:text-emerald-400">
                {Math.round(confidence.home_win_prob * 100)}% - {Math.round(confidence.away_win_prob * 100)}%
              </p>
              <p className="text-xs text-gray-700 dark:text-gray-400">Home vs Away</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

