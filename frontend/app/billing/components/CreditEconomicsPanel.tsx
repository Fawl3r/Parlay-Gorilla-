"use client"

import { motion } from "framer-motion"
import { Coins, Sparkles, CreditCard, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { CheckoutProvider, CreditPack } from "./types"

interface CreditEconomicsPanelProps {
  creditPacks: CreditPack[]
  purchaseLoading: string | null
  onBuy: (packId: string, provider: CheckoutProvider) => void
  isEmailVerified: boolean
  className?: string
}

function bestValuePack(packs: CreditPack[]): CreditPack | null {
  if (!packs.length) return null
  return packs.reduce((best, p) =>
    p.price_per_credit < best.price_per_credit ? p : best
  )
}

export function CreditEconomicsPanel({
  creditPacks,
  purchaseLoading,
  onBuy,
  isEmailVerified,
  className,
}: CreditEconomicsPanelProps) {
  const best = bestValuePack(creditPacks)

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className={cn("rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6", className)}
    >
      <div className="flex items-center gap-2 mb-2">
        <Sparkles className="h-5 w-5 text-[#00FF5E]" />
        <h2 className="text-lg font-black text-white">Optimize Your AI Power</h2>
      </div>
      <p className="text-sm text-white/78 mb-6">
        Credit packs give you more AI parlays and builder usage. Better value on larger packs.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {creditPacks.map((pack, index) => {
          const isBest = best?.id === pack.id
          const isRecommended = pack.is_featured || isBest
          const loading = purchaseLoading === `${pack.id}:stripe`

          return (
            <motion.div
              key={pack.id}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index }}
              whileHover={{ y: -3 }}
              className={cn(
                "relative rounded-xl border p-5 transition-shadow overflow-hidden",
                isRecommended && "pt-10",
                isRecommended
                  ? "bg-gradient-to-br from-[#00FF5E]/10 to-emerald-900/10 border-[#00FF5E]/25 shadow-[0_0_20px_-8px_rgba(0,255,94,0.3)]"
                  : "bg-white/[0.04] border-white/10 hover:border-white/20"
              )}
            >
              {isRecommended && (
                <div className="absolute top-3 left-1/2 -translate-x-1/2 px-2.5 py-1 rounded-full bg-[#00FF5E]/20 border border-[#00FF5E]/40 text-[#00FF5E] text-xs font-bold uppercase tracking-wide whitespace-nowrap">
                  Best for your usage pattern
                </div>
              )}
              {pack.bonus_credits > 0 && (
                <div
                  className={cn(
                    "absolute right-3 px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 text-xs font-semibold",
                    isRecommended ? "top-10" : "top-3"
                  )}
                >
                  +{pack.bonus_credits} bonus
                </div>
              )}
              <div
                className={cn(
                  "flex items-center gap-2 mb-3 min-h-[2rem]",
                  pack.bonus_credits > 0 && "pr-24"
                )}
              >
                <Coins className="h-5 w-5 text-amber-400 shrink-0" />
                <span className="text-2xl font-black text-white">{pack.total_credits}</span>
                <span className="text-sm text-white/70">credits</span>
              </div>
              <div className="mb-3">
                <span className="text-xl font-bold text-white">${pack.price.toFixed(2)}</span>
                <span className="text-xs text-white/70 ml-1">${pack.price_per_credit.toFixed(2)}/credit</span>
              </div>
              {!isEmailVerified && (
                <p className="text-xs text-amber-400 mb-2">Verify email to purchase</p>
              )}
              <button
                onClick={() => onBuy(pack.id, "stripe")}
                disabled={purchaseLoading !== null || !isEmailVerified}
                className={cn(
                  "w-full py-2.5 rounded-lg font-bold text-sm flex items-center justify-center gap-2 transition-all",
                  isRecommended
                    ? "bg-[#00FF5E] text-black hover:bg-[#00FF5E]/90"
                    : "bg-white/10 text-white hover:bg-white/15"
                )}
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <CreditCard className="h-4 w-4" />
                    Get credits
                  </>
                )}
              </button>
            </motion.div>
          )
        })}
      </div>
    </motion.section>
  )
}
