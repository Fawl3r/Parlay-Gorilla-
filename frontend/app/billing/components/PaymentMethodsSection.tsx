"use client"

import Link from "next/link"

import { cn } from "@/lib/utils"

export function PaymentMethodsSection({ className }: { className?: string }) {
  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-6", className)}>
      <div className="mb-4">
        <h2 className="text-xl font-bold text-white">Payment Methods</h2>
        <p className="text-sm text-gray-200/70 mt-1">
          Add or update your payment details — cancellation is always visible and never hidden.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-black text-white">Add / Update Card</div>
          <div className="mt-2 text-sm text-gray-200/70">
            Card billing is handled by our payment provider. If you need to update your card, we’ll help you do it quickly.
          </div>
          <div className="mt-4">
            <Link
              href="/support"
              className="inline-flex items-center justify-center rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 px-4 py-2 text-sm font-bold text-white transition-colors"
            >
              Billing Support
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-black text-white">Crypto Payments</div>
          <div className="mt-2 text-sm text-gray-200/70">
            Crypto access does not auto-renew. You stay in control — renew only when you choose.
          </div>
          <div className="mt-4">
            <Link
              href="/pricing"
              className="inline-flex items-center justify-center rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 px-4 py-2 text-sm font-bold text-white transition-colors"
            >
              View Plans
            </Link>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-black text-white">Cancel Anytime</div>
          <div className="mt-2 text-sm text-gray-200/70">
            You can cancel anytime. Your access continues through the end of your cycle.
          </div>
          <div className="mt-4 text-sm text-gray-200/60">
            Use the cancellation controls in <span className="text-white font-semibold">Current Plan</span>.
          </div>
        </div>
      </div>
    </section>
  )
}

export default PaymentMethodsSection


