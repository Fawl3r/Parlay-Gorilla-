"use client"

export function StatChip({
  label,
  value,
  tone = "emerald",
}: {
  label: string
  value: string
  tone?: "emerald" | "cyan"
}) {
  const toneClasses =
    tone === "cyan"
      ? "border-cyan-400/25 bg-cyan-500/10 text-cyan-200"
      : "border-[#00FF5E]/25 bg-[#00FF5E]/10 text-emerald-200"

  return (
    <div className={`rounded-xl border px-4 py-3 backdrop-blur-sm ${toneClasses}`}>
      <div className="text-[11px] uppercase tracking-wider opacity-80">{label}</div>
      <div className="text-lg font-black leading-tight">{value}</div>
    </div>
  )
}



