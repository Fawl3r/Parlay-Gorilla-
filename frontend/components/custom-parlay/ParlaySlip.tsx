"use client"

import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import type { CounterParlayMode } from "@/lib/api"
import type { SelectedPick } from "@/components/custom-parlay/types"
import { CoveragePackControls } from "@/components/custom-parlay/CoveragePackControls"

export const MAX_CUSTOM_PARLAY_LEGS = 20
export const MIN_CUSTOM_PARLAY_LEGS = 1
/** Minimum picks to generate Counter Ticket or Coverage Pack (reduces wasted compute + better UX). */
export const MIN_PICKS_FOR_HEDGES = 2

export function ParlaySlip({
  picks,
  onRemovePick,
  onAnalyze,
  isAnalyzing,
  onSave,
  isSaving,
  onGenerateCounter,
  isGeneratingCounter,
  counterMode,
  onCounterModeChange,
  counterTargetLegs,
  onCounterTargetLegsChange,
  onGenerateCoveragePack,
  isGeneratingCoveragePack,
  coverageMaxTotalParlays,
  coverageScenarioMax,
  coverageRoundRobinMax,
  coverageRoundRobinSize,
  onCoverageMaxTotalParlaysChange,
  onCoverageScenarioMaxChange,
  onCoverageRoundRobinMaxChange,
  onCoverageRoundRobinSizeChange,
  onClearSlip,
  templatePulseAnalyze,
}: {
  picks: SelectedPick[]
  onRemovePick: (index: number) => void
  onClearSlip?: () => void
  templatePulseAnalyze?: boolean
  onAnalyze: () => void
  isAnalyzing: boolean
  onSave: (title?: string) => void
  isSaving: boolean
  onGenerateCounter: () => void
  isGeneratingCounter: boolean
  counterMode: CounterParlayMode
  onCounterModeChange: (mode: CounterParlayMode) => void
  counterTargetLegs: number
  onCounterTargetLegsChange: (value: number) => void
  onGenerateCoveragePack: () => void
  isGeneratingCoveragePack: boolean
  coverageMaxTotalParlays: number
  coverageScenarioMax: number
  coverageRoundRobinMax: number
  coverageRoundRobinSize: number
  onCoverageMaxTotalParlaysChange: (value: number) => void
  onCoverageScenarioMaxChange: (value: number) => void
  onCoverageRoundRobinMaxChange: (value: number) => void
  onCoverageRoundRobinSizeChange: (value: number) => void
}) {
  const [title, setTitle] = useState<string>("")
  const [pulseAnalyze, setPulseAnalyze] = useState(false)

  useEffect(() => {
    if (templatePulseAnalyze) {
      setPulseAnalyze(true)
      const t = setTimeout(() => setPulseAnalyze(false), 1200)
      return () => clearTimeout(t)
    }
  }, [templatePulseAnalyze])

  const tooManyLegs = picks.length > MAX_CUSTOM_PARLAY_LEGS
  const overBy = Math.max(0, picks.length - MAX_CUSTOM_PARLAY_LEGS)
  const canAnalyze = picks.length >= MIN_CUSTOM_PARLAY_LEGS && !tooManyLegs && !isAnalyzing
  const canSave = picks.length >= MIN_CUSTOM_PARLAY_LEGS && !tooManyLegs && !isSaving
  const canCounter = picks.length >= MIN_PICKS_FOR_HEDGES && !tooManyLegs && !isGeneratingCounter

  const maxTarget = Math.max(1, Math.min(picks.length, MAX_CUSTOM_PARLAY_LEGS))

  return (
    <div
      className="bg-black/60 border border-white/10 rounded-xl p-3 sm:p-4 sticky top-2 sm:top-4 space-y-4"
      data-testid="parlay-slip"
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-white font-bold text-lg">Your Parlay</h3>
        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-1 rounded text-sm ${
              tooManyLegs
                ? "bg-red-500/20 text-red-300 border border-red-500/30"
                : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
            }`}
          >
            Your picks: {picks.length}/{MAX_CUSTOM_PARLAY_LEGS}
          </span>
          {onClearSlip && picks.length > 0 && (
            <button
              type="button"
              onClick={onClearSlip}
              className="text-white/60 hover:text-white text-xs font-medium px-2 py-1 rounded border border-white/20 hover:border-white/40 transition-all"
            >
              Clear slip
            </button>
          )}
        </div>
      </div>

      {tooManyLegs && (
        <div className="bg-red-500/15 border border-red-500/30 rounded-lg p-3 text-red-200 text-sm">
          You can analyze up to {MAX_CUSTOM_PARLAY_LEGS} picks at once. Remove {overBy} pick{overBy !== 1 ? "s" : ""} to continue.
        </div>
      )}

      {picks.length === 0 ? (
        <div className="text-white/40 text-center py-8">
          <p>Select picks from the games list</p>
          <p className="text-sm mt-2">Minimum {MIN_CUSTOM_PARLAY_LEGS} pick required</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto" data-testid="pg-selected-picks">
          {picks.map((pick, index) => (
            <motion.div
              key={`${pick.game_id}-${pick.market_type}-${pick.pick}`}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="bg-white/5 border border-white/10 rounded-lg p-3 flex items-center justify-between"
            >
              <div className="flex-1">
                <div className="text-white/60 text-xs">{pick.gameDisplay}</div>
                <div className="text-white font-medium">{pick.pickDisplay}</div>
                <div className="text-emerald-400 text-sm">{pick.oddsDisplay}</div>
              </div>
              <button onClick={() => onRemovePick(index)} className="text-red-400 hover:text-red-300 p-1">
                ✕
              </button>
            </motion.div>
          ))}
        </div>
      )}

      <div className="space-y-3">
        <div className="rounded-lg border border-white/10 bg-white/5 p-3 space-y-2">
          <div className="text-white/80 text-sm font-semibold">Save Parlay</div>
          <label className="text-xs text-white/60">
            Title (optional)
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={picks.length === 0}
              placeholder="e.g., Sunday slate hedged ticket"
              className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-2 text-white placeholder-white/30"
            />
          </label>
        </div>

        <button
          data-testid="pg-save-slip"
          onClick={() => onSave(title.trim() || undefined)}
          disabled={!canSave}
          className={`w-full py-3 rounded-lg font-bold transition-all ${
            canSave
              ? "bg-gradient-to-r from-cyan-400 to-emerald-500 text-black hover:from-cyan-300 hover:to-emerald-400"
              : "bg-white/10 text-white/40 cursor-not-allowed"
          }`}
        >
          {isSaving ? "Saving..." : "Save Parlay"}
        </button>

        <button
          type="button"
          onClick={onAnalyze}
          disabled={!canAnalyze}
          data-testid="pg-analyze-slip"
          className={`w-full py-3 rounded-lg font-bold transition-all ${
            canAnalyze
              ? "bg-gradient-to-r from-emerald-500 to-green-500 text-black hover:from-emerald-400 hover:to-green-400"
              : "bg-white/10 text-white/40 cursor-not-allowed"
          } ${pulseAnalyze ? "ring-2 ring-emerald-400 ring-offset-2 ring-offset-black animate-pulse" : ""}`}
        >
          {isAnalyzing ? (
            <span className="flex items-center justify-center gap-2">
              <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                🦍
              </motion.span>
              Analyzing...
            </span>
          ) : tooManyLegs ? (
            `Remove ${overBy} pick${overBy !== 1 ? "s" : ""} (max ${MAX_CUSTOM_PARLAY_LEGS})`
          ) : (
            "Get AI Analysis"
          )}
        </button>

        {/* Counter Ticket (Hedge) */}
        <div className="rounded-lg border border-white/5 bg-white/2 p-3 space-y-2">
          <div className="text-white/40 text-sm font-semibold">Counter Ticket (Hedge)</div>
          {picks.length < MIN_PICKS_FOR_HEDGES ? (
            <p className="text-xs text-white/30">
              {picks.length < 1 ? "Add picks to unlock hedges." : "Add at least 2 picks to generate a counter ticket."}
            </p>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-2">
                <label className="text-xs text-white/30">
                  Picks
                  <input
                    type="number"
                    min={1}
                    max={maxTarget}
                    value={Math.min(counterTargetLegs, maxTarget)}
                    onChange={(e) => onCounterTargetLegsChange(Math.max(1, Math.min(maxTarget, Number(e.target.value) || 1)))}
                    className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                  />
                </label>
                <label className="text-xs text-white/30">
                  Mode
                  <select
                    value={counterMode}
                    onChange={(e) => onCounterModeChange((e.target.value as "best_edges" | "flip_all") || "best_edges")}
                    className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                  >
                    <option value="best_edges">Safer hedge</option>
                    <option value="flip_all">Flip all</option>
                  </select>
                </label>
              </div>
              <button
                data-testid="pg-generate-counter"
                onClick={onGenerateCounter}
                disabled={!canCounter || isGeneratingCounter}
                className="w-full py-2.5 rounded-lg font-bold transition-all bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingCounter ? "Generating…" : "Generate Counter Ticket"}
              </button>
              <p className="text-[11px] text-white/30 leading-snug">
                This creates a backup ticket that takes the other side of your riskiest picks.
              </p>
            </>
          )}
        </div>

        <CoveragePackControls
          picksCount={picks.length}
          disabled={tooManyLegs}
          maxTotalParlays={coverageMaxTotalParlays}
          scenarioMax={coverageScenarioMax}
          roundRobinMax={coverageRoundRobinMax}
          roundRobinSize={coverageRoundRobinSize}
          onMaxTotalParlaysChange={onCoverageMaxTotalParlaysChange}
          onScenarioMaxChange={onCoverageScenarioMaxChange}
          onRoundRobinMaxChange={onCoverageRoundRobinMaxChange}
          onRoundRobinSizeChange={onCoverageRoundRobinSizeChange}
          onGenerate={onGenerateCoveragePack}
          isGenerating={isGeneratingCoveragePack}
        />
      </div>
    </div>
  )
}


