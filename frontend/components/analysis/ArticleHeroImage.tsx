"use client"

import { getMatchupTeams, parseMatchup } from "@/lib/team-assets"
import { motion } from "framer-motion"
import { Clock, User } from "lucide-react"

interface ArticleHeroImageProps {
  matchup: string
  league: string
  headline?: string
  subheadline?: string
  publishDate?: string
  readTime?: number
}


/**
 * Hero image banner for game analysis articles
 * Displays in-game action photos similar to Covers.com
 */
export function ArticleHeroImage({ 
  matchup, 
  league, 
  headline, 
  subheadline,
  publishDate,
  readTime = 4
}: ArticleHeroImageProps) {
  const { awayTeam, homeTeam } = getMatchupTeams(matchup, league)
  
  // Format date
  const formattedDate = publishDate 
    ? new Date(publishDate).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      })
    : new Date().toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      })

  return (
    <div className="mb-8">
      {/* Headline Section - Above the image like Covers.com */}
      <div className="mb-6">
        <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-foreground leading-tight mb-4">
          {headline || `${matchup.replace('@', 'vs')} Predictions, Best Bets, Props & Odds`}
        </h1>
        {subheadline && (
          <p className="text-lg md:text-xl text-muted-foreground leading-relaxed max-w-4xl">
            {subheadline}
          </p>
        )}
        
        {/* Author byline - like Covers.com */}
        <div className="flex items-center gap-4 mt-6 pt-4 border-t border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Parlay Gorilla AI</p>
              <p className="text-sm text-muted-foreground">Betting Analyst</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span>{formattedDate}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {readTime} min read
            </span>
          </div>
        </div>
        
        {/* Quick navigation pills */}
        <div className="flex items-center gap-2 mt-4">
          <span className="text-sm text-muted-foreground font-medium">On this page:</span>
          <div className="flex flex-wrap gap-2">
            <a href="#best-bets" className="px-3 py-1 text-sm font-medium border border-border rounded-full hover:border-primary hover:text-primary transition-colors">
              Best Bets
            </a>
            <a href="#trends" className="px-3 py-1 text-sm font-medium border border-border rounded-full hover:border-primary hover:text-primary transition-colors">
              Trends
            </a>
            <a href="#matchup" className="px-3 py-1 text-sm font-medium border border-border rounded-full hover:border-primary hover:text-primary transition-colors">
              Matchup
            </a>
          </div>
        </div>
      </div>
      
      {/* Hero Banner with Team Color Gradient - Photo section removed until licensed APIs */}
      <motion.div 
        className="relative w-full aspect-[2.5/1] md:aspect-[2.8/1] rounded-xl overflow-hidden"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Team color gradient background */}
        <div 
          className="absolute inset-0"
          style={{
            background: `linear-gradient(135deg, 
              ${homeTeam?.primaryColor || '#10b981'} 0%, 
              ${homeTeam?.primaryColor || '#10b981'}99 25%,
              #1a1a2e 50%,
              ${awayTeam?.primaryColor || '#06b6d4'}99 75%,
              ${awayTeam?.primaryColor || '#06b6d4'} 100%)`,
          }}
        />
        
        {/* Subtle pattern overlay */}
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
        
        {/* Dark gradient overlay for text readability */}
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0.2) 100%)',
          }}
        />
        
        {/* Team color accent bars on sides */}
        <div 
          className="absolute top-0 left-0 w-1 h-full" 
          style={{ backgroundColor: awayTeam?.primaryColor || '#06b6d4' }} 
        />
        <div 
          className="absolute top-0 right-0 w-1 h-full" 
          style={{ backgroundColor: homeTeam?.primaryColor || '#10b981' }} 
        />
        
        {/* Team logos overlay at bottom corners */}
        <div className="absolute bottom-4 left-4 flex items-center gap-2">
          {awayTeam?.logo && (
            <div className="w-12 h-12 md:w-16 md:h-16 bg-white/10 backdrop-blur-sm rounded-lg p-2 border border-white/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={awayTeam.logo}
                alt={awayTeam.name}
                className="w-full h-full object-contain"
              />
            </div>
          )}
          <span className="text-white/80 font-bold text-lg md:text-xl">@</span>
          {homeTeam?.logo && (
            <div className="w-12 h-12 md:w-16 md:h-16 bg-white/10 backdrop-blur-sm rounded-lg p-2 border border-white/20">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={homeTeam.logo}
                alt={homeTeam.name}
                className="w-full h-full object-contain"
              />
            </div>
          )}
        </div>
        
        {/* League badge at top right */}
        <div className="absolute top-4 right-4">
          <div className="px-3 py-1.5 bg-white/10 backdrop-blur-sm rounded-full border border-white/20">
            <span className="text-xs font-semibold text-white/90 uppercase tracking-wider">
              {league} Game Preview
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

