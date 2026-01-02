"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { AlertTriangle } from "lucide-react"

export function LandingDisclaimerSection() {
  return (
    <section className="py-8 border-t-2 border-amber-500/30 bg-[#0A0F0A]/80 backdrop-blur-sm">
      <div className="container mx-auto px-4 max-w-5xl">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="p-4 bg-amber-500/10 border border-amber-500/40 rounded-lg backdrop-blur-sm"
        >
          <div className="flex items-start gap-2.5">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-amber-400 font-bold text-sm mb-1.5">
                Not a Sportsbook • Analytics & Research Only
              </p>
              <p className="text-xs text-white/80 leading-relaxed mb-2">
                Parlay Gorilla provides AI-assisted sports analytics and informational insights for research purposes. 
                We do not accept bets, facilitate wagering, or act as a sportsbook. All analysis, probability estimates, 
                and scenarios are hypothetical and for informational/entertainment purposes only.
              </p>
              <div className="flex flex-wrap items-center gap-2 text-[10px] text-white/70">
                <span className="font-semibold text-white">18+ only</span>
                <span>•</span>
                <Link 
                  href="/disclaimer" 
                  className="text-amber-300 hover:text-amber-200 hover:underline font-medium"
                >
                  Full Disclaimer
                </Link>
                <span>•</span>
                <Link 
                  href="/terms" 
                  className="text-amber-300 hover:text-amber-200 hover:underline font-medium"
                >
                  Terms of Service
                </Link>
                <span>•</span>
                <a 
                  href="tel:1-800-522-4700" 
                  className="text-amber-300 hover:text-amber-200 hover:underline font-medium"
                >
                  Problem Gambling Help: 1-800-522-4700
                </a>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

