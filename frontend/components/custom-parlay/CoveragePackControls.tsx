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

  const canGenerate = !disabled && n >= 2 && !sumTooHigh && maxTotal > 0 && !isGenerating

  return (
    <div className="rounded-lg border border-white/5 bg-white/2 p-3 space-y-3">
      <div className="text-white/40 text-sm font-semibold">Upset Possibilities</div>
      {n < 2 ? (
        <p className="text-xs text-white/30">
          {n < 1 ? "Add picks to unlock hedges." : "Add at least 2 picks to generate coverage scenarios."}
        </p>
      ) : (
        <>
          <div className="text-xs text-white/30">
            With {n} game{n !== 1 ? "s" : ""}, there are{" "}
            <span className="text-white/40 font-semibold">{formatInt(totalScenarios)}</span> possible flip combinations.
          </div>
          {n > 0 && (
            <details className="text-xs text-white/30">
              <summary className="cursor-pointer select-none">Breakdown by # of upsets</summary>
              <div className="mt-2 grid grid-cols-2 gap-2">
                {Array.from({ length: n + 1 }).map((_, k) => (
                  <div key={k} className="flex items-center justify-between bg-black/20 border border-white/5 rounded px-2 py-1">
                    <span className="text-white/30">{k} upset{k !== 1 ? "s" : ""}</span>
                    <span className="text-white/30">{formatInt(comb(n, k))}</span>
                  </div>
                ))}
              </div>
            </details>
          )}

          <div className="border-t border-white/5 pt-3 space-y-2">
            <div className="text-white/40 text-sm font-semibold">Coverage Pack (Up to 20 hedge tickets)</div>
            <p className="text-[11px] text-white/30 leading-snug">
              A small set of backup tickets that cover the most likely upset scenarios.
            </p>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs text-white/30">
                Total cap
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={maxTotal}
                  onChange={(e) => onMaxTotalParlaysChange(Math.max(1, Math.min(20, Number(e.target.value) || 20)))}
                  className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                />
              </label>
              <label className="text-xs text-white/30">
                Scenario tickets
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={scenarioMaxClamped}
                  onChange={(e) => onScenarioMaxChange(Math.max(0, Math.min(20, Number(e.target.value) || 0)))}
                  className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                />
              </label>
              <label className="text-xs text-white/30">
                Rotate games tickets
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={rrMaxClamped}
                  onChange={(e) => onRoundRobinMaxChange(Math.max(0, Math.min(20, Number(e.target.value) || 0)))}
                  className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                />
              </label>
              <label className="text-xs text-white/30">
                Rotate size
                <input
                  type="number"
                  min={2}
                  max={roundRobinSizeMax}
                  value={rrSizeClamped}
                  onChange={(e) => onRoundRobinSizeChange(Math.max(2, Math.min(roundRobinSizeMax, Number(e.target.value) || 2)))}
                  className="mt-1 w-full bg-black/20 border border-white/10 rounded px-2 py-1 text-white/80"
                />
              </label>
            </div>

            <button
              onClick={onGenerate}
              disabled={!canGenerate}
              className="w-full py-2.5 rounded-lg font-bold transition-all bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Generate Coverage Pack
            </button>
          </div>
        </>
      )}
    </div>
  )
}


