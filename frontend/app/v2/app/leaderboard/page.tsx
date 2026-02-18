/**
 * V2 LEADERBOARD PAGE
 * V1 vibe + sharp lane design (no avatars, segmented tabs, tabular numbers)
 * Route: /v2/app/leaderboard
 */

'use client'

import { useState } from 'react'
import { MOCK_LEADERBOARD } from '@/lib/v2/mock-data'
import { GlassCard } from '@/components/v2/GlassCard'
import { AnimatedPage } from '@/components/v2/AnimatedPage'
import { CountUpStat } from '@/components/v2/CountUpStat'

export default function V2LeaderboardPage() {
  const [activeTab, setActiveTab] = useState<'daily' | 'weekly' | 'monthly'>('daily')

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto p-4 lg:p-5 space-y-5">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1 tracking-tight">Leaderboard</h2>
          <p className="text-white/60 text-sm">Top performers</p>
        </div>

        {/* Segmented tabs + animated underline (no pills) */}
        <div className="flex gap-6 border-b border-[rgba(255,255,255,0.08)] relative">
          {(['daily', 'weekly', 'monthly'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                px-0 py-3 font-bold text-sm uppercase tracking-wider
                v2-transition-colors relative
                ${activeTab === tab ? 'text-white' : 'text-white/50 hover:text-white/80'}
              `}
            >
              {tab}
              {activeTab === tab && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#00FF5E] v2-animate-fade-in" />
              )}
            </button>
          ))}
        </div>

        {/* Table — lane design, no avatars */}
        <GlassCard padding="none">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-bold text-white/50 uppercase tracking-widest">
                    RNK
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-bold text-white/50 uppercase tracking-widest">
                    User
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-white/50 uppercase tracking-widest">
                    Win %
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-white/50 uppercase tracking-widest">
                    Picks
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-white/50 uppercase tracking-widest">
                    ROI
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-bold text-white/50 uppercase tracking-widest">
                    Conf
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {MOCK_LEADERBOARD.map((entry) => (
                  <tr
                    key={entry.rank}
                    className={`
                      v2-hover-sweep v2-transition-colors hover:bg-white/5
                      ${entry.rank === 1 ? 'border-l-2 border-l-[#00FF5E] bg-[#00FF5E]/5' : ''}
                    `}
                  >
                    <td className="px-4 py-3">
                      <div
                        className={`
                          w-8 h-8 flex items-center justify-center font-bold text-sm rounded
                          tabular-nums
                          ${entry.rank === 1 ? 'text-[#00FF5E] bg-[#00FF5E]/10 border border-[#00FF5E]/40' : ''}
                          ${entry.rank === 2 ? 'text-white/70 bg-white/5 border border-[rgba(255,255,255,0.08)]' : ''}
                          ${entry.rank === 3 ? 'text-orange-400 bg-orange-500/10 border border-orange-500/40' : ''}
                          ${entry.rank > 3 ? 'text-white/50' : ''}
                        `}
                      >
                        {entry.rank}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-bold text-white">{entry.username}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="font-bold text-[#00FF5E] text-base tabular-nums" data-v2-numeric>
                        {entry.winRate}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-white/80 font-mono tabular-nums">{entry.totalPicks}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span
                        className={`font-bold text-base tabular-nums ${
                          entry.roi > 0 ? 'text-[#00FF5E]' : 'text-red-400'
                        }`}
                      >
                        {entry.roi > 0 ? '+' : ''}
                        {entry.roi}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <span className="text-white/60 font-mono text-sm tabular-nums">
                        {entry.avgConfidence}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </GlassCard>

        {/* AI vs Community — V1 glass + count-up */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <GlassCard padding="md" hover>
            <div className="border-l-2 border-[#00FF5E] pl-3 mb-4">
              <h3 className="text-sm font-bold text-[#00FF5E] uppercase tracking-widest">AI Engine</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">Win Rate</span>
                <CountUpStat
                  end={64.2}
                  duration={800}
                  decimals={1}
                  suffix="%"
                  className="text-3xl font-bold text-[#00FF5E] tracking-tight tabular-nums"
                />
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">Total Picks</span>
                <CountUpStat
                  end={487}
                  duration={800}
                  className="text-3xl font-bold text-white tracking-tight tabular-nums"
                />
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">ROI</span>
                <CountUpStat
                  end={12.8}
                  duration={800}
                  decimals={1}
                  prefix="+"
                  suffix="%"
                  className="text-3xl font-bold text-[#00FF5E] tracking-tight tabular-nums"
                />
              </div>
            </div>
          </GlassCard>

          <GlassCard padding="md" hover>
            <div className="border-l-2 border-white/20 pl-3 mb-4">
              <h3 className="text-sm font-bold text-white/70 uppercase tracking-widest">Community Avg</h3>
            </div>
            <div className="space-y-3">
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">Win Rate</span>
                <CountUpStat
                  end={52.1}
                  duration={800}
                  decimals={1}
                  suffix="%"
                  className="text-3xl font-bold text-white/90 tracking-tight tabular-nums"
                />
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">Total Picks</span>
                <CountUpStat
                  end={1294}
                  duration={800}
                  className="text-3xl font-bold text-white tracking-tight tabular-nums"
                />
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-xs text-white/50 uppercase tracking-wider">ROI</span>
                <CountUpStat
                  end={3.2}
                  duration={800}
                  decimals={1}
                  prefix="+"
                  suffix="%"
                  className="text-3xl font-bold text-white/90 tracking-tight tabular-nums"
                />
              </div>
            </div>
          </GlassCard>
        </div>
      </div>
    </AnimatedPage>
  )
}
