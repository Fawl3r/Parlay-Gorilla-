/**
 * V2 Landing Hero — dominant, left-aligned, premium product feel
 */

'use client'

import Link from 'next/link'

const HERO_STATS = [
  { value: '64%', label: 'Avg Win Rate' },
  { value: '10K+', label: 'Parlays Built' },
  { value: 'AI-Driven', label: 'Smart Picks' },
]

export function V2HeroSection() {
  return (
    <section
      className="v2-hero-layer relative min-h-[88vh] flex items-center overflow-hidden bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: "url('/images/s1back.png')" }}
    >
      <div className="absolute inset-0 bg-black/40 z-[1]" />

      <div className="relative z-10 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 lg:py-32">
        <div className="max-w-3xl flex flex-col gap-7">
          {/* Eyebrow — trust badges */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] uppercase tracking-widest font-bold">
            <span className="flex items-center gap-1.5 text-white/45">
              <span className="w-1.5 h-1.5 bg-[#00FF5E] inline-block flex-shrink-0" />
              AI-DRIVEN
            </span>
            <span className="text-white/20">|</span>
            <span className="flex items-center gap-1.5 text-white/45">
              <span className="w-1.5 h-1.5 bg-[#00FF5E] inline-block flex-shrink-0" />
              DATA-BACKED
            </span>
            <span className="text-white/20">|</span>
            <span className="flex items-center gap-1.5 text-white/45">
              <span className="w-1.5 h-1.5 bg-[#00FF5E] inline-block flex-shrink-0" />
              BUILT FOR SERIOUS BETTORS
            </span>
          </div>

          {/* Headline — commanding, left-aligned */}
          <div className="v2-animate-fade-in">
            <h1 className="text-[64px] sm:text-[80px] lg:text-[96px] font-black text-white tracking-[-0.025em] leading-[0.9] mb-3">
              Stop Guessing.
            </h1>
            <h2 className="text-[52px] sm:text-[66px] lg:text-[78px] font-black text-[#00FF5E] tracking-[-0.025em] leading-[0.9]">
              Build Smarter<br />Parlays.
            </h2>
          </div>

          {/* Subtext — 3 stacked short lines, denser than before */}
          <div className="space-y-1">
            <p className="text-base sm:text-lg text-white/60 font-medium leading-snug">
              AI-powered confidence scoring.
            </p>
            <p className="text-base sm:text-lg text-white/60 font-medium leading-snug">
              Correlation-aware parlay modeling.
            </p>
            <p className="text-base sm:text-lg text-white/60 font-medium leading-snug">
              Built for serious bettors, not gut picks.
            </p>
          </div>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row items-start gap-3">
            <Link
              href="/v2/app/builder"
              className="w-full sm:w-auto min-h-[48px] inline-flex items-center justify-center px-8 py-3 bg-[#00FF5E] hover:brightness-110 text-black font-black text-sm uppercase tracking-wider rounded-[8px] transition-all duration-150 v2-press-scale"
            >
              Build a Parlay
            </Link>
            <Link
              href="/v2/app"
              className="w-full sm:w-auto min-h-[48px] inline-flex items-center justify-center px-8 py-3 border border-white/[0.18] text-white font-bold text-sm uppercase tracking-wider rounded-[8px] hover:border-[#00FF5E]/60 hover:bg-white/[0.03] transition-all duration-150 v2-press-scale"
            >
              View Today&apos;s Picks
            </Link>
          </div>

          {/* Micro-metrics stat row — removes empty feeling */}
          <div className="flex flex-wrap items-start gap-2">
            {HERO_STATS.map((stat) => (
              <div
                key={stat.label}
                className="flex flex-col px-4 py-2.5 rounded-[8px] bg-white/[0.04] border border-white/[0.08]"
              >
                <span className="text-xl font-black text-white tabular-nums leading-none mb-0.5">
                  {stat.value}
                </span>
                <span className="text-[10px] text-white/45 uppercase tracking-widest font-bold leading-none">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-white/30">
            Informational tool only. Not a sportsbook. No guarantees. 18+ only.
          </p>
        </div>
      </div>
    </section>
  )
}
