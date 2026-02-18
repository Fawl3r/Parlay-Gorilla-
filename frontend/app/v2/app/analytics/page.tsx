/**
 * V2 ANALYTICS PAGE
 * Route: /v2/app/analytics
 */

'use client'

import { GlassCard } from '@/components/v2/GlassCard'
import { AnimatedPage } from '@/components/v2/AnimatedPage'

export default function V2AnalyticsPage() {
  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto p-4 lg:p-6 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Performance Analytics</h2>
          <p className="text-white/60 text-sm">Track your betting performance over time</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard padding="md" hover>
            <div className="text-white/50 text-sm mb-1">Total Bets</div>
            <div className="text-3xl font-bold text-white tabular-nums">487</div>
            <div className="text-xs text-white/40 mt-1">Last 30 days</div>
          </GlassCard>

          <GlassCard padding="md" hover>
            <div className="text-white/50 text-sm mb-1">Win Rate</div>
            <div className="text-3xl font-bold text-[#00FF5E] tabular-nums">64.2%</div>
            <div className="text-xs text-[#00FF5E] mt-1">+2.3% vs last month</div>
          </GlassCard>

          <GlassCard padding="md" hover>
            <div className="text-white/50 text-sm mb-1">ROI</div>
            <div className="text-3xl font-bold text-[#00FF5E] tabular-nums">+12.8%</div>
            <div className="text-xs text-[#00FF5E] mt-1">Above market avg</div>
          </GlassCard>

          <GlassCard padding="md" hover>
            <div className="text-white/50 text-sm mb-1">Avg Odds</div>
            <div className="text-3xl font-bold text-white tabular-nums">+245</div>
            <div className="text-xs text-white/40 mt-1">Multi-leg parlays</div>
          </GlassCard>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <GlassCard padding="lg" hover>
            <h3 className="text-lg font-bold text-white mb-4">Win Rate by Sport</h3>
            <div className="space-y-3">
              {[
                { sport: 'NFL', rate: 68, color: 'bg-blue-500' },
                { sport: 'NBA', rate: 62, color: 'bg-orange-500' },
                { sport: 'NHL', rate: 59, color: 'bg-cyan-500' },
                { sport: 'MLB', rate: 64, color: 'bg-red-500' },
              ].map((item) => (
                <div key={item.sport}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-semibold text-white">{item.sport}</span>
                    <span className="text-sm text-white/60 tabular-nums">{item.rate}%</span>
                  </div>
                  <div className="w-full h-2 bg-white/10 rounded overflow-hidden">
                    <div
                      className={`${item.color} h-full transition-all duration-300`}
                      style={{ width: `${item.rate}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>

          <GlassCard padding="lg" hover>
            <h3 className="text-lg font-bold text-white mb-4">Confidence vs Outcome</h3>
            <div className="space-y-3">
              {[
                { range: '75-100%', wins: 45, losses: 12, total: 57 },
                { range: '65-74%', wins: 38, losses: 18, total: 56 },
                { range: '50-64%', wins: 25, losses: 22, total: 47 },
              ].map((item) => (
                <div key={item.range} className="p-3 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)]">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-white">{item.range}</span>
                    <span className="text-xs text-white/50">{item.total} bets</span>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1 text-center py-2 bg-[#00FF5E]/20 text-[#00FF5E] rounded text-sm font-semibold">
                      {item.wins}W
                    </div>
                    <div className="flex-1 text-center py-2 bg-red-500/20 text-red-400 rounded text-sm font-semibold">
                      {item.losses}L
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>

        <GlassCard padding="lg" hover>
          <h3 className="text-lg font-bold text-white mb-4">Recent Bets</h3>
          <div className="space-y-2">
            {[
              { date: '2/16', pick: 'Chiefs -3.5', result: 'Win', odds: -110 },
              { date: '2/16', pick: 'Lakers ML', result: 'Win', odds: 150 },
              { date: '2/15', pick: 'Over 228.5', result: 'Loss', odds: -108 },
              { date: '2/15', pick: 'Rangers ML', result: 'Win', odds: 165 },
            ].map((bet, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)]"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-white/40 w-10">{bet.date}</span>
                  <span className="text-sm text-white font-medium">{bet.pick}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-white/60 tabular-nums">{bet.odds > 0 ? '+' : ''}{bet.odds}</span>
                  <span
                    className={`text-sm font-semibold px-2 py-1 rounded ${
                      bet.result === 'Win' ? 'bg-[#00FF5E]/20 text-[#00FF5E]' : 'bg-red-500/20 text-red-400'
                    }`}
                  >
                    {bet.result}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </AnimatedPage>
  )
}
