"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Check } from "lucide-react"

export function LandingCtaSection() {
  return (
    <section className="py-24 border-t-2 border-[#00DD55]/40 relative overflow-hidden z-30">
      {/* Background effects */}
      <div className="absolute inset-0 bg-[#0A0F0A]/70 backdrop-blur-sm" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#00DD55]/10 rounded-full blur-[120px]" />

      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-4xl mx-auto"
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
            <span className="text-white">Ready for </span>
            <span
              className="text-[#00DD55]"
              style={{
                textShadow: "0 0 4px rgba(0, 221, 85, 0.7), 0 0 7px rgba(0, 187, 68, 0.5)",
              }}
            >
              Smarter Analytics
            </span>
            <span className="text-white">?</span>
          </h2>
          <p className="text-xl text-gray-400 mb-10 font-medium">
            Get AI-powered sports analytics with statistical analysis, matchup insights, and research tools to inform your decisions.
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {[
              "AI-powered analysis",
              "Statistical insights",
              "Matchup research",
              "Data-driven context",
              "21+ responsible",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-white/5 border border-white/10">
                <Check className="h-4 w-4 text-[#00DD55]" />
                <span className="text-sm text-gray-300 font-medium">{feature}</span>
              </div>
            ))}
          </div>

          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link
              href="/auth/signup"
              className="inline-flex items-center gap-2 px-10 py-5 text-xl font-bold text-black bg-[#00DD55] rounded-xl hover:bg-[#22DD66] transition-all"
              style={{
                boxShadow: "0 0 6px #00DD55, 0 0 12px #00BB44, 0 0 20px #22DD66",
              }}
            >
              Get Started Free
              <ArrowRight className="h-6 w-6" />
            </Link>
          </motion.div>
        </motion.div>
      </div>
    </section>
  )
}


