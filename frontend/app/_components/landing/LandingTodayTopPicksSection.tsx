"use client"

import { useEffect, useMemo, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { BarChart3, Clock, ExternalLink, Sparkles } from "lucide-react"
import { BlurredPremiumOverlay, InlineUpgradeCta } from "@/components/conversion"
import { getFeaturedIndex } from "@/lib/retention"
import { useSubscription } from "@/lib/subscription-context"

export interface TodaysPickItem {
  sport: string
  event_id: string
  matchup: string
  market: string
  selection: string
  odds: number | null
  confidence: number
  start_time: string | null
  analysis_url: string
  builder_url: string
}

export interface TodaysTopPicksResponse {
  as_of: string
  date: string
  picks: TodaysPickItem[]
}

const MAX_PICKS = 6

function SkeletonCard() {
  return (
    <div
      className="rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm p-4 h-[140px] animate-pulse"
      style={{ minWidth: "260px" }}
    >
      <div className="h-4 w-12 rounded bg-white/20 mb-3" />
      <div className="h-5 w-full rounded bg-white/20 mb-2" />
      <div className="h-4 w-2/3 rounded bg-white/15 mb-3" />
      <div className="h-4 w-16 rounded bg-white/15" />
    </div>
  )
}

function formatStartTime(iso: string | null): string | null {
  if (!iso) return null
  try {
    const dt = new Date(iso)
    const now = new Date()
    const diffMs = dt.getTime() - now.getTime()
    const diffH = diffMs / (1000 * 60 * 60)
    if (diffH < 0 && diffH > -3) return "In progress"
    if (diffH < 0) return null
    if (diffH < 24) {
      return dt.toLocaleTimeString([], { hour: "numeric", minute: "2-digit", timeZoneName: "short" })
    }
    return dt.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" })
  } catch {
    return null
  }
}

/** Relative time from ISO string for social proof (e.g. "3 minutes ago") */
function formatAsOf(iso: string | null): string | null {
  if (!iso) return null
  try {
    const date = new Date(iso)
    const now = new Date()
    const sec = Math.floor((now.getTime() - date.getTime()) / 1000)
    if (sec < 60) return "just now"
    if (sec < 3600) return `${Math.floor(sec / 60)} minutes ago`
    if (sec < 86400) return `${Math.floor(sec / 3600)} hours ago`
    return `${Math.floor(sec / 86400)} days ago`
  } catch {
    return null
  }
}

/** Today's Intelligence — matchups count, sports active, research freshness. No fake numbers. */
function TodaysIntelligenceBlock({
  matchupsCount,
  sportsList,
  researchUpdatedLabel,
}: {
  matchupsCount: number
  sportsList: string[]
  researchUpdatedLabel: string | null
}) {
  const sportsLine = sportsList.length > 0 ? sportsList.join(" + ") : "—"
  return (
    <div className="rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-4 mb-6">
      <h3 className="text-sm font-semibold text-white/90 mb-2 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-[#00FF5E]/80" />
        Today&apos;s Intelligence
      </h3>
      <ul className="text-sm text-white/70 space-y-1">
        <li>{matchupsCount} matchup{matchupsCount === 1 ? "" : "s"} analyzed today</li>
        <li>Sports active: {sportsLine}</li>
        {researchUpdatedLabel && (
          <li>Research updated {researchUpdatedLabel}</li>
        )}
      </ul>
    </div>
  )
}

/** Single featured pick for "Today's Featured Intelligence" — deterministic by date. */
function FeaturedIntelligenceCard({ pick }: { pick: TodaysPickItem }) {
  return (
    <div className="rounded-xl border border-[#00FF5E]/40 bg-black/50 backdrop-blur-sm p-4 mb-6">
      <p className="text-xs font-semibold uppercase tracking-wider text-[#00FF5E]/90 mb-2">
        Today&apos;s Featured Intelligence
      </p>
      <p className="text-white font-semibold mb-1">{pick.matchup}</p>
      <p className="text-sm text-white/70 mb-3">
        {pick.sport.toUpperCase()} · {Math.round(pick.confidence)}% confidence
      </p>
      <Link
        href={pick.analysis_url}
        className="inline-flex items-center gap-2 text-sm font-medium text-[#00FF5E] hover:text-[#22FF6E] transition-colors"
      >
        View full analysis
        <ExternalLink className="h-3.5 w-3.5" />
      </Link>
    </div>
  )
}

function PickCard({
  pick,
  index,
  showLockedOverlay,
}: {
  pick: TodaysPickItem
  index: number
  showLockedOverlay: boolean
}) {
  const sportLabel = pick.sport.toUpperCase()
  const oddsStr =
    pick.odds != null
      ? pick.odds > 0
        ? `+${pick.odds}`
        : String(pick.odds)
      : null
  const timeLabel = formatStartTime(pick.start_time)

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.08, duration: 0.35, ease: [0.25, 0.1, 0.25, 1] }}
      className="relative rounded-lg border border-[#00FF5E]/30 bg-black/40 backdrop-blur-sm p-4 flex flex-col min-h-[140px]"
      style={{
        minWidth: "260px",
        maxWidth: "320px",
        boxShadow: "0 0 12px rgba(0, 255, 94, 0.08)",
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold uppercase tracking-wider text-[#00FF5E]/90">
          {sportLabel}
        </span>
        <span className="text-sm font-bold text-[#00FF5E]">
          {Math.round(pick.confidence)}%
        </span>
      </div>
      <p className="text-white font-semibold text-sm mb-1 line-clamp-2">
        {pick.matchup}
      </p>
      <p className="text-white/80 text-sm mb-2">
        <span className="capitalize text-white/70">{pick.market}</span>
        {" · "}
        {pick.selection}
        {oddsStr != null ? ` (${oddsStr})` : ""}
      </p>
      {timeLabel && (
        <p className="flex items-center gap-1 text-xs text-white/50 mb-2">
          <Clock className="h-3 w-3" />
          {timeLabel}
        </p>
      )}
      <div className="mt-auto flex gap-2">
        <Link
          href={pick.builder_url}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-black bg-[#00FF5E] rounded-lg hover:bg-[#22FF6E] transition-colors min-h-[44px] min-w-[44px] justify-center"
        >
          Build With This
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
        <Link
          href={pick.analysis_url}
          className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-medium text-white border border-white/30 rounded-lg hover:bg-white/10 transition-colors min-h-[44px] min-w-[44px] justify-center"
        >
          View Analysis
        </Link>
      </div>
      {showLockedOverlay && (
        <BlurredPremiumOverlay
          title="Premium AI Insight Locked"
          subtext="Unlock full AI analysis and edge detection."
        />
      )}
    </motion.div>
  )
}

export function LandingTodayTopPicksSection() {
  const [data, setData] = useState<TodaysTopPicksResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const { isPremium, loading: subscriptionLoading } = useSubscription()
  const showUpgradeUi = !subscriptionLoading && !isPremium

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    fetch("/api/public/todays-top-picks", { cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error(res.status === 502 || res.status === 504 ? "Backend unreachable" : "Unavailable")
        return res.json()
      })
      .then((body: TodaysTopPicksResponse) => {
        if (!cancelled) {
          setData(body)
          setError(false)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setData(null)
          setError(true)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const picks = data?.picks ?? []
  const showPicks = !loading && !error && picks.length > 0
  const showUnavailable = !loading && (error || picks.length === 0)
  const asOfLabel = data?.as_of ? formatAsOf(data.as_of) : null

  const uniqueSports = useMemo(() => {
    const set = new Set(picks.map((p) => p.sport.toUpperCase()))
    return Array.from(set).sort()
  }, [picks])

  const featuredPick = useMemo(() => {
    if (picks.length === 0) return null
    const idx = getFeaturedIndex(picks.length)
    return picks[idx] ?? null
  }, [picks])

  return (
    <section className="py-8 md:py-10 border-t border-white/10 bg-black/30 backdrop-blur-sm relative z-20">
      <div className="container mx-auto max-w-7xl px-4 md:px-6">
        {showPicks && (
          <>
            <TodaysIntelligenceBlock
              matchupsCount={picks.length}
              sportsList={uniqueSports}
              researchUpdatedLabel={asOfLabel}
            />
            {featuredPick && <FeaturedIntelligenceCard pick={featuredPick} />}
          </>
        )}

        <div className="mb-6 md:mb-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-1">
            Today&apos;s AI Selections
          </h2>
          <p className="text-sm md:text-base text-white/70 mb-1">
            Highest-confidence Matchup Intelligence — generated by the same engine you use in the app.
          </p>
          <p className="text-xs text-white/50">
            Used by serious bettors daily. Advanced AI research layer.
          </p>
          {showPicks && (picks.length > 0 || asOfLabel) && (
            <p className="text-xs text-white/45 mt-1">
              {picks.length > 0 && `AI selected ${picks.length} matchup${picks.length === 1 ? "" : "s"} today`}
              {picks.length > 0 && asOfLabel && " · "}
              {asOfLabel && `Model updated ${asOfLabel}`}
            </p>
          )}
        </div>

        {loading && (
          <div className="flex gap-4 overflow-x-auto pb-2 md:overflow-x-visible md:flex-wrap md:gap-6 scrollbar-hide">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {showPicks && (
          <>
            {showUpgradeUi && (
              <p className="text-xs text-white/50 mb-3">
                You&apos;re viewing limited analysis. Key edges hidden in free mode.
              </p>
            )}
            <div className="flex gap-4 overflow-x-auto pb-2 md:overflow-x-visible md:flex-wrap md:gap-6 scrollbar-hide -mx-1 px-1 md:mx-0 md:px-0">
              {picks.slice(0, MAX_PICKS).map((pick, index) => (
                <PickCard
                  key={`${pick.event_id}-${pick.market}-${pick.selection}`}
                  pick={pick}
                  index={index}
                  showLockedOverlay={showUpgradeUi}
                />
              ))}
            </div>
            {showUpgradeUi && (
              <div className="mt-6">
                <InlineUpgradeCta />
              </div>
            )}
          </>
        )}

        {showUnavailable && (
          <div className="rounded-lg border border-white/15 bg-white/5 backdrop-blur-sm p-6 md:p-8 text-center">
            <BarChart3 className="h-10 w-10 text-white/40 mx-auto mb-3" />
            <p className="text-white/80 font-medium mb-4">
              AI Selections unavailable right now.
            </p>
            <p className="text-white/50 text-sm mb-4">
              Backend may be offline or no picks today. Check that the API is reachable or try again later.
            </p>
            <Link
              href="/app"
              className="inline-flex items-center gap-2 px-6 py-3 text-base font-semibold text-black bg-[#00FF5E] rounded-lg hover:bg-[#22FF6E] transition-colors min-h-[44px]"
            >
              Open Parlay Builder
              <ExternalLink className="h-4 w-4" />
            </Link>
          </div>
        )}
      </div>
    </section>
  )
}
