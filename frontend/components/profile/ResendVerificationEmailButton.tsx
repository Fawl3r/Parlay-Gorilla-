"use client"

import { useState } from "react"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"
import { api } from "@/lib/api"

interface ResendVerificationEmailButtonProps {
  className?: string
}

export function ResendVerificationEmailButton({ className }: ResendVerificationEmailButtonProps) {
  const [sending, setSending] = useState(false)
  const [sent, setSent] = useState(false)

  const handleResend = async () => {
    if (sending || sent) return
    setSending(true)
    try {
      const data = await api.resendVerificationEmail()
      setSent(true)
      toast.success(data?.message || "Verification email sent. Check your inbox (and spam).")
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Failed to send verification email"
      toast.error(detail)
    } finally {
      setSending(false)
    }
  }

  return (
    <button
      type="button"
      onClick={handleResend}
      disabled={sending || sent}
      className={
        className ||
        "inline-flex items-center gap-2 px-3 py-1.5 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-xs text-yellow-200 hover:bg-yellow-500/15 hover:border-yellow-500/40 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
      }
    >
      {sending ? (
        <>
          <Loader2 className="h-3 w-3 animate-spin" />
          Sending...
        </>
      ) : sent ? (
        "Email sent"
      ) : (
        "Send verification email"
      )}
    </button>
  )
}


