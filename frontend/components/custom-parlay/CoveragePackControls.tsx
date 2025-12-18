"use client"

import { useMemo } from "react"

function formatInt(n: number) {
  try {
    return new Intl.NumberFormat("en-US").format(n)
  } catch {
    return String(n)
  }
}

function comb(n: number, k: number) {
  if (k < 0 || k > n) return 0
  if (k === 0 || k === n) return 1
  const kk = Math.min(k, n - k)
  let result = 1
  for (let i = 1; i <= kk; i++) {
    result = (result * (n - (kk - i))) / i
  }
  return Math.round(result)
}

export function CoveragePackControls({
  picksCount,
  disabled,
  maxTotalParlays,
  scenarioMax,
  roundRobinMax,
  roundRobinSize,
  onMaxTotalParlaysChange,
  onScenarioMaxChange,
  onRoundRobinMaxChange,
  onRoundRobinSizeChange,
  onGenerate,
  isGenerating,
}: {
  picksCount: number
  disabled: boolean
  maxTotalParlays: number
  scenarioMax: number
  roundRobinMax: number
  roundRobinSize: number
  onMaxTotalParlaysChange: (value: number) => void
  onScenarioMaxChange: (value: number) => void
  onRoundRobinMaxChange: (value: number) => void
  onRoundRobinSizeChange: (value: number) => void
  onGenerate: () => void
  isGenerating: boolean
}) {
  const n = Math.max(0, picksCount)
  const totalScenarios = useMemo(() => (n >= 1 ? Math.pow(2, n) : 0), [n])

  const rrEnabled = n >= 2 && roundRobinMax > 0
  const roundRobinSizeMax = Math.max(2, n)
  const maxTotal = Math.max(1, Math.min(20, Math.trunc(maxTotalParlays || 20)))
  const scenarioMaxClamped = Math.max(0, Math.min(20, Math.trunc(scenarioMax || 0)))
  const rrMaxClamped = Math.max(0, Math.min(20, Math.trunc(roundRobinMax || 0)))
  const rrSizeClamped = Math.max(2, Math.min(roundRobinSizeMax, Math.trunc(roundRobinSize || 2)))

  const sumMax = scenarioMaxClamped + rrMaxClamped
  const sumTooHigh = sumMax > maxTotal

  const canGenerate = !disabled && n >= 1 && !sumTooHigh && maxTotal > 0 && !isGenerating

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-3 space-y-3">
      <div className="text-white/80 text-sm font-semibold">Upset Possibilities</div>
      <div className="text-xs text-white/60">
        With {n} game{n !== 1 ? "s" : ""}, there are <span className="text-white font-semibold">{formatInt(totalScenarios)}</span>{" "}
        possible flip-combinations (2^{n}).
      </div>
      {n > 0 && (
        <details className="text-xs text-white/60">
          <summary className="cursor-pointer select-none">Breakdown by # of upsets (C(n,k))</summary>
          <div className="mt-2 grid grid-cols-2 gap-2">
            {Array.from({ length: n + 1 }).map((_, k) => (
              <div key={k} className="flex items-center justify-between bg-black/30 border border-white/10 rounded px-2 py-1">
                <span>{k} upset{k !== 1 ? "s" : ""}</span>
                <span className="text-white/80">{formatInt(comb(n, k))}</span>
              </div>
            ))}
          </div>
        </details>
      )}

      <div className="border-t border-white/10 pt-3 space-y-2">
        <div className="text-white/80 text-sm font-semibold">Coverage Pack (max 20 tickets)</div>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs text-white/60">
            Total cap
            <input
              type="number"
              min={1}
              max={20}
              value={maxTotal}
              onChange={(e) => onMaxTotalParlaysChange(Number(e.target.value))}
              className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
            />
          </label>
          <label className="text-xs text-white/60">
            Scenario tickets
            <input
              type="number"
              min={0}
              max={20}
              value={scenarioMaxClamped}
              onChange={(e) => onScenarioMaxChange(Number(e.target.value))}
              className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
            />
          </label>
          <label className="text-xs text-white/60">
            Round-robin tickets
            <input
              type="number"
              min={0}
              max={20}
              value={rrMaxClamped}
              onChange={(e) => onRoundRobinMaxChange(Number(e.target.value))}
              className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
            />
          </label>
          <label className="text-xs text-white/60">
            Round-robin size
            <input
              type="number"
              min={2}
              max={roundRobinSizeMax}
              value={rrSizeClamped}
              onChange={(e) => onRoundRobinSizeChange(Number(e.target.value))}
              className="mt-1 w-full bg-black/40 border border-white/10 rounded px-2 py-1 text-white"
              disabled={n < 2}
            />
          </label>
        </div>

        {sumTooHigh && (
          <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded p-2">
            Scenario max + round-robin max must be ≤ total cap.
          </div>
        )}
        {rrEnabled && rrSizeClamped > n && (
          <div className="text-xs text-red-300 bg-red-500/10 border border-red-500/30 rounded p-2">
            Round-robin size must be ≤ number of selected legs.
          </div>
        )}
        {n < 2 && rrMaxClamped > 0 && (
          <div className="text-xs text-amber-200 bg-amber-500/10 border border-amber-500/30 rounded p-2">
            Round-robin requires at least 2 legs. Add more games or set round-robin tickets to 0.
          </div>
        )}

        <button
          onClick={onGenerate}
          disabled={!canGenerate}
          className={`w-full py-2.5 rounded-lg font-bold transition-all ${
            canGenerate
              ? "bg-gradient-to-r from-purple-500 to-fuchsia-600 text-white hover:from-purple-400 hover:to-fuchsia-500"
              : "bg-white/10 text-white/40 cursor-not-allowed"
          }`}
        >
          {isGenerating ? "Generating coverage pack..." : "Generate Coverage Pack"}
        </button>
        <p className="text-[11px] text-white/50 leading-snug">
          Scenario tickets cover different upset combinations on the same games. Round-robin tickets cover by omitting games so one upset doesn’t bust every ticket.
        </p>
      </div>
    </div>
  )
}


