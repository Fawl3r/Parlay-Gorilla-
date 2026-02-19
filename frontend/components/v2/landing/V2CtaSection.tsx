/**
 * V2 Final CTA Section
 * Commanding, tight, left-aligned — no gimmicks, no empty space
 */

'use client'

import Link from 'next/link'

export function V2CtaSection() {
  return (
    <section className="py-16 lg:py-24 border-t border-white/[0.06] bg-[#0A0F0A]">
      <div className="v2-section-layer max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <p className="text-[11px] uppercase tracking-widest font-bold text-white/40 mb-4">
            GET STARTED
          </p>
          <h2 className="text-5xl sm:text-6xl font-black text-white tracking-[-0.025em] leading-[0.92] mb-5">
            Ready to Build<br />Smarter Parlays?
          </h2>
          <p className="text-base text-white/55 mb-8 max-w-md leading-relaxed">
            AI-powered picks. Confidence scoring. Correlation protection.
            Built to give serious bettors a real, data-backed edge.
          </p>

          <div className="flex flex-col sm:flex-row items-start gap-3 mb-12">
            <Link
              href="/v2/app/builder"
              className="w-full sm:w-auto min-h-[48px] inline-flex items-center justify-center px-8 py-3 bg-[#00FF5E] hover:brightness-110 text-black font-black text-sm uppercase tracking-wider rounded-[8px] transition-[color,filter] duration-150 v2-press-scale"
            >
              Get Started Free
            </Link>
            <Link
              href="/v2/app"
              className="w-full sm:w-auto min-h-[48px] inline-flex items-center justify-center px-8 py-3 border border-white/[0.15] text-white font-bold text-sm uppercase tracking-wider rounded-[8px] hover:border-[#00FF5E]/50 transition-[color,border-color] duration-150 v2-press-scale"
            >
              Browse Today&apos;s Picks
            </Link>
          </div>

          <div className="pt-6 border-t border-white/[0.06]">
            <p className="text-xs text-white/35 max-w-lg leading-relaxed">
              <strong className="text-white/50">Disclaimer:</strong> Parlay Gorilla is an informational
              tool only. Not a sportsbook. All predictions are for educational purposes only.
              No guarantees of winning. Gambling involves risk. Please bet responsibly. 18+ only.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
