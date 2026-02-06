"use client"

type Props = {
  title?: string
  blockers?: string[]
  className?: string
}

function formatBlocker(b: string): string {
  return b
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/^\w/, (c) => c.toUpperCase())
}

export function ConfidenceUnavailableCard({
  title = "Confidence Breakdown",
  blockers = [],
  className,
}: Props) {
  return (
    <div className={`rounded-2xl border border-white/10 bg-black/40 p-4 shadow-sm ${className ?? ""}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-white">{title}</h3>
        <span className="rounded-full bg-white/10 px-2 py-1 text-xs font-semibold text-white/70">
          Unavailable
        </span>
      </div>

      <p className="mt-2 text-sm text-white/70">
        Confidence couldn’t be calculated for this matchup due to missing or low-quality inputs.
        The pick and win probability are still shown normally.
      </p>

      {blockers.length > 0 && (
        <div className="mt-3">
          <div className="text-xs font-semibold text-white/60">Reason(s)</div>
          <ul className="mt-2 space-y-1">
            {blockers.slice(0, 5).map((b) => (
              <li key={b} className="text-sm text-white/70">
                • {formatBlocker(b)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
