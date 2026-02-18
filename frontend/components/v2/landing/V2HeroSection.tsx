/**
 * V2 Landing Hero — V1 brand vibe + sharp (no bubbles)
 */

'use client'

import Link from 'next/link'

export function V2HeroSection() {
  return (
    <section
      className="relative min-h-[85vh] flex items-center justify-center overflow-hidden"
      style={{
        backgroundImage: "url('/images/s1back.png')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Overlay 0.45–0.55 for readability (Design Director) */}
      <div className="absolute inset-0 bg-black/50 z-[1]" />
      <div className="absolute inset-0 bg-gradient-to-b from-black/50 via-black/30 to-black/50 z-[1]" />

      {/* Subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.03] z-[1]"
        style={{
          backgroundImage: 'radial-gradient(circle, rgba(0,255,94,0.5) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-5 lg:px-8 text-center">
        <div className="space-y-6">
          {/* Trust row — sharp badges */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs">
            <span className="flex items-center gap-2 text-white/60 uppercase tracking-widest font-bold">
              <span className="w-1 h-1 bg-[#00FF5E]" />
              AI-DRIVEN
            </span>
            <span className="text-white/30">|</span>
            <span className="flex items-center gap-2 text-white/60 uppercase tracking-widest font-bold">
              <span className="w-1 h-1 bg-[#00FF5E]" />
              DATA-BACKED
            </span>
            <span className="text-white/30">|</span>
            <span className="flex items-center gap-2 text-white/60 uppercase tracking-widest font-bold">
              <span className="w-1 h-1 bg-[#00FF5E]" />
              BUILT FOR DEGENS
            </span>
          </div>

          <div className="space-y-3">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black text-white tracking-tight">
              Stop Guessing.
              <br />
              <span className="text-[#00FF5E]">Build Smarter Parlays.</span>
            </h1>
            <p className="text-lg sm:text-xl text-white/70 max-w-3xl mx-auto">
              AI-driven picks with confidence scoring. No gut feelings. Just data.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-4">
            <Link
              href="/v2/app/builder"
              className="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center px-8 py-3 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-bold text-base rounded-lg transition-colors v2-press-scale"
            >
              Build a Parlay
            </Link>
            <Link
              href="/v2/app"
              className="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center px-8 py-3 bg-transparent border-2 border-[#00FF5E] text-white font-bold text-base rounded-lg hover:bg-[#00FF5E]/10 transition-colors v2-press-scale"
            >
              View Today&apos;s Picks
            </Link>
          </div>

          <p className="text-xs text-white/40 max-w-2xl mx-auto pt-8">
            Informational tool only. Not a sportsbook. No guarantees. 18+ only.
          </p>
        </div>
      </div>
    </section>
  )
}
