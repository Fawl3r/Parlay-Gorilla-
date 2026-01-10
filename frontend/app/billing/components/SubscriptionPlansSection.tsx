"use client"

import { motion } from "framer-motion"
import { CheckCircle, Crown, Loader2, Zap } from "lucide-react"

import type { AccessStatus, SubscriptionPlan } from "./types"
import { PREMIUM_AI_PARLAYS_PER_PERIOD, PREMIUM_AI_PARLAYS_PERIOD_DAYS, PREMIUM_CUSTOM_PARLAYS_PER_PERIOD, PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS } from "@/lib/pricingConfig"

interface SubscriptionPlansSectionProps {
  subscriptionPlans: SubscriptionPlan[]
  accessStatus: AccessStatus | null
  purchaseLoading: string | null
  onSubscribe: (planId: string) => void
}

export function SubscriptionPlansSection({
  subscriptionPlans,
  accessStatus,
  purchaseLoading,
  onSubscribe,
}: SubscriptionPlansSectionProps) {
  return (
    <section id="subscriptions" className="mb-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Crown className="w-5 h-5 text-emerald-400" />
              Subscription Plans
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {PREMIUM_AI_PARLAYS_PER_PERIOD} Gorilla Parlays / {PREMIUM_AI_PARLAYS_PERIOD_DAYS} days •{" "}
              {PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} 🦍 Gorilla Parlay Builder 🦍/{PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days • premium tools
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {subscriptionPlans.map((plan, index) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * index }}
              className={`p-6 rounded-xl border relative ${
                plan.is_featured
                  ? "bg-gradient-to-br from-emerald-900/20 to-green-900/10 border-emerald-500/30"
                  : "bg-white/5 border-white/10"
              }`}
            >
              {plan.is_featured && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-emerald-500 text-black text-xs font-bold rounded-full">
                  MOST POPULAR
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <p className="text-sm text-gray-400 mt-1">{plan.description}</p>
              </div>

              <div className="mb-4">
                <div className="text-3xl font-black text-white">
                  ${plan.price}
                  {plan.period === "lifetime" ? (
                    <span className="text-lg text-gray-400 font-normal"> one-time</span>
                  ) : (
                  <span className="text-lg text-gray-400 font-normal">
                    /{plan.period === "yearly" ? "year" : "mo"}
                  </span>
                  )}
                </div>
                {plan.period === "yearly" && <div className="text-sm text-emerald-400">Save ~$80/year</div>}
                {plan.period === "lifetime" && (
                  <div className="text-sm text-emerald-400">Lifetime access • No renewals</div>
                )}
              </div>

              <div className="mb-6">
                <div className="flex items-center gap-2 text-sm text-gray-300 mb-2">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span className="font-medium">
                    {plan.daily_parlay_limit && plan.daily_parlay_limit > 0
                      ? `${plan.daily_parlay_limit} parlays/day`
                      : `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`}
                  </span>
                </div>
                <ul className="space-y-2">
                  {plan.features.slice(0, 5).map((feature, i) => (
                    <li key={i} className="flex items-center gap-2 text-sm text-gray-400">
                      <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => onSubscribe(plan.id)}
                disabled={purchaseLoading !== null || accessStatus?.subscription.active}
                className={`w-full py-3 rounded-lg font-bold transition-all ${
                  plan.is_featured
                    ? "bg-emerald-500 text-black hover:bg-emerald-400"
                    : "bg-white/10 text-white hover:bg-white/20"
                } disabled:opacity-50`}
              >
                {purchaseLoading === plan.id ? (
                  <Loader2 className="w-4 h-4 animate-spin mx-auto" />
                ) : accessStatus?.subscription.active ? (
                  "Currently Subscribed"
                ) : plan.period === "lifetime" ? (
                  "Get Lifetime Access"
                ) : (
                  "Subscribe"
                )}
              </button>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  )
}


