/**
 * V2 How It Works Section
 * Sharp, terminal-style steps
 */

'use client'

export function V2HowItWorksSection() {
  const steps = [
    {
      number: '01',
      title: 'Choose Your Sport',
      description: 'Select from NFL, NBA, NHL, MLB, and college sports',
      icon: '🏈',
    },
    {
      number: '02',
      title: 'AI Analyzes Data',
      description: 'Machine learning models process thousands of data points',
      icon: '🤖',
    },
    {
      number: '03',
      title: 'Build Your Parlay',
      description: 'Get optimized picks with confidence scores and correlation awareness',
      icon: '📊',
    },
  ]

  return (
    <section className="py-16 lg:py-20 border-t border-[rgba(255,255,255,0.08)] bg-[#0A0F0A]/50 backdrop-blur-[10px]">
      <div className="max-w-7xl mx-auto px-4 sm:px-5 lg:px-8">
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-black text-white mb-2 tracking-tight">
            How It Works
          </h2>
          <p className="text-white/60 text-sm uppercase tracking-wider" data-v2-label>
            Three steps to smarter parlays
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {steps.map((step) => (
            <div
              key={step.number}
              className="relative p-5 rounded-lg bg-white/[0.02] border border-[rgba(255,255,255,0.08)] hover:border-[#00FF5E]/40 transition-colors v2-hover-sweep"
            >
              <div className="absolute top-4 right-4 text-5xl opacity-[0.03] font-black">
                {step.number}
              </div>
              
              <div className="relative z-10">
                <div className="text-4xl mb-3">{step.icon}</div>
                <div className="text-[#00FF5E] font-bold text-xs mb-2 uppercase tracking-wider">
                  STEP {step.number}
                </div>
                <h3 className="text-lg font-bold text-white mb-2">
                  {step.title}
                </h3>
                <p className="text-white/60 text-sm">
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
