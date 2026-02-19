/**
 * V2 Live Picks Preview Section
 * Product-like picks showcase — structured header, density, hover states
 */

'use client'

import { memo } from 'react'
import Link from 'next/link'
import { MOCK_PICKS } from '@/lib/v2/mock-data'
import { PickCard } from '../PickCard'

function V2LivePicksSectionInner() {
  return (
    <section className="py-12 lg:py-16 border-t border-white/[0.06]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header — left-aligned with hierarchy */}
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-[11px] uppercase tracking-widest font-bold text-white/40 mb-2">
              LIVE ANALYSIS
            </p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-none">
              Today&apos;s Top Picks
            </h2>
          </div>
          <Link
            href="/v2/app"
            className="hidden sm:inline-flex items-center gap-1.5 text-sm font-bold text-[#00FF5E] uppercase tracking-wider hover:brightness-110 transition-all duration-150"
          >
            See All <span aria-hidden>→</span>
          </Link>
        </div>

        {/* Picks — free-flowing horizontal scroll (no snap = no jerk) */}
        <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 v2-scroll-x">
          {MOCK_PICKS.map((pick) => (
            <div
              key={pick.id}
              className="flex-shrink-0 transition-transform duration-150 hover:-translate-y-0.5"
            >
              <PickCard pick={pick} variant="compact" />
            </div>
          ))}
        </div>

        {/* Mobile see all — full width */}
        <div className="mt-4 sm:hidden">
          <Link
            href="/v2/app"
            className="w-full inline-flex items-center justify-center min-h-[44px] border border-white/[0.12] text-white/70 text-sm font-bold uppercase tracking-wider rounded-[8px] hover:border-[#00FF5E]/40 transition-all duration-150"
          >
            See All Picks →
          </Link>
        </div>
      </div>
    </section>
  )
}

export const V2LivePicksSection = memo(V2LivePicksSectionInner)
