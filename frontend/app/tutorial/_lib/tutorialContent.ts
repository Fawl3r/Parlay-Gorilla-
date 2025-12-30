import type { TutorialScreenshotId } from "./tutorialScreenshots"
import {
  INSCRIPTION_COST_USD,
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
  PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS,
} from "@/lib/pricingConfig"

export type TutorialLink = {
  label: string
  href: string
}

export type TutorialStep = {
  title: string
  bullets: string[]
  screenshots?: TutorialScreenshotId[]
  links?: TutorialLink[]
}

export type TutorialSection = {
  id: string
  title: string
  description: string
  steps: TutorialStep[]
}

export const TUTORIAL_SECTIONS: TutorialSection[] = [
  {
    id: "start-here",
    title: "Start here (2-minute overview)",
    description: "The fastest way to understand what Parlay Gorilla does and where to click first.",
    steps: [
      {
        title: "What Parlay Gorilla is (and isn’t)",
        bullets: [
          "Parlay Gorilla provides AI-assisted sports analytics to help you research games faster and build informed slips.",
          "It is not a sportsbook. You place bets (if you choose) on your sportsbook of choice.",
          "Outcomes are never guaranteed — treat this as decision support, not financial advice.",
        ],
        links: [
          { label: "Sports Disclaimer", href: "/disclaimer" },
          { label: "Responsible Gaming", href: "/responsible-gaming" },
        ],
      },
      {
        title: "Two ways to use the app",
        bullets: [
          "Fast path: go to /build (public) to generate an AI parlay immediately.",
          "Power user path: sign up → complete your profile → use the full Gorilla Dashboard at /app.",
        ],
        links: [
          { label: "AI Builder (Public)", href: "/build" },
          { label: "Sign Up", href: "/auth/signup" },
        ],
        screenshots: ["landing_desktop"],
      },
    ],
  },
  {
    id: "glossary",
    title: "Glossary (plain English)",
    description: "Quick definitions for the terms you’ll see in the app.",
    steps: [
      {
        title: "Core terms",
        bullets: [
          "Hit probability: the model’s estimated chance the full parlay wins (higher is safer).",
          "Confidence: how strongly the model prefers each leg (higher is stronger conviction).",
          "Risk profile: Conservative = safer, Balanced = middle, Degen = higher variance.",
          "Credits: pay-per-use balance you can spend when you want more actions.",
          "Free uses: limited starter uses for new accounts (lifetime).",
          "Verify on-chain (optional): you can choose to anchor a Custom AI parlay for proof; it is never automatic.",
        ],
      },
    ],
  },
  {
    id: "age-gate",
    title: "Age gate (21+)",
    description: "The first time you open the site you’ll see an age verification modal.",
    steps: [
      {
        title: "Confirm your age to unlock the site",
        bullets: [
          "Click “I am 21 or older”. This is stored in your browser so you won’t see it every time.",
          "If you click “I am under 21”, the site will direct you to responsible gaming resources.",
        ],
        screenshots: ["ageGate_desktop", "ageGate_mobile"],
      },
    ],
  },
  {
    id: "ai-builder-public",
    title: "AI Parlay Builder (public) — /build",
    description: "Generate AI suggestions quickly, then interpret the results like a pro.",
    steps: [
      {
        title: "Set your build inputs",
        bullets: [
          "Pick a Mode: Single Parlay (manual controls) or Triple Parlays (Safe/Balanced/Degen flight).",
          "Choose a sport (or multiple sports if your plan supports it).",
          "Pick your risk profile and the number of legs you want.",
          "If NFL is selected, choose the week you want to build from.",
        ],
        screenshots: ["buildControls_desktop", "buildControls_mobile"],
      },
      {
        title: "Generate and wait (progress is normal)",
        bullets: [
          "Generation can take 30 seconds to a few minutes depending on traffic and complexity.",
          "Keep the page open while it runs — you’ll see a progress bar and status messages.",
          "If it times out, try fewer legs, a different risk profile, or retry in a minute.",
        ],
      },
      {
        title: "Read the result (confidence, legs, and AI notes)",
        bullets: [
          "Check Hit Probability and Model Confidence first — they tell you how “tight” the slip is.",
          "Scan the Parlay Legs list: each leg shows game, market, odds, win probability, and confidence.",
          "Read AI Summary + Risk Assessment for the reasoning and key caveats.",
          "Use Share to send a friend a reference slip; use Save to keep it in your account history (when signed in).",
        ],
        screenshots: ["buildParlayResult_desktop"],
      },
    ],
  },
  {
    id: "dashboard",
    title: "Gorilla Dashboard (signed-in) — /app",
    description: "Your main workspace: games, builders, and analytics in one place.",
    steps: [
      {
        title: "Upcoming Games tab (pick legs from the slate)",
        bullets: [
          "Choose a sport tab, then move the date forward/back to view different slates.",
          "Use the market filter (Moneyline / Spread / Total) to focus on the bet type you care about.",
          "Tap outcomes to select legs; the bottom bar will show how many legs you’ve selected.",
          "Click “View Parlay” to open the slip view.",
        ],
        screenshots: ["dashboardUpcomingGames_desktop", "dashboardUpcomingGames_mobile"],
      },
      {
        title: "AI Builder tab (same engine, inside your dashboard)",
        bullets: [
          "Use this when you want AI generation but prefer staying inside your dashboard flow.",
          "Free vs Premium limits apply (you’ll see locks/limits in the UI when relevant).",
        ],
        screenshots: ["dashboardAiBuilder_desktop"],
      },
      {
        title: "Custom Builder tab (advanced)",
        bullets: [
          "Pick specific legs manually, then run AI analysis on your exact slip.",
          "If your plan doesn’t include it, you’ll see a lock screen with an upgrade option.",
        ],
        screenshots: ["dashboardCustomBuilderLocked_desktop"],
        links: [{ label: "Pricing", href: "/pricing" }],
      },
      {
        title: "Analytics tab",
        bullets: [
          "Use Analytics to track performance over time (hit rate, calibration error, and history).",
          "If you’re not signed in, /analytics (public page) will prompt you to authenticate.",
        ],
        links: [{ label: "Analytics (Public Page)", href: "/analytics" }],
      },
    ],
  },
  {
    id: "game-analytics",
    title: "Game Analytics (public) — /analysis",
    description: "Read game breakdowns, predictions, and best-bet style insights.",
    steps: [
      {
        title: "Browse the analysis hub",
        bullets: [
          "Open /analysis to browse by sport and see available analysis cards.",
          "Click a matchup to open the full analysis page (shareable URL).",
        ],
        screenshots: ["analysisHub_desktop"],
      },
    ],
  },
  {
    id: "limits-and-upgrades",
    title: "Limits, credits, and upgrades",
    description: "What happens when you hit a limit — and what you can do next.",
    steps: [
      {
        title: "What’s limited (and what isn’t)",
        bullets: [
          `Premium includes ${PREMIUM_AI_PARLAYS_PER_PERIOD} AI parlays per ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (rolling).`,
          `Premium includes ${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} Custom AI actions per ${PREMIUM_CUSTOM_PARLAYS_PERIOD_DAYS} days (rolling).`,
          `On-chain verification is optional and requires opt-in (costs $${INSCRIPTION_COST_USD.toFixed(2)} per Custom AI parlay you verify).`,
          "Credits let you pay per use when you want more actions without changing plans.",
          "When you see a lock icon or a paywall modal, it means the action needs Premium and/or credits.",
        ],
        screenshots: ["pricingPaywall_desktop"],
        links: [
          { label: "Pricing / Upgrade", href: "/pricing" },
          { label: "Docs", href: "/docs" },
        ],
      },
    ],
  },
  {
    id: "troubleshooting",
    title: "Common Questions",
    description: "Fast fixes for the most common “wait, what?” moments.",
    steps: [
      {
        title: "“No games found”",
        bullets: [
          "Try a different sport tab or change the date forward/back.",
          "Hit Refresh in the Upcoming Games toolbar.",
          "Some sports are out of season — the slate may legitimately be empty.",
        ],
      },
      {
        title: "AI generation is slow or times out",
        bullets: [
          "Try fewer legs, or avoid “Degen” with high leg counts during peak traffic.",
          "Retry after 30–60 seconds; the system may be busy.",
          "If you’re on mobile, confirm your connection is stable (cell networks can drop long requests).",
        ],
      },
      {
        title: "Need help?",
        bullets: [
          "If something looks wrong, report it and include what page you were on and what you clicked (screenshots help).",
          "For account/billing issues, use the support form.",
        ],
        links: [
          { label: "Contact Support", href: "/support" },
          { label: "Report a Bug", href: "/report-bug" },
        ],
      },
    ],
  },
]


