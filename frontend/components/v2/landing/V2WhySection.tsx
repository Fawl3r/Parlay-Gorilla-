/**
 * V2 Why Section
 * Sharp, aggressive features grid
 */

'use client'

export function V2WhySection() {
  const features = [
    {
      title: 'AI Confidence Engine',
      description: 'Every pick comes with a confidence score based on historical data and real-time analysis',
      icon: '🎯',
    },
    {
      title: 'Correlation Awareness',
      description: 'Avoid stacking correlated outcomes that tank your parlay odds',
      icon: '🔗',
    },
    {
      title: 'Multi-Sport Support',
      description: 'Build parlays across NFL, NBA, NHL, MLB, and college sports',
      icon: '🏆',
    },
    {
      title: 'No Gut Picks',
      description: 'Data-driven recommendations, not hunches or hot takes',
      icon: '📈',
    },
  ]

  return (
    <section className="py-16 lg:py-20 border-t border-[rgba(255,255,255,0.08)] bg-[#0A0F0A]/50 backdrop-blur-[10px]">
      <div className="max-w-7xl mx-auto px-4 sm:px-5 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-black text-white mb-2 tracking-tight">
            Why Parlay Gorilla?
          </h2>
          <p className="text-white/60 text-sm uppercase tracking-wider" data-v2-label>
            The edge you need to beat the book
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature, idx) => (
            <div
              key={idx}
              className="p-5 rounded-lg bg-white/[0.02] border border-[rgba(255,255,255,0.08)] hover:border-[#00FF5E]/40 transition-colors v2-hover-sweep"
            >
              <div className="flex items-start gap-4">
                <div className="text-3xl">{feature.icon}</div>
                <div>
                  <h3 className="text-base font-bold text-white mb-1.5">
                    {feature.title}
                  </h3>
                  <p className="text-white/60 text-sm">
                    {feature.description}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
