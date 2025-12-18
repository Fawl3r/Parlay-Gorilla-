"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { Coins, Crown, Gift } from "lucide-react"

import type { AccessStatus } from "./types"

interface AccessStatusCardsProps {
  accessStatus: AccessStatus
}

export function AccessStatusCards({ accessStatus }: AccessStatusCardsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8"
    >
      {/* Free Parlays */}
      <div className="p-5 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-2 mb-3">
          <Gift className="w-5 h-5 text-purple-400" />
          <span className="font-medium text-white">Free Parlays</span>
        </div>
        <div className="text-3xl font-black text-white mb-1">
          {accessStatus.free.remaining}
          <span className="text-lg text-gray-400"> / {accessStatus.free.total}</span>
        </div>
        <p className="text-sm text-gray-400">Lifetime free parlays remaining</p>
      </div>

      {/* Subscription */}
      <div
        className={`p-5 rounded-xl border ${
          accessStatus.subscription.active
            ? "bg-emerald-900/20 border-emerald-500/30"
            : "bg-white/5 border-white/10"
        }`}
      >
        <div className="flex items-center gap-2 mb-3">
          <Crown className="w-5 h-5 text-emerald-400" />
          <span className="font-medium text-white">Subscription</span>
        </div>
        {accessStatus.subscription.active ? (
          <>
            <div className="text-3xl font-black text-emerald-400 mb-1">
              {accessStatus.subscription.remaining_today}
              <span className="text-lg text-gray-400">
                {" "}
                / {accessStatus.subscription.daily_limit}
              </span>
            </div>
            <p className="text-sm text-gray-400">
              Daily parlays remaining • {accessStatus.subscription.plan?.replace("_", " ")}
            </p>
          </>
        ) : (
          <>
            <div className="text-xl font-bold text-gray-400 mb-1">No Active Plan</div>
            <Link href="#subscriptions" className="text-sm text-emerald-400 hover:underline">
              Subscribe for unlimited access →
            </Link>
          </>
        )}
      </div>

      {/* Credits */}
      <div className="p-5 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-2 mb-3">
          <Coins className="w-5 h-5 text-amber-400" />
          <span className="font-medium text-white">Credits</span>
        </div>
        <div className="text-3xl font-black text-amber-400 mb-1">{accessStatus.credits.balance}</div>
        <p className="text-sm text-gray-400">
          {accessStatus.credits.standard_cost} credit = 1 standard parlay
        </p>
      </div>
    </motion.div>
  )
}


