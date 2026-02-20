"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { CreditCard, RefreshCw, XCircle, HelpCircle, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { dispatchGorillaBotOpen } from "@/lib/gorilla-bot/events"

interface BillingActionCenterProps {
  onManagePayment: () => void
  onSyncBilling?: () => void
  loadingPortal?: boolean
  loadingSync?: boolean
  className?: string
}

export function BillingActionCenter({
  onManagePayment,
  onSyncBilling,
  loadingPortal = false,
  loadingSync = false,
  className,
}: BillingActionCenterProps) {
  const handleOpenSupportChat = () => {
    dispatchGorillaBotOpen({
      prefill: "I need help with billing and my account access.",
    })
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className={cn(
        "rounded-2xl border border-white/10 bg-black/20 backdrop-blur p-6",
        className
      )}
    >
      <p className="text-xs uppercase tracking-widest text-white/88 mb-4">
        Billing Action Center
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <ActionCard
          icon={CreditCard}
          label="Manage Payment"
          description="Update card or billing details"
          onClick={onManagePayment}
          loading={loadingPortal}
        />
        {onSyncBilling && (
          <ActionCard
            icon={RefreshCw}
            label="Sync Billing"
            description="Refresh from Stripe"
            onClick={onSyncBilling}
            loading={loadingSync}
          />
        )}
        <ActionCard
          icon={XCircle}
          label="Cancel Plan"
          description="Manage in billing portal"
          onClick={onManagePayment}
          variant="secondary"
        />
        <ActionCard
          icon={HelpCircle}
          label="Contact Support"
          description="Help with billing"
          href="/support"
          onLinkClick={handleOpenSupportChat}
          variant="secondary"
        />
      </div>
    </motion.section>
  )
}

function ActionCard({
  icon: Icon,
  label,
  description,
  onClick,
  href,
  onLinkClick,
  loading,
  variant = "primary",
}: {
  icon: React.ElementType
  label: string
  description: string
  onClick?: () => void
  href?: string
  onLinkClick?: () => void
  loading?: boolean
  variant?: "primary" | "secondary"
}) {
  const content = (
    <>
      <div className="flex items-center gap-3 mb-2">
        <div
          className={cn(
            "p-2 rounded-lg",
            variant === "primary"
              ? "bg-[#00FF5E]/10 text-[#00FF5E]"
              : "bg-white/5 text-white/88"
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        <span className="font-bold text-white">{label}</span>
      </div>
      <p className="text-xs text-white/78">{description}</p>
      {href ? (
        <span className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[#00FF5E] hover:text-[#00FF5E]/80 transition-colors">
          Open
        </span>
      ) : (
        <button
          type="button"
          onClick={onClick}
          disabled={loading}
          className={cn(
            "mt-3 w-full py-2 rounded-lg text-sm font-bold transition-all",
            variant === "primary"
              ? "bg-white/10 text-white hover:bg-white/15 border border-white/10"
              : "bg-white/5 text-white/92 hover:bg-white/10 border border-white/10"
          )}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin mx-auto" />
          ) : (
            label
          )}
        </button>
      )}
    </>
  )

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="rounded-xl border border-white/10 bg-white/[0.03] p-4 hover:border-white/15 hover:bg-white/[0.05] transition-colors"
    >
      {href ? (
        <Link
          href={href}
          className="block"
          onClick={(event) => {
            if (!onLinkClick) return
            event.preventDefault()
            onLinkClick()
          }}
        >
          {content}
        </Link>
      ) : (
        content
      )}
    </motion.div>
  )
}
