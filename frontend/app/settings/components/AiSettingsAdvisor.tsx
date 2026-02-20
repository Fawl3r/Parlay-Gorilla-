"use client"

import { motion } from "framer-motion"
import { Sparkles, Lightbulb } from "lucide-react"
import { cn } from "@/lib/utils"

const RECOMMENDATIONS = [
  "Enable advanced insights for better performance tracking.",
  "Turn on AI recommendations to get personalized parlay tips.",
  "Keep beginner mode on if you prefer simpler explanations.",
]

interface AiSettingsAdvisorProps {
  className?: string
}

export function AiSettingsAdvisor({ className }: AiSettingsAdvisorProps) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 }}
      className={cn(
        "rounded-2xl border border-[#00FF5E]/20 bg-[#00FF5E]/5 backdrop-blur p-6",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="h-5 w-5 text-[#00FF5E]" />
        <h2 className="text-lg font-black text-white">Gorilla AI Setup Advisor</h2>
      </div>
      <p className="text-sm text-white/70 mb-4">
        Client-side suggestions to get the most from your account.
      </p>
      <ul className="space-y-3">
        {RECOMMENDATIONS.map((text, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-white/90">
            <Lightbulb className="h-4 w-4 text-[#00FF5E] shrink-0 mt-0.5" />
            {text}
          </li>
        ))}
      </ul>
    </motion.aside>
  )
}
