"use client"

import Link from "next/link"
import { CheckCircle, Receipt, AlertTriangle } from "lucide-react"

import { LegalPageLayout } from "@/components/legal/LegalPageLayout"

const LAST_UPDATED = "December 19, 2025"

export default function RefundsPage() {
  return (
    <LegalPageLayout
      icon={Receipt}
      lastUpdated={LAST_UPDATED}
      title={
        <>
          <span className="text-white">Refund &amp; </span>
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
            Cancellation Policy
          </span>
        </>
      }
    >
      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">1. No Refunds</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>
            <strong className="text-white">All purchases are final.</strong> Due to the digital nature of the service and
            immediate access to premium features/content, we do not provide refunds.
          </p>
          <p>
            If you believe you were charged in error (for example, a duplicate charge), please contact us and we’ll review it.
          </p>
        </div>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">2. Subscription Auto-Renewal</h2>
        <p className="text-gray-400 leading-relaxed">
          Subscriptions (monthly or annual) automatically renew until you cancel.
        </p>
      </section>

      <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">3. How to Cancel</h2>
        <div className="space-y-4 text-gray-400 leading-relaxed">
          <p>You can cancel anytime from your account:</p>
          <ul className="list-disc list-inside space-y-2 ml-4">
            <li>
              Go to{" "}
              <Link href="/profile" className="text-emerald-400 hover:text-emerald-300 hover:underline">
                Profile
              </Link>{" "}
              → Subscription → “Cancel Subscription”
            </li>
            <li>
              Or visit the{" "}
              <Link href="/billing" className="text-emerald-400 hover:text-emerald-300 hover:underline">
                Billing
              </Link>{" "}
              page (if available for your plan)
            </li>
          </ul>
          <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-amber-400 font-semibold mb-1">Access Until Period End</p>
                <p className="text-amber-300 text-sm">
                  When you cancel, you keep access until the end of your current billing period. You won’t be charged again
                  unless you resubscribe.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
        <h2 className="text-2xl font-bold text-white mb-4">4. Contact</h2>
        <div className="space-y-4 text-gray-300 leading-relaxed">
          <p>If you need help with billing or cancellation, contact us at:</p>
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


