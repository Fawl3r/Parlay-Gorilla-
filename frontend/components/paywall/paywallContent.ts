import { Crown, DollarSign, Shield, Sparkles, Target, TrendingUp, Zap } from "lucide-react"

import {
  CREDITS_COST_CUSTOM_BUILDER_ACTION,
  INSCRIPTION_COST_USD,
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
  PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS,
} from "@/lib/pricingConfig"

export type PaywallReason =
  | "ai_parlay_limit_reached"
  | "pay_per_use_required"
  | "feature_premium_only"
  | "custom_builder_locked"
  | "upset_finder_locked"
  | "login_required"

export const PAYWALL_REASON_CONTENT: Record<
  PaywallReason,
  { title: string; subtitle: string; icon: typeof Crown }
> = {
  ai_parlay_limit_reached: {
    title: "You’ve Hit Your Limit",
    subtitle: "Buy credits, purchase a single parlay, or upgrade to Premium to keep going.",
    icon: Zap,
  },
  pay_per_use_required: {
    title: "Need More Parlays?",
    subtitle: "Purchase a single parlay, buy credits, or upgrade to Premium.",
    icon: DollarSign,
  },
  feature_premium_only: {
    title: "Premium Feature",
    subtitle: "This feature is available with Gorilla Premium.",
    icon: Crown,
  },
  custom_builder_locked: {
    title: "Custom Builder Requires Premium",
    subtitle: `Use credits (${CREDITS_COST_CUSTOM_BUILDER_ACTION} per AI action) or upgrade to Premium for included access.`,
    icon: Target,
  },
  upset_finder_locked: {
    title: "Unlock the Upset Finder",
    subtitle: "Find plus-money underdogs with positive expected value.",
    icon: TrendingUp,
  },
  login_required: {
    title: "Login Required",
    subtitle: "Create a free account to use this feature.",
    icon: Shield,
  },
}

export const PAYWALL_PREMIUM_BENEFITS = [
  {
    icon: Zap,
    title: `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI Parlays`,
    description: `${PREMIUM_AI_PARLAYS_PER_PERIOD} AI generations per ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling)`,
  },
  {
    icon: Target,
    title: "Custom Parlay Builder",
    description: `Build your own parlays with AI-powered analysis (${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} per ${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days)`,
  },
  {
    icon: Shield,
    title: "On-chain Verification (optional)",
    description: `Opt-in per Custom AI parlay. Costs $${INSCRIPTION_COST_USD.toFixed(2)} when you choose it.`,
  },
  {
    icon: TrendingUp,
    title: "Gorilla Upset Finder",
    description: "Discover +EV underdogs the market is undervaluing",
  },
  {
    icon: Sparkles,
    title: "Multi-Sport Mixing",
    description: "Cross-sport parlays with smart correlation handling",
  },
]


