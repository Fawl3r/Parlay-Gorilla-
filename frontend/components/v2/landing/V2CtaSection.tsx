/**
 * V2 Final CTA Section
 * Sharp, aggressive CTA
 */

'use client'

import Link from 'next/link'

export function V2CtaSection() {
  return (
    <section className="py-16 lg:py-20 border-t border-[rgba(255,255,255,0.08)] bg-[#0A0F0A]/70 backdrop-blur-[10px]">
      <div className="max-w-4xl mx-auto px-4 sm:px-5 lg:px-8 text-center">
        <h2 className="text-4xl sm:text-5xl font-black text-white mb-4 tracking-tight">
          Ready to Build Smarter Parlays?
        </h2>
        <p className="text-lg text-white/70 mb-8">
          Join thousands of bettors using AI
        </p>
        
        <Link
          href="/v2/app/builder"
          className="inline-flex items-center justify-center min-h-[46px] px-10 py-3 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-bold text-base rounded-lg transition-colors v2-press-scale"
        >
          Get Started Now
        </Link>

        <div className="mt-12 pt-8 border-t border-[rgba(255,255,255,0.08)]">
          <p className="text-xs text-white/50 max-w-2xl mx-auto">
            <strong className="text-white/70">Disclaimer:</strong> Parlay Gorilla is an informational tool only. 
            We are not a sportsbook. All predictions are for educational purposes. 
            No guarantees of winning. Gambling involves risk. 
            Please bet responsibly. 18+ only.
          </p>
        </div>
      </div>
    </section>
  )
}
