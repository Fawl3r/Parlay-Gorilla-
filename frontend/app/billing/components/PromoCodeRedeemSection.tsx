"use client"

import { useState } from "react"
import { Gift, Loader2 } from "lucide-react"
import { toast } from "sonner"

import { api } from "@/lib/api"

type PromoRewardType = "premium_month" | "credits_3"

interface PromoCodeRedeemResponse {
  success: boolean
  reward_type: PromoRewardType
  message: string
  credits_added?: number
  new_credit_balance?: number | null
  premium_until?: string | null
}

interface PromoCodeRedeemSectionProps {
  onRedeemed?: () => Promise<void> | void
}

export function PromoCodeRedeemSection({ onRedeemed }: PromoCodeRedeemSectionProps) {
  const [code, setCode] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleRedeem() {
    const normalized = code.trim().toUpperCase()
    if (!normalized) {
      toast.error("Enter a promo code")
      return
    }

    try {
      setLoading(true)
      const res = await api.post("/api/promo-codes/redeem", { code: normalized })
      const data = res.data as PromoCodeRedeemResponse

      toast.success(data.message || "Promo code redeemed")
      setCode("")
      await onRedeemed?.()
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      toast.error(detail || err?.message || "Failed to redeem code")
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="mb-8">
      <div className="p-5 rounded-xl bg-white/5 border border-white/10">
        <div className="flex items-center gap-2 mb-3">
          <Gift className="w-5 h-5 text-purple-400" />
          <h2 className="font-medium text-white">Promo Code</h2>
        </div>
        <p className="text-sm text-gray-400 mb-4">
          Have a code from Parlay Gorilla? Enter it here to unlock premium time or free AI generations.
        </p>

        <div className="flex flex-col md:flex-row gap-3">
          <input
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter code (e.g., PG1M-ABCD-EFGH)"
            className="flex-1 bg-[#0a0a0f] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30"
          />
          <button
            onClick={handleRedeem}
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            Redeem
          </button>
        </div>
      </div>
    </section>
  )
}


