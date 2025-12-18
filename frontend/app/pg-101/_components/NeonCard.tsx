"use client"

import type { LucideIcon } from "lucide-react"
import { Check } from "lucide-react"

export function NeonCard({
  icon: Icon,
  title,
  description,
  bullets,
}: {
  icon: LucideIcon
  title: string
  description: string
  bullets: string[]
}) {
  return (
    <div className="group relative rounded-3xl border border-white/10 bg-black/40 backdrop-blur-xl p-6 md:p-7 overflow-hidden">
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-br from-[#00DD55]/10 via-transparent to-cyan-500/10" />
      <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-[#00DD55]/10 blur-[80px]" />
      <div className="absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-cyan-500/10 blur-[80px]" />

      <div className="relative">
        <div className="mb-4 flex items-center gap-3">
          <div className="h-11 w-11 rounded-2xl bg-[#00DD55]/10 border border-[#00DD55]/25 flex items-center justify-center">
            <Icon className="h-6 w-6 text-[#00DD55]" />
          </div>
          <div>
            <div className="text-lg font-black text-white">{title}</div>
            <div className="text-xs text-white/60">PG-101 module</div>
          </div>
        </div>

        <p className="text-sm md:text-[15px] text-gray-300 leading-relaxed mb-4">{description}</p>

        <ul className="space-y-2">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2 text-sm text-gray-200/90">
              <Check className="h-4 w-4 text-[#00DD55] mt-0.5 shrink-0" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}



