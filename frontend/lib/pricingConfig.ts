/**
 * Pricing Configuration for Parlay Gorilla
 * 
 * Central place for all pricing-related constants and URLs.
 * Used by PricingTable and PricingPage components.
 */

// Price display string
export const PREMIUM_PRICE_DISPLAY = "$39.99 / month";
export const PREMIUM_PRICE_CENTS = 3999;

// Usage limits & credit costs (must match backend settings)
export const PREMIUM_AI_PARLAYS_PER_PERIOD = 100;
export const PREMIUM_AI_PARLAYS_PERIOD_DAYS = 30;
export const PREMIUM_CUSTOM_PARLAYS_PER_PERIOD = 25;
export const PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS = 30;
export const PREMIUM_INSCRIPTIONS_PER_PERIOD = 15;
export const PREMIUM_INSCRIPTIONS_PERIOD_DAYS = 30;
export const CREDITS_COST_AI_PARLAY = 3;
export const CREDITS_COST_CUSTOM_BUILDER_ACTION = 3;
export const CREDITS_COST_INSCRIPTION = 1;
export const INSCRIPTION_COST_USD = 0.37;
export const INSCRIPTION_REQUIRES_MANUAL_OPT_IN = true;

// Payment URLs - fallback to pricing page if not configured
export const PREMIUM_LEMONSQUEEZY_URL = 
  process.env.NEXT_PUBLIC_PREMIUM_LEMONSQUEEZY_URL || "/pricing";
export const PREMIUM_CRYPTO_URL = 
  process.env.NEXT_PUBLIC_PREMIUM_CRYPTO_URL || "/pricing";

// Feature definitions for pricing table
export interface PricingFeature {
  key: string;
  label: string;
  free: string | boolean;
  premium: string | boolean;
  tooltip?: string;
  comingSoon?: boolean;
}

export const PRICING_FEATURES: PricingFeature[] = [
  {
    key: "price",
    label: "Price",
    free: "$0",
    premium: PREMIUM_PRICE_DISPLAY,
  },
  {
    key: "max_parlays",
    label: "AI Parlays",
    free: "3 / day",
    premium: `${PREMIUM_AI_PARLAYS_PER_PERIOD} / ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days`,
    tooltip: "Gorilla Parlay generations (free resets daily; premium resets on a rolling window)",
  },
  {
    key: "confidence",
    label: "Confidence Meter",
    free: "Basic",
    premium: "Full",
    tooltip: "See detailed confidence breakdowns for each leg",
  },
  {
    key: "ai_explanations",
    label: "AI Explanations",
    free: "Basic",
    premium: "Full analyst mode",
    tooltip: "Get detailed AI analysis of your parlay picks",
  },
  {
    key: "live_scores",
    label: "Live Scores",
    free: true,
    premium: true,
    tooltip: "Real-time score updates",
  },
  {
    key: "drive_tracking",
    label: "Drive-by-Drive Details",
    free: "Limited",
    premium: "Full",
    tooltip: "Detailed play-by-play for NFL games",
  },
  {
    key: "ai_insights",
    label: "AI Live Insights",
    free: false,
    premium: true,
    tooltip: "Real-time AI analysis during live games",
  },
  {
    key: "telegram_alerts",
    label: "Telegram Alerts",
    free: false,
    premium: "Coming Soon",
    tooltip: "Get instant notifications for scoring plays and game updates",
    comingSoon: true,
  },
  {
    key: "parlay_tips",
    label: "Insights & Guidance",
    free: "Basic",
    premium: "Personalized + AI",
    tooltip: "Get AI-tailored insights based on your preferences",
  },
  {
    key: "history",
    label: "Parlay History",
    free: "Recent only",
    premium: "Full + filters",
    tooltip: "Track your complete betting history",
  },
  {
    key: "roi_tracking",
    label: "Performance Tracking",
    free: false,
    premium: true,
    tooltip: "Track your performance over time",
  },
  {
    key: "badges",
    label: "Achievement Badges",
    free: "Basic",
    premium: "All + premium-only",
    tooltip: "Unlock special badges as you use Parlay Gorilla",
  },
  {
    key: "custom_builder",
    label: "Custom Parlay Builder",
    free: false,
    premium: `${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} / ${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days`,
    tooltip: "Build your own custom parlays",
  },
  {
    key: "on_chain_verification",
    label: "Verification (optional)",
    free: false,
    premium: true,
    tooltip: `Opt-in per Custom AI parlay. Creates a permanent, time-stamped proof.`,
  },
  {
    key: "upset_finder",
    label: "Upset Finder (value signals)",
    free: false,
    premium: true,
    tooltip: "Find underdog opportunities using value signals",
  },
  {
    key: "multi_sport",
    label: "Multi-Sport Mixing",
    free: false,
    premium: true,
    tooltip: "Combine picks from different sports",
  },
  {
    key: "support",
    label: "Support",
    free: "Basic",
    premium: "Priority",
    tooltip: "Get faster support response times",
  },
  {
    key: "ads",
    label: "Ads",
    free: "Light",
    premium: "None",
    tooltip: "Ad-free experience for premium users",
  },
];

// Feature highlight cards for pricing page
export interface FeatureHighlight {
  title: string;
  description: string;
  isPremium: boolean;
  icon?: string;
  comingSoon?: boolean;
}

export const FEATURE_HIGHLIGHTS: FeatureHighlight[] = [
  {
    title: "AI Live Insights",
    description: "Your personal sports analyst — but smarter. Real-time commentary, momentum shifts, scoring implications, and probability reads as the game unfolds.",
    isPremium: true,
    icon: "🧠",
  },
  {
    title: "Live Telegram Alerts",
    description:
      "Never miss a scoring drive. Instant alerts: scoring plays, drive summaries, quarter changes, and finals — fast and real-time.",
    isPremium: true,
    icon: "📡",
    comingSoon: true,
  },
  {
    title: "Smarter Parlays, Less Guesswork",
    description: "Free Tier gets fundamentals. Premium unlocks personalized, AI-tailored parlay guidance based on slate + user tendencies.",
    isPremium: false,
    icon: "🎯",
  },
  {
    title: "Track Your Edge Over Time",
    description: "Free = recent parlays only. Premium = full history, ROI charts, confidence vs outcome trends.",
    isPremium: false,
    icon: "📈",
  },
];

