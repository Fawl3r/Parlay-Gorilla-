"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Crown } from "lucide-react"

type Props = {
  plansAnchorId: string
}

export function PricingFinalCtaSection({ plansAnchorId }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35 }}
      className="rounded-3xl border border-emerald-500/25 bg-gradient-to-br from-emerald-900/15 to-cyan-900/10 p-6"
    >
      <div className="flex items-start gap-3">
        <div className="rounded-xl bg-emerald-500/15 p-2">
          <Crown className="h-5 w-5 text-emerald-300" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl md:text-2xl font-black text-white">Ready to upgrade?</h2>
          <p className="mt-1 text-sm text-gray-200/75">
            Cancel any time (Credit Card) and keep access through your billing period. Crypto plans are time-based and renew
            manually.
          </p>

          <div className="mt-4 flex flex-wrap gap-2">
            <Link
              href={`#${plansAnchorId}`}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-5 py-3 font-bold text-black hover:bg-emerald-400 transition-colors"
            >
              See plans
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/billing"
              className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-black/20 px-5 py-3 font-semibold text-white hover:bg-white/10 transition-colors"
            >
              Billing details
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </div>
    </motion.section>
  )
}
