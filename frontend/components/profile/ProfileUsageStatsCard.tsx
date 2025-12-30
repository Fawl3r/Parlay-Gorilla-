"use client"

import Link from "next/link"

import { cn } from "@/lib/utils"

export type UserStatsResponse = {
  ai_parlays: {
    lifetime: number
    last_30_days: number
    period_used: number
    period_limit: number
    period_remaining: number
    period_start?: string | null
    period_end?: string | null
  }
  custom_ai_parlays: {
    saved_lifetime: number
    saved_last_30_days: number
    period_used: number
    period_limit: number
    period_remaining: number
    period_start?: string | null
    period_end?: string | null
  }
  inscriptions: {
    consumed_lifetime: number
    period_used: number
    period_limit: number
    period_remaining: number
    inscription_cost_usd: number
    total_cost_usd: number
    period_start?: string | null
    period_end?: string | null
  }
  verified_wins: {
    lifetime: number
    last_30_days: number
  }
  leaderboards: {
    verified_winners: { rank: number | null }
    ai_usage_30d: { rank: number | null }
    ai_usage_all_time: { rank: number | null }
  }
}

function StatBox({ label, value, subtle }: { label: string; value: string; subtle?: boolean }) {
  return (
    <div className={cn("rounded-xl border border-white/10 bg-white/[0.03] p-4", subtle && "bg-black/20")}>
      <div className="text-xs uppercase tracking-wide text-gray-200/60">{label}</div>
      <div className="mt-1 text-2xl font-black text-white">{value}</div>
    </div>
  )
}

function formatLimit(remaining: number, limit: number) {
  const lim = limit < 0 ? "∞" : String(limit)
  return `${Math.max(0, remaining)}/${lim}`
}

export function ProfileUsageStatsCard({ stats }: { stats: UserStatsResponse | null }) {
  if (!stats) {
    return (
      <div className="rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5">
        <h3 className="text-white font-black">Usage & Leaderboards</h3>
        <p className="mt-1 text-sm text-gray-200/70">Loading usage stats…</p>
      </div>
    )
  }

  return (
    <div className="rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-white font-black">Usage & Leaderboards</h3>
          <p className="mt-1 text-sm text-gray-200/70">
            Clear counts for AI usage, Custom AI, and optional on-chain verification.
          </p>
        </div>
        <Link href="/leaderboards" className="text-sm font-bold text-emerald-300 hover:text-emerald-200 hover:underline">
          View leaderboards
        </Link>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <StatBox label="AI remaining (this period)" value={formatLimit(stats.ai_parlays.period_remaining, stats.ai_parlays.period_limit)} />
        <StatBox label="Custom AI remaining (this period)" value={formatLimit(stats.custom_ai_parlays.period_remaining, stats.custom_ai_parlays.period_limit)} />
        <StatBox label="Verified wins (lifetime)" value={String(stats.verified_wins.lifetime)} />
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <StatBox label="AI generated (lifetime)" value={String(stats.ai_parlays.lifetime)} subtle />
        <StatBox label="Custom saved (lifetime)" value={String(stats.custom_ai_parlays.saved_lifetime)} subtle />
        <StatBox
          label={`On-chain verifications (lifetime)`}
          value={String(stats.inscriptions.consumed_lifetime)}
          subtle
        />
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <div className="text-xs uppercase tracking-wide text-gray-200/60">Leaderboard rank</div>
          <div className="mt-2 space-y-2 text-sm text-gray-200/80">
            <div className="flex items-center justify-between">
              <span>Verified Winners</span>
              <span className="font-black text-white">{stats.leaderboards.verified_winners.rank ? `#${stats.leaderboards.verified_winners.rank}` : "—"}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>AI Power Users (30d)</span>
              <span className="font-black text-white">{stats.leaderboards.ai_usage_30d.rank ? `#${stats.leaderboards.ai_usage_30d.rank}` : "—"}</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 md:col-span-2">
          <div className="text-xs uppercase tracking-wide text-gray-200/60">On-chain verification cost</div>
          <div className="mt-2 text-sm text-gray-200/80">
            <div className="flex items-center justify-between">
              <span>Per verification</span>
              <span className="font-black text-white">${stats.inscriptions.inscription_cost_usd.toFixed(2)}</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span>Lifetime total (estimated)</span>
              <span className="font-black text-white">${stats.inscriptions.total_cost_usd.toFixed(2)}</span>
            </div>
            <div className="mt-2 text-xs text-gray-200/60">
              Verification is opt-in and only applies to Custom AI parlays.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProfileUsageStatsCard


