"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { ChevronRight } from "lucide-react"

export function BillingQuickLinks() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="flex flex-wrap gap-4 justify-center"
    >
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
      <Link
        href="/support"
        className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
      >
        Billing Support <ChevronRight className="w-4 h-4" />
      </Link>
    </motion.div>
  )
}


