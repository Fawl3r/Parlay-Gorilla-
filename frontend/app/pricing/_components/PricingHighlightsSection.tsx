"use client"

import { motion } from "framer-motion"
import { BarChart2, Brain, Radio, Sparkles, Target } from "lucide-react"

import { FEATURE_HIGHLIGHTS, FeatureHighlight } from "@/lib/pricingConfig"

function getHighlightIcon(emoji: string | undefined) {
  switch (emoji) {
    case "🧠":
      return Brain
    case "📡":
      return Radio
    case "🎯":
      return Target
    case "📈":
      return BarChart2
    default:
      return Sparkles
  }
}

function HighlightCard({ item, index }: { item: FeatureHighlight; index: number }) {
  const Icon = getHighlightIcon(item.icon)

  return (
    <motion.article
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.35, delay: index * 0.06 }}
      className="relative rounded-2xl bg-black/25 border border-white/10 backdrop-blur-xl overflow-hidden"
    >
      {/* Accent glow */}
      <div className="absolute inset-0 opacity-40 pointer-events-none">
        <div className="absolute -top-24 -left-24 h-56 w-56 rounded-full bg-emerald-500/20 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-56 w-56 rounded-full bg-cyan-500/15 blur-3xl" />
      </div>

      <div className="relative p-6">
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-300">
            <Icon className="h-4 w-4 text-emerald-300" />
            {item.isPremium ? "Premium" : "Free + Premium"}
            {item.comingSoon && (
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-medium uppercase tracking-wide">
                Coming Soon
              </span>
            )}
          </div>
          <div className="text-[10px] uppercase tracking-wide text-gray-400">Feature highlight</div>
        </div>

        <h3 className="text-xl font-bold text-white mb-2">{item.title}</h3>
        <p className="text-gray-300/90 text-sm leading-relaxed">{item.description}</p>
      </div>
    </motion.article>
  )
}

export function PricingHighlightsSection() {
  return (
    <section>
      <div className="flex items-end justify-between gap-4 mb-5">
        <div>
          <h2 className="text-2xl md:text-3xl font-black text-white">What you get</h2>
          <p className="text-sm text-gray-200/70 mt-1">Clear features and honest limits — no fluff.</p>
        </div>
        <div className="hidden md:flex items-center gap-2 text-xs text-gray-200/70">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Updated as we ship
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {FEATURE_HIGHLIGHTS.map((item, idx) => (
          <HighlightCard key={`${item.title}-${idx}`} item={item} index={idx} />
        ))}
      </div>
    </section>
  )
}
