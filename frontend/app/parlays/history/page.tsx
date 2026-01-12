"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useSubscription } from "@/lib/subscription-context"
import { api } from "@/lib/api"
import type { ParlayHistoryItem, ParlayLegOutcome, ParlayLegStatus } from "@/lib/api/parlay-results-types"
import { 
  History, 
  Calendar, 
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  MinusCircle,
  Loader2,
  Crown,
  Lock,
  ChevronRight,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"
import { getCopy } from "@/lib/content"

type HistoryFilter = "all" | ParlayLegStatus

function formatLegGame(leg: ParlayLegOutcome): string {
  if (leg.game) return leg.game
  const away = leg.away_team || "Away"
  const home = leg.home_team || "Home"
  return `${away} @ ${home}`
}

function formatLegPick(leg: ParlayLegOutcome): string {
  const marketType = String(leg.market_type || "").toLowerCase()
  const outcome = String(leg.outcome || "")

  if (marketType === "h2h") {
    const out = outcome.toLowerCase().trim()
    if (out === "home") return `${leg.home_team || "Home"} ML`
    if (out === "away") return `${leg.away_team || "Away"} ML`
    if (out === "draw") return "Draw"
    return outcome || "Moneyline"
  }

  return outcome || "Pick"
}

export default function ParlayHistoryPage() {
  return (
    <ProtectedRoute>
      <ParlayHistoryContent />
    </ProtectedRoute>
  )
}

function ParlayHistoryContent() {
  const { isPremium, isCreditUser } = useSubscription()
  const [history, setHistory] = useState<ParlayHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<HistoryFilter>("all")
  const [expandedParlay, setExpandedParlay] = useState<string | null>(null)

  useEffect(() => {
    loadHistory()
  }, [])

  async function loadHistory() {
    try {
      setLoading(true)
      const data = await api.getParlayHistory(50, 0)
      setHistory(data)
    } catch (error) {
      console.error("Failed to load parlay history:", error)
    } finally {
      setLoading(false)
    }
  }

  const filteredHistory = history.filter(p => filter === "all" || p.status === filter)
  
  // Calculate stats
  const hits = history.filter(p => p.status === "hit").length
  const misses = history.filter(p => p.status === "missed").length
  const pushes = history.filter(p => p.status === "push").length
  const pending = history.filter(p => p.status === "pending").length
  const resolvedForRate = hits + misses
  const stats = {
    total: history.length,
    hits,
    misses,
    pushes,
    pending,
    hitRate: resolvedForRate > 0 ? (hits / resolvedForRate) * 100 : 0,
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
                    {getCopy("app.history.header")}
                  </h1>
                </div>
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
            <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
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
              <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/30">
                <div className="text-2xl font-black text-sky-300">{stats.pushes}</div>
                <div className="text-xs text-sky-300/60">Push</div>
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
              {(["all", "pending", "hit", "missed", "push"] as const).map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={cn(
                    "px-4 py-2 rounded-full text-sm font-medium transition-all",
                    filter === status
                      ? status === "hit" ? "bg-emerald-500 text-black"
                        : status === "missed" ? "bg-red-500 text-white"
                        : status === "pending" ? "bg-amber-500 text-black"
                        : status === "push" ? "bg-sky-500 text-black"
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
                <span className="ml-3 text-gray-400">{getCopy("states.loading.loadingData")}</span>
              </div>
            ) : displayedHistory.length === 0 ? (
              <div className="text-center py-20">
                <History className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">{getCopy("app.history.emptyState")}</h3>
                <Link href="/app">
                  <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                    {getCopy("cta.primary.buildSlip")}
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {displayedHistory.map((parlay, index) => {
                  const isExpanded = expandedParlay === parlay.id
                  const createdDate = parlay.created_at ? new Date(parlay.created_at) : null
                  
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
                            parlay.status === "push" ? "bg-sky-500/20" :
                            "bg-amber-500/20"
                          )}>
                            {parlay.status === "hit" ? (
                              <CheckCircle className="h-5 w-5 text-emerald-400" />
                            ) : parlay.status === "missed" ? (
                              <XCircle className="h-5 w-5 text-red-400" />
                            ) : parlay.status === "push" ? (
                              <MinusCircle className="h-5 w-5 text-sky-300" />
                            ) : (
                              <Clock className="h-5 w-5 text-amber-400" />
                            )}
                          </div>
                          
                          <div className="text-left flex-1">
                            <div className="flex items-center gap-2 mb-1">
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
                            
                            {/* Quick Leg Status Summary */}
                            <div className="flex items-center gap-2 flex-wrap">
                              {parlay.legs.slice(0, 10).map((leg, legIdx) => (
                                <div
                                  key={legIdx}
                                  className={cn(
                                    "w-5 h-5 rounded flex items-center justify-center text-xs font-bold",
                                    leg.status === "hit" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/50" :
                                    leg.status === "missed" ? "bg-red-500/20 text-red-400 border border-red-500/50" :
                                    leg.status === "push" ? "bg-sky-500/20 text-sky-300 border border-sky-500/50" :
                                    "bg-amber-500/20 text-amber-400 border border-amber-500/50"
                                  )}
                                  title={`${formatLegPick(leg)} - ${leg.status === "hit" ? "Won" : leg.status === "missed" ? "Lost" : leg.status === "push" ? "Push" : "Pending"}`}
                                >
                                  {leg.status === "hit" ? (
                                    <CheckCircle className="h-3 w-3" />
                                  ) : leg.status === "missed" ? (
                                    <XCircle className="h-3 w-3" />
                                  ) : leg.status === "push" ? (
                                    <MinusCircle className="h-3 w-3" />
                                  ) : (
                                    <Clock className="h-3 w-3" />
                                  )}
                                </div>
                              ))}
                              {parlay.legs.length > 10 && (
                                <span className="text-xs text-gray-500">
                                  +{parlay.legs.length - 10} more
                                </span>
                              )}
                            </div>
                            
                            <div className="text-xs text-gray-500 flex items-center gap-2 mt-1">
                              <Calendar className="h-3 w-3" />
                              {createdDate
                                ? createdDate.toLocaleDateString("en-US", {
                                    month: "short",
                                    day: "numeric",
                                    hour: "numeric",
                                    minute: "2-digit",
                                  })
                                : "—"}
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-4">
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
                          {/* Summary Stats */}
                          <div className="grid grid-cols-4 gap-2 mb-4 pb-4 border-b border-white/5">
                            <div className="text-center">
                              <div className="flex items-center justify-center gap-1 mb-1">
                                <CheckCircle className="h-4 w-4 text-emerald-400" />
                                <span className="text-lg font-bold text-emerald-400">
                                  {parlay.legs.filter(l => l.status === "hit").length}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">Won</div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center gap-1 mb-1">
                                <XCircle className="h-4 w-4 text-red-400" />
                                <span className="text-lg font-bold text-red-400">
                                  {parlay.legs.filter(l => l.status === "missed").length}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">Lost</div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center gap-1 mb-1">
                                <MinusCircle className="h-4 w-4 text-sky-300" />
                                <span className="text-lg font-bold text-sky-300">
                                  {parlay.legs.filter(l => l.status === "push").length}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">Push</div>
                            </div>
                            <div className="text-center">
                              <div className="flex items-center justify-center gap-1 mb-1">
                                <Clock className="h-4 w-4 text-amber-400" />
                                <span className="text-lg font-bold text-amber-400">
                                  {parlay.legs.filter(l => l.status === "pending").length}
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">Pending</div>
                            </div>
                          </div>
                          
                          <div className="space-y-2">
                            {parlay.legs.map((leg, legIndex) => (
                              <div
                                key={legIndex}
                                className={cn(
                                  "flex items-center justify-between p-3 rounded-lg border",
                                  leg.status === "hit" ? "bg-emerald-500/10 border-emerald-500/30" :
                                  leg.status === "missed" ? "bg-red-500/10 border-red-500/30" :
                                  leg.status === "push" ? "bg-sky-500/10 border-sky-500/30" :
                                  "bg-amber-500/10 border-amber-500/30"
                                )}
                              >
                                <div className="flex items-center gap-3 flex-1">
                                  {leg.status === "hit" ? (
                                    <CheckCircle className="h-5 w-5 text-emerald-400 flex-shrink-0" />
                                  ) : leg.status === "missed" ? (
                                    <XCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                                  ) : leg.status === "push" ? (
                                    <MinusCircle className="h-5 w-5 text-sky-300 flex-shrink-0" />
                                  ) : (
                                    <Clock className="h-5 w-5 text-amber-400 flex-shrink-0" />
                                  )}
                                  <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium text-white">{formatLegPick(leg)}</div>
                                    <div className="text-xs text-gray-500">{formatLegGame(leg)}</div>
                                  </div>
                                </div>
                                <div className="text-sm font-medium text-gray-400 ml-4">
                                  {leg.odds || "—"}
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
      {isCreditUser && !isPremium && (
        <PremiumBlurOverlay
          title="Premium Page"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access full history."
        />
      )}
    </div>
  )
}




