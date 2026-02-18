/**
 * V2 Live Picks Preview Section
 * Sharp, terminal-style picks showcase
 */

'use client'

import { MOCK_PICKS } from '@/lib/v2/mock-data'
import { PickCard } from '../PickCard'

export function V2LivePicksSection() {
  return (
    <section className="py-12 lg:py-16 border-t border-[rgba(255,255,255,0.08)] bg-[#0A0F0A]/60 backdrop-blur-[10px]">
      <div className="max-w-7xl mx-auto px-4 sm:px-5 lg:px-8">
        <div className="text-center mb-6">
          <h2 className="text-3xl sm:text-4xl font-black text-white mb-2 tracking-tight">
            Today&apos;s Live Picks
          </h2>
          <p className="text-white/60 text-sm uppercase tracking-wider" data-v2-label>
            AI-analyzed opportunities
          </p>
        </div>

        {/* Horizontal scroll container */}
        <div className="relative">
          <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide snap-x snap-mandatory">
            {MOCK_PICKS.map((pick) => (
              <div key={pick.id} className="snap-start">
                <PickCard pick={pick} variant="compact" />
              </div>
            ))}
          </div>
        </div>

        {/* Scroll hint */}
        <div className="text-center mt-4">
          <p className="text-xs text-white/40 uppercase tracking-wider" data-v2-label>
            ← Scroll for more →
          </p>
        </div>
      </div>
    </section>
  )
}
