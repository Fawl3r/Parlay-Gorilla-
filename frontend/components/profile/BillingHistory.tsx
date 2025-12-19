"use client"

import { useState, useEffect } from "react"
import { motion } from "framer-motion"
import { 
  Receipt, 
  Check, 
  X, 
  Clock, 
  Loader2, 
  AlertCircle,
  ChevronDown
} from "lucide-react"
import { api, PaymentHistoryItem, PaymentHistoryResponse } from "@/lib/api"
import { GlassPanel } from "@/components/ui/glass-panel"

interface BillingHistoryProps {
  className?: string
}

export function BillingHistory({ className }: BillingHistoryProps) {
  const [history, setHistory] = useState<PaymentHistoryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      const data = await api.getSubscriptionHistory(20, 0)
      setHistory(data)
    } catch (err: any) {
      setError("Failed to load billing history")
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <GlassPanel className={className}>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
        </div>
      </GlassPanel>
    )
  }

  if (error) {
    return (
      <GlassPanel className={className}>
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="h-5 w-5" />
          <span>{error}</span>
        </div>
      </GlassPanel>
    )
  }

  if (!history || history.payments.length === 0) {
    return (
      <GlassPanel className={className}>
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
          <Receipt className="h-5 w-5 text-gray-500" />
          Billing History
        </h2>
        <p className="text-gray-500 text-center py-4">No payment history yet</p>
      </GlassPanel>
    )
  }

  const displayPayments = showAll ? history.payments : history.payments.slice(0, 5)

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case "paid":
      case "succeeded":
      case "completed":
        return <Check className="h-4 w-4 text-emerald-400" />
      case "pending":
      case "processing":
        return <Clock className="h-4 w-4 text-yellow-400" />
      case "failed":
      case "refunded":
        return <X className="h-4 w-4 text-red-400" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: currency.toUpperCase(),
    }).format(amount)
  }

  return (
    <GlassPanel className={className}>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <Receipt className="h-5 w-5 text-gray-500" />
          Billing History
        </h2>
        <span className="text-sm text-gray-500">{history.total_count} transactions</span>
      </div>

      <div className="space-y-2">
        {displayPayments.map((payment, index) => (
          <motion.div
            key={payment.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between p-3 bg-white/[0.05] border border-white/10 rounded-lg hover:bg-white/[0.08] transition-colors"
          >
            <div className="flex items-center gap-3">
              {getStatusIcon(payment.status)}
              <div>
                <p className="text-sm text-white">{payment.plan}</p>
                <p className="text-xs text-gray-500">
                  {new Date(payment.created_at).toLocaleDateString()} • {payment.provider}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {formatAmount(payment.amount, payment.currency)}
              </p>
              <p className="text-xs text-gray-500 capitalize">{payment.status}</p>
            </div>
          </motion.div>
        ))}
      </div>

      {history.payments.length > 5 && (
        <button
          onClick={() => setShowAll(!showAll)}
          className="w-full mt-4 flex items-center justify-center gap-2 py-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          {showAll ? "Show Less" : `Show All (${history.payments.length})`}
          <ChevronDown className={`h-4 w-4 transition-transform ${showAll ? "rotate-180" : ""}`} />
        </button>
      )}
    </GlassPanel>
  )
}

