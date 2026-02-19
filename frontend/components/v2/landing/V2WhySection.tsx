/**
 * V2 Why Section
 * Feature grid with left accent bars, richer descriptions, structured hierarchy
 */

'use client'

const FEATURES = [
  {
    title: 'AI Confidence Engine',
    description:
      'Every pick carries a confidence score derived from historical data, real-time stats, and predictive modeling — so you always know the strength behind the recommendation.',
  },
  {
    title: 'Correlation Awareness',
    description:
      'Avoid stacking correlated outcomes that collapse parlay odds. Our engine automatically flags risky correlations before you lock in a leg.',
  },
  {
    title: 'Multi-Sport Coverage',
    description:
      'NFL, NBA, NHL, MLB, NCAAF, and NCAAB — all analyzed in one interface with consistent confidence scoring and pick-type filtering.',
  },
  {
    title: 'Zero Gut Picks',
    description:
      'No hunches. No hot takes. Every recommendation traces back to data, giving serious bettors a quantifiable edge over emotional plays.',
  },
]

export function V2WhySection() {
  return (
    <section className="py-14 lg:py-20 border-t border-white/[0.06]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <div className="mb-10">
          <p className="text-[11px] uppercase tracking-widest font-bold text-white/40 mb-2">
            THE EDGE
          </p>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-none">
            Why Parlay Gorilla?
          </h2>
        </div>

        <div className="v2-section-layer grid grid-cols-1 md:grid-cols-2 gap-4">
          {FEATURES.map((feature) => (
            <div
              key={feature.title}
              className="flex gap-4 p-5 rounded-[8px] bg-white/[0.02] border border-white/[0.08] hover:border-[#00FF5E]/30"
            >
              {/* Left accent bar */}
              <div className="flex-shrink-0 w-[3px] rounded-[2px] bg-[#00FF5E]/50 self-stretch" />
              <div>
                <h3 className="text-base font-black text-white mb-1.5 leading-snug">
                  {feature.title}
                </h3>
                <p className="text-sm text-white/55 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
