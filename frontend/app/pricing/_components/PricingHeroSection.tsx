"use client"

import { motion } from "framer-motion"
import Image from "next/image"
import Link from "next/link"
import { Crown, Sparkles, Coins } from "lucide-react"

import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_PRICE_DISPLAY } from "@/lib/pricingConfig"

type Props = {
  subscriptionsAnchorId: string
  creditsAnchorId: string
}

export function PricingHeroSection({ subscriptionsAnchorId, creditsAnchorId }: Props) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
      className="grid gap-8 lg:grid-cols-[1.1fr,0.9fr] items-center"
    >
      <div>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-black/30 border border-white/10 text-gray-200 text-sm backdrop-blur">
          <Crown className="h-4 w-4 text-emerald-400" />
          Pricing
        </div>

        <h1 className="text-4xl md:text-5xl font-black mt-4 mb-3 leading-tight">
          <span className="text-white">Simple </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
            Pricing
          </span>
        </h1>

        <p className="text-gray-200/80 max-w-2xl leading-relaxed">
          Start free and explore AI-assisted sports analytics. Upgrade when you want deeper context, more tools, and fewer limits.
        </p>

        <div className="mt-5 flex flex-wrap gap-2">
          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
            <Sparkles className="h-4 w-4 text-emerald-400" />
            {PREMIUM_AI_PARLAYS_PER_PERIOD} AI parlays / {PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (Premium)
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
            <Sparkles className="h-4 w-4 text-cyan-300" />
            Live insights + alerts
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-black/25 border border-white/10 text-gray-200 text-xs backdrop-blur">
            <Sparkles className="h-4 w-4 text-emerald-300" />
            No hype, just tools
          </div>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link
            href={`#${subscriptionsAnchorId}`}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 text-black font-bold hover:bg-emerald-400 transition-colors"
          >
            Upgrade
            <Crown className="h-4 w-4" />
          </Link>

          <Link
            href={`#${creditsAnchorId}`}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl border border-white/15 bg-black/20 text-white font-semibold hover:bg-white/10 transition-colors"
          >
            Buy Credits
            <Coins className="h-4 w-4 text-amber-300" />
          </Link>
        </div>

        <p className="mt-4 text-sm text-gray-200/70">
          Premium starts at{" "}
          <span className="text-emerald-300 font-semibold">{PREMIUM_PRICE_DISPLAY}</span>. Card plans auto-renew until canceled;
          crypto plans do not auto-renew.
        </p>

        <p className="mt-2 text-xs text-gray-200/60">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-emerald-300 hover:text-emerald-200 hover:underline">
            Sign in
          </Link>
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.45, delay: 0.1 }}
        className="relative"
      >
        <div className="relative aspect-[4/3] w-full overflow-hidden rounded-3xl border border-emerald-500/25 bg-black/30 backdrop-blur shadow-[0_0_40px_rgba(0,221,85,0.10)]">
          <Image
            src="/images/hero.png"
            alt="Parlay Gorilla pricing"
            fill
            className="object-cover"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-tr from-black/55 via-transparent to-black/10" />
        </div>
      </motion.div>
    </motion.section>
  )
}


