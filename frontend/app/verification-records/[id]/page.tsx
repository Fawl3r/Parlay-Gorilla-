"use client"

import { useEffect, useMemo, useState } from "react"
import { Copy, ExternalLink, RefreshCw } from "lucide-react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { VerificationRecordResponse } from "@/lib/api"
import { defaultSuiExplorer } from "@/lib/verification/SuiExplorerUrlBuilder"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

function shortenHash(hash: string) {
  if (!hash) return ""
  if (hash.length <= 18) return hash
  return `${hash.slice(0, 8)}…${hash.slice(-8)}`
}

function statusLabel(status: string): string {
  const s = String(status || "").toLowerCase()
  if (s === "confirmed") return "Confirmed"
  if (s === "failed") return "Failed"
  return "Queued"
}

export default function VerificationRecordPage({ params }: { params: { id: string } }) {
  const id = String(params?.id || "").trim()
  const [record, setRecord] = useState<VerificationRecordResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const shouldPoll = useMemo(() => {
    const s = String(record?.status || "").toLowerCase()
    return Boolean(id) && (s === "queued" || !s)
  }, [id, record?.status])

  const load = async () => {
    if (!id) return
    setLoading(true)
    setError(null)
    try {
      const resp = await api.getVerificationRecord(id)
      setRecord(resp)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to load verification record")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  useEffect(() => {
    if (!shouldPoll) return
    const t = setInterval(() => {
      void load()
    }, 4000)
    return () => clearInterval(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shouldPoll, id])

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-8">
      <Card className="bg-white/[0.02] border-white/10">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="text-white">Verification record</CardTitle>
            <div className="mt-2 text-sm text-gray-300/80">
              This page shows the status of your optional time-stamped verification record.
            </div>
          </div>
          <Button
            variant="outline"
            className="border-white/10 text-gray-200"
            onClick={() => void load()}
            disabled={loading}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            {loading ? "Refreshing..." : "Refresh"}
          </Button>
        </CardHeader>

        <CardContent className="space-y-4">
          {error ? <div className="text-sm text-red-300">{error}</div> : null}

          {!record && !error ? <div className="text-sm text-gray-400">Loading…</div> : null}

          {record ? (
            <>
              <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                <div className="text-xs uppercase tracking-wide text-gray-400">Status</div>
                <div className="mt-1 text-lg font-semibold text-white">{statusLabel(record.status)}</div>
                {String(record.status || "").toLowerCase() === "queued" ? (
                  <div className="mt-1 text-sm text-gray-300/80">This may take a moment. This page will update automatically.</div>
                ) : null}
                {String(record.status || "").toLowerCase() === "failed" && record.error ? (
                  <div className="mt-2 text-sm text-amber-200/90">{record.error}</div>
                ) : null}
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs uppercase tracking-wide text-gray-400">Created</div>
                  <div className="mt-1 text-sm text-white">{record.created_at || "—"}</div>
                </div>
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs uppercase tracking-wide text-gray-400">Confirmed</div>
                  <div className="mt-1 text-sm text-white">{record.confirmed_at || "—"}</div>
                </div>
              </div>

              <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                <div className="text-xs uppercase tracking-wide text-gray-400">Data hash</div>
                <div className="mt-1 flex items-center justify-between gap-2">
                  <div className="min-w-0 font-mono text-sm text-emerald-200 truncate">
                    {record.data_hash ? shortenHash(record.data_hash) : "—"}
                  </div>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="text-gray-200 hover:text-white"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(record.data_hash || "")
                        toast.success("Copied")
                      } catch {
                        toast.error("Failed to copy")
                      }
                    }}
                    aria-label="Copy data hash"
                    disabled={!record.data_hash}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {record.receipt_id ? (
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs uppercase tracking-wide text-gray-400">Transaction Receipt</div>
                  <div className="mt-1 flex items-center justify-between gap-2">
                    <div className="min-w-0 font-mono text-sm text-emerald-200 truncate">
                      {shortenHash(record.receipt_id)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-gray-200 hover:text-white"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(record.receipt_id || "")
                            toast.success("Copied")
                          } catch {
                            toast.error("Failed to copy")
                          }
                        }}
                        aria-label="Copy receipt id"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-gray-200 hover:text-white"
                        onClick={() => {
                          const url = defaultSuiExplorer.txUrl(record.receipt_id || "")
                          window.open(url, "_blank", "noopener,noreferrer")
                        }}
                        aria-label="View on Sui Explorer"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ) : null}

              {record.record_object_id ? (
                <div className="rounded-xl border border-white/10 bg-black/30 p-4">
                  <div className="text-xs uppercase tracking-wide text-gray-400">Proof Object</div>
                  <div className="mt-1 flex items-center justify-between gap-2">
                    <div className="min-w-0 font-mono text-sm text-emerald-200 truncate">
                      {shortenHash(record.record_object_id)}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-gray-200 hover:text-white"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(record.record_object_id || "")
                            toast.success("Copied")
                          } catch {
                            toast.error("Failed to copy")
                          }
                        }}
                        aria-label="Copy object id"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="text-gray-200 hover:text-white"
                        onClick={() => {
                          const url = defaultSuiExplorer.objectUrl(record.record_object_id || "")
                          window.open(url, "_blank", "noopener,noreferrer")
                        }}
                        aria-label="View on Sui Explorer"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ) : null}
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}


