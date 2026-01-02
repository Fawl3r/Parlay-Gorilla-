"use client"

import Link from "next/link"
import { AlertTriangle, CheckCircle, FileText, Shield } from "lucide-react"

import { LegalPageLayout } from "@/components/legal/LegalPageLayout"

const LAST_UPDATED = "December 19, 2025"

export default function TermsPage() {
  return (
    <LegalPageLayout
      icon={FileText}
      lastUpdated={LAST_UPDATED}
      title={
        <>
          <span className="text-white">Terms of </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Service</span>
        </>
      }
    >
      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">1. Agreement to These Terms</h2>
        <p className="text-gray-400 leading-relaxed">
          By accessing or using Parlay Gorilla (the “Service”), you agree to these Terms of Service (“Terms”). If you do not
          agree, do not use the Service.
        </p>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Shield className="h-6 w-6 text-emerald-400" />
          2. Eligibility
        </h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            You must be at least 18 years old to use Parlay Gorilla.
          </p>
          <p>
            Parlay Gorilla is an analytics and research platform and does not facilitate gambling or wagering.
          </p>
          <p>
            By creating an account, you confirm you are at least 18 years old.
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">3. What Parlay Gorilla Is (and Is Not)</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            <strong className="text-white">
              Parlay Gorilla provides AI-assisted sports analytics and informational insights.
            </strong>{" "}
            We may show probability estimates, risk indicators, and analysis to help you make your own decisions.
          </p>

          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-amber-400 font-semibold mb-1">Important: Not a Sportsbook</p>
                <p className="text-amber-300 text-sm">
                  Parlay Gorilla does not accept bets, place wagers, set odds, or act as a sportsbook. We do not process
                  gambling transactions. Any betting decisions are your responsibility.
                </p>
              </div>
            </div>
          </div>

          <p>
            Parlay Gorilla is not affiliated with, endorsed by, or sponsored by any sportsbook. Sportsbook names and odds (if
            shown) are provided for informational comparison only.
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">4. No Guaranteed Outcomes</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            <strong className="text-white">Results are not guaranteed.</strong> Sports outcomes are unpredictable. Any models,
            probabilities, or insights we provide can be wrong, incomplete, or outdated.
          </p>
          <p>
            Parlay Gorilla is designed to save you hours of research and help you make your best informed attempt at building winning
            parlays by providing AI-assisted analysis, probability estimates, and explanations. You are responsible for your own
            decisions and any outcomes.
          </p>
          <p>
            You should never bet money you cannot afford to lose. If you need help, visit{" "}
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
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">5. Accounts and Acceptable Use</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>You are responsible for your account and must keep your login credentials secure.</p>
          <p>You agree not to:</p>
          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>Use the Service for any illegal purpose</li>
            <li>Attempt to access or disrupt our systems (including scraping or automation that harms performance)</li>
            <li>Bypass paywalls, limits, or security controls</li>
            <li>Impersonate others or provide false account information</li>
          </ul>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">6. Subscriptions, Billing, and Refunds</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            Paid features may be offered via subscriptions or one-time purchases. Payments are processed by third-party
            providers such as <strong className="text-white">Stripe</strong>. We do not store your full payment card details.
          </p>
          <p>
            <strong className="text-white">All purchases are final.</strong> Please review our{" "}
            <Link href="/refunds" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              Refund &amp; Cancellation Policy
            </Link>{" "}
            for details (including how to cancel and when access ends).
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">7. Termination</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            We may suspend or terminate your account or access to the Service at any time (for example, if you violate these
            Terms, misuse the Service, or for security reasons).
          </p>
          <p>
            You may stop using the Service at any time. If you have an active subscription, you can cancel it (see{" "}
            <Link href="/refunds" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              /refunds
            </Link>
            ).
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">8. Disclaimer</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            The Service is provided for informational and entertainment purposes only. It is not financial, investment, or
            legal advice. For more, see our{" "}
            <Link href="/disclaimer" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              Disclaimer
            </Link>
            .
          </p>
        </div>
      </section>

      <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">9. Contact Information</h2>
        <div className="space-y-4 text-gray-300 leading-relaxed">
          <p>If you have questions about these Terms, contact us at:</p>
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

