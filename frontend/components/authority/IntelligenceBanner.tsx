"use client"

/**
 * Persistent intelligence banner — top of app.
 * Authority layer: institutional presence, no hype.
 */
export function IntelligenceBanner() {
  return (
    <div
      className="w-full border-b border-white/5 bg-black/20 py-1.5 px-3 text-center"
      role="status"
      aria-label="Platform status"
    >
      <p className="text-[10px] md:text-[11px] font-medium tracking-wide text-white/50 uppercase">
        Parlay Gorilla Intelligence System Active
      </p>
      <p className="text-[9px] md:text-[10px] text-white/40 mt-0.5">
        Multi-sport analytical models running.
      </p>
    </div>
  )
}
