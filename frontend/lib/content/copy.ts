/**
 * Centralized Copy System
 * All user-facing text following the "sharp bettor edge" voice:
 * - Calm, confident, short sentences
 * - No corporate buzzwords
 * - No "lock/guarantee" language
 */

import { checkVoice } from "./voiceLint"

export const copy = {
  site: {
    home: {
      hero: {
        headline: "Check it before you bet it.",
        subheadline: "Parlay Gorilla shows confidence, risk, and what to cut — before you place the bet.",
        ctaPrimary: "Build a slip",
        ctaSecondary: "See how it works",
        trustLine: "No team logos. No gimmicks. Just the check.",
        badge: "AI Sports Analytics Platform",
      },
      features: {
        title: "Why Parlay Gorilla?",
        subtitle: "Practical insights to help you evaluate matchups and build clean slips.",
        items: [
          {
            title: "Confidence Scores",
            description: "See probability estimates and matchup context. Understand the why, not just the pick.",
          },
          {
            title: "Fast Builder",
            description: "Generate 1–20 leg parlays in seconds. Adjust legs, sports, and risk to explore scenarios.",
          },
          {
            title: "Risk Indicators",
            description: "Choose conservative, balanced, or high-risk profiles. We show what's weak so you can cut it.",
          },
          {
            title: "Major Sports",
            description: "Build across NFL, NBA, NHL, MLB, and more. Mix sports when it makes sense.",
          },
          {
            title: "Odds Comparison",
            description: "Compare odds across major platforms. Parlay Gorilla is not affiliated with any sportsbook.",
          },
          {
            title: "Track Results",
            description: "Save slips and review outcomes over time. No hype—just feedback and iteration.",
          },
          {
            title: "Arcade Leaderboards",
            description: "Win verified 5+ leg parlays to earn points and climb the leaderboard. Compete with the community and track your progress.",
          },
        ],
      },
      howItWorks: {
        title: "How It Works",
        subtitle: "Get started in three steps",
        steps: [
          {
            step: "01",
            title: "Build your slip",
            description: "Pick your sport(s), number of legs (1–20), and a risk profile.",
          },
          {
            step: "02",
            title: "Run the check",
            description: "We show confidence, risk, and what to cut before you bet.",
          },
          {
            step: "03",
            title: "Decide & Compete",
            description: "Use the info as decision support. Track results, climb the leaderboard, and compete with the community.",
          },
        ],
      },
      cta: {
        headline: "Ready to build picks?",
        subheadline: "Build. Check. Decide.",
        ctaPrimary: "Build Picks Now",
        ctaSecondary: "See pricing",
        features: ["Confidence Mode · never forced", "Slip breakdown", "Matchup research", "Clean insights", "18+ only"],
      },
    },
    pricing: {
      hero: {
        title: "Simple pricing. No tricks.",
        subtitle: "Choose what works for you.",
      },
      plans: {
        standard: {
          name: "Standard",
          tagline: "The check.",
          features: [
            "Confidence score",
            "Slip breakdown",
            "Save slips",
            "Basic insights",
          ],
        },
        elite: {
          name: "Elite",
          tagline: "Deeper reads + more angles.",
          features: [
            "Everything in Standard",
            "Sharper insights",
            "More context",
            "Advanced filters",
            "Priority support",
          ],
        },
      },
      faq: {
        needSubscription: {
          question: "Do I need a subscription?",
          answer: "No. You can buy credit packs and pay per use.",
        },
        cancel: {
          question: "Can I cancel?",
          answer: "Yes. Cancel any time. Your access stays active until the period ends.",
        },
        credits: {
          question: "How do credits work?",
          answer: "Credits are deducted when you generate or unlock pay-per-use actions.",
        },
      },
    },
    about: {
      headline: "Built for bettors who want the edge.",
      body: [
        "Parlay Gorilla doesn't sell dreams. It filters bad bets.",
        "You still decide. We just show you what matters.",
      ],
    },
  },
  app: {
    onboarding: {
      title: "Welcome to Parlay Gorilla.",
      subtitle: "Build a slip. We'll check it.",
      primary: "Start",
      optional: {
        showConfidence: "Show confidence scores",
        showVerdict: "Show quick verdict",
      },
    },
    slipBuilder: {
      header: "Build a Parlay",
      helper: "Pick your sport and options. We'll find your best picks.",
      emptyState: "No picks yet. Add one.",
      addLeg: "Add a pick",
      generate: "Generate parlay",
      generateTriple: "Generate triple parlays",
    },
    analysis: {
      header: "The check.",
      confidence: {
        high: "High",
        solid: "Solid",
        risky: "Risky",
        low: "Low",
      },
      verdict: {
        clean: "Clean",
        risky: "Risky",
        pass: "Pass",
      },
      sections: {
        strong: "What's strong",
        weak: "What's weak",
        watch: "What to watch",
        forcing: "If you're forcing it…",
      },
      callouts: {
        swingLeg: "This leg is the swing.",
        weakLeg: "This is where slips die.",
        keepOne: "If you keep one, keep this one.",
        cutOne: "If you cut one, cut this one.",
      },
    },
    history: {
      header: "Your slips.",
      emptyState: "Nothing saved yet. Build one.",
    },
    save: {
      modal: {
        title: "Save this slip?",
        subtitle: "So you can come back before kickoff.",
        button: "Save slip",
      },
      share: {
        share: "Share the slip",
        copyLink: "Copy link",
      },
    },
  },
  states: {
    loading: {
      checking: "Checking…",
      runningNumbers: "Running the numbers…",
      verifying: "Hold up. Verifying the slip…",
      loading: "Loading…",
      loadingGames: "Loading games…",
      loadingAnalyses: "Loading analyses…",
      loadingData: "Loading data…",
    },
    empty: {
      nothingHere: "Nothing here yet.",
      addLeg: "Add a leg to start.",
      noGames: "No games found for this date.",
      noAnalyses: "No analysis available yet.",
      noSlips: "Nothing saved yet. Build one.",
    },
    errors: {
      generic: "Something broke. Try again.",
      loadFailed: "Couldn't load that. Refresh.",
      connection: "No connection. Try again.",
      rateLimit: "Rate limit. Try again in a few minutes.",
      timeout: "This is taking longer than expected. Try again with fewer legs.",
      generationFailed: "Failed to generate parlay.",
    },
  },
  cta: {
    primary: {
      buildSlip: "Build a slip",
      checkSlip: "Check this slip",
      runCheck: "Run the check",
      checkThis: "Check this",
    },
    secondary: {
      seeHow: "See how it works",
      skip: "Skip",
      cancel: "Cancel",
    },
    destructive: {
      removeLeg: "Remove leg",
      delete: "Delete",
    },
    neutral: {
      pass: "Pass",
      save: "Save",
      share: "Share",
    },
  },
  notifications: {
    success: {
      slipSaved: "Slip saved.",
      legRemoved: "Leg removed.",
      checkComplete: "Check complete.",
      parlayGenerated: "Parlay generated.",
    },
    warning: {
      lowConfidence: "Low confidence. Consider a cut.",
      riskyLeg: "Risky leg detected.",
    },
    info: {
      highConfidence: "High confidence. This is cleaner.",
      cleanSlip: "Clean slip. Looks good.",
    },
    error: {
      saveFailed: "Failed to save slip.",
      generationFailed: "Failed to generate parlay.",
      loadFailed: "Failed to load data.",
    },
  },
  paywall: {
    aiParlayLimit: {
      title: "That's Elite.",
      subtitle: "Upgrade to unlock deeper reads.",
    },
    /** Premium upsell variants (Growth System v1) — trigger: confidence_disabled | mixed_sports_locked | thin_slate */
    premiumUpsell: {
      confidenceDisabled: {
        A: {
          title: "Confidence Mode needs more strong picks",
          body: "Premium lets us pull from more games so Confidence Mode is available more often.",
          cta: "Unlock Premium",
        },
        B: {
          title: "Today's slate is thin",
          body: "Premium unlocks more opportunities when there aren't enough strong picks in one sport.",
          cta: "See Premium Options",
        },
        C: {
          title: "We won't force a third pick",
          body: "Premium helps Confidence Mode find strong picks across more games — without lowering standards.",
          cta: "Upgrade to Premium",
        },
      },
      mixedSportsLocked: {
        A: {
          title: "More sports, more chances",
          body: "Premium lets Confidence Mode pull from multiple sports when one slate is thin.",
          cta: "Unlock Premium",
        },
        B: {
          title: "Premium expands the slate",
          body: "See more combinations without forcing weaker picks.",
          cta: "See Premium Options",
        },
      },
      thinSlate: {
        A: {
          title: "Run into thin slates?",
          body: "Premium reduces \"not enough picks\" days by widening what the AI can safely use.",
          cta: "Unlock Premium",
        },
        B: {
          title: "Premium = fewer dead ends",
          body: "More games. Same discipline.",
          cta: "See Premium Options",
        },
      },
    },
    payPerUse: {
      title: "Need more?",
      subtitle: "Buy credits or upgrade to Elite.",
    },
    featurePremium: {
      title: "Elite feature",
      subtitle: "This feature is available with Elite.",
    },
    customBuilder: {
      title: "Gorilla Parlay Builder requires Elite",
      subtitle: "Use credits ({credits} per AI action) or upgrade to Elite for included access.",
    },
    inscriptions: {
      title: "Need credits for verification",
      subtitle: "You've used your included verifications. Buy credits to continue.",
    },
    upsetFinder: {
      title: "Unlock the Upset Finder",
      subtitle: "Find plus-money underdogs with positive expected value.",
    },
    loginRequired: {
      title: "Login required",
      subtitle: "Create a free account to use this feature.",
    },
    benefits: [
      {
        title: "Gorilla Parlays",
        description: "{count} generations per {days} days (rolling)",
      },
      {
        title: "Gorilla Parlay Builder",
        description: "Build your own parlays with analysis ({count} per {days} days)",
      },
      {
        title: "Automatic Verification",
        description: "Every Custom parlay is automatically verified with a permanent record.",
      },
      {
        title: "Detailed Confidence Breakdowns",
        description: "Understand why each pick has edge with detailed confidence analysis and EV calculations.",
      },
      {
        title: "Gorilla Upset Finder",
        description: "Discover +EV underdogs the market is undervaluing",
      },
      {
        title: "Multi-Sport Mixing",
        description: "Cross-sport parlays with smart correlation handling",
      },
    ],
  },
  confidence: {
    tooltip: {
      title: "What is confidence?",
      explanation: "Confidence is our model's certainty that this pick has positive expected value (EV). It's not the same as win probability. A 67% confidence means we're 67% certain this pick has edge over the market odds.",
      winProbability: "Win probability is the estimated chance this pick wins. Confidence is how certain we are that the pick has value.",
      example: "Example: A pick with 45% win probability but 70% confidence means we're confident it's undervalued by the market.",
    },
    firstParlay: {
      title: "Understanding Confidence Scores",
      subtitle: "Here's what these numbers mean for your parlay",
      explanation: "Confidence scores show how certain our model is that each pick has positive expected value. This is different from win probability.",
      winProbabilityLabel: "Win Probability",
      winProbabilityDesc: "The estimated chance this pick wins (e.g., 60% = 60% chance to win).",
      confidenceLabel: "Confidence",
      confidenceDesc: "How certain we are this pick has edge over the market (e.g., 75% = we're 75% certain it's undervalued).",
      howToUse: "How to use this:",
      tip1: "Higher confidence = stronger edge over market odds",
      tip2: "Look for legs with both solid win probability and high confidence",
      tip3: "Low confidence? Consider cutting that leg — it may not have value",
      cta: "Got it",
      dontShowAgain: "Don't show this again",
    },
  },
  backend: {
    errors: {
      accessDenied: "Access denied.",
      limitReached: "Limit reached. Buy credits or upgrade.",
      invalidRequest: "Invalid request.",
      serverError: "Server error. Try again.",
      timeout: "Request timed out. Try again.",
      notEnoughGames: "Not enough games available. Try again later.",
      databaseError: "Database error. Try again.",
    },
  },
} as const

// Run voice lint in development
if (typeof window !== "undefined" && process.env.NODE_ENV === "development") {
  checkVoice(copy, true)
}

