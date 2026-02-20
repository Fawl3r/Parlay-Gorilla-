"use client"

import { motion } from "framer-motion"
import Link from "next/link"
import { AlertCircle, CheckCircle } from "lucide-react"

import type { AccessStatus } from "./types"

interface AccessIndicatorProps {
  accessStatus: AccessStatus
}

export function AccessIndicator({ accessStatus }: AccessIndicatorProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className={`p-4 rounded-xl mb-8 flex items-center gap-4 ${
        accessStatus.can_generate.standard
          ? "bg-emerald-500/10 border border-emerald-500/20"
          : "bg-red-500/10 border border-red-500/20"
      }`}
    >
      {accessStatus.can_generate.standard ? (
        <>
          <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0" />
          <div>
            <div className="font-medium text-white">You can generate parlays</div>
            <div className="text-sm text-gray-200">
              {accessStatus.free.remaining > 0
                ? "Using your free parlays"
                : accessStatus.subscription.active
                  ? "Using your subscription"
                  : "Using your credits"}
            </div>
          </div>
        </>
      ) : (
        <>
          <AlertCircle className="w-6 h-6 text-red-400 shrink-0" />
          <div className="flex-1">
            <div className="font-medium text-white">No access available</div>
            <div className="text-sm text-gray-200">Subscribe or buy credits to generate more parlays</div>
          </div>
          <Link
            href="#credits"
            className="px-4 py-2 bg-amber-500 text-black font-bold rounded-lg text-sm shrink-0"
          >
            Buy Credits
          </Link>
        </>
      )}
    </motion.div>
  )
}


