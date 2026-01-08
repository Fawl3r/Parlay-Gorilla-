import type { TutorialScreenshotId } from "./tutorialScreenshots"
import {
  PREMIUM_AI_PARLAYS_PER_PERIOD,
  PREMIUM_AI_PARLAYS_PERIOD_DAYS,
  PREMIUM_CUSTOM_PARLAYS_PER_PERIOD,
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
    id: "what-parlay-gorilla-does",
    title: "What Parlay Gorilla does",
    description: "A simple goal: help you build a smarter parlay faster — without guessing.",
    steps: [
      {
        title: "Important Disclaimer",
        bullets: [
          "Parlay Gorilla does not accept bets or facilitate wagering. All scenarios are hypothetical.",
        ],
      },
      {
        title: "In plain English",
        bullets: [
          "Parlay Gorilla helps you turn today's games into a clear, research-backed hypothetical parlay scenario in minutes.",
          "You can generate suggestions (Gorilla Parlays), or analyze your own picks (🦍 Gorilla Parlay Builder 🦍).",
          "Next: tap \"Start Building\" to generate your first Gorilla Parlay.",
        ],
        links: [
          { label: "Start Building", href: "/build" },
          { label: "View Game Analytics", href: "/analysis" },
        ],
      },
    ],
  },
  {
    id: "core-concepts",
    title: "Core concepts (explained simply)",
    description: "If you understand these, the rest of the app becomes easy.",
    steps: [
      {
        title: "Gorilla Parlays",
        bullets: [
          "Plain English: pick a sport + risk level + number of legs, and the app suggests a full parlay.",
          "Why you'd do this: it's the fastest way to get an idea when you're new.",
          "Example: \"NBA • 3 legs • Balanced\" → Generate → review the slip + summary.",
        ],
        links: [{ label: "Start Building", href: "/build" }],
      },
      {
        title: "🦍 Gorilla Parlay Builder 🦍",
        bullets: [
          "Plain English: you choose the exact legs, then run AI analysis on your specific slip.",
          "Why you'd do this: you already have picks and want a quick risk check.",
          "Example: pick 2–4 legs → run 🦍 Gorilla Parlay Builder 🦍 → read the risk notes before you commit.",
        ],
        links: [{ label: "Go to Dashboard", href: "/app" }],
      },
      {
        title: "Credits",
        bullets: [
          "Plain English: an optional “pay-per-use” balance you can spend when you want more actions.",
          "Why you’d do this: you hit a limit and don’t want to wait for the next reset.",
          "Reassurance: nothing is charged automatically. You decide if/when to buy credits.",
        ],
        links: [{ label: "See Plans & Credits", href: "/pricing" }],
      },
      {
        title: "Automatic Verification",
        bullets: [
          "Every Custom AI parlay is automatically verified with a permanent, time-stamped record.",
          "This happens server-side — no user action required.",
          "Verification creates a tamper-resistant proof that your parlay analysis existed at a specific time.",
        ],
      },
      {
        title: "Limits",
        bullets: [
          `Gorilla Parlays: ${PREMIUM_AI_PARLAYS_PER_PERIOD} per month.`,
          `🦍 Gorilla Parlay Builder 🦍 actions: ${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} per month.`,
          `Resets: your allowance refreshes every ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (about monthly).`,
          "When you hit a limit, you’ll see a lock with clear options (wait, use credits, or upgrade).",
        ],
      },
    ],
  },
  {
    id: "step-by-step",
    title: "Step-by-step tutorial",
    description: "Build your first Gorilla Parlay, then learn how to read the results.",
    steps: [
      {
        title: "Step 1: Access the Gorilla Parlay Builder",
        bullets: [
          "Go to /build (public). You can start without an account.",
          "If you want to save results later, you can sign up after your first build.",
          "Next: choose sport, legs, and risk profile.",
        ],
        links: [
          { label: "Start Building", href: "/build" },
          { label: "Sign Up (optional)", href: "/auth/signup" },
        ],
      },
      {
        title: "Step 2: Pick sport / legs / risk profile",
        bullets: [
          "What this UI does: Sport = which games to use. Legs = how many picks in the parlay. Risk = how aggressive it is.",
          "What to do first: start with 2–4 legs and “Balanced”.",
          "If you’re unsure: change only Sport + Legs, then generate.",
          "Next: tap Generate and let it run.",
        ],
        screenshots: ["buildControls_desktop", "buildControls_mobile"],
      },
      {
        title: "Step 3: Generate",
        bullets: [
          "A short wait is normal — keep the page open while it works.",
          "If it times out: try fewer legs, switch to Balanced, then retry in a minute.",
          "Next: when results appear, read the top numbers first.",
        ],
      },
      {
        title: "Step 4: Interpret results (what to look at first)",
        bullets: [
          "Look first: Hit Probability (estimated chance the full parlay wins).",
          "Then: Model Confidence (how strongly the model likes the picks).",
          "Then: scan each leg to spot the “weak link” (lowest confidence / probability).",
          "Finally: read the summary for the “why” and any caveats.",
          "Next: share it, tweak inputs, or build again with fewer legs.",
        ],
        screenshots: ["buildParlayResult_desktop"],
        links: [{ label: "Glossary", href: "#glossary" }],
      },
    ],
  },
  {
    id: "real-examples",
    title: "Real examples",
    description: "Two quick flows you can copy right now.",
    steps: [
      {
        title: "Example 1: A simple Gorilla Parlay (fast)",
        bullets: [
          "Go to /build → choose a sport.",
          "Set Legs to 3 and pick “Balanced”.",
          "Tap Generate → check Hit Probability + Model Confidence.",
          "If it feels too risky: drop to 2 legs or switch to “Conservative”, then regenerate.",
          "Next: try one more build with a different risk profile so you feel the difference.",
        ],
        links: [{ label: "Start Building", href: "/build" }],
      },
      {
        title: "Example 2: 🦍 Gorilla Parlay Builder 🦍 parlay with automatic verification",
        bullets: [
          "Sign in → go to /app → pick a few legs from Upcoming Games.",
          "Open 🦍 Gorilla Parlay Builder 🦍 → run analysis on your exact slip.",
          "Verification happens automatically — every Custom AI parlay gets a permanent, time-stamped record.",
          "If you see a lock: you hit a limit or the feature isn't on your plan (upgrade or use credits).",
          "Next: view your verification records anytime from the analysis results.",
        ],
        screenshots: ["dashboardUpcomingGames_desktop", "dashboardCustomBuilderLocked_desktop"],
        links: [
          { label: "Sign Up", href: "/auth/signup" },
          { label: "Go to Dashboard", href: "/app" },
          { label: "Plans & Credits", href: "/pricing" },
        ],
      },
    ],
  },
  {
    id: "limits-and-numbers",
    title: "Limits & what these numbers mean",
    description: "Clear rules, no surprises. You’re always in control.",
    steps: [
      {
        title: "Monthly usage limits",
        bullets: [
          `Gorilla Parlays: ${PREMIUM_AI_PARLAYS_PER_PERIOD} per month.`,
          `🦍 Gorilla Parlay Builder 🦍 actions: ${PREMIUM_CUSTOM_PARLAYS_PER_PERIOD} per month.`,
          `Resets: your allowance refreshes every ${PREMIUM_AI_PARLAYS_PERIOD_DAYS} days (about monthly).`,
          "When you hit a limit, the UI will show a lock and explain your options.",
          "Next: if you’re blocked, use Game Analytics while you wait — or use credits.",
        ],
        links: [
          { label: "View Game Analytics", href: "/analysis" },
          { label: "Understand Usage & Billing", href: "/pricing" },
        ],
      },
      {
        title: "Automatic Verification",
        bullets: [
          "Every Custom AI parlay is automatically verified with a permanent, time-stamped record.",
          "Verification happens server-side — no user action required.",
          "This creates a tamper-resistant proof that your parlay analysis existed at a specific time.",
          "Next: view verification records from your analysis results.",
        ],
      },
      {
        title: "Credits (optional)",
        bullets: [
          "Credits are a manual top-up you can use when you want more actions.",
          "Credits are not automatic charges — you decide when to buy and when to spend.",
          "Next: if you want more actions today, check Plans & Credits.",
        ],
        screenshots: ["pricingPaywall_desktop"],
        links: [{ label: "Plans & Credits", href: "/pricing" }],
      },
    ],
  },
  {
    id: "troubleshooting",
    title: "Troubleshooting",
    description: "Short, calm fixes for the most common issues.",
    steps: [
      {
        title: "“No games found”",
        bullets: [
          "Try a different sport or adjust the date (some sports are out of season).",
          "Refresh the page and try again.",
          "Next: if the slate is empty, use Game Analytics instead.",
        ],
        links: [{ label: "View Game Analytics", href: "/analysis" }],
      },
      {
        title: "AI generation is slow or times out",
        bullets: [
          "Try fewer legs (2–3) and use “Balanced”.",
          "Retry after 30–60 seconds — the system may be busy.",
          "On mobile, switch to a stronger connection if possible.",
          "Next: if it keeps timing out, contact support.",
        ],
        links: [{ label: "Contact Support", href: "/support" }],
      },
      {
        title: "I see a lock / I hit a limit",
        bullets: [
          "A lock means the action is unavailable on your plan or you’ve used your monthly allowance.",
          "Use credits, wait for the reset, or upgrade — the lock message will tell you what applies.",
          "Next: open Plans & Credits to see your options.",
        ],
        links: [{ label: "Plans & Credits", href: "/pricing" }],
      },
      {
        title: "I’m not sure what to look at first",
        bullets: [
          "Start with Hit Probability, then Model Confidence, then the weakest leg.",
          "Use the Glossary if a term is unfamiliar.",
          "Next: do one more build with fewer legs so the signal is clearer.",
        ],
        links: [{ label: "Glossary", href: "#glossary" }],
      },
      {
        title: "Still stuck?",
        bullets: [
          "Contact support and tell us what page you were on and what you clicked.",
          "Screenshots help a lot.",
          "Next: use Contact Support or Report a Bug.",
        ],
        links: [
          { label: "Contact Support", href: "/support" },
          { label: "Report a Bug", href: "/report-bug" },
        ],
      },
    ],
  },
  {
    id: "glossary",
    title: "Glossary (expandable)",
    description: "One-sentence definitions. No jargon.",
    steps: [
      {
        title: "Model confidence",
        bullets: ["How strongly the model likes the picks you’re seeing (higher = stronger conviction)."],
      },
      {
        title: "Hit probability",
        bullets: ["The estimated chance the full parlay wins (higher = generally safer)."],
      },
      {
        title: "Moneyline (ML)",
        bullets: ["A simple pick: which team wins the game."],
      },
      {
        title: "Spread",
        bullets: ["A pick with a points handicap (a team must win by enough, or stay close enough)."],
      },
      {
        title: "Total",
        bullets: ["A pick on whether the combined points go over or under a number."],
      },
      {
        title: "Lock / feature lock",
        bullets: ["A feature is unavailable on your plan or you hit a limit — the screen will tell you how to unlock it."],
      },
      {
        title: "Automatic Verification",
        bullets: ["Every Custom AI parlay is automatically verified with a permanent, time-stamped proof that your analysis existed at a specific time."],
      },
    ],
  },
  {
    id: "next-steps",
    title: "Next steps",
    description: "Pick one action and keep momentum.",
    steps: [
      {
        title: "What to do now",
        bullets: [
          "Build your first Gorilla Parlay (fastest way to learn).",
          "View Game Analytics when you want deeper matchup context.",
          "Review Usage & Billing if you hit a limit or see a lock.",
          "Contact support if something feels off.",
        ],
        links: [
          { label: "Build Your First Gorilla Parlay", href: "/build" },
          { label: "View Game Analytics", href: "/analysis" },
          { label: "Understand Usage & Billing", href: "/pricing" },
          { label: "Contact Support", href: "/support" },
        ],
      },
    ],
  },
]


