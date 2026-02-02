"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Check } from "lucide-react"
import { getCopy, getCopyObject } from "@/lib/content"
import { PwaInstallCta } from "@/components/pwa/PwaInstallCta"

export function LandingCtaSection() {
  return (
    <section className="py-24 border-t-2 border-[#00FF5E]/40 relative overflow-hidden z-30">
      {/* Background effects */}
      <div className="absolute inset-0 bg-[#0A0F0A]/70 backdrop-blur-sm" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#00FF5E]/10 rounded-full blur-[120px]" />

      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-4xl mx-auto"
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
            {getCopy("site.home.cta.headline")}
          </h2>
          <p className="text-xl text-gray-400 mb-10 font-medium">
            {getCopy("site.home.cta.subheadline")}
          </p>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-3 mb-10">
            {getCopyObject("site.home.cta.features").map((feature: string) => (
              <div key={feature} className="flex items-center gap-2 px-4 py-2.5 rounded-full bg-white/5 border border-white/10">
                <Check className="h-4 w-4 text-[#00FF5E]" />
                <span className="text-sm text-gray-300 font-medium">{feature}</span>
              </div>
            ))}
          </div>

          <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
            <Link
              href="/auth/signup"
              className="inline-flex items-center gap-2 px-10 py-5 text-xl font-bold text-black bg-[#00FF5E] rounded-xl hover:bg-[#22FF6E] transition-all"
              style={{
                boxShadow: "0 0 6px #00FF5E, 0 0 12px #00CC4B, 0 0 20px #22FF6E",
              }}
            >
              {getCopy("site.home.cta.ctaPrimary")}
              <ArrowRight className="h-6 w-6" />
            </Link>
          </motion.div>

          {/* PWA install callout */}
          <div className="mt-10 flex flex-col items-center gap-3">
            <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-[#00FF5E]/20 text-[#00FF5E] border border-[#00FF5E]/40">
              Installable App
            </span>
            <p className="text-sm text-gray-400 max-w-md">
              Install Parlay Gorilla on your phone in 10 seconds — no App Store.
            </p>
            <PwaInstallCta variant="card" context="landing" className="w-full max-w-md" />
          </div>
        </motion.div>
      </div>
    </section>
  )
}


