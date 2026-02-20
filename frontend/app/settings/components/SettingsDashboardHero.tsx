"use client"

import { motion } from "framer-motion"
import { Sliders, Sparkles, Bell, Shield } from "lucide-react"
import { cn } from "@/lib/utils"

export type QuickToggleId = "beginner" | "aiGuidance" | "notifications" | "privacy"

export interface ToggleState {
  beginner: boolean
  aiGuidance: "minimal" | "standard" | "advanced"
  notifications: boolean
  privacy: boolean
}

interface SettingsDashboardHeroProps {
  toggles: ToggleState
  onToggle: (id: QuickToggleId, value: boolean | string) => void
  className?: string
}

function QuickToggle({
  icon: Icon,
  label,
  description,
  checked,
  onChange,
}: {
  icon: React.ElementType
  label: string
  description: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:border-white/15 transition-colors">
      <div className="flex items-center gap-2 mb-2">
        <Icon className="h-4 w-4 text-[#00FF5E]" />
        <span className="font-bold text-white text-sm">{label}</span>
      </div>
      <p className="text-xs text-white/50 mb-3">{description}</p>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative w-12 h-6 rounded-full transition-colors",
          checked ? "bg-[#00FF5E]" : "bg-white/20"
        )}
      >
        <span
          className={cn(
            "absolute top-1 w-4 h-4 rounded-full bg-white transition-transform",
            checked ? "left-7" : "left-1"
          )}
        />
      </button>
    </div>
  )
}

export function SettingsDashboardHero({
  toggles,
  onToggle,
  className,
}: SettingsDashboardHeroProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(
        "relative rounded-2xl border overflow-hidden",
        "bg-gradient-to-br from-white/[0.08] to-white/[0.02] backdrop-blur-xl border-white/10",
        "shadow-[0_0_40px_-12px_rgba(0,255,94,0.12)]",
        className
      )}
    >
      <div className="absolute inset-0 rounded-2xl border border-[#00FF5E]/10 pointer-events-none opacity-80" />
      <div className="relative p-6 md:p-8">
        <div className="flex items-center gap-2 mb-2">
          <Sliders className="h-5 w-5 text-[#00FF5E]" />
          <h1 className="text-2xl md:text-3xl font-black text-white">Account Control</h1>
        </div>
        <p className="text-sm text-white/60 mb-6">
          Quick toggles for your experience. Changes save automatically.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <QuickToggle
            icon={Sparkles}
            label="Beginner Mode"
            description="Simpler explanations"
            checked={toggles.beginner}
            onChange={(v) => onToggle("beginner", v)}
          />
          <QuickToggle
            icon={Sparkles}
            label="AI Guidance Level"
            description={toggles.aiGuidance}
            checked={toggles.aiGuidance !== "minimal"}
            onChange={(v) => onToggle("aiGuidance", v ? "standard" : "minimal")}
          />
          <QuickToggle
            icon={Bell}
            label="Notifications"
            description="Alerts and recommendations"
            checked={toggles.notifications}
            onChange={(v) => onToggle("notifications", v)}
          />
          <QuickToggle
            icon={Shield}
            label="Privacy Mode"
            description="Reduce tracking"
            checked={toggles.privacy}
            onChange={(v) => onToggle("privacy", v)}
          />
        </div>
      </div>
    </motion.section>
  )
}
