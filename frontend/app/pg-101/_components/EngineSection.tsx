"use client"

import { motion } from "framer-motion"
import { BarChart3, Brain, Shield, Sparkles, Target } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"
import { NeonCard } from "@/app/pg-101/_components/NeonCard"

export function EngineSection() {
  return (
    <section id="engine" className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <motion.div {...SECTION_ANIM} className="mb-10 md:mb-12">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 backdrop-blur-md">
            <Sparkles className="h-4 w-4 text-[#00FF5E]" />
            <span className="text-sm text-white/80">How it works</span>
          </div>
          <h2 className="mt-4 text-3xl md:text-5xl font-black text-white">
            A <span className="text-neon">predictive engine</span>, not a hype machine
          </h2>
          <p className="mt-3 text-gray-400 max-w-2xl">
            This is the same philosophy used by sharp bettors: estimate true probability, compare to the market, then
            size risk.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.05 }}>
            <NeonCard
              icon={Shield}
              title="Data Pipeline"
              description="We ingest real odds and context so we’re not blind to what the market is pricing."
              bullets={[
                "Sportsbook odds (moneyline, spread, totals)",
                "Team + player context (injuries, form, matchup)",
                "Weather and situational factors (when relevant)",
              ]}
            />
          </motion.div>
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.08 }}>
            <NeonCard
              icon={Brain}
              title="Per-sport Probability Models"
              description="We estimate true probabilities per sport instead of copying consensus picks."
              bullets={[
                "Win probability + spread cover probability",
                "Total projections and confidence bands",
                "Calibration that improves with results",
              ]}
            />
          </motion.div>
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.11 }}>
            <NeonCard
              icon={BarChart3}
              title="Value Detection (EV)"
              description="If the market implies 54% but our model estimates 62%, that’s an edge worth considering."
              bullets={[
                "Model prob vs implied prob comparison",
                "Flags mispriced lines and soft markets",
                "Keeps you off the overpriced public side",
              ]}
            />
          </motion.div>
          <motion.div {...SECTION_ANIM} transition={{ delay: 0.14 }}>
            <NeonCard
              icon={Target}
              title="Parlay Assembly"
              description="We build slips around correlation and risk fit—not just “best looking odds.”"
              bullets={[
                "Safe / Balanced / Degen profiles",
                "Avoids stacking correlated outcomes",
                "Explains every leg in plain English",
              ]}
            />
          </motion.div>
        </div>
      </div>
    </section>
  )
}



