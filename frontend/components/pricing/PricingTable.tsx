"use client"

import { Check, X, Lock, CreditCard, Bitcoin } from "lucide-react"
import { motion } from "framer-motion"
import { 
  PRICING_FEATURES, 
  PREMIUM_LEMONSQUEEZY_URL, 
  PREMIUM_CRYPTO_URL,
  PREMIUM_PRICE_DISPLAY,
} from "@/lib/pricingConfig"
import { useAuth } from "@/lib/auth-context"
import { useRouter } from "next/navigation"

type PricingButtonLoadingKey =
  | "card-monthly"
  | "card-lifetime"
  | "crypto-monthly"
  | "crypto-annual"
  | "crypto-lifetime"
  | null

interface PricingTableProps {
  loadingKey?: PricingButtonLoadingKey
  onUpgradeCardMonthly?: () => void
  onUpgradeCardLifetime?: () => void
  onUpgradeCryptoMonthly?: () => void
  onUpgradeCryptoAnnual?: () => void
  onUpgradeCryptoLifetime?: () => void
}

export function PricingTable({
  loadingKey = null,
  onUpgradeCardMonthly,
  onUpgradeCardLifetime,
  onUpgradeCryptoMonthly,
  onUpgradeCryptoAnnual,
  onUpgradeCryptoLifetime,
}: PricingTableProps) {
  const { user } = useAuth()
  const router = useRouter()
  const isBusy = Boolean(loadingKey)

  const handleUpgradeCardMonthly = () => {
    if (onUpgradeCardMonthly) {
      onUpgradeCardMonthly()
      return
    }
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing")
      router.push("/auth/login")
      return
    }
    window.location.href = PREMIUM_LEMONSQUEEZY_URL
  }

  const handleUpgradeCryptoLifetime = () => {
    if (onUpgradeCryptoLifetime) {
      onUpgradeCryptoLifetime()
      return
    }
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing")
      router.push("/auth/login")
      return
    }
    window.location.href = PREMIUM_CRYPTO_URL
  }

  const renderValue = (value: string | boolean, isPremium: boolean = false, comingSoon: boolean = false) => {
    if (typeof value === "boolean") {
      return value ? (
        <Check className={`w-5 h-5 ${isPremium ? "text-emerald-400" : "text-white/60"}`} />
      ) : (
        <div className="flex items-center gap-1">
          <Lock className="w-4 h-4 text-gray-500" />
          <X className="w-4 h-4 text-gray-500" />
        </div>
      );
    }
    
    if (comingSoon || value === "Coming Soon") {
      return (
        <span className="px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-medium uppercase tracking-wide">
          Coming Soon
        </span>
      );
    }
    
    return (
      <span className={isPremium ? "text-emerald-300 font-medium" : "text-white/60"}>
        {value}
      </span>
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto pt-4" data-testid="pricing-table">
      {/* Table Container */}
      <div className="relative overflow-hidden rounded-2xl bg-black/25 border border-white/10 backdrop-blur-xl">
        {/* Accent glow */}
        <div className="absolute inset-0 opacity-35 pointer-events-none">
          <div className="absolute -top-24 -left-24 h-56 w-56 rounded-full bg-emerald-500/20 blur-3xl" />
          <div className="absolute -bottom-24 -right-24 h-56 w-56 rounded-full bg-cyan-500/15 blur-3xl" />
        </div>

        <div className="relative">
          {/* Header Row */}
          <div className="grid grid-cols-3 bg-gradient-to-r from-emerald-500/20 to-transparent">
            <div className="p-4 md:p-6">
              <span className="text-sm text-white/60 uppercase tracking-wider">Feature</span>
            </div>
            <div className="p-4 md:p-6 text-center border-l border-white/10">
              <span className="text-sm text-white/60 uppercase tracking-wider">Free</span>
              <div className="mt-1 text-xl font-bold text-white">$0</div>
            </div>
            <div className="p-4 md:p-6 text-center border-l border-emerald-500/20 bg-emerald-500/5 relative">
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10">
                <span 
                  className="px-3 py-1 text-xs font-bold text-black bg-[#00DD55] rounded-full whitespace-nowrap"
                  style={{
                    boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                  }}
                >
                  MOST POPULAR
                </span>
              </div>
              <span className="text-sm text-emerald-300 uppercase tracking-wider">Premium</span>
              <div className="mt-1 text-xl font-bold text-white">{PREMIUM_PRICE_DISPLAY}</div>
            </div>
          </div>

          {/* Feature Rows */}
          <div className="divide-y divide-white/10">
            {PRICING_FEATURES.filter((f) => f.key !== "price").map((feature, index) => (
              <motion.div
                key={feature.key}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="grid grid-cols-3 hover:bg-white/5 transition-colors"
              >
                {/* Feature Name */}
                <div className="p-3 md:p-4 flex items-center">
                  <span className="text-sm text-gray-300" title={feature.tooltip}>
                    {feature.label}
                  </span>
                </div>

                {/* Free Value */}
                <div className="p-3 md:p-4 flex items-center justify-center border-l border-white/10">
                  {renderValue(feature.free)}
                </div>

                {/* Premium Value */}
                <div className="p-3 md:p-4 flex items-center justify-center border-l border-emerald-500/20 bg-emerald-500/5">
                  {renderValue(feature.premium, true, feature.comingSoon)}
                </div>
              </motion.div>
            ))}
          </div>

          {/* CTA Row */}
          <div className="grid grid-cols-3 bg-gradient-to-r from-transparent via-emerald-500/10 to-emerald-500/20 border-t border-white/10">
            <div className="p-4 md:p-6">
              {/* Empty cell */}
            </div>
            <div className="p-4 md:p-6 flex items-center justify-center border-l border-white/10">
              <button
                onClick={() => router.push("/app")}
                disabled={isBusy}
                className="px-4 py-2 text-sm text-white/60 hover:text-white border border-white/15 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
              >
                Continue Free
              </button>
            </div>
            <div className="p-4 md:p-6 flex flex-col items-center gap-2 border-l border-emerald-500/20 bg-emerald-500/5">
              <button
                onClick={handleUpgradeCardMonthly}
                disabled={isBusy}
                className="w-full px-4 py-2.5 text-sm font-bold text-black bg-[#00DD55] rounded-lg hover:bg-[#22DD66] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                style={{
                  boxShadow: '0 0 6px #00DD55, 0 0 12px #00BB44'
                }}
              >
                <CreditCard className="w-4 h-4" />
                {loadingKey === "card-monthly" ? "Loading..." : "Monthly (Card)"}
              </button>

              {onUpgradeCardLifetime && (
                <button
                  onClick={onUpgradeCardLifetime}
                  disabled={isBusy}
                  className="w-full px-4 py-2 text-sm text-white border border-white/15 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CreditCard className="w-4 h-4" />
                  {loadingKey === "card-lifetime" ? "Loading..." : "Lifetime $500 (Card)"}
                </button>
              )}

              {(onUpgradeCryptoMonthly || onUpgradeCryptoAnnual || onUpgradeCryptoLifetime) && (
                <div className="w-full h-px bg-white/10 my-1" />
              )}

              {onUpgradeCryptoMonthly && (
                <button
                  onClick={onUpgradeCryptoMonthly}
                  disabled={isBusy}
                  className="w-full px-4 py-2 text-sm text-emerald-200 border border-white/15 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Bitcoin className="w-4 h-4" />
                  {loadingKey === "crypto-monthly" ? "Loading..." : "Monthly (Crypto)"}
                </button>
              )}

              {onUpgradeCryptoAnnual && (
                <button
                  onClick={onUpgradeCryptoAnnual}
                  disabled={isBusy}
                  className="w-full px-4 py-2 text-sm text-emerald-200 border border-white/15 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Bitcoin className="w-4 h-4" />
                  {loadingKey === "crypto-annual" ? "Loading..." : "Annual (Crypto)"}
                </button>
              )}

              <button
                onClick={handleUpgradeCryptoLifetime}
                disabled={isBusy}
                className="w-full px-4 py-2 text-sm text-emerald-200 border border-white/15 rounded-lg hover:bg-white/10 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Bitcoin className="w-4 h-4" />
                {loadingKey === "crypto-lifetime" ? "Loading..." : "Lifetime (Crypto)"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PricingTable

