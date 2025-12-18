"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { X, Users, DollarSign, ArrowRight, Sparkles } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"

const AFFILIATE_BANNER_DISMISSED_KEY = "parlay_gorilla_affiliate_banner_dismissed"
const AFFILIATE_POPUP_DISMISSED_KEY = "parlay_gorilla_affiliate_popup_dismissed"

type BannerVariant = "banner" | "popup"

interface AffiliatePromoBannerProps {
  variant?: BannerVariant
  showOnPages?: string[] // Pages where banner should show (empty = all pages)
  hideOnPages?: string[] // Pages where banner should hide
}

export function AffiliatePromoBanner({ 
  variant = "banner",
  showOnPages = [],
  hideOnPages = ["/affiliates", "/affiliates/dashboard", "/affiliates/join"]
}: AffiliatePromoBannerProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [mounted, setMounted] = useState(false)
  const router = useRouter()
  const { user } = useAuth()
  const pathname = typeof window !== "undefined" ? window.location.pathname : ""

  useEffect(() => {
    setMounted(true)
    
    // Check if banner should be shown
    if (hideOnPages.some(page => pathname.startsWith(page))) {
      setIsVisible(false)
      return
    }

    if (showOnPages.length > 0 && !showOnPages.some(page => pathname.startsWith(page))) {
      setIsVisible(false)
      return
    }

    // Check localStorage for dismissal
    const dismissedKey = variant === "banner" 
      ? AFFILIATE_BANNER_DISMISSED_KEY 
      : AFFILIATE_POPUP_DISMISSED_KEY
    
    try {
      const dismissed = localStorage.getItem(dismissedKey)
      if (dismissed === "true") {
        setIsVisible(false)
        return
      }
    } catch (error) {
      console.error("Error accessing localStorage:", error)
    }

    // Show banner after a short delay for better UX
    const timer = setTimeout(() => {
      setIsVisible(true)
    }, variant === "popup" ? 2000 : 500)

    return () => clearTimeout(timer)
  }, [variant, pathname, showOnPages, hideOnPages])

  const handleDismiss = () => {
    setIsVisible(false)
    const dismissedKey = variant === "banner" 
      ? AFFILIATE_BANNER_DISMISSED_KEY 
      : AFFILIATE_POPUP_DISMISSED_KEY
    
    try {
      localStorage.setItem(dismissedKey, "true")
    } catch (error) {
      console.error("Error saving to localStorage:", error)
    }
  }

  const handleCtaClick = () => {
    if (user) {
      router.push("/affiliates/dashboard")
    } else {
      router.push("/affiliates")
    }
    handleDismiss()
  }

  if (!mounted) return null

  if (variant === "banner") {
    return (
      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            transition={{ duration: 0.3 }}
            className="relative z-40 w-full bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-emerald-500/20 border-b border-emerald-500/30"
          >
            <div className="container mx-auto px-4 py-3">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1">
                  <div className="p-2 bg-emerald-500/20 rounded-lg">
                    <Sparkles className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-white">
                      💰 <span className="text-emerald-300">Earn Passive Income</span> with Parlay Gorilla Affiliates
                    </p>
                    <p className="text-xs text-gray-300 mt-0.5">
                      Up to 35% commission on referrals • Join free today
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCtaClick}
                    className="px-4 py-1.5 text-xs font-bold text-black bg-emerald-400 rounded-lg hover:bg-emerald-300 transition-all flex items-center gap-1"
                  >
                    Learn More
                    <ArrowRight className="h-3 w-3" />
                  </button>
                  <button
                    onClick={handleDismiss}
                    className="p-1.5 text-gray-400 hover:text-white transition-colors"
                    aria-label="Dismiss banner"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    )
  }

  // Popup variant
  return (
    <AnimatePresence>
      {isVisible && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
            onClick={handleDismiss}
          />
          
          {/* Popup */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.3, type: "spring", stiffness: 300, damping: 30 }}
            className="fixed inset-0 z-[101] flex items-center justify-center p-4 pointer-events-none"
          >
            <div 
              className="relative w-full max-w-md bg-gradient-to-br from-[#0A0F0A] via-[#0d1117] to-[#0A0F0A] border border-emerald-500/30 rounded-2xl shadow-2xl overflow-hidden pointer-events-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Decorative gradient overlay */}
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-transparent to-green-500/10" />
              <div className="absolute top-0 right-0 w-64 h-64 bg-emerald-500/5 rounded-full blur-3xl" />
              
              <div className="relative p-6">
                {/* Close button */}
                <button
                  onClick={handleDismiss}
                  className="absolute top-4 right-4 p-1.5 text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-white/5"
                  aria-label="Close popup"
                >
                  <X className="h-5 w-5" />
                </button>

                {/* Icon */}
                <div className="flex justify-center mb-4">
                  <div className="p-4 bg-gradient-to-br from-emerald-500/20 to-green-500/20 rounded-2xl">
                    <Users className="h-10 w-10 text-emerald-400" />
                  </div>
                </div>

                {/* Content */}
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-black text-white mb-2">
                    Join the <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">Affiliate Squad</span>
                  </h3>
                  <p className="text-gray-300 text-sm mb-4">
                    Turn your audience into passive income. Earn up to <span className="font-bold text-emerald-400">35% commission</span> on every subscription and credit pack you refer.
                  </p>
                  
                  {/* Features */}
                  <div className="grid grid-cols-2 gap-3 mb-6">
                    <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <DollarSign className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
                      <p className="text-xs text-gray-300">Up to 20% on subscriptions</p>
                    </div>
                    <div className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <Users className="h-5 w-5 text-emerald-400 mx-auto mb-1" />
                      <p className="text-xs text-gray-300">Up to 35% on credits</p>
                    </div>
                  </div>
                </div>

                {/* CTA Button */}
                <button
                  onClick={handleCtaClick}
                  className="w-full px-6 py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2"
                >
                  {user ? "Open Dashboard" : "Get Started Free"}
                  <ArrowRight className="h-5 w-5" />
                </button>

                <p className="text-xs text-gray-500 text-center mt-4">
                  No upfront costs • Start earning today
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}




