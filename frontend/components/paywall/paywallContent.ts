import { Crown, DollarSign, Shield, Sparkles, Target, TrendingUp, Zap } from "lucide-react"

import {
  CREDITS_COST_CUSTOM_BUILDER_ACTION,
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
  PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS,
} from "@/lib/pricingConfig"
import { getCopy } from "@/lib/content"

export type PaywallReason =
  | "ai_parlay_limit_reached"
  | "pay_per_use_required"
  | "feature_premium_only"
  | "custom_builder_locked"
  | "inscriptions_overage"
  | "upset_finder_locked"
  | "login_required"

export const PAYWALL_REASON_CONTENT: Record<
  PaywallReason,
  { title: string; subtitle: string; icon: typeof Crown }
> = {
  ai_parlay_limit_reached: {
    title: getCopy("paywall.aiParlayLimit.title"),
    subtitle: getCopy("paywall.aiParlayLimit.subtitle"),
    icon: Zap,
  },
  pay_per_use_required: {
    title: getCopy("paywall.payPerUse.title"),
    subtitle: getCopy("paywall.payPerUse.subtitle"),
    icon: DollarSign,
  },
  feature_premium_only: {
    title: getCopy("paywall.featurePremium.title"),
    subtitle: getCopy("paywall.featurePremium.subtitle"),
    icon: Crown,
  },
  custom_builder_locked: {
    title: getCopy("paywall.customBuilder.title"),
    subtitle: getCopy("paywall.customBuilder.subtitle").replace("{credits}", String(CREDITS_COST_CUSTOM_BUILDER_ACTION)),
    icon: Target,
  },
  inscriptions_overage: {
    title: getCopy("paywall.inscriptions.title"),
    subtitle: getCopy("paywall.inscriptions.subtitle"),
    icon: Shield,
  },
  upset_finder_locked: {
    title: getCopy("paywall.upsetFinder.title"),
    subtitle: getCopy("paywall.upsetFinder.subtitle"),
    icon: TrendingUp,
  },
  login_required: {
    title: getCopy("paywall.loginRequired.title"),
    subtitle: getCopy("paywall.loginRequired.subtitle"),
    icon: Shield,
  },
}

export const PAYWALL_PREMIUM_BENEFITS = [
  {
    icon: Zap,
    title: getCopy("paywall.benefits.0.title"),
    description: getCopy("paywall.benefits.0.description")
      .replace("{count}", String(PREMIUM_AI_PARLAYS_PER_PERIOD))
      .replace("{days}", String(PREMIUM_AI_PARLAYS_PERIOD_DAYS)),
  },
  {
    icon: Target,
    title: getCopy("paywall.benefits.1.title"),
    description: getCopy("paywall.benefits.1.description")
      .replace("{count}", String(PREMIUM_CUSTOM_PARLAYS_PER_PERIOD))
      .replace("{days}", String(PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS)),
  },
  {
    icon: Shield,
    title: getCopy("paywall.benefits.2.title"),
    description: getCopy("paywall.benefits.2.description"),
  },
  {
    icon: Target,
    title: getCopy("paywall.benefits.3.title"),
    description: getCopy("paywall.benefits.3.description"),
  },
  {
    icon: TrendingUp,
    title: getCopy("paywall.benefits.4.title"),
    description: getCopy("paywall.benefits.4.description"),
  },
  {
    icon: Sparkles,
    title: getCopy("paywall.benefits.5.title"),
    description: getCopy("paywall.benefits.5.description"),
  },
]


