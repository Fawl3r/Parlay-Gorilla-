"use client"

import Link from "next/link"
import { AlertTriangle, CheckCircle } from "lucide-react"

import { LegalPageLayout } from "@/components/legal/LegalPageLayout"

const LAST_UPDATED = "December 19, 2025"

export default function DisclaimerPage() {
  return (
    <LegalPageLayout
      icon={AlertTriangle}
      lastUpdated={LAST_UPDATED}
      title={
        <>
          <span className="text-white">Sports &amp; </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
            Financial Disclaimer
          </span>
        </>
      }
    >
      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">1. Not a Sportsbook</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            <strong className="text-white">Parlay Gorilla does not accept bets, place wagers, or act as a sportsbook.</strong>{" "}
            We do not facilitate gambling transactions or take deposits.
          </p>
          <p>
            We are not affiliated with, endorsed by, or sponsored by any sportsbook. Any sportsbook names, odds, or lines shown
            are for informational comparison only.
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">2. Informational &amp; Entertainment Purposes Only</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            Parlay Gorilla provides AI-assisted sports analytics and informational insights. Content may include probability
            analysis, risk indicators, and general commentary.
          </p>
          <p>
            <strong className="text-white">This is not financial, investment, legal, or tax advice.</strong> You are responsible
            for your own decisions and actions.
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">3. No Guaranteed Outcomes</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            <strong className="text-white">No results are guaranteed.</strong> Sports outcomes are unpredictable. Our models and
            insights may be wrong, incomplete, or outdated.
          </p>
          <p>
            Parlay Gorilla is designed to save you hours of research by bringing odds, stats, and context into one place. Our goal
            is to help you make your best informed attempt at building winning parlays — but you are responsible for your own
            betting decisions.
          </p>
          <p>You should never bet money you cannot afford to lose.</p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">4. Responsible Gaming</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            Parlay Gorilla is intended for users who are <strong className="text-white">21+</strong> (and of legal gambling age
            in their jurisdiction).
          </p>
          <p>
            If you or someone you know needs help with problem gambling, visit{" "}
            <a
              href="https://www.ncpgambling.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-emerald-400 hover:text-emerald-300 hover:underline"
            >
              ncpgambling.org
            </a>{" "}
            or call{" "}
            <a href="tel:1-800-522-4700" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              1-800-522-4700
            </a>
            .
          </p>
          <p>
            You can also review our{" "}
            <Link href="/responsible-gaming" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              Responsible Gaming
            </Link>{" "}
            page.
          </p>
        </div>
      </section>

      <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">5. Contact</h2>
        <div className="space-y-4 text-gray-300 leading-relaxed">
          <p>If you have questions about this disclaimer, contact us at:</p>
          <div className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-400" />
            <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300 font-medium">
              contact@f3ai.dev
            </a>
          </div>
        </div>
      </section>
    </LegalPageLayout>
  )
}


