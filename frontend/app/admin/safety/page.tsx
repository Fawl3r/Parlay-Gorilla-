"use client";

import { useEffect, useState } from "react";
import { adminApi } from "@/lib/admin-api";
import type { SafetySnapshotResponse } from "@/lib/api/types/system";
import { Shield, RefreshCw, AlertTriangle, CheckCircle } from "lucide-react";

const ENABLE_SAFETY_DASHBOARD = process.env.NEXT_PUBLIC_ENABLE_ADMIN_SAFETY === "true";

function formatTs(ts: number | undefined): string {
  if (ts == null) return "—";
  try {
    const d = new Date(ts * 1000);
    return Number.isNaN(d.getTime()) ? "—" : d.toISOString();
  } catch {
    return "—";
  }
}

/** Presentational view of a safety snapshot (state, reasons, events, telemetry). Safe when keys are missing. */
export function SafetySnapshotView({ snap }: { snap: SafetySnapshotResponse }) {
  const state = snap?.state ?? "GREEN";
  const reasons = snap?.reasons ?? [];
  const events = snap?.events ?? [];
  const telemetry = snap?.telemetry ?? {};
  const healthScore = snap?.health_score ?? 0;
  const recommendedAction = snap?.recommended_action ?? "";

  const stateBadge =
    state === "GREEN" ? (
      <span className="inline-flex items-center gap-2 rounded-lg bg-emerald-500/20 px-4 py-2 text-2xl font-bold text-emerald-400 border border-emerald-500/30">
        <CheckCircle className="h-8 w-8" /> GREEN
      </span>
    ) : state === "YELLOW" ? (
      <span className="inline-flex items-center gap-2 rounded-lg bg-amber-500/20 px-4 py-2 text-2xl font-bold text-amber-400 border border-amber-500/30">
        <AlertTriangle className="h-8 w-8" /> YELLOW
      </span>
    ) : (
      <span className="inline-flex items-center gap-2 rounded-lg bg-red-500/20 px-4 py-2 text-2xl font-bold text-red-400 border border-red-500/30">
        <Shield className="h-8 w-8" /> RED
      </span>
    );

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-emerald-900/30 bg-[#111118] p-6">
        <h2 className="mb-2 text-sm font-medium text-gray-400">Current state</h2>
        <div>{stateBadge}</div>
        {typeof healthScore === "number" && (
          <p className="mt-2 text-sm text-gray-400">Health score: {healthScore}/100</p>
        )}
      </div>
      {recommendedAction && (
        <div className="rounded-xl border border-emerald-900/30 bg-[#111118] p-6">
          <h2 className="mb-2 text-sm font-medium text-gray-400">Recommended action</h2>
          <p className="text-white">{recommendedAction}</p>
        </div>
      )}
      {reasons.length > 0 && (
        <div className="rounded-xl border border-emerald-900/30 bg-[#111118] p-6">
          <h2 className="mb-2 text-sm font-medium text-gray-400">Reasons</h2>
          <ul className="list-inside list-disc space-y-1 text-white">
            {reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}
      {events.length > 0 && (
        <div className="rounded-xl border border-emerald-900/30 bg-[#111118] p-6">
          <h2 className="mb-2 text-sm font-medium text-gray-400">Timeline (events)</h2>
          <ul className="space-y-2 text-sm">
            {events.map((ev, i) => (
              <li key={i} className="text-gray-300">
                {formatTs(ev.ts)} — {ev.from_state} → {ev.to_state}
                {ev.reasons?.length ? ` (${ev.reasons.join(", ")})` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="rounded-xl border border-emerald-900/30 bg-[#111118] p-6">
        <h2 className="mb-2 text-sm font-medium text-gray-400">Key telemetry</h2>
        <div className="grid gap-2 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">last_successful_odds_refresh_at</span>
            <span className="text-white">{formatTs(telemetry.last_successful_odds_refresh_at as number)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">last_successful_games_refresh_at</span>
            <span className="text-white">{formatTs(telemetry.last_successful_games_refresh_at as number)}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">error_count_5m</span>
            <span className="text-white">{String(telemetry.error_count_5m ?? "—")}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-gray-500">estimated_api_calls_today / daily_api_budget</span>
            <span className="text-white">
              {String(telemetry.estimated_api_calls_today ?? "—")} / {String(telemetry.daily_api_budget ?? "—")}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminSafetyPage() {
  const [snap, setSnap] = useState<SafetySnapshotResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSafety = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await adminApi.getSafetySnapshot();
      setSnap(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load safety snapshot");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!ENABLE_SAFETY_DASHBOARD) return;
    fetchSafety();
  }, []);

  if (!ENABLE_SAFETY_DASHBOARD) {
    return (
      <div className="rounded-xl border border-amber-900/30 bg-amber-900/10 p-6 text-amber-200">
        <p>Safety dashboard is disabled. Set NEXT_PUBLIC_ENABLE_ADMIN_SAFETY=true to enable.</p>
      </div>
    );
  }

  if (loading && !snap) {
    return (
      <div className="flex items-center justify-center py-12">
        <span className="text-emerald-400 animate-pulse">Loading safety snapshot…</span>
      </div>
    );
  }

  if (error && !snap) {
    return (
      <div className="rounded-xl border border-red-900/30 bg-red-900/10 p-6 text-red-200">
        <p>{error}</p>
        <button
          type="button"
          onClick={fetchSafety}
          className="mt-4 rounded-lg bg-red-500/20 px-4 py-2 text-red-300 hover:bg-red-500/30"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-white">Safety Mode</h1>
        <button
          type="button"
          onClick={fetchSafety}
          className="flex items-center gap-2 rounded-lg bg-emerald-500/20 px-4 py-2 text-emerald-300 hover:bg-emerald-500/30"
        >
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>
      {snap ? <SafetySnapshotView snap={snap} /> : null}
    </div>
  );
}
