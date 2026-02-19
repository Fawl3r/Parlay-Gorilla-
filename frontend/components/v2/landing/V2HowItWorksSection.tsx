/**
 * V2 How It Works Section
 * Connected step grid — structural separation via dividers, not card stacking
 */

'use client'

const STEPS = [
  {
    number: '01',
    title: 'Choose Your Sport',
    description:
      'Select from NFL, NBA, NHL, MLB, and college sports. Filter by date, team, or matchup type to narrow your focus.',
  },
  {
    number: '02',
    title: 'AI Analyzes Data',
    description:
      'Machine learning processes thousands of data points: injuries, trends, historical matchups, line movement, and weather.',
  },
  {
    number: '03',
    title: 'Build Your Parlay',
    description:
      'Get ranked picks with confidence scores, correlation warnings, and expected value breakdowns — then export to your book.',
  },
]

export function V2HowItWorksSection() {
  return (
    <section className="py-14 lg:py-20 border-t border-white/[0.06]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header — left-aligned, clear hierarchy */}
        <div className="mb-10">
          <p className="text-[11px] uppercase tracking-widest font-bold text-white/40 mb-2">
            PROCESS
          </p>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-none">
            How It Works
          </h2>
        </div>

        {/* Steps — connected grid; layer so scroll doesn't repaint */}
        <div className="v2-section-layer grid grid-cols-1 md:grid-cols-3 gap-px bg-white/[0.06] rounded-[8px] overflow-hidden">
          {STEPS.map((step) => (
            <div
              key={step.number}
              className="relative p-6 bg-[#0A0F0A] hover:bg-white/[0.02]"
            >
              {/* Large step number — background accent, non-interactive */}
              <div
                className="absolute top-3 right-4 font-black text-white/[0.04] leading-none select-none"
                style={{ fontSize: '72px' }}
                aria-hidden
              >
                {step.number}
              </div>

              <div className="relative z-10">
                <p className="text-[#00FF5E] font-black text-[11px] uppercase tracking-widest mb-3">
                  STEP {step.number}
                </p>
                <h3 className="text-lg font-black text-white mb-2 leading-snug">
                  {step.title}
                </h3>
                <p className="text-sm text-white/50 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
