"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { api } from "@/lib/api"
import { 
  Trophy, 
  Flame, 
  Target, 
  Zap, 
  ArrowRight, 
  Calendar,
  TrendingUp,
  Loader2
} from "lucide-react"

interface SportInfo {
  slug: string
  code: string
  display_name: string
  default_markets: string[]
}

// Sport configurations with icons, colors, and descriptions
const SPORT_CONFIG: Record<string, {
  icon: React.ReactNode
  gradient: string
  bgGlow: string
  description: string
  features: string[]
}> = {
  nfl: {
    icon: <Trophy className="h-10 w-10" />,
    gradient: "from-green-500 to-emerald-600",
    bgGlow: "bg-green-500/20",
    description: "America's game. Get AI-powered predictions for every NFL matchup with spread, moneyline, and total picks.",
    features: ["Weekly matchup analysis", "Injury impact ratings", "Weather considerations"]
  },
  nba: {
    icon: <Flame className="h-10 w-10" />,
    gradient: "from-orange-500 to-red-600",
    bgGlow: "bg-orange-500/20",
    description: "Fast-paced basketball action. Our model factors in pace, offensive/defensive ratings, and rest days.",
    features: ["Pace-adjusted projections", "Back-to-back detection", "Player prop insights"]
  },
  nhl: {
    icon: <Zap className="h-10 w-10" />,
    gradient: "from-blue-500 to-cyan-600",
    bgGlow: "bg-blue-500/20",
    description: "Ice hockey predictions powered by goal differential, special teams, and goalie performance data.",
    features: ["Goalie matchup analysis", "Power play efficiency", "Home ice advantage"]
  },
  mlb: {
    icon: <Target className="h-10 w-10" />,
    gradient: "from-red-500 to-rose-600",
    bgGlow: "bg-red-500/20",
    description: "Baseball predictions with starting pitcher analysis, bullpen strength, and run line picks.",
    features: ["Starting pitcher ratings", "Bullpen ERA analysis", "Park factor adjustments"]
  },
  soccer_epl: {
    icon: <TrendingUp className="h-10 w-10" />,
    gradient: "from-purple-500 to-violet-600",
    bgGlow: "bg-purple-500/20",
    description: "Premier League predictions using xG (expected goals), form analysis, and head-to-head data.",
    features: ["xG-based projections", "Form analysis", "Home/away splits"]
  },
  soccer_usa_mls: {
    icon: <TrendingUp className="h-10 w-10" />,
    gradient: "from-sky-500 to-blue-600",
    bgGlow: "bg-sky-500/20",
    description: "MLS predictions with travel distance factors, altitude adjustments, and roster analysis.",
    features: ["Travel fatigue factor", "Conference analysis", "Playoff implications"]
  },
}

// Fallback config for sports not in the list
const DEFAULT_SPORT_CONFIG = {
  icon: <Trophy className="h-10 w-10" />,
  gradient: "from-gray-500 to-gray-600",
  bgGlow: "bg-gray-500/20",
  description: "AI-powered predictions for this sport.",
  features: ["Model predictions", "Odds analysis", "Value detection"]
}

export default function SportsSelectionPage() {
  const [sports, setSports] = useState<SportInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFilter, setSelectedFilter] = useState<"all" | "today" | "upcoming">("all")

  useEffect(() => {
    async function loadSports() {
      try {
        const sportsList = await api.listSports()
        setSports(sportsList)
      } catch (error) {
        console.error("Failed to load sports:", error)
      } finally {
        setLoading(false)
      }
    }
    loadSports()
  }, [])

  const getConfig = (slug: string) => {
    return SPORT_CONFIG[slug] || DEFAULT_SPORT_CONFIG
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-950/30 via-black/50 to-black/30" />
          
          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center max-w-3xl mx-auto"
            >
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
                <span className="text-white">Choose Your </span>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                  Sport
                </span>
              </h1>
              <p className="text-xl text-gray-300 mb-8">
                Get AI-powered predictions and build winning parlays across all major sports
              </p>
              
              {/* Filter Tabs */}
              <div className="flex justify-center gap-2 mb-8">
                {[
                  { value: "all", label: "All Sports" },
                  { value: "today", label: "Today's Games" },
                  { value: "upcoming", label: "Upcoming" },
                ].map((filter) => (
                  <button
                    key={filter.value}
                    onClick={() => setSelectedFilter(filter.value as any)}
                    className={`px-5 py-2.5 rounded-full text-sm font-semibold transition-all ${
                      selectedFilter === filter.value
                        ? "bg-emerald-500 text-black"
                        : "bg-white/10 text-gray-300 hover:bg-white/20"
                    }`}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Sports Grid */}
        <section className="py-12 bg-black/30 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                <span className="ml-3 text-gray-400">Loading sports...</span>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sports.map((sport, index) => {
                  const config = getConfig(sport.slug)
                  return (
                    <motion.div
                      key={sport.slug}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.1 }}
                    >
                      <Link href={`/games/${sport.slug}/today`}>
                        <div className="group relative rounded-2xl bg-white/[0.02] border border-white/10 hover:border-emerald-500/50 transition-all duration-300 overflow-hidden h-full">
                          {/* Background Glow */}
                          <div className={`absolute top-0 right-0 w-40 h-40 ${config.bgGlow} rounded-full blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />
                          
                          <div className="relative p-6">
                            {/* Icon & Title */}
                            <div className="flex items-start justify-between mb-4">
                              <div className={`p-3 rounded-xl bg-gradient-to-br ${config.gradient} text-white`}>
                                {config.icon}
                              </div>
                              <ArrowRight className="h-5 w-5 text-gray-500 group-hover:text-emerald-400 group-hover:translate-x-1 transition-all" />
                            </div>
                            
                            <h3 className="text-2xl font-bold text-white mb-2">
                              {sport.display_name}
                            </h3>
                            
                            <p className="text-gray-400 text-sm mb-4 line-clamp-2">
                              {config.description}
                            </p>
                            
                            {/* Features */}
                            <div className="space-y-2 mb-4">
                              {config.features.map((feature, i) => (
                                <div key={i} className="flex items-center gap-2 text-xs text-gray-500">
                                  <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                  {feature}
                                </div>
                              ))}
                            </div>
                            
                            {/* Markets */}
                            <div className="flex flex-wrap gap-1.5">
                              {sport.default_markets.slice(0, 3).map((market) => (
                                <span
                                  key={market}
                                  className="px-2 py-1 rounded-md bg-white/5 text-xs text-gray-400 border border-white/10"
                                >
                                  {market === "h2h" ? "Moneyline" : market === "spreads" ? "Spread" : "Total"}
                                </span>
                              ))}
                            </div>
                          </div>
                          
                          {/* Bottom Bar */}
                          <div className="px-6 py-3 bg-white/[0.02] border-t border-white/5 flex items-center justify-between">
                            <div className="flex items-center gap-2 text-xs text-gray-500">
                              <Calendar className="h-3.5 w-3.5" />
                              <span>View Games</span>
                            </div>
                            <div className="text-xs font-semibold text-emerald-400 group-hover:text-emerald-300">
                              Explore →
                            </div>
                          </div>
                        </div>
                      </Link>
                    </motion.div>
                  )
                })}
              </div>
            )}
          </div>
        </section>

        {/* Quick Actions */}
        <section className="py-16 bg-gradient-to-b from-black/30 to-emerald-950/20">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
              >
                <Link href="/build">
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-green-500/10 border border-emerald-500/30 hover:border-emerald-500/50 transition-all group">
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-xl bg-emerald-500/20">
                        <Zap className="h-6 w-6 text-emerald-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white mb-1">AI Parlay Builder</h3>
                        <p className="text-sm text-gray-400">Generate AI-optimized parlays across all sports</p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-emerald-400 ml-auto group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </Link>
              </motion.div>
              
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
              >
                <Link href="/analysis">
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/20 to-violet-500/10 border border-purple-500/30 hover:border-purple-500/50 transition-all group">
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-xl bg-purple-500/20">
                        <Target className="h-6 w-6 text-purple-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white mb-1">Game Analysis</h3>
                        <p className="text-sm text-gray-400">Deep-dive matchup breakdowns & picks</p>
                      </div>
                      <ArrowRight className="h-5 w-5 text-purple-400 ml-auto group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </Link>
              </motion.div>
            </div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}

