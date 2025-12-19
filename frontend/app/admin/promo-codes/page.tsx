"use client"

import { useEffect, useMemo, useState } from "react"
import { Ban, Copy, Gift, Loader2, Plus, RefreshCw } from "lucide-react"
import { toast } from "sonner"

import {
  PromoCode,
  PromoRewardType,
  promoCodesAdminApi,
} from "@/lib/admin/promo-codes-api"

function formatReward(rewardType: PromoRewardType): string {
  if (rewardType === "premium_month") return "1 Month Premium"
  return "3 Credits"
}

function isExpired(expiresAtIso: string): boolean {
  const dt = new Date(expiresAtIso)
  return Number.isFinite(dt.getTime()) ? dt.getTime() <= Date.now() : false
}

function isoFromDatetimeLocal(value: string): string | null {
  if (!value) return null
  const dt = new Date(value)
  if (!Number.isFinite(dt.getTime())) return null
  return dt.toISOString()
}

export default function AdminPromoCodesPage() {
  const [loading, setLoading] = useState(true)
  const [codes, setCodes] = useState<PromoCode[]>([])
  const [total, setTotal] = useState(0)

  const [page, setPage] = useState(1)
  const pageSize = 50

  const [search, setSearch] = useState("")
  const [filterRewardType, setFilterRewardType] = useState<PromoRewardType | "all">("all")
  const [filterActive, setFilterActive] = useState<"all" | "active" | "inactive">("all")

  const [createRewardType, setCreateRewardType] = useState<PromoRewardType>("premium_month")
  const [createExpiresAtLocal, setCreateExpiresAtLocal] = useState("")
  const [createMaxUsesTotal, setCreateMaxUsesTotal] = useState(1)
  const [createCustomCode, setCreateCustomCode] = useState("")
  const [createNotes, setCreateNotes] = useState("")
  const [createLoading, setCreateLoading] = useState(false)

  const [bulkCount, setBulkCount] = useState(25)
  const [bulkRewardType, setBulkRewardType] = useState<PromoRewardType>("credits_3")
  const [bulkExpiresAtLocal, setBulkExpiresAtLocal] = useState("")
  const [bulkMaxUsesTotal, setBulkMaxUsesTotal] = useState(1)
  const [bulkNotes, setBulkNotes] = useState("")
  const [bulkLoading, setBulkLoading] = useState(false)

  const isActiveQuery = useMemo(() => {
    if (filterActive === "all") return undefined
    return filterActive === "active"
  }, [filterActive])

  async function fetchCodes() {
    try {
      setLoading(true)
      const res = await promoCodesAdminApi.list({
        page,
        page_size: pageSize,
        search: search.trim() || undefined,
        reward_type: filterRewardType === "all" ? undefined : filterRewardType,
        is_active: isActiveQuery,
      })
      setCodes(res.codes || [])
      setTotal(res.total || 0)
    } catch (err: any) {
      console.error("Failed to fetch promo codes:", err)
      toast.error(err?.response?.data?.detail || err?.message || "Failed to load promo codes")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCodes()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, filterRewardType, filterActive])

  async function handleCreate() {
    const expiresAtIso = isoFromDatetimeLocal(createExpiresAtLocal)
    if (!expiresAtIso) {
      toast.error("Please choose an expiration date/time")
      return
    }

    try {
      setCreateLoading(true)
      const promo = await promoCodesAdminApi.create({
        reward_type: createRewardType,
        expires_at: expiresAtIso,
        max_uses_total: Math.max(1, Number(createMaxUsesTotal) || 1),
        code: createCustomCode.trim() ? createCustomCode.trim() : undefined,
        notes: createNotes.trim() ? createNotes.trim() : undefined,
      })
      toast.success(`Created code: ${promo.code}`)
      setCreateCustomCode("")
      setCreateNotes("")
      await fetchCodes()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Failed to create promo code")
    } finally {
      setCreateLoading(false)
    }
  }

  async function handleBulkCreate() {
    const expiresAtIso = isoFromDatetimeLocal(bulkExpiresAtLocal)
    if (!expiresAtIso) {
      toast.error("Please choose an expiration date/time for bulk codes")
      return
    }

    const count = Math.max(1, Math.min(500, Number(bulkCount) || 1))
    const maxUses = Math.max(1, Number(bulkMaxUsesTotal) || 1)

    try {
      setBulkLoading(true)
      const created = await promoCodesAdminApi.bulkCreate({
        count,
        reward_type: bulkRewardType,
        expires_at: expiresAtIso,
        max_uses_total: maxUses,
        notes: bulkNotes.trim() ? bulkNotes.trim() : undefined,
      })
      toast.success(`Created ${created.length} promo codes`)
      setBulkNotes("")
      await fetchCodes()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Bulk create failed")
    } finally {
      setBulkLoading(false)
    }
  }

  async function handleCopy(code: string) {
    try {
      await navigator.clipboard.writeText(code)
      toast.success("Copied code")
    } catch {
      toast.error("Failed to copy")
    }
  }

  async function handleDeactivate(promo: PromoCode) {
    if (!confirm(`Deactivate promo code ${promo.code}?`)) return
    try {
      await promoCodesAdminApi.deactivate(promo.id)
      toast.success("Deactivated")
      await fetchCodes()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || err?.message || "Failed to deactivate")
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Promo Codes</h1>
          <p className="text-gray-400 mt-1">Create expiring, one-time-per-account promo codes.</p>
        </div>
        <button
          onClick={() => fetchCodes()}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* Create single */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Plus className="w-4 h-4 text-emerald-400" />
          <h2 className="text-white font-semibold">Create Code</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Reward</label>
            <select
              value={createRewardType}
              onChange={(e) => setCreateRewardType(e.target.value as PromoRewardType)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="premium_month">1 Month Premium</option>
              <option value="credits_3">3 Credits</option>
            </select>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Expires (local time)</label>
            <input
              type="datetime-local"
              value={createExpiresAtLocal}
              onChange={(e) => setCreateExpiresAtLocal(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Max uses (total)</label>
            <input
              type="number"
              min={1}
              value={createMaxUsesTotal}
              onChange={(e) => setCreateMaxUsesTotal(Number(e.target.value))}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs text-gray-400 mb-1">Custom code (optional)</label>
            <input
              value={createCustomCode}
              onChange={(e) => setCreateCustomCode(e.target.value)}
              placeholder="Leave blank to auto-generate"
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>

          <div className="md:col-span-3">
            <label className="block text-xs text-gray-400 mb-1">Notes (optional)</label>
            <input
              value={createNotes}
              onChange={(e) => setCreateNotes(e.target.value)}
              placeholder="Internal notes"
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={handleCreate}
            disabled={createLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
          >
            {createLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Gift className="w-4 h-4" />}
            Create
          </button>
        </div>
      </div>

      {/* Bulk create */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Gift className="w-4 h-4 text-emerald-400" />
          <h2 className="text-white font-semibold">Bulk Create</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Count</label>
            <input
              type="number"
              min={1}
              max={500}
              value={bulkCount}
              onChange={(e) => setBulkCount(Number(e.target.value))}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Reward</label>
            <select
              value={bulkRewardType}
              onChange={(e) => setBulkRewardType(e.target.value as PromoRewardType)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            >
              <option value="credits_3">3 Credits</option>
              <option value="premium_month">1 Month Premium</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Expires (local time)</label>
            <input
              type="datetime-local"
              value={bulkExpiresAtLocal}
              onChange={(e) => setBulkExpiresAtLocal(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Max uses (total)</label>
            <input
              type="number"
              min={1}
              value={bulkMaxUsesTotal}
              onChange={(e) => setBulkMaxUsesTotal(Number(e.target.value))}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
          <div className="md:col-span-4">
            <label className="block text-xs text-gray-400 mb-1">Notes (optional)</label>
            <input
              value={bulkNotes}
              onChange={(e) => setBulkNotes(e.target.value)}
              className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
            />
          </div>
        </div>

        <div className="mt-4">
          <button
            onClick={handleBulkCreate}
            disabled={bulkLoading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors disabled:opacity-50"
          >
            {bulkLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
            Create {bulkCount}
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col md:flex-row gap-3 items-start md:items-center">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search code…"
          className="w-full md:w-80 bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
        />
        <button
          onClick={() => {
            setPage(1)
            fetchCodes()
          }}
          className="px-3 py-2 rounded-lg bg-white/5 border border-white/10 text-sm text-gray-200 hover:bg-white/10"
        >
          Apply Search
        </button>

        <div className="flex gap-3">
          <select
            value={filterRewardType}
            onChange={(e) => {
              setPage(1)
              setFilterRewardType(e.target.value as any)
            }}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="all">All rewards</option>
            <option value="premium_month">1 Month Premium</option>
            <option value="credits_3">3 Credits</option>
          </select>
          <select
            value={filterActive}
            onChange={(e) => {
              setPage(1)
              setFilterActive(e.target.value as any)
            }}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-sm text-white"
          >
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Codes table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#0a0a0f]">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Code
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Reward
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Expires
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                Uses
              </th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-emerald-900/20">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-10 text-center">
                  <div className="inline-flex items-center gap-2 text-gray-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading…
                  </div>
                </td>
              </tr>
            ) : codes.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-10 text-center text-gray-500">
                  No promo codes found
                </td>
              </tr>
            ) : (
              codes.map((p) => {
                const expired = isExpired(p.expires_at)
                const statusLabel = !p.is_active ? "Inactive" : expired ? "Expired" : "Active"
                const statusClass = !p.is_active
                  ? "bg-gray-500/10 text-gray-300 border-gray-500/30"
                  : expired
                    ? "bg-red-500/10 text-red-300 border-red-500/30"
                    : "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"

                return (
                  <tr key={p.id} className="hover:bg-white/5">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm text-white">{p.code}</span>
                        <button
                          onClick={() => handleCopy(p.code)}
                          className="p-1 rounded hover:bg-white/10 text-gray-300"
                          title="Copy"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="text-[11px] text-gray-500">Created {new Date(p.created_at).toLocaleString()}</div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-200">{formatReward(p.reward_type)}</td>
                    <td className="px-6 py-4 text-sm text-gray-300">{new Date(p.expires_at).toLocaleString()}</td>
                    <td className="px-6 py-4 text-center text-sm text-gray-200">
                      {p.redeemed_count} / {p.max_uses_total}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span className={`inline-flex px-2 py-1 rounded border text-xs ${statusClass}`}>
                        {statusLabel}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDeactivate(p)}
                        disabled={!p.is_active}
                        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-200 hover:bg-red-500/15 disabled:opacity-50"
                      >
                        <Ban className="w-4 h-4" />
                        Deactivate
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-emerald-900/20">
          <div className="text-sm text-gray-400">
            Page {page} of {totalPages} • {total} total
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded bg-white/5 border border-white/10 text-sm text-gray-200 disabled:opacity-50"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded bg-white/5 border border-white/10 text-sm text-gray-200 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}


