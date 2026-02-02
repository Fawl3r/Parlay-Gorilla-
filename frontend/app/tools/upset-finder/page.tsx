"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { TrendingUp, AlertTriangle } from "lucide-react"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { DashboardAccountCommandCenter } from "@/components/usage/DashboardAccountCommandCenter"
import { motion } from "framer-motion"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { api, type UpsetFinderToolsResponse } from "@/lib/api"
import { getPaywallError, isPaywallError, type PaywallError, useSubscription } from "@/lib/subscription-context"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"
import { UpsetFinderFilters } from "./_components/UpsetFinderFilters"
import { UpsetFinderResults } from "./_components/UpsetFinderResults"
import type { UpsetFinderEmptyStateActionId } from "./_components/UpsetFinderEmptyStateModelBuilder"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"

export default function UpsetFinderPage() {
  return (
    <ProtectedRoute>
      <UpsetFinderContent />
    </ProtectedRoute>
  )
}

function UpsetFinderContent() {
  const { isPremium, isCreditUser, canUseUpsetFinder, refreshStatus } = useSubscription()
  const { nudgeInstallCta } = usePwaInstallNudge()

  const [selectedSport, setSelectedSport] = useState<string>("nba")
  const [inSeasonBySport, setInSeasonBySport] = useState<Record<string, boolean>>({})
  const [days, setDays] = useState<number>(7)
  const [minEdgePct, setMinEdgePct] = useState<number>(3)
  const [maxResults, setMaxResults] = useState<number>(20)

  const [isResolvingDefaultSport, setIsResolvingDefaultSport] = useState(true)
  const [defaultSportResolved, setDefaultSportResolved] = useState(false)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<UpsetFinderToolsResponse | null>(null)
  const [lastGoodResponse, setLastGoodResponse] = useState<UpsetFinderToolsResponse | null>(null)

  const [showPaywall, setShowPaywall] = useState(false)
  const [paywallReason, setPaywallReason] = useState<PaywallReason>("upset_finder_locked")
  const [paywallError, setPaywallError] = useState<PaywallError | null>(null)

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
    // Default sport resolver ALWAYS runs for everyone using meta_only=1 (no auth required).
    let cancelled = false
    async function resolveDefaultSport() {
      setIsResolvingDefaultSport(true)
      try {
        const checkDays = 7
        const candidates = ["nfl", "nba", "all"] as const
        for (const s of candidates) {
          const resp = await api.getUpsets({ sport: s, days: checkDays, meta_only: 1 })
          const gamesWithOdds = resp?.meta?.games_with_odds ?? 0
          if (gamesWithOdds > 0) {
            if (!cancelled) setSelectedSport(s)
            break
          }
        }
      } catch {
        // Best-effort; fallback to existing default.
      } finally {
        if (!cancelled) {
          setDefaultSportResolved(true)
          setIsResolvingDefaultSport(false)
        }
      }
    }
    resolveDefaultSport()
    return () => {
      cancelled = true
    }
  }, [])

  const canFetch = useMemo(() => {
    if (!Number.isFinite(minEdgePct) || minEdgePct < 0) return false
    if (!Number.isFinite(maxResults) || maxResults < 1) return false
    if (!Number.isFinite(days) || days < 1) return false
    return true
  }, [minEdgePct, maxResults, days])

  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }

  const queryRef = useRef({ minEdgePct, maxResults, days })
  useEffect(() => {
    queryRef.current = { minEdgePct, maxResults, days }
  }, [minEdgePct, maxResults, days])

  const loadUpsets = useCallback(async (options?: {
    force?: boolean
    override?: Partial<{ sport: string; days: number; minEdgePct: number; maxResults: number }>
  }) => {
    setError(null)
    setLoading(true)
    try {
      const { minEdgePct: minEdgePctLatest, maxResults: maxResultsLatest, days: daysLatest } = queryRef.current
      const override = options?.override ?? {}
      const sportToUse = override.sport ?? selectedSport
      const daysToUse = override.days ?? daysLatest
      const minEdgeToUse = override.minEdgePct ?? minEdgePctLatest
      const maxResultsToUse = override.maxResults ?? maxResultsLatest

      if (override.sport && override.sport !== selectedSport) setSelectedSport(override.sport)
      if (override.days != null) setDays(override.days)
      if (override.minEdgePct != null) setMinEdgePct(override.minEdgePct)
      if (override.maxResults != null) setMaxResults(override.maxResults)

      const resp = await api.getUpsets({
        sport: sportToUse,
        days: Math.max(1, Math.min(30, Math.trunc(daysToUse))),
        min_edge: Math.max(0, minEdgeToUse),
        max_results: Math.max(1, Math.min(50, Math.trunc(maxResultsToUse))),
        force: options?.force ? 1 : 0,
      })
      if (resp?.error) {
        // Keep last-good results visible and surface a small error state.
        setError(resp.error)
        setResponse(lastGoodResponse)
        return
      }
      setResponse(resp)
      setLastGoodResponse(resp)
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
      setResponse(lastGoodResponse)
    } finally {
      setLoading(false)
    }
  }, [lastGoodResponse, selectedSport])

  const loadUpsetsRef = useRef(loadUpsets)
  loadUpsetsRef.current = loadUpsets

  useEffect(() => {
    if (!canFetch || !defaultSportResolved) return
    loadUpsetsRef.current()
  }, [canFetch, defaultSportResolved])

  const candidates = response?.candidates ?? []
  const meta = response?.meta ?? null
  const sport = response?.sport ?? selectedSport
  const access = response?.access ?? null

  const resultsRef = useRef<HTMLDivElement | null>(null)
  const scrollResultsIntoView = () => {
    try {
      resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    } catch {
      // ignore
    }
  }

  const handleResultsAction = async (action: UpsetFinderEmptyStateActionId) => {
    if (action === "unlock") {
      setPaywallReason("upset_finder_locked")
      setShowPaywall(true)
      return
    }
    if (action === "refresh") {
      await loadUpsets({ force: true })
      scrollResultsIntoView()
      return
    }
    if (action === "set_sport_all") {
      await loadUpsets({ override: { sport: "all" } })
      scrollResultsIntoView()
      return
    }
    if (action === "set_days_14") {
      await loadUpsets({ override: { days: 14 } })
      scrollResultsIntoView()
      return
    }
    if (action === "set_min_edge_2") {
      await loadUpsets({ override: { minEdgePct: 2 } })
      scrollResultsIntoView()
      return
    }
    if (action === "set_min_edge_1") {
      await loadUpsets({ override: { minEdgePct: 1 } })
      scrollResultsIntoView()
      return
    }
  }

  const effectiveLoading = loading || (isResolvingDefaultSport && !response)

  // Smart install nudge: when user sees Upset Finder results, allow CTA to re-appear
  useEffect(() => {
    if (candidates.length > 0) nudgeInstallCta()
  }, [candidates.length, nudgeInstallCta])

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
                  <p className="text-gray-400">Plus-money underdogs where the model sees a meaningful edge (next X days).</p>
                </div>

                <UpsetFinderFilters
                  selectedSport={selectedSport}
                  inSeasonBySport={inSeasonBySport}
                  onSportChange={setSelectedSport}
                  days={days}
                  onDaysChange={setDays}
                  minEdgePct={minEdgePct}
                  onMinEdgePctChange={setMinEdgePct}
                  maxResults={maxResults}
                  onMaxResultsChange={setMaxResults}
                  onRefresh={() => loadUpsets({ force: true })}
                  loading={effectiveLoading}
                  canFetch={canFetch}
                />

                {isResolvingDefaultSport ? (
                  <div className="text-xs text-gray-500">Checking odds coverage…</div>
                ) : null}

                <div className="mt-3 text-xs text-gray-500 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-400 shrink-0" />
                  <p>
                    If a sport shows no results, it usually means there are no upcoming games with odds loaded right now (or data is stale). Try another sport or increase days.
                  </p>
                </div>

                <div ref={resultsRef} className="py-6">
                  <UpsetFinderResults
                    candidates={candidates}
                    meta={meta}
                    access={access}
                    sport={sport}
                    days={days}
                    minEdgePct={minEdgePct}
                    loading={effectiveLoading}
                    error={error}
                    onAction={handleResultsAction}
                  />
                </div>
              </motion.div>
            </div>
          </section>
        </div>
      </div>
      <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
      {isCreditUser && !isPremium && !canUseUpsetFinder && (
        <PremiumBlurOverlay
          title="Premium Page"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Upset Finder."
        />
      )}
    </DashboardLayout>
  )
}
