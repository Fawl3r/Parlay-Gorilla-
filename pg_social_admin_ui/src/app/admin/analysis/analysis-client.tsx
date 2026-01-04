"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { AdminPageHeader } from "@/components/admin/AdminPageHeader";
import { AdminPageShell } from "@/components/admin/AdminPageShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";
import { errorMessage } from "@/lib/errorMessage";
import { BotAdminApiClient } from "@/services/botAdminApiClient";
import type { CachedAnalysisItem } from "@/types/analysis";

type AnalysisState = {
  loading: boolean;
  error: string;
  items: CachedAnalysisItem[];
};

function fmt(iso: string) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function AnalysisClient() {
  const api = useMemo(() => new BotAdminApiClient(), []);
  const router = useRouter();
  const toast = useToast();
  const [state, setState] = useState<AnalysisState>({ loading: true, error: "", items: [] });

  async function refresh() {
    setState((s) => ({ ...s, loading: true, error: "" }));
    try {
      const feed = await api.analysisFeed(50);
      setState({ loading: false, error: "", items: feed.items });
    } catch (e: unknown) {
      setState({ loading: false, error: errorMessage(e, "Failed loading analysis feed"), items: [] });
    }
  }

  async function refreshFromUpstream() {
    setState((s) => ({ ...s, error: "" }));
    try {
      await api.refreshAnalysis();
      await refresh();
    } catch (e: unknown) {
      setState((s) => ({ ...s, error: errorMessage(e, "Refresh failed") }));
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <AdminPageShell>
      <AdminPageHeader
        title="Analysis Feed"
        description="Cached angles and insights pulled from the upstream feed."
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={refresh} disabled={state.loading}>
              Refresh (cache)
            </Button>
            <Button onClick={refreshFromUpstream} disabled={state.loading}>
              Pull upstream
            </Button>
          </div>
        }
      />

      {state.error ? <div className="text-base text-red-500">{state.error}</div> : null}
      {state.loading ? <div className="text-base text-white/70">Loading…</div> : null}

      <div className="space-y-3">
        {state.items.map((item) => (
          <Card key={item.slug}>
            <CardHeader className="flex flex-row items-start justify-between gap-3">
              <div className="min-w-0">
                <CardTitle className="text-base truncate">{item.slug}</CardTitle>
                <div className="text-sm text-white/60">Last seen: {fmt(item.last_seen_at)}</div>
              </div>
              <Button
                variant="outline"
                onClick={async () => {
                  try {
                    const result = await api.generatePostFromAnalysis(item.slug);
                    toast.push({ 
                      title: "Post created", 
                      description: "Redirecting to queue...", 
                      variant: "success" 
                    });
                    // Navigate to queue and show the newly created post
                    router.push(`/admin/queue?highlight=${result.post_id}`);
                  } catch (e: unknown) {
                    const msg = errorMessage(e, "Generate post failed");
                    setState((s) => ({ ...s, error: msg }));
                    toast.push({ title: "Generate post failed", description: msg, variant: "error" });
                  }
                }}
              >
                Generate post
              </Button>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-base text-white whitespace-pre-wrap">{item.angle}</div>
              {item.key_points?.length ? (
                <ul className="list-disc pl-5 text-base text-white">
                  {item.key_points.slice(0, 3).map((kp) => (
                    <li key={kp}>{kp}</li>
                  ))}
                </ul>
              ) : null}
              {item.risk_note ? <div className="text-sm text-amber-400">Risk: {item.risk_note}</div> : null}
              <div className="text-sm text-white/60 truncate">CTA: {item.cta_url}</div>
            </CardContent>
          </Card>
        ))}
      </div>
    </AdminPageShell>
  );
}




