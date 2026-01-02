"use client"

import { motion } from "framer-motion"
import { BarChart3, Brain, Shield, Target, Zap } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"
import { StatChip } from "@/app/pg-101/_components/StatChip"

export function ValueSection() {
  return (
    <section id="value" className="py-16 md:py-20 border-y border-white/5 bg-black/30">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <motion.div {...SECTION_ANIM} className="lg:col-span-6">
            <h2 className="text-3xl md:text-5xl font-black text-white">
              Why Parlay Gorilla beats <span className="text-white/70">"picks"</span>
            </h2>
            <p className="mt-4 text-gray-400 text-lg leading-relaxed">
              Sportsbooks set lines to balance action and bake in margin. That doesn’t mean the line is “right”—it
              means it’s <span className="text-emerald-200 font-semibold">priced</span>. Our job is to find where it’s
              mispriced.
            </p>

            <div className="mt-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                {
                  icon: BarChart3,
                  title: "Odds aren’t probabilities",
                  desc: "Odds imply probability with margin. We estimate probability first, then compare.",
                },
                {
                  icon: Target,
                  title: "Correlation kills parlays",
                  desc: "Stacking correlated legs looks smart but often reduces true hit rate.",
                },
                {
                  icon: Brain,
                  title: "Narrative isn’t signal",
                  desc: "Hot takes are already priced in. Data gaps are where edges live.",
                },
                {
                  icon: Shield,
                  title: "Risk-fit matters",
                  desc: "Safe/Balanced/Degen isn’t aesthetic—it’s bankroll protection.",
                },
              ].map((c) => (
                <div key={c.title} className="rounded-2xl border border-white/10 bg-black/35 backdrop-blur-md p-4">
                  <div className="flex items-center gap-2 text-white font-bold">
                    <c.icon className="h-5 w-5 text-[#00FF5E]" />
                    {c.title}
                  </div>
                  <p className="mt-2 text-sm text-gray-300 leading-relaxed">{c.desc}</p>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div {...SECTION_ANIM} transition={{ delay: 0.08 }} className="lg:col-span-6">
            <div className="rounded-3xl border border-[#00FF5E]/25 bg-black/40 backdrop-blur-xl p-6 md:p-7 overflow-hidden relative">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,rgba(0,221,85,0.18),transparent_45%),radial-gradient(circle_at_90%_30%,rgba(34,221,102,0.12),transparent_50%)]" />
              <div className="relative">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Zap className="h-5 w-5 text-[#00FF5E]" />
                    <div className="text-white font-black">Market vs Model</div>
                  </div>
                  <div className="text-xs text-white/60">WHY IT WINS</div>
                </div>

                <div className="mt-5 grid grid-cols-1 gap-3">
                  {[
                    { label: "Sportsbook implied probability", value: 54, tone: "bg-white/10" },
                    {
                      label: "Parlay Gorilla model probability",
                      value: 62,
                      tone: "bg-gradient-to-r from-[#00FF5E] to-[#22FF6E]",
                    },
                  ].map((row) => (
                    <div key={row.label} className="rounded-2xl border border-white/10 bg-black/30 p-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white/80">{row.label}</span>
                        <span className="text-emerald-200 font-bold">{row.value}%</span>
                      </div>
                      <div className="mt-3 h-2.5 rounded-full bg-white/10 overflow-hidden">
                        <div className={`h-full ${row.tone}`} style={{ width: `${row.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-5 grid grid-cols-2 gap-3">
                  <StatChip label="Edge found" value="+8.0%" tone="emerald" />
                  <StatChip label="Slip fit" value="Balanced" tone="cyan" />
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}



