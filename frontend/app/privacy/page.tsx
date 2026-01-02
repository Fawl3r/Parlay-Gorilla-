"use client"

import { AlertCircle, CheckCircle, Database, Eye, Lock, Shield } from "lucide-react"

import { LegalPageLayout } from "@/components/legal/LegalPageLayout"

const LAST_UPDATED = "December 19, 2025"

export default function PrivacyPage() {
  return (
    <LegalPageLayout
      icon={Shield}
      lastUpdated={LAST_UPDATED}
      title={
        <>
          <span className="text-white">Privacy </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Policy</span>
        </>
      }
    >
      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Lock className="h-6 w-6 text-emerald-400" />
          1. Overview
        </h2>
        <p className="text-gray-400 leading-relaxed">
          This Privacy Policy explains what information we collect, how we use it, and who we share it with when you use
          Parlay Gorilla.
        </p>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Database className="h-6 w-6 text-emerald-400" />
          2. Information We Collect
        </h2>
        <div className="space-y-5 text-gray-400 leading-relaxed">
          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Account Information</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Email address and basic account/profile information</li>
              <li>
                Authentication data (we store a secure hashed version of your password, not your plain-text password)
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Usage and Device Data</h3>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Pages viewed and features used</li>
              <li>Device and browser information</li>
              <li>IP address and approximate location (for security and compliance)</li>
              <li>Error logs and performance diagnostics</li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold text-white mb-2">Payments</h3>
            <p>
              Payments are handled by third-party processors such as <strong className="text-white">Stripe</strong> (and other providers we may use).{" "}
              <strong className="text-white">We do not store your full credit card details</strong>.
            </p>
            <p className="mt-2">
              We may receive limited payment-related information like a customer ID, subscription status, plan name, and
              receipt/transaction identifiers so we can provide access and support.
            </p>
          </div>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Eye className="h-6 w-6 text-emerald-400" />
          3. How We Use Your Information
        </h2>
        <ul className="list-disc list-inside space-y-2 ml-4 text-gray-400 leading-relaxed">
          <li>Provide, maintain, and improve the Service</li>
          <li>Account management and customer support</li>
          <li>Security, fraud prevention, and abuse detection</li>
          <li>Analytics and product improvement</li>
          <li>Billing access control (confirming subscription/entitlements)</li>
        </ul>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">4. Sharing Your Information</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>We do not sell your personal information. We may share it with:</p>
          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>
              <strong className="text-white">Payment processors</strong> (Stripe) for checkout and
              subscription management
            </li>
            <li>
              <strong className="text-white">Infrastructure providers</strong> (hosting, storage, email delivery) needed to
              run the Service
            </li>
            <li>
              <strong className="text-white">Analytics/advertising providers</strong> if enabled (for example, Google AdSense
              may use cookies to show and measure ads)
            </li>
            <li>
              <strong className="text-white">Legal compliance</strong> when required by law or to protect our rights, users, or
              the public
            </li>
          </ul>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">5. Cookies</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            We may use cookies and similar technologies for essential functionality, preferences, and analytics. If we run ads,
            advertising partners may also use cookies.
          </p>
          <p>You can control cookies through your browser settings.</p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">6. Data Security</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>We use reasonable safeguards to protect your data. However:</p>
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-amber-400 font-semibold mb-1">No system is 100% secure</p>
                <p className="text-amber-300 text-sm">
                  We can’t guarantee absolute security. Please use a strong password and keep your account details private.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">7. Your Privacy Choices</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            You can request access, correction, or deletion of your personal information by contacting us at{" "}
            <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300 hover:underline">
              contact@f3ai.dev
            </a>
            .
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">8. Age Restriction</h2>
        <p className="text-gray-400 leading-relaxed">
          Parlay Gorilla is intended for users who are 21+ (and of legal gambling age in their jurisdiction). We do not
          knowingly collect personal information from children.
        </p>
      </section>

      <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">9. Contact for Privacy</h2>
        <div className="space-y-4 text-gray-300 leading-relaxed">
          <p>If you have questions about this Privacy Policy, contact us at:</p>
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

