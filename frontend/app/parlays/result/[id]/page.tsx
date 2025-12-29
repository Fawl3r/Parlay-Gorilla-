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
  MinusCircle,
  CheckCircle,
  XCircle,
  Clock,
  Target,
  BarChart3,
  Loader2,
  Share2,
  Check
} from "lucide-react"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import type { ParlayDetail, ParlayLegOutcome, ParlayLegStatus } from "@/lib/api/parlay-results-types"

interface PageProps {
  params: Promise<{
    id: string
  }>
}

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

function parseAmericanOdds(raw: string | null | undefined): number | null {
  if (!raw) return null
  const cleaned = String(raw).trim().replace("−", "-")
  const value = Number(cleaned)
  if (!Number.isFinite(value) || value === 0) return null
  return value
}

function americanToImpliedProbability(raw: string | null | undefined): number | null {
  const odds = parseAmericanOdds(raw)
  if (odds === null) return null
  if (odds > 0) return 100 / (odds + 100)
  return Math.abs(odds) / (Math.abs(odds) + 100)
}

function americanToDecimalOdds(raw: string | null | undefined): number | null {
  const odds = parseAmericanOdds(raw)
  if (odds === null) return null
  if (odds > 0) return odds / 100 + 1
  return 100 / Math.abs(odds) + 1
}

function averageConfidence(legs: ParlayLegOutcome[]): number {
  const values = legs
    .map((l) => (typeof l.confidence === "number" ? l.confidence : null))
    .filter((v): v is number => v !== null)
  if (values.length === 0) return 0
  return values.reduce((a, b) => a + b, 0) / values.length
}

function computeBustRisk(legs: ParlayLegOutcome[]) {
  return legs
    .map((leg, idx) => {
      const p = typeof leg.probability === "number" ? leg.probability : null
      const bust = p !== null ? Math.max(0, Math.min(1, 1 - p)) : 0.5
      return { leg_index: idx, leg_pick: formatLegPick(leg), bust_probability: bust }
    })
    .sort((a, b) => b.bust_probability - a.bust_probability)
    .slice(0, 5)
}

export default function ParlayResultPage({ params }: PageProps) {
  const { id } = use(params)
  const [result, setResult] = useState<ParlayDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadResult()
  }, [id])

  async function loadResult() {
    try {
      setLoading(true)
      const data = await api.getParlayDetail(id)
      setResult(data)
    } catch (error) {
      console.error("Failed to load parlay result:", error)
      setResult(null)
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

  const legs = result.legs || []
  const modelConfidence = Math.round(averageConfidence(legs))
  const combinedHitProbability = result.parlay_hit_prob || 0
  const combinedImpliedProbability = legs.reduce((acc, leg) => acc * (americanToImpliedProbability(leg.odds) ?? 0.5), 1)
  const combinedDecimalOdds = legs.reduce((acc, leg) => acc * (americanToDecimalOdds(leg.odds) ?? 2.0), 1)
  const parlayEv = combinedHitProbability * combinedDecimalOdds - 1
  const bustRisk = computeBustRisk(legs)
  const pushLegs = legs.filter((l) => l.status === "push").length

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
                      result.status === "push" ? "bg-sky-500/20 text-sky-200 border-sky-500/30" :
                      "bg-amber-500/20 text-amber-400 border-amber-500/30"
                    )}
                  >
                    {result.status === "hit" ? (
                      <><CheckCircle className="h-3 w-3 mr-1" /> Hit</>
                    ) : result.status === "missed" ? (
                      <><XCircle className="h-3 w-3 mr-1" /> Missed</>
                    ) : result.status === "push" ? (
                      <><MinusCircle className="h-3 w-3 mr-1" /> Push</>
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
                <ConfidenceRing score={modelConfidence} size={60} />
                <div>
                  <div className="text-xs text-gray-500">Model Confidence</div>
                  <div className="text-xl font-bold text-white">{modelConfidence}%</div>
                </div>
              </div>
              
              {/* Hit Probability */}
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs text-gray-500">Hit Probability</span>
                </div>
                <div className="text-xl font-bold text-emerald-400">
                  {(combinedHitProbability * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500">
                  vs {(combinedImpliedProbability * 100).toFixed(1)}% implied
                </div>
              </div>
              
              {/* Expected Value */}
              <div className={cn(
                "p-4 rounded-xl border",
                parlayEv > 0 
                  ? "bg-emerald-500/10 border-emerald-500/30" 
                  : "bg-red-500/10 border-red-500/30"
              )}>
                <div className="flex items-center gap-2 mb-1">
                  {parlayEv > 0 ? (
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-400" />
                  )}
                  <span className="text-xs text-gray-500">Expected Value</span>
                </div>
                <div className={cn(
                  "text-xl font-bold",
                  parlayEv > 0 ? "text-emerald-400" : "text-red-400"
                )}>
                  {parlayEv > 0 ? "+" : ""}{(parlayEv * 100).toFixed(1)}%
                </div>
              </div>
              
              {/* Push Legs */}
              <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/30">
                <div className="flex items-center gap-2 mb-1">
                  <MinusCircle className="h-4 w-4 text-sky-300" />
                  <span className="text-xs text-gray-500">Push Legs</span>
                </div>
                <div className="text-xl font-bold text-sky-300">
                  {pushLegs}
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
              {legs.map((leg, index) => {
                const modelProb = typeof leg.probability === "number" ? leg.probability : 0.5
                const impliedProb = americanToImpliedProbability(leg.odds) ?? 0.5
                const edge = (modelProb - impliedProb) * 100

                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={cn(
                      "p-4 rounded-xl border",
                      leg.status === "hit" ? "bg-emerald-500/5 border-emerald-500/30" :
                      leg.status === "missed" ? "bg-red-500/5 border-red-500/30" :
                      leg.status === "push" ? "bg-sky-500/5 border-sky-500/30" :
                      "bg-white/[0.02] border-white/10"
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          {leg.status === "hit" ? (
                            <CheckCircle className="h-4 w-4 text-emerald-400" />
                          ) : leg.status === "missed" ? (
                            <XCircle className="h-4 w-4 text-red-400" />
                          ) : leg.status === "push" ? (
                            <MinusCircle className="h-4 w-4 text-sky-300" />
                          ) : (
                            <Clock className="h-4 w-4 text-amber-400" />
                          )}
                          <span className="font-bold text-white">{formatLegPick(leg)}</span>
                        </div>
                        <div className="text-sm text-gray-400 mb-3">{formatLegGame(leg)}</div>

                        {/* Probability Bars */}
                        <div className="space-y-2">
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-500">Model Prob</span>
                              <span className="text-emerald-400 font-medium">
                                {(modelProb * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-emerald-500 rounded-full"
                                style={{ width: `${Math.max(0, Math.min(100, modelProb * 100))}%` }}
                              />
                            </div>
                          </div>
                          <div>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-500">Implied Prob</span>
                              <span className="text-gray-400 font-medium">
                                {(impliedProb * 100).toFixed(1)}%
                              </span>
                            </div>
                            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-gray-500 rounded-full"
                                style={{ width: `${Math.max(0, Math.min(100, impliedProb * 100))}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="text-lg font-bold text-white">{leg.odds || "—"}</div>
                        <div
                          className={cn(
                            "text-sm font-medium",
                            edge > 0 ? "text-emerald-400" : "text-gray-400"
                          )}
                        >
                          {edge > 0 ? "+" : ""}{edge.toFixed(1)}% edge
                        </div>
                      </div>
                    </div>
                  </motion.div>
                )
              })}
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
              {bustRisk.map((risk, index) => (
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
                <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-line">{result.ai_summary}</p>
              </div>
              
              <div className="p-6 rounded-xl bg-amber-500/10 border border-amber-500/30">
                <h3 className="font-bold text-amber-300 mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Risk Assessment
                </h3>
                <p className="text-amber-100/80 text-sm leading-relaxed whitespace-pre-line">{result.ai_risk_notes}</p>
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

