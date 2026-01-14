"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import type { ReactNode } from "react"

import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import {
  leaderboardsApi,
  type AiPowerUsersEntry,
  type VerifiedWinnersEntry,
  type ArcadePointsEntry,
  type RecentWinFeedItem,
} from "@/lib/leaderboards-api"
import { cn } from "@/lib/utils"

type TabId = "verified" | "usage" | "arcade"
type UsagePeriod = "30d" | "all_time"

type ProfileMeResponse = {
  user?: {
    display_name?: string | null
    leaderboard_visibility?: "public" | "anonymous" | "hidden" | string
  }
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "px-4 py-2 rounded-xl border text-sm font-bold transition-colors",
        active ? "bg-emerald-500 text-black border-emerald-400" : "bg-white/5 text-gray-200 border-white/10 hover:bg-white/10"
      )}
    >
      {children}
    </button>
  )
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-black/25 border border-white/10 px-3 py-1 text-xs text-gray-200/80">
      <span className="text-gray-200/60">{label}</span>
      <span className="font-bold text-white">{value}</span>
    </div>
  )
}

export function LeaderboardsPageClient() {
  const { user } = useAuth()
  const [tab, setTab] = useState<TabId>("verified")
  const [usagePeriod, setUsagePeriod] = useState<UsagePeriod>("30d")

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [verified, setVerified] = useState<VerifiedWinnersEntry[]>([])
  const [usage, setUsage] = useState<AiPowerUsersEntry[]>([])
  const [arcadePoints, setArcadePoints] = useState<ArcadePointsEntry[]>([])
  const [recentWins, setRecentWins] = useState<RecentWinFeedItem[]>([])
  const [arcadePeriod, setArcadePeriod] = useState<UsagePeriod>("all_time")
  const [myDisplayName, setMyDisplayName] = useState<string | null>(null)
  const [myVisibility, setMyVisibility] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadProfile() {
      if (!user) return
      try {
        const res = await api.get("/api/profile/me")
        const profile = res.data as ProfileMeResponse
        if (cancelled) return
        setMyDisplayName((profile.user?.display_name || "").trim() || null)
        setMyVisibility((profile.user?.leaderboard_visibility || "").trim() || null)
      } catch {
        if (!cancelled) {
          setMyDisplayName(null)
          setMyVisibility(null)
        }
      }
    }
    loadProfile()
    return () => {
      cancelled = true
    }
  }, [user])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        if (tab === "verified") {
          const res = await leaderboardsApi.getVerifiedWinners(50)
          if (!cancelled) setVerified(res.leaderboard || [])
        } else if (tab === "usage") {
          const res = await leaderboardsApi.getAiUsage({ period: usagePeriod, limit: 50 })
          if (!cancelled) setUsage(res.leaderboard || [])
        } else if (tab === "arcade") {
          const [pointsRes, winsRes] = await Promise.all([
            leaderboardsApi.getArcadePoints({ period: arcadePeriod, limit: 50 }),
            leaderboardsApi.getRecentWins(20),
          ])
          if (!cancelled) {
            setArcadePoints(pointsRes.leaderboard || [])
            setRecentWins(winsRes.wins || [])
          }
        }
      } catch (err: any) {
        if (!cancelled) setError(err?.response?.data?.detail || err?.message || "Failed to load leaderboards")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [tab, usagePeriod, arcadePeriod])

  const highlightName = useMemo(() => (myDisplayName || "").trim(), [myDisplayName])

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 className="text-3xl md:text-4xl font-black text-white">Leaderboards</h1>
          <p className="mt-1 text-sm text-gray-200/70">
            Fun rankings built around engagement and prestige — with privacy controls.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <TabButton active={tab === "verified"} onClick={() => setTab("verified")}>
            Verified Winners
          </TabButton>
          <TabButton active={tab === "usage"} onClick={() => setTab("usage")}>
            AI Power Users
          </TabButton>
          <TabButton active={tab === "arcade"} onClick={() => setTab("arcade")}>
            Arcade Points
          </TabButton>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="text-sm font-bold text-white">
              {tab === "verified"
                ? "🦍 Gorilla Parlay Builder 🦍 Leaderboard (Verified)"
                : tab === "usage"
                  ? "AI Gorilla Parlays Usage Leaderboard"
                  : "Arcade Points Leaderboard"}
            </div>
            <div className="text-xs text-gray-200/70">
              {tab === "verified"
                ? "Only 🦍 Gorilla Parlay Builder 🦍 parlays that you choose to verify, and that WIN after final results."
                : tab === "usage"
                  ? "Counts AI picks that the AI generates. Win or loss — no verification record required."
                  : "Verified 5+ leg wins earn arcade points. Climb the leaderboard and compete with the community."}
            </div>
          </div>

          {tab === "arcade" ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setArcadePeriod("30d")}
                className={cn(
                  "px-3 py-2 rounded-xl border text-xs font-bold transition-colors",
                  arcadePeriod === "30d"
                    ? "bg-emerald-500 text-black border-emerald-400"
                    : "bg-white/5 text-gray-200 border-white/10 hover:bg-white/10"
                )}
              >
                Last 30 days
              </button>
              <button
                type="button"
                onClick={() => setArcadePeriod("all_time")}
                className={cn(
                  "px-3 py-2 rounded-xl border text-xs font-bold transition-colors",
                  arcadePeriod === "all_time"
                    ? "bg-emerald-500 text-black border-emerald-400"
                    : "bg-white/5 text-gray-200 border-white/10 hover:bg-white/10"
                )}
              >
                All time
              </button>
            </div>
          ) : tab === "usage" ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setUsagePeriod("30d")}
                className={cn(
                  "px-3 py-2 rounded-xl border text-xs font-bold transition-colors",
                  usagePeriod === "30d"
                    ? "bg-emerald-500 text-black border-emerald-400"
                    : "bg-white/5 text-gray-200 border-white/10 hover:bg-white/10"
                )}
              >
                Last 30 days
              </button>
              <button
                type="button"
                onClick={() => setUsagePeriod("all_time")}
                className={cn(
                  "px-3 py-2 rounded-xl border text-xs font-bold transition-colors",
                  usagePeriod === "all_time"
                    ? "bg-emerald-500 text-black border-emerald-400"
                    : "bg-white/5 text-gray-200 border-white/10 hover:bg-white/10"
                )}
              >
                All time
              </button>
            </div>
          ) : null}
        </div>

        <details className="mt-4 rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <summary className="cursor-pointer select-none text-sm font-bold text-white">How it works</summary>
          <div className="mt-3 space-y-2 text-sm text-gray-200/80">
            {tab === "verified" ? (
              <ul className="list-disc pl-5 space-y-1">
                <li>Only 🦍 Gorilla Parlay Builder 🦍 parlays that are explicitly verified.</li>
                <li>Counts only after all legs are resolved and the final result is known.</li>
                <li>Only wins appear on this board.</li>
              </ul>
            ) : tab === "usage" ? (
              <ul className="list-disc pl-5 space-y-1">
                <li>Counts Gorilla Parlay generations (win or loss).</li>
                <li>Verification is not required.</li>
                <li>Designed to reward consistent engagement and learning.</li>
              </ul>
            ) : (
              <ul className="list-disc pl-5 space-y-1">
                <li>Only verified custom parlays with 5+ legs that win earn points.</li>
                <li>Higher leg counts = more points (5=100, 6=140, 7=200, 8=280, 9=400, 10=560, 11+=+25% per leg).</li>
                <li>Track your results and climb the leaderboard to compete with the community.</li>
              </ul>
            )}

            <div className="pt-2">
              <Link href="/profile" className="text-emerald-300 hover:text-emerald-200 hover:underline">
                Manage leaderboard privacy in Profile
              </Link>
              {myVisibility ? <span className="ml-2 text-xs text-gray-200/60">(Currently: {myVisibility})</span> : null}
            </div>
          </div>
        </details>

        {!user ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-gray-200/70">
              Sign in to see your balances and personalized rank highlights.
            </div>
            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black text-black hover:bg-emerald-400 transition-colors"
            >
              Sign in
            </Link>
          </div>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {tab === "verified" ? (
          <>
            <StatPill label="Entries" value={String(verified.length)} />
            <StatPill label="Highlight" value={highlightName ? highlightName : "—"} />
          </>
        ) : tab === "usage" ? (
          <>
            <StatPill label="Entries" value={String(usage.length)} />
            <StatPill label="Period" value={usagePeriod === "30d" ? "30d" : "All time"} />
          </>
        ) : (
          <>
            <StatPill label="Entries" value={String(arcadePoints.length)} />
            <StatPill label="Period" value={arcadePeriod === "30d" ? "30d" : "All time"} />
            <StatPill label="Recent Wins" value={String(recentWins.length)} />
          </>
        )}
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-black/25 backdrop-blur overflow-hidden">
        <div className="grid grid-cols-[72px,1fr,140px] gap-2 px-4 py-3 border-b border-white/10 text-xs font-bold text-gray-200/70">
          <div>Rank</div>
          <div>Player</div>
          <div className="text-right">
            {tab === "verified" ? "Wins" : tab === "usage" ? "AI Parlay uses" : "Points"}
          </div>
        </div>

        {error ? (
          <div className="p-6 text-sm text-red-200">{error}</div>
        ) : loading ? (
          <div className="p-6 text-sm text-gray-200/70">Loading…</div>
        ) : tab === "arcade" ? (
          <div className="divide-y divide-white/10">
            {arcadePoints.length === 0 ? (
              <div className="p-6 text-sm text-gray-200/70">No arcade points yet. Win verified 5+ leg parlays to earn points!</div>
            ) : (
              arcadePoints.map((row) => {
                const isMe = highlightName && row.username === highlightName
                return (
                  <div
                    key={`${row.rank}-${row.username}`}
                    className={cn(
                      "grid grid-cols-[72px,1fr,140px] gap-2 px-4 py-3 text-sm",
                      isMe ? "bg-emerald-500/10" : "hover:bg-white/[0.04]"
                    )}
                  >
                    <div className="text-gray-200/80 font-semibold">#{row.rank}</div>
                    <div className="min-w-0">
                      <div className="text-white font-semibold truncate">{row.username}</div>
                      <div className="text-xs text-gray-200/60">
                        {row.total_qualifying_wins} win{row.total_qualifying_wins !== 1 ? "s" : ""}
                        {row.last_win_at ? ` • ${new Date(row.last_win_at).toLocaleDateString()}` : ""}
                      </div>
                    </div>
                    <div className="text-right text-white font-black">{row.total_points.toLocaleString()}</div>
                  </div>
                )
              })
            )}
          </div>
        ) : tab === "verified" ? (
          <div className="divide-y divide-white/10">
            {verified.length === 0 ? (
              <div className="p-6 text-sm text-gray-200/70">No verified winners yet.</div>
            ) : (
              verified.map((row) => {
                const isMe = highlightName && row.username === highlightName
                return (
                  <div
                    key={`${row.rank}-${row.username}`}
                    className={cn(
                      "grid grid-cols-[72px,1fr,140px] gap-2 px-4 py-3 text-sm",
                      isMe ? "bg-emerald-500/10" : "hover:bg-white/[0.04]"
                    )}
                  >
                    <div className="text-gray-200/80 font-semibold">#{row.rank}</div>
                    <div className="min-w-0">
                      <div className="text-white font-semibold truncate">{row.username}</div>
                      <div className="text-xs text-gray-200/60">
                        Win rate: {(row.win_rate * 100).toFixed(0)}%
                        {row.inscription_id ? " • Verified" : ""}
                      </div>
                    </div>
                    <div className="text-right text-white font-black">{row.verified_wins}</div>
                  </div>
                )
              })
            )}
          </div>
        ) : (
          <div className="divide-y divide-white/10">
            {usage.length === 0 ? (
              <div className="p-6 text-sm text-gray-200/70">No usage yet.</div>
            ) : (
              usage.map((row) => {
                const isMe = highlightName && row.username === highlightName
                return (
                  <div
                    key={`${row.rank}-${row.username}`}
                    className={cn(
                      "grid grid-cols-[72px,1fr,140px] gap-2 px-4 py-3 text-sm",
                      isMe ? "bg-emerald-500/10" : "hover:bg-white/[0.04]"
                    )}
                  >
                    <div className="text-gray-200/80 font-semibold">#{row.rank}</div>
                    <div className="min-w-0">
                      <div className="text-white font-semibold truncate">{row.username}</div>
                      <div className="text-xs text-gray-200/60">
                        Last active: {row.last_generated_at ? new Date(row.last_generated_at).toLocaleDateString() : "—"}
                      </div>
                    </div>
                    <div className="text-right text-white font-black">{row.ai_parlays_generated}</div>
                  </div>
                )
              })
            )}
          </div>
        )}
      </div>

      {tab === "arcade" && recentWins.length > 0 && (
        <div className="mt-6 rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-4">
          <div className="mb-3 text-sm font-bold text-white">Recent Verified Wins</div>
          <div className="space-y-2">
            {recentWins.slice(0, 10).map((win, idx) => (
              <div
                key={`${win.resolved_at}-${idx}`}
                className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm"
              >
                <div className="min-w-0 flex-1">
                  <div className="text-white font-semibold truncate">{win.username}</div>
                  <div className="text-xs text-gray-200/60">
                    {win.num_legs} leg{win.num_legs !== 1 ? "s" : ""}
                    {win.parlay_title ? ` • ${win.parlay_title}` : ""}
                  </div>
                </div>
                <div className="ml-3 text-right">
                  <div className="text-emerald-400 font-black">+{win.points_awarded.toLocaleString()}</div>
                  <div className="text-xs text-gray-200/60">
                    {new Date(win.resolved_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LeaderboardsPageClient


