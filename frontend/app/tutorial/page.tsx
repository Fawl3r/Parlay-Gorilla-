import type { Metadata } from "next"
import Link from "next/link"
import { ArrowRight, Book, Mail, Zap } from "lucide-react"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

import { TutorialTableOfContents } from "./_components/TutorialTableOfContents"
import { TutorialSection } from "./_components/TutorialSection"
import { TUTORIAL_SECTIONS } from "./_lib/tutorialContent"

export const metadata: Metadata = {
  title: "How to Use Parlay Gorilla (Tutorial) | Parlay Gorilla",
  description:
    "Learn Parlay Gorilla in minutes: build your first Gorilla Parlay, understand Gorilla Parlays vs Custom AI, credits and limits, automatic verification, and what to do next.",
  alternates: { canonical: "/tutorial" },
}

export default function TutorialPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f]" data-testid="tutorial-page">
      <Header />

      <main className="flex-1 py-16 sm:py-20">
        <div className="container mx-auto px-4 max-w-6xl">
          {/* Hero */}
          <section className="mb-10 sm:mb-12">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-6">
              <Book className="h-7 w-7 text-black" />
            </div>
            <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white">
              Tutorial: How to use Parlay Gorilla
            </h1>
            <p className="mt-4 text-base sm:text-lg text-white/70 max-w-3xl">
              A practical, click-by-click guide to build AI-powered parlays, explore game analytics, and
              understand what the numbers mean.
            </p>

            <div className="mt-6 flex flex-col sm:flex-row gap-3">
              <Link
                href="/build"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
              >
                <Zap className="h-5 w-5" />
                Start Building
                <ArrowRight className="h-5 w-5" />
              </Link>
              <Link
                href="/support"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/10 text-white/80 font-semibold rounded-lg hover:border-emerald-500/40 hover:bg-emerald-500/10 transition-all"
              >
                <Mail className="h-5 w-5 text-emerald-300" />
                Need help? Contact support
              </Link>
              <Link
                href="/app"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/10 bg-white/[0.03] text-white/80 font-semibold rounded-lg hover:border-emerald-500/40 hover:bg-emerald-500/10 transition-all"
              >
                Skip tutorial
                <ArrowRight className="h-5 w-5 text-emerald-300" />
              </Link>
            </div>

            <div className="mt-6 bg-white/[0.02] border border-white/10 rounded-2xl p-5">
              <p className="text-sm text-white/70">
                <span className="font-bold text-white">Reminder:</span> Parlay Gorilla provides AI-assisted
                sports analytics and informational insights. Not a sportsbook. Outcomes are not guaranteed.
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link
                  href="/disclaimer"
                  className="text-xs font-semibold text-emerald-300 hover:text-emerald-200 hover:underline"
                >
                  Read the full disclaimer
                </Link>
                <span className="text-white/30">•</span>
                <Link
                  href="/responsible-gaming"
                  className="text-xs font-semibold text-emerald-300 hover:text-emerald-200 hover:underline"
                >
                  Responsible gaming resources
                </Link>
              </div>
            </div>

            <div
              className="mt-6 rounded-2xl border border-emerald-500/20 bg-gradient-to-br from-emerald-950/40 to-cyan-950/30 p-6"
              data-testid="tutorial-quick-start"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl sm:text-2xl font-black text-white">Quick Start (60 seconds)</h2>
                  <p className="mt-2 text-sm text-white/70 max-w-3xl">
                    Build your first Gorilla Parlay fast. No sign-up required.
                  </p>
                </div>
                <Link
                  href="#what-parlay-gorilla-does"
                  className="text-sm font-bold text-emerald-300 hover:text-emerald-200 hover:underline"
                >
                  Read the basics ↓
                </Link>
              </div>

              <ol className="mt-4 grid gap-3 md:grid-cols-3">
                {[
                  { title: "1) Open", body: "Tap Start Building to open the AI Builder." },
                  { title: "2) Choose", body: "Pick a sport, set legs (2–4), and use Balanced." },
                  { title: "3) Generate", body: "Generate, then read Hit Probability + Confidence first." },
                ].map((s) => (
                  <li key={s.title} className="rounded-xl border border-white/10 bg-black/30 p-4">
                    <div className="text-sm font-black text-white">{s.title}</div>
                    <div className="mt-1 text-sm text-white/70">{s.body}</div>
                  </li>
                ))}
              </ol>

              <div className="mt-4 flex flex-wrap gap-2">
                <Link
                  href="/build"
                  className="inline-flex items-center gap-2 rounded-xl bg-emerald-500 px-4 py-2 text-sm font-black text-black hover:bg-emerald-400 transition-colors"
                >
                  Start Building
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/analysis"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-bold text-white/80 hover:bg-white/[0.06] transition-colors"
                >
                  Browse game analysis
                </Link>
                <Link
                  href="/pricing"
                  className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2 text-sm font-bold text-white/80 hover:bg-white/[0.06] transition-colors"
                >
                  Understand usage & billing
                </Link>
              </div>
            </div>
          </section>

          {/* Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-4">
              <div className="lg:sticky lg:top-24 space-y-4">
                <TutorialTableOfContents sections={TUTORIAL_SECTIONS} />
                <div className="bg-white/[0.02] border border-white/10 rounded-2xl p-5">
                  <h2 className="text-sm font-bold text-white">Quick links</h2>
                  <div className="mt-3 flex flex-col gap-2 text-sm">
                    <Link className="text-white/70 hover:text-emerald-300 transition-colors" href="/build">
                      AI Builder (public)
                    </Link>
                    <Link className="text-white/70 hover:text-emerald-300 transition-colors" href="/analysis">
                      Game Analytics (public)
                    </Link>
                    <Link className="text-white/70 hover:text-emerald-300 transition-colors" href="/auth/signup">
                      Create an account
                    </Link>
                    <Link className="text-white/70 hover:text-emerald-300 transition-colors" href="/pricing">
                      Pricing / Upgrade
                    </Link>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-8 space-y-12">
              {TUTORIAL_SECTIONS.map((section, idx) => (
                <TutorialSection key={section.id} section={section} isFirst={idx === 0} />
              ))}
            </div>
          </div>

          {/* Footer CTA */}
          <section className="mt-14 sm:mt-16 text-center">
            <div className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-3">Still stuck?</h2>
              <p className="text-white/70 mb-6 max-w-2xl mx-auto">
                If something isn’t working, use the support form or report a bug with what you clicked and
                what you expected to happen.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link
                  href="/support"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
                >
                  Contact Support
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  href="/report-bug"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-white/10 text-white/80 font-semibold rounded-lg hover:border-emerald-500/40 hover:bg-emerald-500/10 transition-all"
                >
                  Report a bug
                </Link>
              </div>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  )
}


