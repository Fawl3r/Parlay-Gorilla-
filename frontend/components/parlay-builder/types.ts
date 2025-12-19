export const SPORT_OPTIONS = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "MLS", "EPL"] as const

export type BuilderMode = "single" | "triple"
export type SportOption = (typeof SPORT_OPTIONS)[number]
export type RiskProfile = "conservative" | "balanced" | "degen"

// Sport badges with a consistent landing-page neon palette (minimalistic UI).
export const SPORT_COLORS: Record<SportOption, { bg: string; text: string; border: string }> = {
  NFL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NBA: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NHL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  MLB: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NCAAF: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  NCAAB: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  MLS: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
  EPL: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/50" },
}


