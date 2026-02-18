import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import SportsShowcase from "@/components/SportsShowcase"
import { LandingHeroSection } from "./_components/landing/LandingHeroSection"
import { LandingTodayTopPicksSection } from "./_components/landing/LandingTodayTopPicksSection"
import { LandingStatsSection } from "./_components/landing/LandingStatsSection"
import { LandingFeaturesSection } from "./_components/landing/LandingFeaturesSection"
import { LandingHowItWorksSection } from "./_components/landing/LandingHowItWorksSection"
import { LandingCtaSection } from "./_components/landing/LandingCtaSection"
import { LandingDisclaimerSection } from "./_components/landing/LandingDisclaimerSection"

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        <LandingHeroSection />
        <LandingTodayTopPicksSection />
        <LandingStatsSection />

        {/* Sports Showcase - Gorilla Fade-In Section */}
        <SportsShowcase />

        <LandingFeaturesSection />

        <LandingHowItWorksSection />
        <LandingCtaSection />
        <LandingDisclaimerSection />
      </main>
      
      <Footer />
    </div>
  )
}
