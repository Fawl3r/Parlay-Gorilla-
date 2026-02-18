/**
 * V2 APP DASHBOARD PAGE
 * Sharp, terminal-style dashboard with animated stats
 * Route: /v2/app
 */

'use client'

import { MOCK_PICKS } from '@/lib/v2/mock-data'
import { PickCard } from '@/components/v2/PickCard'
import { GlassCard } from '@/components/v2/GlassCard'
import { AnimatedPage } from '@/components/v2/AnimatedPage'
import { useCountUp } from '@/lib/v2/count-up'

function StatCard({ label, value, suffix = '', prefix = '', subtext, subtextColor = 'text-emerald-400' }: {
  label: string
  value: number
  suffix?: string
  prefix?: string
  subtext: string
  subtextColor?: string
}) {
  const animated = useCountUp({ 
    end: value, 
    duration: 700,
    decimals: suffix === '%' ? 1 : 0,
    suffix,
    prefix,
  })

  return (
    <GlassCard padding="md" hover>
      <div className="text-xs text-white/50 mb-1 uppercase tracking-wider font-bold">{label}</div>
      <div className="text-3xl lg:text-4xl font-bold text-white tracking-tight tabular-nums">{animated}</div>
      <div className={`${subtextColor} text-xs mt-1 font-bold`}>{subtext}</div>
    </GlassCard>
  )
}

export default function V2AppDashboard() {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto p-4 lg:p-5 space-y-5">
        {/* Stats Overview - Sharp Cards with Count-Up */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatCard
            label="Win Rate"
            value={64.2}
            suffix="%"
            subtext="+2.3% Week"
            subtextColor="text-[#00FF5E]"
          />
          <StatCard
            label="Total Picks"
            value={487}
            subtext="30 Days"
            subtextColor="text-white/50"
          />
          <StatCard
            label="Avg Conf"
            value={73.5}
            suffix="%"
            subtext="High Quality"
            subtextColor="text-[#00FF5E]"
          />
          <StatCard
            label="ROI"
            value={12.8}
            prefix="+"
            suffix="%"
            subtext="Beating Market"
            subtextColor="text-[#00FF5E]"
          />
        </div>

        {/* Today's Picks */}
        <div>
        <div className="flex items-center justify-between mb-4 border-l-2 border-[#00FF5E] pl-3">
          <h2 className="text-xl font-bold text-white tracking-tight">Today&apos;s AI Picks</h2>
          <button className="text-xs text-[#00FF5E] hover:text-[#22FF6E] font-bold v2-transition-colors">
            View All →
          </button>
        </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {MOCK_PICKS.slice(0, 4).map((pick) => (
              <PickCard key={pick.id} pick={pick} variant="full" />
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <GlassCard padding="md">
          <h3 className="text-sm font-bold text-white mb-3 tracking-tight border-l-2 border-[rgba(255,255,255,0.08)] pl-2">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-2">
            <button className="min-h-[44px] px-4 py-3 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-bold text-sm rounded-lg v2-transition-colors v2-press-scale">
              Build Parlay
            </button>
            <button className="min-h-[44px] px-4 py-3 bg-white/5 hover:bg-white/10 text-white font-bold text-sm rounded-lg border border-[rgba(255,255,255,0.08)] v2-transition-colors v2-press-scale">
              View Analytics
            </button>
          </div>
        </GlassCard>
      </div>
    </AnimatedPage>
  )
}
