"use client"

import { useState, useEffect, use } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ConfidenceRing } from "@/components/ConfidenceRing"
import { 
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Target,
  BarChart3,
  Loader2,
  Share2,
  Copy,
  Check
} from "lucide-react"
import { cn } from "@/lib/utils"

interface PageProps {
  params: Promise<{
    id: string
  }>
}

interface ParlayLeg {
  game: string
  home_team: string
  away_team: string
  market_type: string
  pick: string
  odds: string
  model_probability: number
  implied_probability: number
  edge: number
  is_upset: boolean
  result?: "hit" | "missed" | "pending"
}

interface ParlayResult {
  id: string
  created_at: string
  num_legs: number
  risk_profile: string
  status: "pending" | "hit" | "missed"
  legs: ParlayLeg[]
  combined_hit_probability: number
  combined_implied_probability: number
  parlay_ev: number
  model_confidence: number
  bust_risk: {
    leg_index: number
    leg_pick: string
    bust_probability: number
  }[]
  ai_summary: string
  ai_risk_notes: string
}

// Mock data - in production, fetch from API
const MOCK_RESULT: ParlayResult = {
  id: "abc123",
  created_at: new Date(Date.now() - 3600000).toISOString(),
  num_legs: 5,
  risk_profile: "balanced",
  status: "pending",
  legs: [
    {
      game: "Bills @ Dolphins",
      home_team: "Dolphins",
      away_team: "Bills",
      market_type: "h2h",
      pick: "Bills ML",
      odds: "-145",
      model_probability: 0.62,
      implied_probability: 0.59,
      edge: 3.0,
      is_upset: false,
      result: "pending"
    },
    {
      game: "Lakers @ Celtics",
      home_team: "Celtics",
      away_team: "Lakers",
      market_type: "spreads",
      pick: "Lakers +4.5",
      odds: "-110",
      model_probability: 0.54,
      implied_probability: 0.52,
      edge: 2.0,
      is_upset: false,
      result: "pending"
    },
    {
      game: "Rangers @ Bruins",
      home_team: "Bruins",
      away_team: "Rangers",
      market_type: "totals",
      pick: "Over 5.5",
      odds: "-115",
      model_probability: 0.58,
      implied_probability: 0.53,
      edge: 5.0,
      is_upset: false,
      result: "pending"
    },
    {
      game: "Chiefs @ Raiders",
      home_team: "Raiders",
      away_team: "Chiefs",
      market_type: "spreads",
      pick: "Raiders +10.5",
      odds: "+125",
      model_probability: 0.48,
      implied_probability: 0.44,
      edge: 4.0,
      is_upset: true,
      result: "pending"
    },
    {
      game: "Suns @ Warriors",
      home_team: "Warriors",
      away_team: "Suns",
      market_type: "h2h",
      pick: "Warriors ML",
      odds: "+130",
      model_probability: 0.46,
      implied_probability: 0.43,
      edge: 3.0,
      is_upset: true,
      result: "pending"
    }
  ],
  combined_hit_probability: 0.089,
  combined_implied_probability: 0.065,
  parlay_ev: 0.12,
  model_confidence: 72,
  bust_risk: [
    { leg_index: 3, leg_pick: "Raiders +10.5", bust_probability: 0.52 },
    { leg_index: 4, leg_pick: "Warriors ML", bust_probability: 0.54 },
    { leg_index: 1, leg_pick: "Lakers +4.5", bust_probability: 0.46 }
  ],
  ai_summary: "This balanced 5-leg parlay combines solid favorites with two calculated upset plays. The Bills and Over 5.5 provide a stable foundation, while the Raiders and Warriors picks offer significant value based on our model's analysis of recent performance trends.",
  ai_risk_notes: "The two upset legs (Raiders +10.5, Warriors ML) carry the highest bust risk. If you want to reduce variance, consider removing one of these legs. The parlay has positive expected value (+12%) which suggests long-term profitability."
}

export default function ParlayResultPage({ params }: PageProps) {
  const { id } = use(params)
  const [result, setResult] = useState<ParlayResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadResult()
  }, [id])

  async function loadResult() {
    try {
      setLoading(true)
      // In production: await api.get(`/api/parlays/${id}`)
      await new Promise(resolve => setTimeout(resolve, 500))
      setResult(MOCK_RESULT)
    } catch (error) {
      console.error("Failed to load parlay result:", error)
    } finally {
      setLoading(false)
    }
  }

  async function handleCopyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error("Failed to copy link:", error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
        </main>
        <Footer />
      </div>
    )
  }

  if (!result) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-white mb-4">Parlay Not Found</h1>
            <Link href="/parlays/history">
              <Button variant="outline">Back to History</Button>
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Header */}
        <section className="relative py-8 border-b border-white/10 bg-black/40 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between">
              <div>
                <Link 
                  href="/parlays/history"
                  className="flex items-center gap-2 text-sm text-gray-400 hover:text-emerald-400 transition-colors mb-2"
                >
                  <ArrowLeft className="h-4 w-4" />
                  Back to History
                </Link>
                <h1 className="text-3xl md:text-4xl font-black">
                  <span className="text-white">{result.num_legs}-Leg </span>
                  <span className="text-emerald-400">Parlay</span>
                </h1>
                <div className="flex items-center gap-3 mt-2">
                  <Badge 
                    variant="outline"
                    className={cn(
                      "capitalize",
                      result.risk_profile === "conservative" ? "border-emerald-500/50 text-emerald-400" :
                      result.risk_profile === "balanced" ? "border-amber-500/50 text-amber-400" :
                      "border-purple-500/50 text-purple-400"
                    )}
                  >
                    {result.risk_profile}
                  </Badge>
                  <Badge
                    className={cn(
                      result.status === "hit" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" :
                      result.status === "missed" ? "bg-red-500/20 text-red-400 border-red-500/30" :
                      "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    )}
                  >
                    {result.status === "hit" ? (
                      <><CheckCircle className="h-3 w-3 mr-1" /> Hit</>
                    ) : result.status === "missed" ? (
                      <><XCircle className="h-3 w-3 mr-1" /> Missed</>
                    ) : (
                      <><Clock className="h-3 w-3 mr-1" /> Pending</>
                    )}
                  </Badge>
                </div>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyLink}
                className="border-white/20"
              >
                {copied ? (
                  <><Check className="h-4 w-4 mr-2" /> Copied!</>
                ) : (
                  <><Share2 className="h-4 w-4 mr-2" /> Share</>
                )}
              </Button>
            </div>
          </div>
        </section>

        {/* Key Metrics */}
        <section className="py-8 bg-black/20">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {/* Model Confidence */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 flex items-center gap-4">
                <ConfidenceRing score={result.model_confidence} size={60} />
                <div>
                  <div className="text-xs text-gray-500">Model Confidence</div>
                  <div className="text-xl font-bold text-white">{result.model_confidence}%</div>
                </div>
              </div>
              
              {/* Hit Probability */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs text-gray-500">Hit Probability</span>
                </div>
                <div className="text-xl font-bold text-emerald-400">
                  {(result.combined_hit_probability * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  vs {(result.combined_implied_probability * 100).toFixed(1)}% implied
                </div>
              </div>
              
              {/* Expected Value */}
              <div className={cn(
                "p-4 rounded-xl border",
                result.parlay_ev > 0 
                  ? "bg-emerald-500/10 border-emerald-500/30" 
                  : "bg-red-500/10 border-red-500/30"
              )}>
                <div className="flex items-center gap-2 mb-1">
                  {result.parlay_ev > 0 ? (
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span className="text-xs text-gray-500">Expected Value</span>
                </div>
                <div className={cn(
                  "text-xl font-bold",
                  result.parlay_ev > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {result.parlay_ev > 0 ? "+" : ""}{(result.parlay_ev * 100).toFixed(1)}%
                </div>
              </div>
              
              {/* Upset Legs */}
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/30">
                <div className="flex items-center gap-2 mb-1">
                  <AlertTriangle className="h-4 w-4 text-purple-400" />
                  <span className="text-xs text-gray-500">Gorilla Upsets</span>
                </div>
                <div className="text-xl font-bold text-purple-400">
                  🦍 {result.legs.filter(l => l.is_upset).length}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Legs Breakdown */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            <h2 className="text-xl font-bold text-white mb-4">Leg Breakdown</h2>
            
            <div className="space-y-3">
              {result.legs.map((leg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={cn(
                    "p-4 rounded-xl border",
                    leg.result === "hit" ? "bg-emerald-500/5 border-emerald-500/30" :
                    leg.result === "missed" ? "bg-red-500/5 border-red-500/30" :
                    "bg-white/[0.02] border-white/10"
                  )}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        {leg.result === "hit" ? (
                          <CheckCircle className="h-4 w-4 text-emerald-400" />
                        ) : leg.result === "missed" ? (
                          <XCircle className="h-4 w-4 text-red-400" />
                        ) : (
                          <Clock className="h-4 w-4 text-amber-400" />
                        )}
                        <span className="font-bold text-white">{leg.pick}</span>
                        {leg.is_upset && (
                          <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30 text-xs">
                            🦍 Upset
                          </Badge>
                        )}
                      </div>
                      <div className="text-sm text-gray-400 mb-3">{leg.game}</div>
                      
                      {/* Probability Bars */}
                      <div className="space-y-2">
                        <div>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-500">Model Prob</span>
                            <span className="text-emerald-400 font-medium">
                              {(leg.model_probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500 rounded-full"
                              style={{ width: `${leg.model_probability * 100}%` }}
                            />
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-gray-500">Implied Prob</span>
                            <span className="text-gray-400 font-medium">
                              {(leg.implied_probability * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gray-500 rounded-full"
                              style={{ width: `${leg.implied_probability * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-lg font-bold text-white">{leg.odds}</div>
                      <div className={cn(
                        "text-sm font-medium",
                        leg.edge > 0 ? "text-emerald-400" : "text-gray-400"
                      )}>
                        {leg.edge > 0 ? "+" : ""}{leg.edge.toFixed(1)}% edge
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Bust Risk Analysis */}
        <section className="py-8 bg-black/20">
          <div className="container mx-auto px-4">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-amber-400" />
              Bust Risk Breakdown
            </h2>
            <p className="text-sm text-gray-400 mb-4">
              Which legs are most likely to bust your ticket
            </p>
            
            <div className="space-y-3">
              {result.bust_risk.map((risk, index) => (
                <div
                  key={index}
                  className="p-4 rounded-xl bg-white/[0.02] border border-white/10"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-white">{risk.leg_pick}</span>
                    <span className={cn(
                      "text-sm font-bold",
                      risk.bust_probability > 0.5 ? "text-red-400" :
                      risk.bust_probability > 0.4 ? "text-amber-400" :
                      "text-emerald-400"
                    )}>
                      {(risk.bust_probability * 100).toFixed(0)}% bust risk
                    </span>
                  </div>
                  <div className="h-3 bg-white/5 rounded-full overflow-hidden">
                    <div 
                      className={cn(
                        "h-full rounded-full transition-all",
                        risk.bust_probability > 0.5 ? "bg-red-500" :
                        risk.bust_probability > 0.4 ? "bg-amber-500" :
                        "bg-emerald-500"
                      )}
                      style={{ width: `${risk.bust_probability * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* AI Analysis */}
        <section className="py-8">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 rounded-xl bg-white/[0.02] border border-white/10">
                <h3 className="font-bold text-white mb-3">AI Summary</h3>
                <p className="text-gray-300 text-sm leading-relaxed">{result.ai_summary}</p>
              </div>
              
              <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <h3 className="font-bold text-amber-300 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Risk Assessment
                </h3>
                <p className="text-amber-100/80 text-sm leading-relaxed">{result.ai_risk_notes}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Actions */}
        <section className="py-8 border-t border-white/10">
          <div className="container mx-auto px-4">
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/build">
                <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                  Build New Parlay
                </Button>
              </Link>
              <Link href="/parlays/history">
                <Button variant="outline" className="border-white/20">
                  View All History
                </Button>
              </Link>
            </div>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}

