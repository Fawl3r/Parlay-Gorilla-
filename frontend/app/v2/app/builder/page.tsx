/**
 * V2 PARLAY BUILDER PAGE
 * Route: /v2/app/builder
 */

'use client'

import { useState } from 'react'
import { MOCK_PICKS, MockPick } from '@/lib/v2/mock-data'
import { PickCard } from '@/components/v2/PickCard'
import { GlassCard } from '@/components/v2/GlassCard'
import { ConfidenceMeter } from '@/components/v2/ConfidenceMeter'
import { OddsChip } from '@/components/v2/OddsChip'
import { AnimatedPage } from '@/components/v2/AnimatedPage'

export default function V2BuilderPage() {
  const [selectedPicks, setSelectedPicks] = useState<MockPick[]>([])

  const togglePick = (pick: MockPick) => {
    if (selectedPicks.find((p) => p.id === pick.id)) {
      setSelectedPicks(selectedPicks.filter((p) => p.id !== pick.id))
    } else {
      setSelectedPicks([...selectedPicks, pick])
    }
  }

  const avgConfidence =
    selectedPicks.length > 0
      ? selectedPicks.reduce((sum, p) => sum + p.confidence, 0) / selectedPicks.length
      : 0

  const totalOdds = selectedPicks.length > 0 ? 350 : 0 // Mock calculation

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto p-4 lg:p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Available Picks */}
          <div className="lg:col-span-2 space-y-4">
            <div>
              <h2 className="text-2xl font-bold text-white mb-1">Available Picks</h2>
              <p className="text-white/60 text-sm">Click to add to your parlay</p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {MOCK_PICKS.map((pick) => {
                const isSelected = selectedPicks.find((p) => p.id === pick.id)
                return (
                  <div
                    key={pick.id}
                    className={`${isSelected ? 'ring-2 ring-[#00FF5E]' : ''} rounded-lg`}
                    onClick={() => togglePick(pick)}
                  >
                  <PickCard pick={pick} variant="full" />
                </div>
              )
            })}
          </div>
          </div>

          {/* Parlay Slip */}
          <div className="lg:sticky lg:top-20 h-fit">
          <GlassCard padding="lg">
            <h3 className="text-xl font-bold text-white mb-4">Your Parlay</h3>

            {selectedPicks.length === 0 ? (
              <div className="text-center py-8 text-white/50">
                <div className="text-4xl mb-2">🎯</div>
                <p>Select picks to build your parlay</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  {selectedPicks.map((pick) => (
                    <div
                      key={pick.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)]"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white/50 truncate">{pick.matchup}</p>
                        <p className="text-sm font-semibold text-white truncate">{pick.pick}</p>
                      </div>
                      <button
                        onClick={() => togglePick(pick)}
                        className="ml-2 text-red-400 hover:text-red-300"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>

                {/* Stats */}
                <div className="space-y-3 pt-4 border-t border-[rgba(255,255,255,0.08)]">
                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Legs</span>
                    <span className="font-bold text-white">{selectedPicks.length}</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-white/50">Total Odds</span>
                    <OddsChip odds={totalOdds} />
                  </div>

                  <ConfidenceMeter confidence={Math.round(avgConfidence)} />
                </div>

                {/* Stake input */}
                <div>
                  <label className="text-sm text-white/50 mb-2 block">Stake Amount</label>
                  <input
                    type="number"
                    placeholder="10"
                    className="w-full px-4 py-3 bg-white/5 text-white rounded-lg border border-[rgba(255,255,255,0.08)] focus:border-[#00FF5E] focus:outline-none"
                  />
                </div>

                <div className="p-4 rounded-lg bg-[#00FF5E]/10 border border-[#00FF5E]/30">
                  <div className="text-sm text-[#00FF5E] mb-1">Potential Payout</div>
                  <div className="text-2xl font-bold text-white tabular-nums">$45.00</div>
                </div>

                <button className="w-full min-h-[44px] px-4 py-3 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-bold rounded-lg v2-transition-colors v2-press-scale">
                  Build Parlay
                </button>
              </div>
            )}
          </GlassCard>
          </div>
        </div>
      </div>
    </AnimatedPage>
  )
}
