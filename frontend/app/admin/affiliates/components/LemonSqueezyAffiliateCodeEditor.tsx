"use client"

import { useMemo, useState } from "react"
import { Save, X } from "lucide-react"

import { adminApi } from "@/lib/admin-api"

type Props = {
  affiliateId: string
  value: string | null | undefined
  onUpdated: (nextValue: string | null) => void
}

export function LemonSqueezyAffiliateCodeEditor({ affiliateId, value, onUpdated }: Props) {
  const initial = useMemo(() => (value || "").trim(), [value])
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(initial)
  const [saving, setSaving] = useState(false)

  const startEditing = () => {
    setDraft(initial)
    setIsEditing(true)
  }

  const cancel = () => {
    setDraft(initial)
    setIsEditing(false)
  }

  const save = async () => {
    const next = draft.trim() || null
    try {
      setSaving(true)
      const res = await adminApi.updateAffiliateLemonSqueezyAffiliateCode(affiliateId, next)
      onUpdated(res.lemonsqueezy_affiliate_code)
      setIsEditing(false)
    } finally {
      setSaving(false)
    }
  }

  if (!isEditing) {
    return (
      <div className="flex items-center gap-2">
        <span className="text-gray-400 font-mono">{initial || "—"}</span>
        <button
          type="button"
          onClick={startEditing}
          className="text-[11px] text-emerald-300 hover:text-emerald-200 hover:underline"
        >
          Edit
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        placeholder="1234"
        className="w-20 bg-[#0a0a0f] border border-emerald-900/40 rounded-md px-2 py-1 text-xs text-white font-mono"
        disabled={saving}
      />
      <button
        type="button"
        onClick={save}
        disabled={saving}
        className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 disabled:opacity-50"
      >
        <Save className="w-3 h-3" />
        Save
      </button>
      <button
        type="button"
        onClick={cancel}
        disabled={saving}
        className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-white/5 border border-white/10 text-gray-200 text-xs hover:bg-white/10 disabled:opacity-50"
      >
        <X className="w-3 h-3" />
        Cancel
      </button>
    </div>
  )
}


