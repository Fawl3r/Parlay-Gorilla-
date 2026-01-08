"use client"

import Link from "next/link"
import { useEffect } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Copy, ExternalLink, X } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"

export type VerificationSuccessModalPayload = {
  verificationRecordId: string
  parlayTitle?: string
  viewerUrl: string
  receiptId?: string | null
}

type Props = {
  open: boolean
  payload: VerificationSuccessModalPayload | null
  onClose: () => void
}

function shortenHash(hash: string) {
  if (!hash) return ""
  if (hash.length <= 16) return hash
  return `${hash.slice(0, 6)}…${hash.slice(-6)}`
}

function toAbsoluteViewerUrl(viewerUrl: string): string {
  const raw = String(viewerUrl || "").trim()
  if (!raw) return ""
  if (raw.startsWith("http://") || raw.startsWith("https://")) return raw
  if (typeof window === "undefined") return raw
  if (raw.startsWith("/")) return `${window.location.origin}${raw}`
  return `${window.location.origin}/${raw}`
}

export function VerificationSuccessModal({ open, payload, onClose }: Props) {
  useEffect(() => {
    if (!open || !payload) return

    let cancelled = false
    async function fire() {
      try {
        const mod = await import("canvas-confetti")
        if (cancelled) return
        const confetti = mod.default
        const colors = ["#00FF5E", "#22FF6E", "#00CC4B", "#9AE6B4", "#FFD166"]

        confetti({ particleCount: 110, spread: 70, startVelocity: 40, origin: { y: 0.65 }, colors })
        confetti({ particleCount: 70, spread: 100, startVelocity: 30, origin: { y: 0.65 }, colors })
      } catch {
        // Confetti is optional; ignore failures.
      }
    }

    fire()
    return () => {
      cancelled = true
    }
  }, [open, payload])

  if (!open || !payload) return null

  const absoluteViewerUrl = toAbsoluteViewerUrl(payload.viewerUrl)

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4"
        onClick={onClose}
        role="dialog"
        aria-modal="true"
        aria-label="Verification created"
        data-testid="verification-success-modal"
      >
        <motion.div
          initial={{ scale: 0.92, opacity: 0, y: 12 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.92, opacity: 0, y: 12 }}
          transition={{ type: "spring", stiffness: 420, damping: 32 }}
          onClick={(e) => e.stopPropagation()}
          className="relative w-full max-w-md overflow-hidden rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-gray-900 via-black to-gray-900 p-6 text-center shadow-2xl"
        >
          <button
            onClick={onClose}
            className="absolute right-3 top-3 rounded-md p-2 text-gray-400 hover:text-white"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>

          <div className="mb-5">
            <div className="text-emerald-300 text-sm font-semibold">Verification created</div>
            <div className="mt-1 text-2xl font-extrabold text-white">Time-stamped record</div>
            <div className="mt-2 text-sm text-gray-300/80">
              A permanent, time-stamped verification record is now available for this saved parlay.
            </div>
          </div>

          {payload.parlayTitle ? (
            <div className="mb-4 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3">
              <div className="text-[11px] uppercase tracking-wide text-gray-400">Parlay</div>
              <div className="mt-1 truncate text-sm font-semibold text-white">{payload.parlayTitle}</div>
            </div>
          ) : null}

          {payload.receiptId ? (
            <div className="mb-4 rounded-xl border border-white/10 bg-black/30 px-4 py-3 text-left">
              <div className="text-[11px] uppercase tracking-wide text-gray-400">Receipt ID</div>
              <div className="mt-1 flex items-center justify-between gap-2">
                <div className="min-w-0 font-mono text-sm text-emerald-200 truncate">
                  {shortenHash(payload.receiptId)}
                </div>
                <Button
                  size="icon"
                  variant="ghost"
                  className="text-gray-200 hover:text-white"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(payload.receiptId || "")
                      toast.success("Copied")
                    } catch {
                      toast.error("Failed to copy")
                    }
                  }}
                  aria-label="Copy receipt id"
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ) : null}

          <div className="grid gap-2 sm:grid-cols-2">
            <Button asChild className="w-full bg-emerald-500 text-black hover:bg-emerald-400">
              <Link href={payload.viewerUrl}>
                <ExternalLink className="h-4 w-4 mr-2" />
                View record
              </Link>
            </Button>
            <Button
              variant="outline"
              className="w-full border-white/15 text-white hover:bg-white/10"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(absoluteViewerUrl || payload.viewerUrl)
                  toast.success("Link copied")
                } catch {
                  toast.error("Failed to copy")
                }
              }}
            >
              <Copy className="h-4 w-4 mr-2" />
              Copy link
            </Button>
          </div>

          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-emerald-500/10 to-transparent" />
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default VerificationSuccessModal


