"use client"

import Link from "next/link"
import { Crown, CreditCard, Lock } from "lucide-react"

import { cn } from "@/lib/utils"

type OverlayVariant = "fullscreen" | "container"

interface PremiumBlurOverlayProps {
  variant?: OverlayVariant
  title?: string
  message?: string
  className?: string
}

export function PremiumBlurOverlay({
  variant = "fullscreen",
  title = "Premium Required",
  message = "Credits unlock AI Builder + Custom Builder only. Upgrade to access this page.",
  className,
}: PremiumBlurOverlayProps) {
  const wrapperClass =
    variant === "fullscreen"
      ? "fixed inset-0 z-50"
      : "absolute inset-0 z-20"

  return (
    <div className={cn(wrapperClass, "bg-black/60 backdrop-blur-sm", className)}>
      <div className="w-full h-full flex items-center justify-center p-6">
        <div className="max-w-md w-full bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border border-emerald-500/30 rounded-2xl p-8 shadow-2xl">
          <div className="w-14 h-14 rounded-full bg-emerald-500/15 flex items-center justify-center mb-5">
            <Lock className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
          <p className="text-gray-400 mb-6">{message}</p>

          <div className="flex flex-col gap-3">
            <Link
              href="/pricing"
              className="w-full py-3 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
            >
              <Crown className="h-5 w-5" />
              Upgrade to Premium
            </Link>
            <Link
              href="/billing#credits"
              className="w-full py-3 px-6 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-xl transition-all flex items-center justify-center gap-2"
            >
              <CreditCard className="h-5 w-5" />
              Buy Credits
            </Link>
            <Link href="/app" className="w-full py-2 text-gray-400 hover:text-white text-sm text-center transition-colors">
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}


