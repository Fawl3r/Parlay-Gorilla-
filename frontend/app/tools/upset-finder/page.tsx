"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import Link from "next/link"
import { TrendingUp, Crown, Lock, Loader2, Filter, RefreshCw, AlertTriangle } from "lucide-react"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { DashboardAccountCommandCenter } from "@/components/usage/DashboardAccountCommandCenter"
import { motion } from "framer-motion"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { api, UpsetCandidateResponse, UpsetRiskTier } from "@/lib/api"
import { sportsUiPolicy } from "@/lib/sports/SportsUiPolicy"
import { getPaywallError, isPaywallError, type PaywallError, useSubscription } from "@/lib/subscription-context"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"

type SportOption = { id: string; label: string }

const SPORTS: SportOption[] = [
  { id: "nfl", label: "NFL" },
  { id: "ncaaf", label: "NCAAF" },
  { id: "nba", label: "NBA" },
  { id: "nhl", label: "NHL" },
  { id: "ncaab", label: "NCAAB" },
  { id: "epl", label: "EPL" },
  { id: "laliga", label: "La Liga" },
]

function formatPercent(prob0to1: number) {
  if (!Number.isFinite(prob0to1)) return "0.0%"
  return `${(prob0to1 * 100).toFixed(1)}%`
}

function formatSignedPercent(value: number) {
  if (!Number.isFinite(value)) return "0.0%"
  const pct = (value * 100).toFixed(1)
  return `${value >= 0 ? "+" : ""}${pct}%`
}

function riskTierBadgeClass(tier: UpsetRiskTier) {
  if (tier === "low") return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
  if (tier === "medium") return "bg-amber-500/20 text-amber-300 border-amber-500/30"
  return "bg-rose-500/20 text-rose-300 border-rose-500/30"
}

export default function UpsetFinderPage() {
  return (
    <ProtectedRoute>
      <UpsetFinderContent />
    </ProtectedRoute>
  )
}

function UpsetFinderContent() {
  const { isPremium, isCreditUser, canUseUpsetFinder, refreshStatus } = useSubscription()

  const [selectedSport, setSelectedSport] = useState<string>("nfl")
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})
  const [riskTier, setRiskTier] = useState<UpsetRiskTier | "all">("all")
  const [minEdgePct, setMinEdgePct] = useState<number>(3)
  const [maxResults, setMaxResults] = useState<number>(20)
  const [selectedWeek, setSelectedWeek] = useState<number | undefined>(undefined)
  const [availableWeeks, setAvailableWeeks] = useState<Array<{ week: number; label: string; is_current: boolean; is_available: boolean }> | null>(
    null
  )

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [upsets, setUpsets] = useState<UpsetCandidateResponse[]>([])

  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("upset_finder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)

  const isNFL = selectedSport.toLowerCase() === "nfl"

  useEffect(() => {
    let cancelled = false
    async function loadSportsStatus() {
      try {
        const sportsList = await api.listSports()
        if (cancelled) return
        const map: Record<string, boolean> = {}
        for (const s of sportsList) {
          map[s.slug] = s.in_season !== false
        }
        setInSeasonBySport(map)
      } catch {
        if (!cancelled) setInSeasonBySport({})
      }
    }
    loadSportsStatus()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!Object.keys(inSeasonBySport).length) return
    if (inSeasonBySport[selectedSport] !== false) return
    const firstAvailable = SPORTS.find((s) => inSeasonBySport[s.id] !== false)?.id
    if (firstAvailable && firstAvailable !== selectedSport) setSelectedSport(firstAvailable)
  }, [inSeasonBySport, selectedSport])

  useEffect(() => {
    let cancelled = false
    async function loadWeeks() {
      try {
        const weeks = await api.getNFLWeeks()
        const available = weeks.weeks.filter((w) => w.is_available)
        if (cancelled) return
        setAvailableWeeks(available)
        const current = available.find((w) => w.is_current)
        setSelectedWeek((prev) => prev ?? current?.week ?? available[0]?.week)
      } catch {
        if (!cancelled) setAvailableWeeks([])
      }
    }
    if (isNFL) loadWeeks()
    return () => {
      cancelled = true
    }
  }, [isNFL])

  const canFetch = useMemo(() => {
    if (!canUseUpsetFinder) return false
    if (!Number.isFinite(minEdgePct) || minEdgePct < 0) return false
    if (!Number.isFinite(maxResults) || maxResults < 1) return false
    return true
  }, [canUseUpsetFinder, minEdgePct, maxResults])

  const sortedUpsets = useMemo(() => {
    return [...upsets].sort((a, b) => (b.ev ?? 0) - (a.ev ?? 0))
  }, [upsets])

  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }

  const queryRef = useRef({ minEdgePct, maxResults })
  useEffect(() => {
    queryRef.current = { minEdgePct, maxResults }
  }, [minEdgePct, maxResults])

  const loadUpsets = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const { minEdgePct: minEdgePctLatest, maxResults: maxResultsLatest } = queryRef.current
      const resp = await api.getUpsets({
        sport: selectedSport,
        min_edge: Math.max(0, minEdgePctLatest) / 100,
        max_results: Math.max(1, Math.min(50, Math.trunc(maxResultsLatest))),
        risk_tier: riskTier === "all" ? undefined : riskTier,
        week: isNFL ? selectedWeek : undefined,
      })
      setUpsets(resp.upsets || [])
    } catch (err: unknown) {
      if (isPaywallError(err)) {
        const pw = getPaywallError(err)
        setPaywallError(pw)
        setPaywallReason("upset_finder_locked")
        setShowPaywall(true)
        return
      }
      const message = err instanceof Error ? err.message : "Failed to load upset candidates."
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [isNFL, riskTier, selectedSport, selectedWeek])

  useEffect(() => {
    if (!canFetch) return
    loadUpsets()
  }, [canFetch, loadUpsets])

  if (!canUseUpsetFinder) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
          <AnimatedBackground variant="intense" />
          <div className="flex-1 relative z-10 flex flex-col">
            <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
              <div className="container mx-auto px-2 sm:px-4 py-3 sm:py-4 md:py-5">
                <div className="mb-3 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                  <BalanceStrip compact />
                </div>
                <DashboardAccountCommandCenter />
              </div>
            </section>

            <section className="flex-1">
              <div className="container mx-auto px-2 sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-8 w-8 text-emerald-400" />
                    <h1 className="text-3xl md:text-4xl font-black text-white">Gorilla Upset Finder</h1>
                    <Lock className="h-6 w-6 text-gray-500" />
                  </div>
                  <p className="text-gray-400">Find plus-money underdogs with positive expected value.</p>
                </div>

                <div className="max-w-xl mx-auto bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border border-emerald-500/20 rounded-2xl p-8 text-center">
                  <div className="mx-auto w-14 h-14 rounded-full bg-emerald-500/15 flex items-center justify-center mb-5">
                    <Lock className="h-7 w-7 text-emerald-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Premium Feature</h2>
                  <p className="text-gray-400 mb-6">
                    The Gorilla Upset Finder is available to Premium members. Upgrade to unlock +EV underdogs ranked by edge and EV.
                  </p>
                  <Button
                    onClick={() => setShowPaywall(true)}
                    className="w-full bg-emerald-500 hover:bg-emerald-400 text-black font-bold"
                  >
                    <Crown className="h-4 w-4 mr-2" />
                    Unlock Premium
                  </Button>
                </div>
              </div>
            </section>
          </div>
        </div>
        <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
        {isCreditUser && !isPremium && (
          <PremiumBlurOverlay
            title="Premium Page"
            message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Upset Finder."
          />
        )}
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
        <AnimatedBackground variant="intense" />
        <div className="flex-1 relative z-10 flex flex-col">
          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-3 sm:py-4 md:py-5">
              <div className="mb-3 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                <BalanceStrip compact />
              </div>
              <DashboardAccountCommandCenter />
            </div>
          </section>

          <section className="flex-1">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                <div className="mb-8">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-8 w-8 text-emerald-400" />
                    <h1 className="text-3xl md:text-4xl font-black text-white">Gorilla Upset Finder</h1>
                  </div>
                  <p className="text-gray-400">Plus-money underdogs where the model sees a meaningful edge.</p>
                </div>

                {/* Filters */}
                <div className="py-4 border-b border-white/5 bg-black/20 rounded-lg px-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Sport:</span>
                {SPORTS.map((sport) => {
                  const isComingSoon = sportsUiPolicy.isComingSoon(sport.id)
                  const isDisabled = inSeasonBySport[sport.id] === false || isComingSoon
                  const disabledLabel = isComingSoon ? "Coming Soon" : "Not in season"

                  return (
                    <button
                      key={sport.id}
                      onClick={() => setSelectedSport(sport.id)}
                      disabled={isDisabled}
                      className={cn(
                        "px-3 py-1.5 rounded-full text-xs font-medium uppercase transition-all",
                        selectedSport === sport.id
                          ? "bg-emerald-500 text-black"
                          : isDisabled
                            ? "bg-white/5 text-gray-500 cursor-not-allowed opacity-50"
                            : "bg-white/5 text-gray-400 hover:bg-white/10"
                      )}
                      title={isDisabled ? disabledLabel : undefined}
                    >
                      {sport.label}
                      {isDisabled ? (
                        <span className="ml-2 text-[10px] font-bold uppercase">{disabledLabel}</span>
                      ) : null}
                    </button>
                  )
                })}
              </div>

              <div className="h-6 w-px bg-white/10" />

              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-500" />
                {(["all", "low", "medium", "high"] as const).map((tier) => (
                  <button
                    key={tier}
                    onClick={() => setRiskTier(tier)}
                    className={cn(
                      "px-3 py-1.5 rounded-full text-xs font-medium transition-all uppercase",
                      riskTier === tier ? "bg-white/20 text-white" : "bg-white/5 text-gray-400 hover:bg-white/10"
                    )}
                  >
                    {tier}
                  </button>
                ))}
              </div>

              <div className="h-6 w-px bg-white/10" />

              <label className="flex items-center gap-2 text-xs text-gray-500">
                Min edge:
                <input
                  type="number"
                  min={0}
                  max={25}
                  value={minEdgePct}
                  onChange={(e) => setMinEdgePct(Number(e.target.value))}
                  className="w-16 bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
                />
                %
              </label>

              <label className="flex items-center gap-2 text-xs text-gray-500">
                Max results:
                <input
                  type="number"
                  min={1}
                  max={50}
                  value={maxResults}
                  onChange={(e) => setMaxResults(Number(e.target.value))}
                  className="w-16 bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
                />
              </label>

              {isNFL && availableWeeks?.length ? (
                <label className="flex items-center gap-2 text-xs text-gray-500">
                  Week:
                  <select
                    value={selectedWeek ?? ""}
                    onChange={(e) => setSelectedWeek(Number(e.target.value))}
                    className="bg-black/40 border border-white/10 rounded px-2 py-1 text-white text-xs"
                  >
                    {availableWeeks.map((w) => (
                      <option key={w.week} value={w.week}>
                        {w.label}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <div className="ml-auto flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadUpsets}
                  disabled={!canFetch || loading}
                  className="border-white/20"
                >
                  {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                  Refresh
                </Button>
              </div>
            </div>

                  <div className="mt-3 text-xs text-gray-500 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-400" />
                    <p>
                      If a sport shows no results, it usually means there are no upcoming games with odds loaded right now (or data is stale). Try another sport.
                    </p>
                  </div>
                </div>

                {/* Results */}
                <div className="py-6">
                  {error && (
                    <div className="mb-6 bg-red-500/15 border border-red-500/30 rounded-lg p-4 text-red-200 text-sm">
                      {error}
                    </div>
                  )}

                  {loading ? (
                    <div className="flex justify-center items-center py-20">
                      <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
                      <span className="ml-3 text-gray-400">Loading upset candidates...</span>
                    </div>
                  ) : !error && sortedUpsets.length === 0 ? (
                    <div className="text-center text-gray-400 py-12">
                      <TrendingUp className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                      <h3 className="text-xl font-bold text-white mb-2">No Upset Candidates Found</h3>
                      <p>Try adjusting your filters or selecting a different sport.</p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {sortedUpsets.map((u, idx) => (
                        <motion.div
                          key={`${u.game_id || "game"}-${u.team}-${idx}`}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.05 }}
                          className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-colors"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <div className="text-white font-bold truncate">{u.team} vs {u.opponent}</div>
                              <div className="text-xs text-white/60">
                                {u.sport} • {u.market_type.toUpperCase()} • Odds {u.odds > 0 ? "+" : ""}
                                {u.odds}
                              </div>
                            </div>
                            <Badge variant="outline" className={cn("text-xs border", riskTierBadgeClass(u.risk_tier))}>
                              {u.risk_tier.toUpperCase()}
                            </Badge>
                          </div>

                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <div className="bg-black/30 border border-white/10 rounded p-2">
                              <div className="text-[11px] text-white/50">Model prob</div>
                              <div className="text-white font-semibold">{formatPercent(u.model_prob)}</div>
                            </div>
                            <div className="bg-black/30 border border-white/10 rounded p-2">
                              <div className="text-[11px] text-white/50">Implied prob</div>
                              <div className="text-white font-semibold">{formatPercent(u.implied_prob)}</div>
                            </div>
                            <div className="bg-black/30 border border-white/10 rounded p-2">
                              <div className="text-[11px] text-white/50">Edge</div>
                              <div className={cn("font-semibold", u.edge >= 0 ? "text-emerald-300" : "text-rose-300")}>
                                {formatSignedPercent(u.edge)}
                              </div>
                            </div>
                            <div className="bg-black/30 border border-white/10 rounded p-2">
                              <div className="text-[11px] text-white/50">EV</div>
                              <div className={cn("font-semibold", u.ev >= 0 ? "text-emerald-300" : "text-rose-300")}>
                                {formatSignedPercent(u.ev)}
                              </div>
                            </div>
                          </div>

                          {u.reasoning ? (
                            <p className="mt-3 text-xs text-white/60 leading-snug whitespace-pre-line">{u.reasoning}</p>
                          ) : null}
                        </motion.div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            </div>
          </section>
        </div>
      </div>
      <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
    </DashboardLayout>
  )
}


