import type { Metadata } from "next"
import Link from "next/link"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { BalanceStrip } from "@/components/billing/BalanceStrip"
import { ParlayBuilder } from "@/components/ParlayBuilder"

export const metadata: Metadata = {
  title: "🦍 Gorilla Parlay Builder 🦍 | Parlay Gorilla",
  description:
    "Generate AI-powered parlays with real odds, win probability estimates, and risk profiles. Build slips across in-season sports.",
  alternates: {
    canonical: "/build",
  },
}

/**
 * Public AI Parlay Builder page.
 *
 * `/app` remains the authenticated dashboard; `/build` is the public entrypoint
 * used across marketing pages and CTAs.
 */
export default function BuildPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <section className="py-8">
          <div className="container mx-auto px-4">
            <div className="empty:hidden mb-4 rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm p-2">
              <BalanceStrip compact />
            </div>
            <ParlayBuilder />

            <div className="mt-10">
              <h2 className="text-lg font-black text-white">More ways to build</h2>
              <p className="mt-1 text-sm text-white/60">Explore alternate builder modes without cluttering navigation.</p>

              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <NavCard
                  href="/parlays/same-game"
                  title="Same-Game Builder"
                  description="Build a single-game slip with tighter correlation."
                />
                <NavCard
                  href="/parlays/round-robin"
                  title="Round Robin Builder"
                  description="Generate combinations for broader coverage."
                />
                <NavCard
                  href="/parlays/teasers"
                  title="Teaser Builder"
                  description="Adjust lines and explore risk tradeoffs."
                />
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

function NavCard({ href, title, description }: { href: string; title: string; description: string }) {
  return (
    <Link
      href={href}
      className={[
        "rounded-2xl border border-white/10 bg-white/[0.03] hover:bg-white/[0.06] transition-colors",
        "p-5 block",
      ].join(" ")}
    >
      <div className="text-white font-black">{title}</div>
      <div className="mt-1 text-sm text-white/60">{description}</div>
    </Link>
  )
}
