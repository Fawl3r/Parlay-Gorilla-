"use client"

import Link from "next/link"
import { Copy, ExternalLink, RefreshCw } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SavedParlayResponse } from "@/lib/api"
import { InscriptionStatusPill } from "@/components/analytics/InscriptionStatusPill"

function shortenHash(hash: string) {
  if (!hash) return ""
  if (hash.length <= 16) return hash
  return `${hash.slice(0, 6)}…${hash.slice(-6)}`
}

export function SavedParlayRow({
  item,
  onRetry,
}: {
  item: SavedParlayResponse
  onRetry: (id: string) => Promise<void>
}) {
  const legsCount = Array.isArray(item.legs) ? item.legs.length : 0
  const created = item.created_at ? new Date(item.created_at) : null

  const typeBadge =
    item.parlay_type === "custom"
      ? "bg-cyan-500/15 text-cyan-200 border-cyan-500/30"
      : "bg-purple-500/15 text-purple-200 border-purple-500/30"

  const showInscription = item.parlay_type === "custom"

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
            {showInscription && <InscriptionStatusPill status={item.inscription_status} />}
          </div>
          {created && (
            <div className="text-xs text-gray-400 mt-1">
              {created.toLocaleDateString()} • {created.toLocaleTimeString()}
            </div>
          )}
        </div>

        {showInscription && item.inscription_status === "failed" && (
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



