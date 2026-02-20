"use client"

import { motion } from "framer-motion"

function formatProviderName(provider: string): string {
  const p = (provider || "").trim().toLowerCase()
  if (!p) return ""
  if (p === "stripe") return "Stripe"
  if (p === "lemonsqueezy") return "LemonSqueezy"
  return p.charAt(0).toUpperCase() + p.slice(1)
}

export function ProviderLabel({ provider }: { provider: string | null }) {
  if (!provider) return null

  const providerName = formatProviderName(provider)
  if (!providerName) return null

  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.8 }}
      className="mt-6 text-gray-300 text-sm"
    >
      Payment processed via {providerName}
    </motion.p>
  )
}


