"use client"

import { motion } from "framer-motion"
import { Check } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"

export function DifferentSection() {
  return (
    <section id="different" className="py-16 md:py-20">
      <div className="container mx-auto px-4">
        <motion.div {...SECTION_ANIM} className="text-center mb-10 md:mb-12">
          <h2 className="text-3xl md:text-5xl font-black text-white">Different from odds-chasers & consensus sites</h2>
          <p className="mt-3 text-gray-400 max-w-3xl mx-auto">
            If a site just repeats popular picks or “line movement,” you’re already late. We’re built to find hidden
            value and explain it.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <motion.div
            {...SECTION_ANIM}
            transition={{ delay: 0.05 }}
            className="rounded-3xl border border-white/10 bg-black/35 backdrop-blur-xl p-6"
          >
            <div className="text-white font-black text-xl mb-4">Typical prediction sites</div>
            <ul className="space-y-3">
              {[
                "Chase public money and consensus picks",
                "Optimized for clicks, not EV",
                "No transparency on probability vs odds",
                "Overweight narratives and trends",
                "Rarely account for correlation in parlays",
              ].map((t) => (
                <li key={t} className="flex items-start gap-3 text-gray-300">
                  <span className="mt-1 h-2.5 w-2.5 rounded-full bg-white/30 shrink-0" />
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </motion.div>

          <motion.div
            {...SECTION_ANIM}
            transition={{ delay: 0.08 }}
            className="rounded-3xl border border-[#00FF5E]/25 bg-black/45 backdrop-blur-xl p-6 relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_10%,rgba(0,221,85,0.16),transparent_55%)]" />
            <div className="relative">
              <div className="text-white font-black text-xl mb-4 flex items-center justify-center gap-2">
                <span className="text-neon-strong">Parlay Gorilla</span>
                <span className="text-white/70">approach</span>
              </div>
              <ul className="space-y-3">
                {[
                  "Model probability first, then compare to implied odds",
                  "Edge-based filtering to avoid overpriced legs",
                  "Risk-fit modes: Safe / Balanced / Degen",
                  "Multi-sport mixing to reduce correlation",
                  "Explainable picks with confidence + reasoning",
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2 text-gray-200">
                    <Check className="h-5 w-5 text-[#00FF5E] mt-0.5 shrink-0" />
                    <span>{t}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}



