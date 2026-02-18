"use client"

import { motion } from "framer-motion"
import { getCopy, getCopyObject } from "@/lib/content"
import { APP_VERSION } from "@/lib/constants/appVersion"

export function LandingHowItWorksSection() {
  return (
    <section
      id="how-it-works"
      className="py-10 md:py-12 border-t border-[#00FF5E]/40 bg-[#0A0F0A]/60 backdrop-blur-sm relative z-30"
    >
      <div className="container mx-auto px-4 md:px-8 max-w-7xl">
        <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-10">
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight mb-2">
            {getCopy("site.home.howItWorks.title")}
          </h2>
          <p className="text-sm text-white/60 max-w-xl mx-auto">
            {getCopy("site.home.howItWorks.subtitle")}
          </p>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          {getCopyObject("site.home.howItWorks.steps").map((item: any, index: number) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              className="relative text-center"
            >
              {/* Connector line */}
              {index < 2 && (
                <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-0.5 bg-gradient-to-r from-[#00FF5E]/50 to-transparent" />
              )}

              <div
                className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-[#00FF5E] text-black text-xl font-black mb-4"
                style={{
                  boxShadow: "0 0 6px #00FF5E, 0 0 12px #00CC4B",
                }}
              >
                {item.step}
              </div>
              <h3 className="text-2xl font-bold text-white mb-3">{item.title}</h3>
              <p className="text-gray-400 leading-relaxed">{item.description}</p>
            </motion.div>
          ))}
        </div>

        {/* Application Version Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.6 }}
          className="mt-16 max-w-3xl mx-auto text-center"
        >
          <h3 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Application Version
          </h3>
          <p className="text-base md:text-lg text-gray-400 leading-relaxed mb-2">
            Parlay Gorilla is a continuously evolving analysis engine.
          </p>
          <p className="text-base md:text-lg text-gray-400 leading-relaxed mb-3">
            You are currently viewing Version {APP_VERSION} — the first public release
            focused on speed, transparency, and disciplined decision-making.
          </p>
          <p className="text-sm text-gray-500">
            Major upgrades are released incrementally as the engine improves.
          </p>
        </motion.div>
      </div>
    </section>
  )
}


