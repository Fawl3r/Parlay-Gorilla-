"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import type { CounterParlayMode } from "@/lib/api"
import type { SelectedPick } from "@/components/custom-parlay/types"
import { CoveragePackControls } from "@/components/custom-parlay/CoveragePackControls"

export const MAX_CUSTOM_PARLAY_LEGS = 20
export const MIN_CUSTOM_PARLAY_LEGS = 1

export function ParlaySlip({
  picks,
  onRemovePick,
  onAnalyze,
  isAnalyzing,
  onSave,
  isSaving,
  verifyOnChain,
  onVerifyOnChainChange,
  canVerifyOnChain,
  inscriptionCostUsd,
  customAiRemaining,
  customAiLimit,
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
}: {
  picks: SelectedPick[]
  onRemovePick: (index: number) => void
  onAnalyze: () => void
  isAnalyzing: boolean
  onSave: (title?: string) => void
  isSaving: boolean
  verifyOnChain: boolean
  onVerifyOnChainChange: (value: boolean) => void
  canVerifyOnChain: boolean
  inscriptionCostUsd: number
  customAiRemaining: number
  customAiLimit: number
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

  const tooManyLegs = picks.length > MAX_CUSTOM_PARLAY_LEGS
  const overBy = Math.max(0, picks.length - MAX_CUSTOM_PARLAY_LEGS)
  const canAnalyze = picks.length >= MIN_CUSTOM_PARLAY_LEGS && !tooManyLegs && !isAnalyzing
  const canSave = picks.length >= MIN_CUSTOM_PARLAY_LEGS && !tooManyLegs && !isSaving
  const canCounter = picks.length >= MIN_CUSTOM_PARLAY_LEGS && !tooManyLegs && !isGeneratingCounter

  const maxTarget = Math.max(1, Math.min(picks.length, MAX_CUSTOM_PARLAY_LEGS))

  return (
    <div className="bg-black/60 border border-white/10 rounded-xl p-3 sm:p-4 sticky top-2 sm:top-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-white font-bold text-lg">Your Parlay</h3>
        <span
          className={`px-2 py-1 rounded text-sm ${
            tooManyLegs
              ? "bg-red-500/20 text-red-300 border border-red-500/30"
              : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
          }`}
        >
          {picks.length}/{MAX_CUSTOM_PARLAY_LEGS} leg{picks.length !== 1 ? "s" : ""}
        </span>
      </div>

      {tooManyLegs && (
        <div className="bg-red-500/15 border border-red-500/30 rounded-lg p-3 text-red-200 text-sm">
          Max {MAX_CUSTOM_PARLAY_LEGS} legs per analysis. Remove {overBy} leg{overBy !== 1 ? "s" : ""} to continue.
        </div>
      )}

      {picks.length === 0 ? (
        <div className="text-white/40 text-center py-8">
          <p>Select picks from the games list</p>
          <p className="text-sm mt-2">Minimum {MIN_CUSTOM_PARLAY_LEGS} leg required</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-[400px] overflow-y-auto">
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
          <div className="rounded-lg border border-white/10 bg-black/30 p-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="text-xs font-semibold text-white/80">Verify on-chain (optional)</div>
                <div className="mt-1 text-[11px] text-white/50 leading-snug">
                  Opt-in per parlay. Costs ${inscriptionCostUsd.toFixed(2)} when you choose it.
                </div>
                {canVerifyOnChain ? (
                  <div className="mt-1 text-[11px] text-white/50">
                    Custom AI remaining this period: {customAiRemaining}/{customAiLimit < 0 ? "∞" : customAiLimit}
                  </div>
                ) : (
                  <div className="mt-1 text-[11px] text-white/50">Premium required for on-chain verification.</div>
                )}
              </div>
              <label className="shrink-0 inline-flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={verifyOnChain}
                  onChange={(e) => onVerifyOnChainChange(e.target.checked)}
                  disabled={!canVerifyOnChain || picks.length === 0}
                  className="h-4 w-4 accent-emerald-400"
                  aria-label="Verify this parlay on-chain"
                />
                <span className="text-xs text-white/70">{verifyOnChain ? "On" : "Off"}</span>
              </label>
            </div>
          </div>
        </div>

        <button
          onClick={() => onSave(title.trim() || undefined)}
          disabled={!canSave}
          className={`w-full py-3 rounded-lg font-bold transition-all ${
            canSave
              ? "bg-gradient-to-r from-cyan-400 to-emerald-500 text-black hover:from-cyan-300 hover:to-emerald-400"
              : "bg-white/10 text-white/40 cursor-not-allowed"
          }`}
        >
          {isSaving ? "Saving..." : verifyOnChain && canVerifyOnChain ? "Save + Verify" : "Save Parlay"}
        </button>

        <button
          onClick={onAnalyze}
          disabled={!canAnalyze}
          className={`w-full py-3 rounded-lg font-bold transition-all ${
            canAnalyze
              ? "bg-gradient-to-r from-emerald-500 to-green-500 text-black hover:from-emerald-400 hover:to-green-400"
              : "bg-white/10 text-white/40 cursor-not-allowed"
          }`}
        >
          {isAnalyzing ? (
            <span className="flex items-center justify-center gap-2">
              <motion.span animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
                🦍
              </motion.span>
              Analyzing...
            </span>
          ) : tooManyLegs ? (
            `Remove ${overBy} leg${overBy !== 1 ? "s" : ""} (max ${MAX_CUSTOM_PARLAY_LEGS})`
          ) : (
            "Get AI Analysis"
          )}
        </button>

        {/* Counter ticket controls */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-3 space-y-2">
          <div className="text-white/80 text-sm font-semibold">Counter / Upset Ticket</div>
          <div className="grid grid-cols-2 gap-2">
            <label className="text-xs text-white/60">
              Legs
              <input
                type="number"
                min={1}
                max={maxTarget}
                value={Math.min(counterTargetLegs, maxTarget)}
                onChange={(e) => onCounterTargetLegsChange(Number(e.target.value))}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
              />
            </label>
            <label className="text-xs text-white/60">
              Mode
              <select
                value={counterMode}
                onChange={(e) => onCounterModeChange(e.target.value as CounterParlayMode)}
                className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
              >
                <option value="best_edges">Best edges</option>
                <option value="flip_all">Flip all</option>
              </select>
            </label>
          </div>

          <button
            onClick={onGenerateCounter}
            disabled={!canCounter}
            className={`w-full py-2.5 rounded-lg font-bold transition-all ${
              canCounter
                ? "bg-gradient-to-r from-emerald-500 to-green-600 text-black hover:from-emerald-400 hover:to-green-500"
                : "bg-white/10 text-white/40 cursor-not-allowed"
            }`}
          >
            {isGeneratingCounter ? "Building counter ticket..." : "Generate Counter Ticket"}
          </button>
          <p className="text-[11px] text-white/50 leading-snug">
            Best edges = flips the games where the model sees the strongest value against your picks. Flip all = strict opposite of every leg.
          </p>
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


