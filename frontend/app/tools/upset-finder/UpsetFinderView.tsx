"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { motion } from "framer-motion"
import { AlertTriangle } from "lucide-react"
import { api, type UpsetFinderToolsResponse } from "@/lib/api"
import { getPaywallError, isPaywallError, type PaywallError, useSubscription } from "@/lib/subscription-context"
import { PaywallModal, type PaywallReason } from "@/components/paywall/PaywallModal"
import { SectionHeader } from "@/components/ui/SectionHeader"
import { ToolShell } from "@/components/tools/ToolShell"
import { UpsetFinderFilters } from "./_components/UpsetFinderFilters"
import { UpsetFinderResults } from "./_components/UpsetFinderResults"
import type { UpsetFinderEmptyStateActionId } from "./_components/UpsetFinderEmptyStateModelBuilder"
import { usePwaInstallNudge } from "@/lib/pwa/PwaInstallContext"

/**
 * Upset Finder content: hero, filters, results, paywall modal.
 * No layout (DashboardLayout/stripe). Use in app tab or standalone page.
 */
export function UpsetFinderView() {
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
          const key = (s.slug || "").toLowerCase()
          map[key] = typeof s.is_enabled === "boolean" ? s.is_enabled : (s.in_season !== false)
        }
        setInSeasonBySport(map)
      } catch {
        if (!cancelled) setInSeasonBySport({})
      }
    }
    loadSportsStatus()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
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
        // best-effort
      } finally {
        if (!cancelled) {
          setDefaultSportResolved(true)
          setIsResolvingDefaultSport(false)
        }
      }
    }
    resolveDefaultSport()
    return () => { cancelled = true }
  }, [])

  const canFetch = useMemo(
    () =>
      Number.isFinite(minEdgePct) &&
      minEdgePct >= 0 &&
      Number.isFinite(maxResults) &&
      maxResults >= 1 &&
      Number.isFinite(days) &&
      days >= 1,
    [minEdgePct, maxResults, days]
  )

  const handlePaywallClose = () => {
    setShowPaywall(false)
    setPaywallError(null)
    refreshStatus()
  }

  const queryRef = useRef({ minEdgePct, maxResults, days })
  useEffect(() => {
    queryRef.current = { minEdgePct, maxResults, days }
  }, [minEdgePct, maxResults, days])

  const loadUpsets = useCallback(
    async (options?: {
      force?: boolean
      override?: Partial<{ sport: string; days: number; minEdgePct: number; maxResults: number }>
    }) => {
      setError(null)
      setLoading(true)
      try {
        const { minEdgePct: m1, maxResults: m2, days: d } = queryRef.current
        const override = options?.override ?? {}
        const sportToUse = override.sport ?? selectedSport
        const daysToUse = override.days ?? d
        const minEdgeToUse = override.minEdgePct ?? m1
        const maxResultsToUse = override.maxResults ?? m2

        if (override.sport != null && override.sport !== selectedSport) setSelectedSport(override.sport)
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
        setError(err instanceof Error ? err.message : "Failed to load upset candidates.")
        setResponse(lastGoodResponse)
      } finally {
        setLoading(false)
      }
    },
    [selectedSport, lastGoodResponse]
  )

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

  useEffect(() => {
    if (candidates.length > 0) nudgeInstallCta()
  }, [candidates.length, nudgeInstallCta])

  const leftPanel = (
    <>
      <SectionHeader title="Filters" description="Sport, window, and edge threshold" />
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
      {isResolvingDefaultSport ? <div className="text-xs text-gray-500 mt-2">Checking odds coverage…</div> : null}
      <div className="mt-3 text-xs text-white/50 flex items-start gap-2">
        <AlertTriangle className="h-4 w-4 mt-0.5 text-amber-400 shrink-0" />
        <p>If a sport shows no results, try another sport or increase days.</p>
      </div>
    </>
  )

  const rightContent = (
    <div ref={resultsRef}>
      <SectionHeader title="Results" description="Upset candidates ranked by edge" />
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
  )

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="overflow-x-hidden"
      >
        <ToolShell
          title="Upset Finder"
          subtitle="Plus-money underdogs where the model sees a meaningful edge (next X days)."
          left={leftPanel}
          right={rightContent}
        />
      </motion.div>
      <PaywallModal isOpen={showPaywall} onClose={handlePaywallClose} reason={paywallReason} error={paywallError} />
    </>
  )
}
