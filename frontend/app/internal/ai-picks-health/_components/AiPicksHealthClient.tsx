"use client"

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import type { AiPicksHealthResponse } from "@/lib/api/services/InternalMetricsApi"
import { getFailReasonLabel, getQuickActionLabel } from "../_lib/labels"

const DAYS_OPTIONS = [7, 14, 30] as const

function Card({
  title,
  children,
  className = "",
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={`rounded-lg border border-border bg-card p-4 ${className}`}>
      <h3 className="text-sm font-semibold text-muted-foreground mb-3">{title}</h3>
      {children}
    </div>
  )
}

export function AiPicksHealthClient() {
  const [days, setDays] = useState<number>(7)
  const [data, setData] = useState<AiPicksHealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    api
      .getAiPicksHealth(days)
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err: any) => {
        if (!cancelled) {
          const status = err?.response?.status
          const msg = status === 404 ? "Not found" : err?.response?.data?.detail || err?.message || "Failed to load"
          setError(msg)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [days])

  if (loading && !data) {
    return (
      <div className="p-6">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (!data) return null

  const { totals, success_rate, beginner, standard, fail_reasons_top, quick_actions, graduation, premium } = data

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-xl font-semibold">AI Picks Health</h1>
        <div className="flex gap-2">
          {DAYS_OPTIONS.map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              className={`rounded-md border px-3 py-1.5 text-sm ${days === d ? "border-primary bg-primary/10" : "border-border"}`}
            >
              {d} days
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card title="Activation (app opened)">
          <p className="text-2xl font-mono">{totals.app_opened}</p>
        </Card>
        <Card title="Attempts">
          <p className="text-2xl font-mono">{totals.ai_picks_generate_attempt}</p>
        </Card>
        <Card title="Success">
          <p className="text-2xl font-mono">{totals.ai_picks_generate_success}</p>
        </Card>
        <Card title="Fail">
          <p className="text-2xl font-mono">{totals.ai_picks_generate_fail}</p>
        </Card>
      </div>

      <Card title="Success Rate">
        <p className="text-2xl font-mono">{success_rate}%</p>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card title="Beginner">
          <p className="text-muted-foreground text-sm">Success: {beginner.success} · Fail: {beginner.fail}</p>
          <p className="text-xl font-mono mt-1">{beginner.success_rate}% success rate</p>
        </Card>
        <Card title="Standard">
          <p className="text-muted-foreground text-sm">Success: {standard.success} · Fail: {standard.fail}</p>
          <p className="text-xl font-mono mt-1">{standard.success_rate}% success rate</p>
        </Card>
      </div>

      <Card title="Top Fail Reasons">
        <ul className="space-y-1">
          {fail_reasons_top.map(({ reason, count }) => (
            <li key={reason} className="flex justify-between text-sm">
              <span>{getFailReasonLabel(reason)}</span>
              <span className="font-mono">{count}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Quick Action Clicks">
        <ul className="space-y-1">
          {quick_actions.map(({ action_id, clicked }) => (
            <li key={action_id} className="flex justify-between text-sm">
              <span>{getQuickActionLabel(action_id)}</span>
              <span className="font-mono">{clicked}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Graduation Nudge">
        <p className="text-muted-foreground text-sm">Shown: {graduation.nudge_shown}</p>
        <p className="text-sm">Profile clicks: {graduation.nudge_clicked_profile} · Dismiss: {graduation.nudge_clicked_dismiss}</p>
        <p className="text-xl font-mono mt-1">CTR: {graduation.ctr}%</p>
      </Card>

      <Card title="Premium (upsell)">
        <p className="text-muted-foreground text-sm">Upsell shown: {premium.upsell_shown} · Upgrade clicked: {premium.upgrade_clicked}</p>
        <p className="text-xl font-mono mt-1">CTR: {premium.ctr}%</p>
      </Card>
    </div>
  )
}
