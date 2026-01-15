"use client"

import { useEffect } from "react"

type ReporterPayload = {
  sessionId: string
  runId: string
  hypothesisId: string
  location: string
  message: string
  data?: Record<string, unknown>
  timestamp: number
}

class ClientRuntimeErrorReportingManager {
  private readonly sessionId: string
  private readonly runId: string
  private installed = false

  constructor(params: { sessionId: string; runId: string }) {
    this.sessionId = params.sessionId
    this.runId = params.runId
  }

  install(): () => void {
    if (this.installed) return () => {}
    this.installed = true

    const onError = (evt: ErrorEvent) => {
      const msg = String(evt.message || "")
      if (!msg) return

      // Focus on the specific dev crash we're debugging.
      if (!msg.toLowerCase().includes("rendered more hooks")) return

      const payload: ReporterPayload = {
        sessionId: this.sessionId,
        runId: this.runId,
        hypothesisId: "HOOKS",
        location: "ClientRuntimeErrorReporter:onError",
        message: "window.error",
        data: {
          message: msg,
          filename: evt.filename,
          lineno: evt.lineno,
          colno: evt.colno,
          stack: (evt.error && typeof evt.error === "object" && "stack" in evt.error)
            ? String((evt.error as { stack?: unknown }).stack || "").slice(0, 4000)
            : undefined,
          pathname: typeof window !== "undefined" ? window.location.pathname : undefined,
        },
        timestamp: Date.now(),
      }

      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(()=>{});
      // #endregion
    }

    const onUnhandledRejection = (evt: PromiseRejectionEvent) => {
      const reason = evt.reason
      const msg =
        typeof reason === "string"
          ? reason
          : reason instanceof Error
            ? reason.message
            : ""
      if (!msg.toLowerCase().includes("rendered more hooks")) return

      const payload: ReporterPayload = {
        sessionId: this.sessionId,
        runId: this.runId,
        hypothesisId: "HOOKS",
        location: "ClientRuntimeErrorReporter:onUnhandledRejection",
        message: "window.unhandledrejection",
        data: {
          message: msg,
          stack: reason instanceof Error ? String(reason.stack || "").slice(0, 4000) : undefined,
          pathname: typeof window !== "undefined" ? window.location.pathname : undefined,
        },
        timestamp: Date.now(),
      }

      // #region agent log
      fetch('http://127.0.0.1:7242/ingest/abd8edf1-767f-4ebd-9040-91726939b7d4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).catch(()=>{});
      // #endregion
    }

    window.addEventListener("error", onError)
    window.addEventListener("unhandledrejection", onUnhandledRejection)

    return () => {
      window.removeEventListener("error", onError)
      window.removeEventListener("unhandledrejection", onUnhandledRejection)
    }
  }
}

export function ClientRuntimeErrorReporter() {
  useEffect(() => {
    // Never run this in production builds.
    if (process.env.NODE_ENV === "production") return
    const manager = new ClientRuntimeErrorReportingManager({ sessionId: "debug-session", runId: "hooks-run1" })
    return manager.install()
  }, [])

  return null
}

