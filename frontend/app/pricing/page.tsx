"use client"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { SportBackground } from "@/components/games/SportBackground"
import { PricingHeroSection } from "@/app/pricing/_components/PricingHeroSection"
import { PricingPlansSection } from "@/app/pricing/_components/PricingPlansSection"
import { PricingHighlightsSection } from "@/app/pricing/_components/PricingHighlightsSection"
import { PricingFinalCtaSection } from "@/app/pricing/_components/PricingFinalCtaSection"
import { usePricingCheckoutCoordinator } from "@/app/pricing/_hooks/usePricingCheckoutCoordinator"

export default function PricingPage() {
  const checkout = usePricingCheckoutCoordinator()

  return (
    <div className="min-h-screen flex flex-col relative" data-testid="pricing-page">
      <SportBackground imageUrl="/images/hero.png" overlay="strong" fit="cover" />

      <div className="relative z-10 min-h-screen flex flex-col">
        <Header />

        <main className="flex-1 py-10 md:py-14">
          <div className="container mx-auto px-4 max-w-6xl">
            <PricingHeroSection plansAnchorId="plans" />

            <div className="mt-10 md:mt-12 space-y-10 md:space-y-12">
              <PricingPlansSection
                sectionId="plans"
                loadingKey={checkout.loadingKey}
                onUpgradeCardMonthly={checkout.startCardMonthly}
                onUpgradeCardAnnual={checkout.startCardAnnual}
                onUpgradeCardLifetime={checkout.startCardLifetime}
                onUpgradeCryptoMonthly={checkout.startCryptoMonthly}
                onUpgradeCryptoAnnual={checkout.startCryptoAnnual}
                onUpgradeCryptoLifetime={checkout.startCryptoLifetime}
              />

              <PricingHighlightsSection />

              <PricingFinalCtaSection plansAnchorId="plans" />
            </div>
          </div>
        </main>

        <Footer />
      </div>
    </div>
  )
}
