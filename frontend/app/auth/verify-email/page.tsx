"use client"

import { useState, useEffect, Suspense } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { motion } from "framer-motion"
import Link from "next/link"
import Image from "next/image"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"
import { Check, Loader2, AlertCircle, Mail } from "lucide-react"

function VerifyEmailContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const token = searchParams.get("token")
  const { refreshUser } = useAuth()

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying")
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (token) {
      verifyEmail(token)
    } else {
      setStatus("error")
      setError("No verification token found. Please check your email for the correct link.")
    }
  }, [token])

  const verifyEmail = async (verificationToken: string) => {
    try {
      await api.verifyEmail(verificationToken)
      setStatus("success")
      
      // Refresh user data to update email_verified status
      await refreshUser()
      
      // Redirect to app after 3 seconds
      setTimeout(() => {
        router.push("/app")
      }, 3000)
    } catch (err: any) {
      setStatus("error")
      setError(err.response?.data?.detail || "Failed to verify email. The link may have expired.")
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md"
      >
        <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-8 text-center">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="relative flex h-12 w-12 items-center justify-center rounded-xl overflow-hidden">
              <Image
                src="/logoo.png"
                alt="Parlay Gorilla Logo"
                width={48}
                height={48}
                className="object-contain"
              />
            </div>
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

