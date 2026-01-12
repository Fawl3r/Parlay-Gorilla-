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
        badge: "Sports Analytics Platform",
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
            title: "Decide",
            description: "Use the info as decision support. You still decide.",
          },
        ],
      },
      cta: {
        headline: "Ready to check your slip?",
        subheadline: "Build. Check. Decide.",
        ctaPrimary: "Build a slip",
        ctaSecondary: "See pricing",
        features: ["Confidence scores", "Slip breakdown", "Matchup research", "Clean insights", "18+ only"],
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
      header: "Build your slip.",
      helper: "Keep it clean. We'll tell you what to cut.",
      emptyState: "No legs yet. Add one.",
      addLeg: "Add a leg",
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
        title: "Gorilla Upset Finder",
        description: "Discover +EV underdogs the market is undervaluing",
      },
      {
        title: "Multi-Sport Mixing",
        description: "Cross-sport parlays with smart correlation handling",
      },
    ],
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

