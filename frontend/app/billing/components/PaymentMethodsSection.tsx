"use client"

import { useState } from "react"
import { RefreshCw, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

interface PaymentMethodsSectionProps {
  className?: string
  onOpenStripePortal?: () => Promise<void>
  onSync?: () => Promise<void>
}

export function PaymentMethodsSection({ className, onOpenStripePortal, onSync }: PaymentMethodsSectionProps) {
  const [loadingPortal, setLoadingPortal] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const handleOpenPortal = async () => {
    if (!onOpenStripePortal) return
    try {
      setLoadingPortal(true)
      await onOpenStripePortal()
    } catch (err) {
      console.error("Error opening Stripe portal:", err)
    } finally {
      setLoadingPortal(false)
    }
  }

  const handleSync = async () => {
    if (!onSync) return
    try {
      setSyncing(true)
      await onSync()
    } catch (err) {
      console.error("Error syncing billing data:", err)
    } finally {
      setSyncing(false)
    }
  }

  return (
    <section className={cn("rounded-2xl border border-white/10 bg-black/25 backdrop-blur p-6", className)}>
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">Payment Methods</h2>
        </div>
        {onSync && (
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 text-gray-300 rounded-lg hover:bg-white/10 transition-all disabled:opacity-50"
            title="Sync billing data from Stripe"
          >
            {syncing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            <span className="text-sm">Sync</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-black text-white">Add / Update Card</div>
          <div className="mt-2 text-sm text-gray-200/70">
            Update your payment method through our billing portal.
          </div>
          <div className="mt-4">
            <button
              onClick={handleOpenPortal}
              disabled={loadingPortal || !onOpenStripePortal}
              className="inline-flex items-center justify-center rounded-lg bg-white/10 hover:bg-white/15 border border-white/10 px-4 py-2 text-sm font-bold text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loadingPortal ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                  Opening...
                </>
              ) : (
                "Billing Support"
              )}
            </button>
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
          <div className="text-sm font-black text-white">Cancel Anytime</div>
          <div className="mt-2 text-sm text-gray-200/70">
            Manage cancellation in <span className="text-white font-semibold">Current Plan</span>.
          </div>
        </div>
      </div>
    </section>
  )
}

export default PaymentMethodsSection


