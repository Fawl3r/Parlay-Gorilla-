"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { Check, Loader2, AlertCircle } from "lucide-react"
import { Header } from "@/components/Header"
import { ParlayGorillaLogo } from "@/components/ParlayGorillaLogo"
import { api } from "@/lib/api"

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const { refreshUser } = useAuth()

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setError("No verification token found. Please check your email for the correct link.")
      return
    }

    api
      .verifyEmail(token)
      .then(async () => {
        setStatus("success")
        await refreshUser()
        setTimeout(() => {
          router.push("/app")
        }, 3000)
      })
      .catch((err: any) => {
        setStatus("error")
        setError(err?.response?.data?.detail || err?.message || "Failed to verify email. The link has expired or is invalid.")
      })
  }, [token, refreshUser, router, searchParams])

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <div className="flex-1 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-8 text-center">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <ParlayGorillaLogo size="md" showText={false} />
          </div>

          {status === "verifying" && (
            <>
              <div className="h-16 w-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Loader2 className="h-8 w-8 text-blue-400 animate-spin" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Verifying Email...</h1>
              <p className="text-gray-400">
                Please wait while we verify your email address.
              </p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="h-16 w-16 bg-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Check className="h-8 w-8 text-emerald-400" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Email Verified!</h1>
              <p className="text-gray-400 mb-6">
                Your email has been verified successfully. Redirecting you to the app...
              </p>
              <div className="flex items-center justify-center gap-2 text-emerald-400">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Redirecting...</span>
              </div>
            </>
          )}

          {status === "error" && (
            <>
              <div className="h-16 w-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertCircle className="h-8 w-8 text-red-400" />
              </div>
              <h1 className="text-2xl font-bold text-white mb-2">Verification Failed</h1>
              <p className="text-gray-400 mb-6">
                {error}
              </p>
              <div className="space-y-3">
                <Link
                  href="/app"
                  className="block w-full py-3 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all"
                >
                  Go to App
                </Link>
                <p className="text-sm text-gray-500">
                  Need a new verification link?{" "}
                  <button
                    onClick={async () => {
                      try {
                        await api.resendVerificationEmail()
                        setError("A new verification email has been sent!")
                      } catch {
                        setError("Please log in and request a new verification email.")
                      }
                    }}
                    className="text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Resend email
                  </button>
                </p>
              </div>
            </>
          )}
        </div>
      </motion.div>
      </div>
    </div>
  )
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  )
}

