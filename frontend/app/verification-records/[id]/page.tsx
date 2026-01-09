"use client"

import { use, useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft, Copy, ExternalLink, RefreshCw } from "lucide-react"
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

function ExplorerLinkRow({
  label,
  url,
}: {
  label: string
  url: string
}) {
  const display = shortenHash(url)
  return (
    <div className="mt-2 rounded-lg border border-white/10 bg-black/25 p-3">
      <div className="text-[11px] uppercase tracking-wide text-gray-400">{label}</div>
      <div className="mt-1 flex items-center justify-between gap-2">
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="min-w-0 font-mono text-xs text-emerald-200 truncate hover:text-emerald-100 hover:underline"
          title={url}
        >
          {display || url}
        </a>
        <div className="flex items-center gap-1">
          <Button
            size="icon"
            variant="ghost"
            className="text-gray-200 hover:text-white"
            onClick={async () => {
              try {
                await navigator.clipboard.writeText(url)
                toast.success("Link copied")
              } catch {
                toast.error("Failed to copy")
              }
            }}
            aria-label={`Copy ${label} link`}
          >
            <Copy className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="text-gray-200 hover:text-white"
            onClick={() => window.open(url, "_blank", "noopener,noreferrer")}
            aria-label={`Open ${label} link`}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

type PageProps = {
  params: Promise<{
    id: string
  }>
}

export default function VerificationRecordPage({ params }: PageProps) {
  // Next.js App Router (client pages) may provide `params` as a Promise.
  // Keep this aligned with other dynamic client pages in this repo.
  const { id: rawId } = use(params)
  const id = String(rawId || "").trim()
  const router = useRouter()
  const [record, setRecord] = useState<VerificationRecordResponse | null>(null)
  const [loading, setLoading] = useState(true) // Start as true since we load on mount
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
      console.error("Error loading verification record:", err)
      // Handle different error formats
      let errorMessage = "Failed to load verification record"
      if (err?.response?.data?.detail) {
        errorMessage = err.response.data.detail
      } else if (err?.response?.data?.message) {
        errorMessage = err.response.data.message
      } else if (err?.message) {
        errorMessage = err.message
      } else if (typeof err === "string") {
        errorMessage = err
      }
      
      // Handle specific error cases
      if (err?.response?.status === 401 || err?.response?.status === 403) {
        errorMessage = "Authentication required. Please log in to view this verification record."
      } else if (err?.response?.status === 404) {
        errorMessage = "Verification record not found. It may not exist or you may not have permission to view it."
      } else if (err?.response?.status === 400) {
        errorMessage = "Invalid verification record ID."
      }
      
      setError(errorMessage)
      setRecord(null) // Clear record on error
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
      <div className="mb-6 flex items-center gap-3">
        <Button
          variant="outline"
          className="border-white/10 text-gray-200 hover:bg-white/5"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Link
          href="/app"
          className="px-4 py-2 text-sm font-medium text-gray-200 hover:text-white border border-white/10 rounded-lg hover:bg-white/5 transition-colors"
        >
          Dashboard
        </Link>
      </div>
      <Card className="bg-white/[0.02] border-white/10">
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="text-white">Verification record</CardTitle>
            <div className="mt-2 text-sm text-gray-300/80">
              This page shows the status of your time-stamped verification record.
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
          {error ? (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
              <div className="text-sm font-medium text-red-300">{error}</div>
              <div className="mt-2 text-xs text-red-200/70">
                If this record should be accessible, please check that you're logged in with the correct account.
              </div>
            </div>
          ) : null}

          {loading && !record && !error ? (
            <div className="text-sm text-gray-400">Loading…</div>
          ) : null}
          
          {!loading && !record && !error ? (
            <div className="text-sm text-gray-400">No data available.</div>
          ) : null}

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

                  <ExplorerLinkRow
                    label="Sui Explorer (tx)"
                    url={defaultSuiExplorer.txUrl(record.receipt_id || "")}
                  />
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

                  <ExplorerLinkRow
                    label="Sui Explorer (object)"
                    url={defaultSuiExplorer.objectUrl(record.record_object_id || "")}
                  />
                </div>
              ) : null}
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}


