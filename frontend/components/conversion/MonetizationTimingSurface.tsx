"use client"

import { useEffect, useState } from "react"
import {
  getRecommendedSurface,
  markPromptShownThisSession,
  recordDismissal,
  emitIntentEvent,
  type UpgradeSurfaceType,
} from "@/lib/monetization-timing"
import { ValueReinforcementStrip } from "./ValueReinforcementStrip"
import { SoftUpgradeEngaged } from "./SoftUpgradeEngaged"
import { SoftUpgradePowerUser } from "./SoftUpgradePowerUser"
import { SoftUpgradeHighIntent } from "./SoftUpgradeHighIntent"
import { cn } from "@/lib/utils"

export type MonetizationTimingSurfaceProps = {
  /** Where this is shown: after_analysis, after_builder, after_blurred, after_scroll */
  context: string
  /** Value reinforcement: show before upgrade prompt when available */
  analysisUpdated?: boolean
  modelEdge?: boolean
  researchDepth?: "high" | "medium" | "low" | null
  /** Only render when this is true (e.g. after scroll completion). Never on load. */
  visible: boolean
  /** When false (subscription still loading), render nothing to avoid flicker. Default true. */
  authResolved?: boolean
  /** When true, render nothing (premium users never see upgrade surfaces). */
  isPremium?: boolean
  className?: string
}

/**
 * Renders the appropriate soft upgrade surface when intent threshold and timing allow.
 * Max one per session; 24h cooldown after dismiss; never interrupts workflow.
 */
export function MonetizationTimingSurface({
  context,
  analysisUpdated,
  modelEdge,
  researchDepth,
  visible,
  authResolved = true,
  isPremium = false,
  className,
}: MonetizationTimingSurfaceProps) {
  const [surface, setSurface] = useState<UpgradeSurfaceType | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!mounted || !visible || isPremium || !authResolved) return
    const recommended = getRecommendedSurface()
    if (!recommended) return
    setSurface(recommended)
    markPromptShownThisSession(recommended)
    emitIntentEvent("upgrade_prompt_shown", { surface: recommended, context })
  }, [mounted, visible, context, isPremium, authResolved])

  const handleDismiss = () => {
    if (!surface) return
    recordDismissal(surface)
    emitIntentEvent("upgrade_dismissed", { surface })
    setSurface(null)
  }

  const handleLearnMore = () => {
    emitIntentEvent("upgrade_learn_more_clicked", { context })
  }

  const handleViewPlans = () => {
    emitIntentEvent("upgrade_view_plans_clicked", { context })
  }

  if (!visible || !surface || isPremium || !authResolved) return null

  const showValueStrip = analysisUpdated || modelEdge || researchDepth

  return (
    <div className={cn("space-y-2", className)}>
      {showValueStrip && (
        <ValueReinforcementStrip
          analysisUpdated={analysisUpdated}
          modelEdge={modelEdge}
          researchDepth={researchDepth ?? undefined}
        />
      )}
      {surface === "engaged" && <SoftUpgradeEngaged />}
      {surface === "powerUser" && (
        <SoftUpgradePowerUser onDismiss={handleDismiss} onLearnMore={handleLearnMore} />
      )}
      {surface === "highIntent" && (
        <SoftUpgradeHighIntent onDismiss={handleDismiss} onViewPlans={handleViewPlans} />
      )}
      {/* Link click tracking: wrap or rely on default - we emit on click in parent if needed. Links are to /pricing; event hooks already in SoftUpgrade* for Learn More / View Plans. */}
    </div>
  )
}
