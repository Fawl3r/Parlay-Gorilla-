"use client"

import Link from "next/link"
import { CheckCircle, Clock, Copy, ExternalLink, MinusCircle, RefreshCw, XCircle, Link2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SavedParlayResponse } from "@/lib/api"
import { InscriptionStatusPill } from "@/components/analytics/InscriptionStatusPill"

type SavedParlayWithResults = SavedParlayResponse & {
  results?: {
    status?: string
    hit?: boolean | null
    legs_hit?: number
    legs_missed?: number
    resolved_at?: string | null
    leg_results?: Array<Record<string, any>>
  } | null
}

function shortenHash(hash: string) {
  if (!hash) return ""
  if (hash.length <= 16) return hash
  return `${hash.slice(0, 6)}…${hash.slice(-6)}`
}

function formatLegLabel(leg: Record<string, any>): string {
  if (!leg) return "Leg"
  if (typeof leg.pick === "string" && leg.pick.trim()) {
    const point = leg.point !== undefined && leg.point !== null ? ` ${leg.point}` : ""
    return `${leg.pick}${point}`.trim()
  }
  if (typeof leg.outcome === "string" && leg.outcome.trim()) return leg.outcome
  return "Leg"
}

export function SavedParlayRow({
  item,
  onRetry,
  onInscribe,
}: {
  item: SavedParlayWithResults
  onRetry: (id: string) => Promise<void>
  onInscribe?: (id: string) => Promise<void>
}) {
  const legsCount = Array.isArray(item.legs) ? item.legs.length : 0
  const created = item.created_at ? new Date(item.created_at) : null

  const typeBadge =
    item.parlay_type === "custom"
      ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/30"
      : "bg-purple-500/15 text-purple-200 border-purple-500/30"

  const canInscribe = item.inscription_status === "none" && onInscribe
  const showInscription = item.inscription_status !== "none"

  const results = item.results || null
  const status = (results?.status || "").toLowerCase().trim()
  const statusBadge =
    status === "hit"
      ? "bg-emerald-500/15 text-emerald-200 border-emerald-500/30"
      : status === "missed"
        ? "bg-red-500/15 text-red-200 border-red-500/30"
        : status === "push"
          ? "bg-sky-500/15 text-sky-200 border-sky-500/30"
          : status === "pending"
            ? "bg-amber-500/15 text-amber-200 border-amber-500/30"
            : "bg-white/[0.03] text-gray-200 border-white/10"

  const legResults = Array.isArray(results?.leg_results) ? results?.leg_results : []
  const missedLegs = legResults.filter((l) => String(l?.status || "").toLowerCase() === "missed")
  const pushLegs = legResults.filter((l) => String(l?.status || "").toLowerCase() === "push")

  return (
    <div className="border border-white/10 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors p-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <div className="font-semibold text-white truncate">{item.title}</div>
            <Badge variant="outline" className={cn("text-xs border", typeBadge)}>
              {item.parlay_type === "custom" ? "Custom (On-chain)" : "AI Generated"}
            </Badge>
            <Badge variant="outline" className="text-xs border-white/10 text-gray-300 bg-white/[0.03]">
              {legsCount} legs
            </Badge>
            {!!status && (
              <Badge variant="outline" className={cn("text-xs border inline-flex items-center gap-1", statusBadge)}>
                {status === "hit" ? <CheckCircle className="h-3 w-3" /> : null}
                {status === "missed" ? <XCircle className="h-3 w-3" /> : null}
                {status === "push" ? <MinusCircle className="h-3 w-3" /> : null}
                {status === "pending" ? <Clock className="h-3 w-3" /> : null}
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </Badge>
            )}
            {showInscription && <InscriptionStatusPill status={item.inscription_status} />}
          </div>
          {created && (
            <div className="text-xs text-gray-400 mt-1">
              {created.toLocaleDateString()} • {created.toLocaleTimeString()}
            </div>
          )}
          {!!status && (
            <div className="mt-2 text-xs text-gray-300/80">
              {typeof results?.legs_hit === "number" && typeof results?.legs_missed === "number" ? (
                <span>
                  {results.legs_hit} hit • {results.legs_missed} missed
                  {pushLegs.length ? ` • ${pushLegs.length} push` : ""}
                </span>
              ) : null}
              {missedLegs.length ? (
                <div className="mt-1 text-xs text-red-200/90">
                  Missed: {missedLegs.slice(0, 2).map(formatLegLabel).join(", ")}
                  {missedLegs.length > 2 ? ` +${missedLegs.length - 2} more` : ""}
                </div>
              ) : null}
            </div>
          )}
        </div>

        <div className="flex gap-2">
          {canInscribe && (
            <Button
              size="sm"
              variant="outline"
              className="border-emerald-500/30 text-emerald-200 hover:bg-emerald-500/10"
              onClick={() => onInscribe?.(item.id)}
            >
              <Link2 className="h-4 w-4 mr-2" />
              Inscribe
            </Button>
          )}
          {item.inscription_status === "failed" && (
            <Button
              size="sm"
              variant="outline"
              className="border-amber-500/30 text-amber-200 hover:bg-amber-500/10"
              onClick={() => onRetry(item.id)}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry Inscription
            </Button>
          )}
        </div>
      </div>

      {showInscription && item.inscription_status === "confirmed" && item.inscription_hash && (
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <div className="rounded-lg border border-white/10 bg-black/30 p-3">
            <div className="text-xs text-gray-400 mb-1">Inscription Hash</div>
            <div className="flex items-center justify-between gap-2">
              <div className="font-mono text-sm text-emerald-200 truncate">{shortenHash(item.inscription_hash)}</div>
              <Button
                size="icon"
                variant="ghost"
                className="text-gray-300 hover:text-white"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(item.inscription_hash || "")
                    toast.success("Hash copied")
                  } catch {
                    toast.error("Failed to copy")
                  }
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-black/30 p-3 flex items-end justify-between gap-3">
            <div className="min-w-0">
              <div className="text-xs text-gray-400 mb-1">Verification</div>
              <div className="text-sm text-gray-200 truncate">
                {item.inscription_tx ? shortenHash(item.inscription_tx) : "—"}
              </div>
            </div>
            {item.solscan_url && (
              <Button asChild size="sm" className="bg-emerald-500 text-black hover:bg-emerald-400">
                <Link href={item.solscan_url} target="_blank" rel="noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  View on Solscan
                </Link>
              </Button>
            )}
          </div>
        </div>
      )}

      {showInscription && item.inscription_status === "failed" && item.inscription_error && (
        <div className="mt-3 text-xs text-amber-200/90">
          {item.inscription_error}
        </div>
      )}
    </div>
  )
}



