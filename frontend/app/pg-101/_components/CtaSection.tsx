"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight } from "lucide-react"

import { SECTION_ANIM } from "@/app/pg-101/_components/animations"

export function CtaSection() {
  return (
    <section className="py-20 md:py-24">
      <div className="container mx-auto px-4">
        <motion.div
          {...SECTION_ANIM}
          className="relative overflow-hidden rounded-[2rem] border border-[#00DD55]/25 bg-black/45 backdrop-blur-xl p-10 md:p-14"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_0%,rgba(0,221,85,0.22),transparent_55%),radial-gradient(circle_at_80%_70%,rgba(34,221,102,0.14),transparent_55%)]" />
          <div className="relative text-center">
            <h3 className="text-3xl md:text-5xl font-black text-white">
              Build smarter parlays in <span className="text-neon-strong">60 seconds</span>
            </h3>
            <p className="mt-4 text-gray-300 max-w-2xl mx-auto text-lg">
              Get your 2 free parlays, see the confidence + EV logic, and start betting like a sharp.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href="/auth/signup"
                className="glow-neon inline-flex items-center justify-center gap-2 rounded-xl bg-[#00DD55] px-7 py-3.5 text-black font-black hover:bg-[#22DD66] transition-colors"
              >
                Start Free
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-white/5 border border-white/15 px-7 py-3.5 text-white font-semibold hover:bg-white/10 transition-colors"
              >
                See Plans
                <ArrowRight className="h-5 w-5 text-[#00DD55]" />
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}



