"use client"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SportBackground } from "@/components/games/SportBackground"
import { PricingHeroSection } from "@/app/pricing/_components/PricingHeroSection"
import { usePricingCheckoutCoordinator } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"
import { PricingTabs, type PricingTabId } from "@/app/pricing/_components/PricingTabs"
import { PricingSubscriptionsCompact } from "@/app/pricing/_components/PricingSubscriptionsCompact"
import { CreditPacksSection } from "@/app/pricing/_components/CreditPacksSection"
import { PricingAccordion } from "@/app/pricing/_components/PricingAccordion"
import { PricingStickyCtaBar } from "@/app/pricing/_components/PricingStickyCtaBar"
import { useAuth } from "@/lib/auth-context"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { useState } from "react"

export default function PricingPage() {
  const checkout = usePricingCheckoutCoordinator()
  const { user } = useAuth()
  const [tab, setTab] = useState<PricingTabId>("subscriptions")

  return (
    <div className="min-h-screen flex flex-col relative" data-testid="pricing-page">
      <SportBackground imageUrl="/images/hero.png" overlay="strong" fit="cover" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1 py-10 md:py-14">
          <div className="container mx-auto px-4 max-w-6xl">
            <PricingHeroSection subscriptionsAnchorId="subscriptions" creditsAnchorId="credits" />

            {user ? (
              <div className="mt-6">
                <BalanceStrip />
              </div>
            ) : null}

            <PricingTabs value={tab} onChange={setTab} />

            <div className="mt-8 space-y-10 pb-24 sm:pb-0">
              {tab === "subscriptions" ? <PricingSubscriptionsCompact checkout={checkout} /> : null}
              {tab === "credits" ? <CreditPacksSection /> : null}

              <PricingAccordion title="Compare features">
                <ul className="list-disc pl-5 space-y-2">
                  <li>Premium: higher limits, more tools, and fewer restrictions.</li>
                  <li>Credits: pay-per-use access without a subscription.</li>
                  <li>Free: start exploring and upgrade when you want more.</li>
                </ul>
              </PricingAccordion>

              <PricingAccordion title="FAQ">
                <div className="space-y-4">
                  <div>
                    <div className="font-bold text-white">Do I need a subscription?</div>
                    <div className="text-gray-200/80">No. You can buy credit packs and pay per use.</div>
                  </div>
                  <div>
                    <div className="font-bold text-white">Can I cancel?</div>
                    <div className="text-gray-200/80">Card subscriptions can be canceled any time and remain active until the period ends.</div>
                  </div>
                  <div>
                    <div className="font-bold text-white">How do credits work?</div>
                    <div className="text-gray-200/80">Credits are deducted when you generate or unlock pay-per-use actions.</div>
                  </div>
                </div>
              </PricingAccordion>
            </div>
          </div>
        </main>

        <Footer />
      </div>

      <PricingStickyCtaBar
        onUpgrade={() => {
          setTab("subscriptions")
          if (typeof window !== "undefined") {
            window.setTimeout(() => {
              document.getElementById("subscriptions")?.scrollIntoView({ behavior: "smooth", block: "start" })
            }, 50)
          }
        }}
        onBuyCredits={() => {
          setTab("credits")
          if (typeof window !== "undefined") {
            window.setTimeout(() => {
              document.getElementById("credits")?.scrollIntoView({ behavior: "smooth", block: "start" })
            }, 50)
          }
        }}
      />
    </div>
  )
}
