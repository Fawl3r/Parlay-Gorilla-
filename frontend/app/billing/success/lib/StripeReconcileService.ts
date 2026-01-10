import { api } from "@/lib/api"

export type StripeReconcileResponse = {
  status: "applied" | "pending" | "skipped"
  message: string
  session_id?: string | null
  mode?: string | null
  purchase_type?: string | null
  subscription_id?: string | null
}

export class StripeReconcileService {
  async reconcileLatest(): Promise<StripeReconcileResponse> {
    const res = await api.post("/api/billing/stripe/reconcile-latest")
    return res.data as StripeReconcileResponse
  }

  async reconcileSession(sessionId: string): Promise<StripeReconcileResponse> {
    const res = await api.post("/api/billing/stripe/reconcile", { session_id: sessionId })
    return res.data as StripeReconcileResponse
  }
}


