"use client"

import { motion } from "framer-motion"
import { Coins, CreditCard, Loader2 } from "lucide-react"

import type { CheckoutProvider, CreditPack } from "./types"

interface CreditPacksSectionProps {
  creditPacks: CreditPack[]
  purchaseLoading: string | null
  onBuy: (packId: string, provider: CheckoutProvider) => void
  isEmailVerified: boolean
}

function isLoading(purchaseLoading: string | null, packId: string, provider: CheckoutProvider) {
  return purchaseLoading === `${packId}:${provider}`
}

export function CreditPacksSection({ creditPacks, purchaseLoading, onBuy, isEmailVerified }: CreditPacksSectionProps) {
  return (
    <section id="credits" className="mb-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Coins className="w-5 h-5 text-amber-400" />
              Credit Packs
            </h2>
            <p className="text-sm text-gray-400 mt-1">Pay per use — no subscription required</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {creditPacks.map((pack, index) => (
            <motion.div
              key={pack.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
              className={`p-5 rounded-xl border relative ${
                pack.is_featured
                  ? "bg-gradient-to-br from-amber-900/20 to-yellow-900/10 border-amber-500/30"
                  : "bg-white/5 border-white/10"
              }`}
            >
              {pack.is_featured && (
                <div className="absolute -top-2 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-amber-500 text-black text-xs font-bold rounded-full">
                  BEST VALUE
                </div>
              )}

              <div className="text-center mb-4">
                <div className="text-3xl font-black text-white mb-1">{pack.total_credits}</div>
                <div className="text-sm text-gray-400">credits</div>
                {pack.bonus_credits > 0 && (
                  <div className="text-xs text-emerald-400 mt-1">+{pack.bonus_credits} bonus credits!</div>
                )}
              </div>

              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-amber-400">${pack.price.toFixed(2)}</div>
                <div className="text-xs text-gray-500">${pack.price_per_credit.toFixed(2)} per credit</div>
              </div>

              <div className="space-y-2">
                {!isEmailVerified && (
                  <div className="text-xs text-amber-400 mb-2 text-center">
                    Verify your email to purchase
                  </div>
                )}
                <button
                  onClick={() => onBuy(pack.id, "stripe")}
                  disabled={purchaseLoading !== null || !isEmailVerified}
                  className={`w-full py-2 rounded-lg font-bold text-sm transition-all flex items-center justify-center gap-2 ${
                    pack.is_featured
                      ? "bg-amber-500 text-black hover:bg-amber-400"
                      : "bg-white/10 text-white hover:bg-white/20"
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {isLoading(purchaseLoading, pack.id, "stripe") ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      <CreditCard className="w-4 h-4" />
                      Pay with Card
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  )
}


