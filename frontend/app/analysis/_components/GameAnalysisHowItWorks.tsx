"use client"

import { BarChart3, Target, Zap, Shield } from "lucide-react"

/**
 * Explainer shown while the sports list loads on the Game Analysis hub.
 * Gives the list time to load and sets expectations for how analysis works.
 */
export function GameAnalysisHowItWorks() {
  return (
    <section
      className="container mx-auto px-4 py-10 max-w-2xl"
      aria-label="How game analysis works"
    >
      <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
        <BarChart3 className="h-5 w-5 text-emerald-400" aria-hidden />
        How game analysis works
      </h2>
      <ul className="space-y-5 text-sm text-white/80">
        <li className="flex gap-3">
          <span className="shrink-0 w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold">1</span>
          <div>
            <strong className="text-white/90">Pick a sport and matchup.</strong>
            <span className="block mt-0.5 text-white/60">
              Leagues and games are loaded from our live feed. Choose a sport above, then tap a game to open the full breakdown.
            </span>
          </div>
        </li>
        <li className="flex gap-3">
          <span className="shrink-0 w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold">2</span>
          <div>
            <strong className="text-white/90">Read the AI research layer.</strong>
            <span className="block mt-0.5 text-white/60">
              Each analysis combines model probabilities, key drivers, and matchup intelligence so you see why the edge exists — not just a pick.
            </span>
          </div>
        </li>
        <li className="flex gap-3">
          <span className="shrink-0 w-8 h-8 rounded-lg bg-emerald-500/20 flex items-center justify-center text-emerald-400 font-bold">3</span>
          <div>
            <strong className="text-white/90">Use it in your process.</strong>
            <span className="block mt-0.5 text-white/60">
              Add a leg to your parlay, save the analysis, or dig into trends and props. The same engine powers our Strategy Builder and AI Selections.
            </span>
          </div>
        </li>
      </ul>
      <div className="mt-8 pt-6 border-t border-white/10 flex flex-wrap items-center gap-4 text-xs text-white/50">
        <span className="inline-flex items-center gap-1.5">
          <Target className="h-3.5 w-3.5" aria-hidden />
          Multi-league coverage
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Zap className="h-3.5 w-3.5" aria-hidden />
          Model-updated
        </span>
        <span className="inline-flex items-center gap-1.5">
          <Shield className="h-3.5 w-3.5" aria-hidden />
          Research verified
        </span>
      </div>
      <p className="mt-4 text-xs text-white/40">
        Loading available sports and matchups…
      </p>
    </section>
  )
}
