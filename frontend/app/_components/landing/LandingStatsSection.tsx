"use client"

import { motion } from "framer-motion"

export function LandingStatsSection() {
  return (
    <section className="py-16 border-t-2 border-[#00FF5E]/40 border-b-2 border-[#00FF5E]/40 bg-[#0A0F0A]/70 backdrop-blur-sm relative z-30">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { value: "1–20", label: "Legs per parlay" },
            { value: "AI", label: "Explanations" },
            { value: "Live", label: "Odds + context" },
            { value: "18+", label: "Age requirement" },
          ].map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="text-center"
            >
              <div
                className="text-3xl md:text-4xl font-black text-[#00FF5E] mb-2"
                style={{
                  textShadow: "0 0 4px rgba(0, 255, 94, 0.7), 0 0 7px rgba(0, 204, 75, 0.5)",
                }}
              >
                {stat.value}
              </div>
              <div className="text-sm text-white font-medium drop-shadow-[0_0_4px_rgba(0,0,0,0.6)]">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}


