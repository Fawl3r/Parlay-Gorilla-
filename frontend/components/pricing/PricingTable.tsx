"use client";

import { Check, X, Lock, CreditCard, Bitcoin } from "lucide-react";
import { motion } from "framer-motion";
import { 
  PRICING_FEATURES, 
  PREMIUM_LEMONSQUEEZY_URL, 
  PREMIUM_CRYPTO_URL,
  PREMIUM_PRICE_DISPLAY,
} from "@/lib/pricingConfig";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";

interface PricingTableProps {
  onUpgradeCard?: () => void;
  onUpgradeCrypto?: () => void;
}

export function PricingTable({ onUpgradeCard, onUpgradeCrypto }: PricingTableProps) {
  const { user } = useAuth();
  const router = useRouter();

  const handleUpgradeCard = () => {
    if (onUpgradeCard) {
      onUpgradeCard();
    } else if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing");
      router.push("/auth/login");
    } else {
      window.location.href = PREMIUM_LEMONSQUEEZY_URL;
    }
  };

  const handleUpgradeCrypto = () => {
    if (onUpgradeCrypto) {
      onUpgradeCrypto();
    } else if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing");
      router.push("/auth/login");
    } else {
      window.location.href = PREMIUM_CRYPTO_URL;
    }
  };

  const renderValue = (value: string | boolean, isPremium: boolean = false) => {
    if (typeof value === "boolean") {
      return value ? (
        <Check className={`w-5 h-5 ${isPremium ? "text-emerald-400" : "text-gray-400"}`} />
      ) : (
        <div className="flex items-center gap-1">
          <Lock className="w-4 h-4 text-gray-500" />
          <X className="w-4 h-4 text-gray-500" />
        </div>
      );
    }
    return (
      <span className={isPremium ? "text-emerald-400 font-medium" : "text-gray-400"}>
        {value}
      </span>
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Table Container */}
      <div className="overflow-hidden rounded-2xl border border-emerald-900/30 bg-[#0a0a0f]/80 backdrop-blur-xl">
        {/* Header Row */}
        <div className="grid grid-cols-3 bg-gradient-to-r from-emerald-900/20 to-transparent">
          <div className="p-4 md:p-6">
            <span className="text-sm text-gray-400 uppercase tracking-wider">Feature</span>
          </div>
          <div className="p-4 md:p-6 text-center border-l border-emerald-900/20">
            <span className="text-sm text-gray-400 uppercase tracking-wider">Free</span>
            <div className="mt-1 text-xl font-bold text-white">$0</div>
          </div>
          <div className="p-4 md:p-6 text-center border-l border-emerald-500/30 bg-emerald-500/5 relative">
            {/* Popular Badge */}
            <div className="absolute -top-0 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <span className="px-3 py-1 text-xs font-bold text-black bg-gradient-to-r from-emerald-400 to-green-400 rounded-full">
                MOST POPULAR
              </span>
            </div>
            <span className="text-sm text-emerald-400 uppercase tracking-wider">Premium</span>
            <div className="mt-1 text-xl font-bold text-white">{PREMIUM_PRICE_DISPLAY}</div>
          </div>
        </div>

        {/* Feature Rows */}
        <div className="divide-y divide-emerald-900/20">
          {PRICING_FEATURES.filter(f => f.key !== "price").map((feature, index) => (
            <motion.div
              key={feature.key}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.03 }}
              className="grid grid-cols-3 hover:bg-emerald-900/5 transition-colors"
            >
              {/* Feature Name */}
              <div className="p-3 md:p-4 flex items-center">
                <span className="text-sm text-gray-300" title={feature.tooltip}>
                  {feature.label}
                </span>
              </div>

              {/* Free Value */}
              <div className="p-3 md:p-4 flex items-center justify-center border-l border-emerald-900/20">
                {renderValue(feature.free)}
              </div>

              {/* Premium Value */}
              <div className="p-3 md:p-4 flex items-center justify-center border-l border-emerald-500/30 bg-emerald-500/5">
                {renderValue(feature.premium, true)}
              </div>
            </motion.div>
          ))}
        </div>

        {/* CTA Row */}
        <div className="grid grid-cols-3 bg-gradient-to-r from-transparent via-emerald-900/10 to-emerald-900/20 border-t border-emerald-900/30">
          <div className="p-4 md:p-6">
            {/* Empty cell */}
          </div>
          <div className="p-4 md:p-6 flex items-center justify-center border-l border-emerald-900/20">
            <button
              onClick={() => router.push("/app")}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white border border-gray-600 rounded-lg hover:border-gray-400 transition-colors"
            >
              Continue Free
            </button>
          </div>
          <div className="p-4 md:p-6 flex flex-col items-center gap-2 border-l border-emerald-500/30 bg-emerald-500/5">
            <button
              onClick={handleUpgradeCard}
              className="w-full px-4 py-2.5 text-sm font-bold text-black bg-gradient-to-r from-emerald-400 to-green-400 rounded-lg hover:from-emerald-300 hover:to-green-300 transition-all flex items-center justify-center gap-2"
            >
              <CreditCard className="w-4 h-4" />
              Upgrade with Card
            </button>
            <button
              onClick={handleUpgradeCrypto}
              className="w-full px-4 py-2 text-sm text-emerald-400 border border-emerald-500/50 rounded-lg hover:bg-emerald-500/10 transition-colors flex items-center justify-center gap-2"
            >
              <Bitcoin className="w-4 h-4" />
              Upgrade with Crypto
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default PricingTable;

