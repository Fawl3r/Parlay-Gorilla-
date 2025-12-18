"use client"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

import { HeroSection } from "@/app/pg-101/_components/HeroSection"
import { EngineSection } from "@/app/pg-101/_components/EngineSection"
import { ValueSection } from "@/app/pg-101/_components/ValueSection"
import { DifferentSection } from "@/app/pg-101/_components/DifferentSection"
import { OnChainProofSection } from "@/app/pg-101/_components/OnChainProofSection"
import { CtaSection } from "@/app/pg-101/_components/CtaSection"

export default function PG101Page() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0A0F0A] overflow-hidden">
      <Header />

      <main className="flex-1 relative z-10">
        <HeroSection />
        <EngineSection />
        <ValueSection />
        <DifferentSection />
        <OnChainProofSection />
        <CtaSection />
      </main>

      <Footer />
    </div>
  )
}
