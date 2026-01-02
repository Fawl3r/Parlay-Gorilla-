"use client";

import { motion } from "framer-motion";
import { Award, Target, TrendingUp, Trophy } from "lucide-react";

import type { AffiliateTier } from "../types";

const TIER_ICONS: Record<string, typeof Trophy> = {
  rookie: Target,
  pro: TrendingUp,
  all_star: Award,
  hall_of_fame: Trophy,
};

export type AffiliateTiersSectionProps = {
  tiers: AffiliateTier[];
};

export function AffiliateTiersSection({ tiers }: AffiliateTiersSectionProps) {
  return (
    <section id="tiers" className="py-16 md:py-20 bg-black/30 border-y border-white/5">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-black text-white mb-4">Commission tiers</h2>
          <p className="text-gray-400 max-w-2xl mx-auto">
            Start as a Rookie and climb the ranks. As your referrals grow, your commission rates automatically
            upgrade.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {tiers.map((tier, index) => {
            const TierIcon = TIER_ICONS[tier.tier] || Target;
            const isTopTier = tier.tier === "hall_of_fame";

            return (
              <motion.div
                key={tier.tier}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={`p-6 rounded-xl border relative ${
                  isTopTier
                    ? "bg-gradient-to-br from-[#00FF5E]/15 to-black/30 border-[#00FF5E]/30"
                    : "bg-black/35 border-white/10"
                }`}
              >
                {isTopTier && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-[#00FF5E] text-black text-xs font-black rounded-full">
                    HALL OF FAME
                  </div>
                )}

                <div
                  className="w-12 h-12 rounded-full flex items-center justify-center mb-4"
                  style={{ backgroundColor: `${tier.badge_color}20` }}
                >
                  <TierIcon className="w-6 h-6" style={{ color: tier.badge_color }} />
                </div>

                <h3 className="text-xl font-bold text-white mb-1">{tier.name}</h3>
                <p className="text-sm text-gray-400 mb-4">
                  {tier.revenue_threshold === 0 ? "Starting tier" : `$${tier.revenue_threshold.toLocaleString()}+ referred`}
                </p>

                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">First Sub</span>
                    <span className="font-black text-[#00FF5E]">
                      {(tier.commission_rate_sub_first * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Recurring</span>
                    <span className="font-black text-[#00FF5E]">
                      {(tier.commission_rate_sub_recurring * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-400">Credit Packs</span>
                    <span className="font-black text-emerald-200">
                      {(tier.commission_rate_credits * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}



