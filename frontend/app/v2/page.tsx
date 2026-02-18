/**
 * V2 LANDING PAGE
 * Completely isolated redesign
 * Route: /v2
 */

import { V2HeroSection } from '@/components/v2/landing/V2HeroSection'
import { V2LivePicksSection } from '@/components/v2/landing/V2LivePicksSection'
import { V2HowItWorksSection } from '@/components/v2/landing/V2HowItWorksSection'
import { V2WhySection } from '@/components/v2/landing/V2WhySection'
import { V2CtaSection } from '@/components/v2/landing/V2CtaSection'

export default function V2LandingPage() {
  return (
    <div className="min-h-screen bg-[#0A0F0A]">
      <V2HeroSection />
      <V2LivePicksSection />
      <V2HowItWorksSection />
      <V2WhySection />
      <V2CtaSection />
    </div>
  )
}
