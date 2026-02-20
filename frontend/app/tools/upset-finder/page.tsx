"use client"

import { DashboardLayout } from "@/components/layout/DashboardLayout"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { DashboardAccountCommandCenter } from "@/components/usage/DashboardAccountCommandCenter"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { useSubscription } from "@/lib/subscription-context"
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay"
import { UpsetFinderView } from "./UpsetFinderView"

export default function UpsetFinderPage() {
  return (
    <ProtectedRoute>
      <UpsetFinderPageContent />
    </ProtectedRoute>
  )
}

function UpsetFinderPageContent() {
  const { isPremium, isCreditUser, canUseUpsetFinder } = useSubscription()

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col relative overflow-x-hidden bg-gradient-to-b from-black via-black/95 to-black/90">
        <AnimatedBackground variant="intense" />
        <div className="flex-1 relative z-10 flex flex-col">
          <section className="border-b border-white/10 bg-black/40 backdrop-blur-md">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-4 py-3 sm:py-4 md:py-5">
              <div className="mb-3 sm:mb-4 rounded-xl border border-white/10 bg-black/25 backdrop-blur-sm p-1.5 sm:p-2">
                <BalanceStrip compact />
              </div>
              <DashboardAccountCommandCenter />
            </div>
          </section>

          <section className="flex-1">
            <div className="w-full px-2 sm:container sm:mx-auto sm:px-3 md:px-4 py-3 sm:py-4 md:py-6 pb-24 sm:pb-6 md:pb-6">
              <UpsetFinderView />
            </div>
          </section>
        </div>
      </div>
      {isCreditUser && !isPremium && !canUseUpsetFinder && (
        <PremiumBlurOverlay
          title="Premium Page"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to access the Upset Finder."
        />
      )}
    </DashboardLayout>
  )
}
