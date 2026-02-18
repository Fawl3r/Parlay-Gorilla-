"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { BarChart3, ExternalLink } from "lucide-react"

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

function PickCard({ pick, index }: { pick: TodaysPickItem; index: number }) {
  const sportLabel = pick.sport.toUpperCase()
  const oddsStr =
    pick.odds != null
      ? pick.odds > 0
        ? `+${pick.odds}`
        : String(pick.odds)
      : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.05 }}
      className="rounded-lg border border-[#00FF5E]/30 bg-black/40 backdrop-blur-sm p-4 flex flex-col"
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
      <p className="text-white/80 text-sm mb-3">
        <span className="capitalize text-white/70">{pick.market}</span>
        {" · "}
        {pick.selection}
        {oddsStr != null ? ` (${oddsStr})` : ""}
      </p>
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
    </motion.div>
  )
}

export function LandingTodayTopPicksSection() {
  const [data, setData] = useState<TodaysTopPicksResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(false)
    fetch("/api/public/todays-top-picks", { cache: "no-store" })
      .then((res) => {
        if (!res.ok) throw new Error("Unavailable")
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

  return (
    <section className="py-8 md:py-10 border-t border-white/10 bg-black/30 backdrop-blur-sm relative z-20">
      <div className="container mx-auto max-w-7xl px-4 md:px-6">
        <div className="mb-6 md:mb-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-1">
            Today&apos;s Top Picks
          </h2>
          <p className="text-sm md:text-base text-white/70">
            Highest-confidence picks today — updated automatically.
          </p>
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
            <div className="flex gap-4 overflow-x-auto pb-2 md:overflow-x-visible md:flex-wrap md:gap-6 scrollbar-hide -mx-1 px-1 md:mx-0 md:px-0">
              {picks.slice(0, MAX_PICKS).map((pick, index) => (
                <PickCard key={`${pick.event_id}-${pick.market}-${pick.selection}`} pick={pick} index={index} />
              ))}
            </div>
          </>
        )}

        {showUnavailable && (
          <div className="rounded-lg border border-white/15 bg-white/5 backdrop-blur-sm p-6 md:p-8 text-center">
            <BarChart3 className="h-10 w-10 text-white/40 mx-auto mb-3" />
            <p className="text-white/80 font-medium mb-4">
              Top Picks unavailable right now.
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
