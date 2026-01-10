"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { ChevronRight, Loader2 } from "lucide-react"

import { useSubscription } from "@/lib/subscription-context"

interface BillingQuickLinksProps {
  onOpenPortal?: () => Promise<void>
}

export function BillingQuickLinks({ onOpenPortal }: BillingQuickLinksProps) {
  const { createPortal } = useSubscription()
  const [loadingPortal, setLoadingPortal] = useState(false)

  const handleOpenPortal = async () => {
    if (onOpenPortal) {
      await onOpenPortal()
      return
    }

    try {
      setLoadingPortal(true)
      const portalUrl = await createPortal()
      window.location.href = portalUrl
    } catch (err) {
      console.error("Error opening Stripe portal:", err)
    } finally {
      setLoadingPortal(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="flex flex-wrap gap-4 justify-center"
    >
      <Link
        href="/usage"
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
      >
        Usage &amp; Performance <ChevronRight className="w-4 h-4" />
      </Link>
      <Link
        href="/profile"
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
      >
        View Profile <ChevronRight className="w-4 h-4" />
      </Link>
      <Link
        href="/affiliates"
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
      >
        Earn with Affiliates <ChevronRight className="w-4 h-4" />
      </Link>
      <button
        onClick={handleOpenPortal}
        disabled={loadingPortal}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loadingPortal ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Opening...
          </>
        ) : (
          <>
            Billing Support <ChevronRight className="w-4 h-4" />
          </>
        )}
      </button>
    </motion.div>
  )
}


