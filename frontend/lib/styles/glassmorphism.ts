/**
 * Glassmorphism utility classes and styles
 */

export const glassmorphism = {
  panel: {
    default: "bg-[rgba(18,18,23,0.6)] backdrop-blur-md border-white/8",
    strong: "bg-[rgba(18,18,23,0.8)] backdrop-blur-xl border-white/12",
    subtle: "bg-[rgba(18,18,23,0.4)] backdrop-blur-sm border-white/6",
  },
  sidebar: "bg-[rgba(26,26,31,0.8)] backdrop-blur-xl border-white/10",
  header: {
    default: "bg-[rgba(10,10,15,0.7)] backdrop-blur-lg",
    scrolled: "bg-[rgba(10,10,15,0.85)] backdrop-blur-xl",
  },
  card: {
    default: "bg-[rgba(18,18,23,0.6)] backdrop-blur-md border-white/8",
    hover: "hover:border-white/12 hover:shadow-lg hover:shadow-emerald-500/10",
  },
} as const

export const glassmorphismClasses = {
  panel: "bg-[rgba(18,18,23,0.6)] backdrop-blur-md border border-white/8 rounded-xl",
  panelStrong: "bg-[rgba(18,18,23,0.8)] backdrop-blur-xl border border-white/12 rounded-xl",
  panelSubtle: "bg-[rgba(18,18,23,0.4)] backdrop-blur-sm border border-white/6 rounded-xl",
  sidebar: "bg-[rgba(26,26,31,0.8)] backdrop-blur-xl border-r border-white/10",
  header: "bg-[rgba(10,10,15,0.7)] backdrop-blur-lg border-b border-white/10",
  card: "bg-[rgba(18,18,23,0.6)] backdrop-blur-md border border-white/8 rounded-xl",
} as const
