"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Mail, X, Loader2 } from "lucide-react"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"

export function VerificationBanner() {
  const { user } = useAuth()
  const [dismissed, setDismissed] = useState(false)
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  // Don't show if user is verified or not logged in
  if (!user || user.email_verified || dismissed) {
    return null
  }

  const handleResend = async () => {
    setSending(true)
    try {
      await api.resendVerificationEmail()
      setSent(true)
    } catch {
      // Silently fail - user will try again
    } finally {
      setSending(false)
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="fixed top-0 left-0 right-0 z-50 bg-yellow-500/10 border-b border-yellow-500/30 backdrop-blur-sm"
      >
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-yellow-400" />
              <p className="text-sm text-yellow-200">
                {sent ? (
                  "Verification email sent! Check your inbox."
                ) : (
                  <>
                    Please verify your email address.{" "}
                    <button
                      onClick={handleResend}
                      disabled={sending}
                      className="underline hover:no-underline text-yellow-400 inline-flex items-center gap-1"
                    >
                      {sending ? (
                        <>
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        "Resend verification email"
                      )}
                    </button>
                  </>
                )}
              </p>
            </div>
            <button
              onClick={() => setDismissed(true)}
              className="text-yellow-400/50 hover:text-yellow-400 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}

