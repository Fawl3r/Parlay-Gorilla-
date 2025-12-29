"use client"

import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { api } from "@/lib/api"
import type { InscriptionStatus, SavedParlayResponse } from "@/lib/api"
import { SavedParlayRow } from "@/components/analytics/SavedParlayRow"

type Tab = "all" | "custom" | "ai"

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

function hasQueued(items: SavedParlayResponse[]) {
  return items.some((i) => (i.inscription_status as InscriptionStatus) === "queued")
}

export function SavedParlaysSection() {
  const [tab, setTab] = useState<Tab>("all")
  const [items, setItems] = useState<SavedParlayWithResults[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const counts = useMemo(() => {
    const total = items.length
    const custom = items.filter((i) => i.parlay_type === "custom").length
    const ai = items.filter((i) => i.parlay_type === "ai_generated").length
    return { total, custom, ai }
  }, [items])

  const filtered = useMemo(() => {
    if (tab === "custom") return items.filter((i) => i.parlay_type === "custom")
    if (tab === "ai") return items.filter((i) => i.parlay_type === "ai_generated")
    return items
  }, [items, tab])

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await api.listSavedParlays("all", 100, true)
      setItems(resp)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load saved parlays")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Poll while queued exists.
  useEffect(() => {
    if (!hasQueued(items)) return
    const id = setInterval(() => {
      load()
    }, 4000)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items])

  const retry = async (id: string) => {
    try {
      const updated = await api.retryParlayInscription(id)
      toast.success("Retry queued")
      setItems((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Retry failed")
    }
  }

  const inscribe = async (id: string) => {
    try {
      const updated = await api.queueInscription(id)
      toast.success("Inscription queued")
      setItems((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || "Inscription failed"
      toast.error(detail)
    }
  }

  return (
    <Card className="bg-white/[0.02] border-white/10">
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="text-white">Saved Parlays</CardTitle>
            <CardDescription className="text-gray-400">
              Select parlays to inscribe on Solana for on-chain proof. Premium users get 15 inscriptions per month.
            </CardDescription>
          </div>
          <Button variant="outline" className="border-white/10 text-gray-200" onClick={load} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        </div>

        <div className="mt-4 flex gap-2 flex-wrap">
          {([
            { id: "all" as const, label: `All (${counts.total})` },
            { id: "custom" as const, label: `Custom (On-chain) (${counts.custom})` },
            { id: "ai" as const, label: `AI Generated (${counts.ai})` },
          ] as const).map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={cn(
                "px-4 py-2 rounded-md border-2 transition-colors text-sm",
                tab === t.id ? "border-emerald-500 bg-emerald-500/10 text-emerald-300" : "border-white/10 bg-white/5 text-gray-300 hover:border-white/20"
              )}
            >
              {t.label}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {error ? (
          <div className="text-sm text-red-300">{error}</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-10 text-gray-400">No saved parlays yet.</div>
        ) : (
          <div className="space-y-3">
            {filtered.map((item) => (
              <SavedParlayRow key={item.id} item={item} onRetry={retry} onInscribe={inscribe} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}



