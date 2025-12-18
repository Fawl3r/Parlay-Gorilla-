"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { api, ParlayResponse } from "@/lib/api"
import { 
  History, 
  Calendar, 
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Loader2,
  Crown,
  Lock,
  ChevronRight,
  Trophy,
  AlertTriangle
} from "lucide-react"
import { cn } from "@/lib/utils"

interface HistoricalParlay {
  id: string
  created_at: string
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  status: "pending" | "hit" | "missed"
  legs: {
    game: string
    pick: string
    odds: string
    result?: "hit" | "missed" | "pending"
  }[]
  payout?: number
}

// Mock data for demonstration - in production, this comes from the API
const MOCK_HISTORY: HistoricalParlay[] = [
  {
    id: "1",
    created_at: new Date(Date.now() - 86400000).toISOString(),
    num_legs: 5,
    risk_profile: "balanced",
    parlay_hit_prob: 0.12,
    status: "hit",
    legs: [
      { game: "Bills @ Dolphins", pick: "Bills ML", odds: "-145", result: "hit" },
      { game: "Lakers @ Celtics", pick: "Lakers +4.5", odds: "-110", result: "hit" },
      { game: "Rangers @ Bruins", pick: "Over 5.5", odds: "-115", result: "hit" },
      { game: "Chiefs @ Raiders", pick: "Chiefs -6.5", odds: "-110", result: "hit" },
      { game: "Suns @ Warriors", pick: "Warriors ML", odds: "+130", result: "hit" },
    ],
    payout: 485
  },
  {
    id: "2",
    created_at: new Date(Date.now() - 172800000).toISOString(),
    num_legs: 8,
    risk_profile: "degen",
    parlay_hit_prob: 0.04,
    status: "missed",
    legs: [
      { game: "Packers @ Bears", pick: "Packers -3.5", odds: "-110", result: "hit" },
      { game: "49ers @ Seahawks", pick: "49ers ML", odds: "-180", result: "hit" },
      { game: "Nets @ Knicks", pick: "Over 215.5", odds: "-110", result: "hit" },
      { game: "Heat @ Bucks", pick: "Heat +6.5", odds: "-110", result: "missed" },
      { game: "Penguins @ Capitals", pick: "Penguins ML", odds: "+140", result: "hit" },
      { game: "Red Sox @ Yankees", pick: "Over 8.5", odds: "-105", result: "hit" },
      { game: "Dodgers @ Giants", pick: "Dodgers -1.5", odds: "+120", result: "hit" },
      { game: "Cowboys @ Eagles", pick: "Eagles ML", odds: "-135", result: "missed" },
    ]
  },
  {
    id: "3",
    created_at: new Date(Date.now() - 3600000).toISOString(),
    num_legs: 4,
    risk_profile: "conservative",
    parlay_hit_prob: 0.25,
    status: "pending",
    legs: [
      { game: "Ravens @ Bengals", pick: "Ravens ML", odds: "-150", result: "pending" },
      { game: "Nuggets @ Clippers", pick: "Under 224.5", odds: "-110", result: "pending" },
      { game: "Oilers @ Flames", pick: "Oilers ML", odds: "-135", result: "pending" },
      { game: "Cardinals @ Cubs", pick: "Cardinals ML", odds: "+105", result: "pending" },
    ]
  }
]

export default function ParlayHistoryPage() {
  return (
    <ProtectedRoute>
      <ParlayHistoryContent />
    </ProtectedRoute>
  )
}

function ParlayHistoryContent() {
  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const [history, setHistory] = useState<HistoricalParlay[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<"all" | "pending" | "hit" | "missed">("all")
  const [expandedParlay, setExpandedParlay] = useState<string | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  async function loadHistory() {
    try {
      setLoading(true)
      // In production, fetch from API: await api.get('/api/parlays/history')
      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 500))
      setHistory(MOCK_HISTORY)
    } catch (error) {
      console.error("Failed to load parlay history:", error)
    } finally {
      setLoading(false)
    }
  }

  const filteredHistory = history.filter(p => filter === "all" || p.status === filter)
  
  // Calculate stats
  const stats = {
    total: history.length,
    hits: history.filter(p => p.status === "hit").length,
    misses: history.filter(p => p.status === "missed").length,
    pending: history.filter(p => p.status === "pending").length,
    hitRate: history.length > 0 
      ? (history.filter(p => p.status === "hit").length / history.filter(p => p.status !== "pending").length * 100) || 0
      : 0
  }

  // Free users can only see last 5 parlays
  const displayedHistory = isPremium ? filteredHistory : filteredHistory.slice(0, 5)
  const hasMoreLocked = !isPremium && filteredHistory.length > 5

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Header Section */}
        <section className="relative py-12 border-b border-white/10 bg-black/40 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <History className="h-6 w-6 text-emerald-400" />
                  <h1 className="text-3xl md:text-4xl font-black text-white">
                    Parlay History
                  </h1>
                </div>
                <p className="text-gray-400">
                  Track your past parlays and see how your picks performed
                </p>
              </div>
              
              {!isPremium && (
                <Link href="/premium">
                  <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 cursor-pointer hover:bg-emerald-500/30">
                    <Crown className="h-3 w-3 mr-1" />
                    Upgrade for Full History
                  </Badge>
                </Link>
              )}
            </div>
          </div>
        </section>

        {/* Stats Cards */}
        <section className="py-6 bg-black/20">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
                <div className="text-2xl font-black text-white">{stats.total}</div>
                <div className="text-xs text-gray-500">Total Parlays</div>
              </div>
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30">
                <div className="text-2xl font-black text-emerald-400">{stats.hits}</div>
                <div className="text-xs text-emerald-400/60">Hits</div>
              </div>
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                <div className="text-2xl font-black text-red-400">{stats.misses}</div>
                <div className="text-xs text-red-400/60">Misses</div>
              </div>
              <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <div className="text-2xl font-black text-amber-400">{stats.pending}</div>
                <div className="text-xs text-amber-400/60">Pending</div>
              </div>
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                <div className="text-2xl font-black text-purple-400">{stats.hitRate.toFixed(0)}%</div>
                <div className="text-xs text-purple-400/60">Hit Rate</div>
              </div>
            </div>
          </div>
        </section>

        {/* Filters */}
        <section className="py-4 border-b border-white/5">
          <div className="container mx-auto px-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              {(["all", "pending", "hit", "missed"] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium transition-all",
                    filter === status
                      ? status === "hit" ? "bg-emerald-500 text-black"
                        : status === "missed" ? "bg-red-500 text-white"
                        : status === "pending" ? "bg-amber-500 text-black"
                        : "bg-white/20 text-white"
                      : "bg-white/5 text-gray-400 hover:bg-white/10"
                  )}
                >
                  {status === "all" ? "All" : status.charAt(0).toUpperCase() + status.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* History List */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            {loading ? (
              <div className="flex justify-center items-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                <span className="ml-3 text-gray-400">Loading history...</span>
              </div>
            ) : displayedHistory.length === 0 ? (
              <div className="text-center py-20">
                <History className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">No Parlays Yet</h3>
                <p className="text-gray-400 mb-6">Start building parlays to see your history here</p>
                <Link href="/build">
                  <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                    Build Your First Parlay
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {displayedHistory.map((parlay, index) => {
                  const isExpanded = expandedParlay === parlay.id
                  const createdDate = new Date(parlay.created_at)
                  
                  return (
                    <motion.div
                      key={parlay.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden"
                    >
                      {/* Parlay Header */}
                      <button
                        onClick={() => setExpandedParlay(isExpanded ? null : parlay.id)}
                        className="w-full p-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          {/* Status Icon */}
                          <div className={cn(
                            "w-10 h-10 rounded-full flex items-center justify-center",
                            parlay.status === "hit" ? "bg-emerald-500/20" :
                            parlay.status === "missed" ? "bg-red-500/20" :
                            "bg-amber-500/20"
                          )}>
                            {parlay.status === "hit" ? (
                              <CheckCircle className="h-5 w-5 text-emerald-400" />
                            ) : parlay.status === "missed" ? (
                              <XCircle className="h-5 w-5 text-red-400" />
                            ) : (
                              <Clock className="h-5 w-5 text-amber-400" />
                            )}
                          </div>
                          
                          <div className="text-left">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white">
                                {parlay.num_legs}-Leg Parlay
                              </span>
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "text-xs capitalize",
                                  parlay.risk_profile === "conservative" ? "border-emerald-500/50 text-emerald-400" :
                                  parlay.risk_profile === "balanced" ? "border-amber-500/50 text-amber-400" :
                                  "border-purple-500/50 text-purple-400"
                                )}
                              >
                                {parlay.risk_profile}
                              </Badge>
                            </div>
                            <div className="text-xs text-gray-500 flex items-center gap-2">
                              <Calendar className="h-3 w-3" />
                              {createdDate.toLocaleDateString("en-US", { 
                                month: "short", 
                                day: "numeric",
                                hour: "numeric",
                                minute: "2-digit"
                              })}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
                          {parlay.status === "hit" && parlay.payout && (
                            <div className="text-right">
                              <div className="text-lg font-bold text-emerald-400">
                                +${parlay.payout}
                              </div>
                              <div className="text-xs text-gray-500">Payout</div>
                            </div>
                          )}
                          
                          <div className="text-right">
                            <div className="text-sm font-medium text-gray-300">
                              {(parlay.parlay_hit_prob * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500">Hit Prob</div>
                          </div>
                          
                          <ChevronRight className={cn(
                            "h-5 w-5 text-gray-500 transition-transform",
                            isExpanded && "rotate-90"
                          )} />
                        </div>
                      </button>
                      
                      {/* Expanded Legs */}
                      {isExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="border-t border-white/5 p-4"
                        >
                          <div className="space-y-2">
                            {parlay.legs.map((leg, legIndex) => (
                              <div
                                key={legIndex}
                                className={cn(
                                  "flex items-center justify-between p-3 rounded-lg",
                                  leg.result === "hit" ? "bg-emerald-500/10" :
                                  leg.result === "missed" ? "bg-red-500/10" :
                                  "bg-white/5"
                                )}
                              >
                                <div className="flex items-center gap-3">
                                  {leg.result === "hit" ? (
                                    <CheckCircle className="h-4 w-4 text-emerald-400" />
                                  ) : leg.result === "missed" ? (
                                    <XCircle className="h-4 w-4 text-red-400" />
                                  ) : (
                                    <Clock className="h-4 w-4 text-amber-400" />
                                  )}
                                  <div>
                                    <div className="text-sm font-medium text-white">{leg.pick}</div>
                                    <div className="text-xs text-gray-500">{leg.game}</div>
                                  </div>
                                </div>
                                <div className="text-sm font-medium text-gray-400">
                                  {leg.odds}
                                </div>
                              </div>
                            ))}
                          </div>
                          
                          <div className="mt-4 flex justify-end">
                            <Link href={`/parlays/result/${parlay.id}`}>
                              <Button variant="outline" size="sm" className="border-white/20">
                                View Full Analysis
                                <ChevronRight className="h-4 w-4 ml-1" />
                              </Button>
                            </Link>
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  )
                })}
                
                {/* Locked Content for Free Users */}
                {hasMoreLocked && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="relative"
                  >
                    <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/80 z-10" />
                    <div className="p-8 bg-white/[0.02] border border-white/10 rounded-xl text-center relative z-20">
                      <Lock className="h-10 w-10 text-gray-500 mx-auto mb-4" />
                      <h3 className="text-xl font-bold text-white mb-2">
                        {filteredHistory.length - 5} More Parlays
                      </h3>
                      <p className="text-gray-400 mb-6">
                        Upgrade to Premium to see your complete parlay history
                      </p>
                      <Link href="/premium">
                        <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                          <Crown className="h-4 w-4 mr-2" />
                          Unlock Full History
                        </Button>
                      </Link>
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}




