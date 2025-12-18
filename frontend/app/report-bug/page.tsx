"use client"

import { Suspense, useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import { AlertCircle, CheckCircle, Loader2, Send, Bug } from "lucide-react"
import { usePathname, useSearchParams } from "next/navigation"

import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth-context"

type Severity = "low" | "medium" | "high"

type FormState = {
  title: string
  description: string
  severity: Severity
  contact_email: string
  steps_to_reproduce: string
  expected_result: string
  actual_result: string
  page_path: string
  page_url: string
}

function ReportBugContent() {
  const { user } = useAuth()
  const pathname = usePathname()
  const search = useSearchParams()

  const from = search.get("from") || ""
  const resolvedPagePath = from || pathname || ""

  const [form, setForm] = useState<FormState>({
    title: "",
    description: "",
    severity: "medium",
    contact_email: "",
    steps_to_reproduce: "",
    expected_result: "",
    actual_result: "",
    page_path: resolvedPagePath,
    page_url: "",
  })
  const [status, setStatus] = useState<"idle" | "sending" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")

  useEffect(() => {
    // Pre-fill context in a safe way (no secrets, no tokens).
    const url = typeof window !== "undefined" ? window.location.href : ""
    setForm((prev) => ({
      ...prev,
      page_path: resolvedPagePath,
      page_url: url,
      contact_email: prev.contact_email || user?.email || "",
    }))
  }, [resolvedPagePath, user?.email])

  const canSubmit = useMemo(() => {
    if (status === "sending") return false
    if (form.title.trim().length < 4) return false
    if (form.description.trim().length < 10) return false
    return true
  }, [form.description, form.title, status])

  const handleChange = (key: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus("sending")
    setErrorMessage("")

    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        severity: form.severity,
        contact_email: form.contact_email.trim() || undefined,
        page_path: form.page_path.trim() || undefined,
        page_url: form.page_url.trim() || undefined,
        steps_to_reproduce: form.steps_to_reproduce.trim() || undefined,
        expected_result: form.expected_result.trim() || undefined,
        actual_result: form.actual_result.trim() || undefined,
        metadata: {
          source: "report-bug-page",
        },
      }

      await api.post("/api/bug-reports", payload, { timeout: 15000 })
      setStatus("success")
      setForm((prev) => ({
        ...prev,
        title: "",
        description: "",
        severity: "medium",
        steps_to_reproduce: "",
        expected_result: "",
        actual_result: "",
      }))

      setTimeout(() => setStatus("idle"), 6000)
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "We couldn’t submit your report. Please try again in a moment."
      setStatus("error")
      setErrorMessage(String(msg))
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f]">
      <Header />

      <main className="flex-1 py-16">
        <div className="container mx-auto px-4 max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="text-center mb-10"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-gray-300 text-sm">
              <Bug className="h-4 w-4 text-emerald-400" />
              Report a bug
            </div>
            <h1 className="text-4xl md:text-5xl font-black mt-4 mb-3">
              <span className="text-white">Help us </span>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">
                improve
              </span>
            </h1>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Tell us what you ran into. Keep it simple — we’ll take it from there.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.05 }}
            className="bg-white/[0.03] border border-white/10 rounded-2xl p-6 md:p-8 backdrop-blur-xl"
          >
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Title</label>
                <input
                  value={form.title}
                  onChange={(e) => handleChange("title", e.target.value)}
                  required
                  placeholder="Example: Odds don’t match what I’m seeing"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Severity</label>
                  <select
                    value={form.severity}
                    onChange={(e) => handleChange("severity", e.target.value)}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Email (optional)</label>
                  <input
                    type="email"
                    value={form.contact_email}
                    onChange={(e) => handleChange("contact_email", e.target.value)}
                    placeholder="So we can follow up if needed"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">What happened?</label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                  required
                  rows={5}
                  placeholder="Describe the problem in your own words."
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Expected</label>
                  <textarea
                    value={form.expected_result}
                    onChange={(e) => handleChange("expected_result", e.target.value)}
                    rows={3}
                    placeholder="What did you expect to happen?"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Actual</label>
                  <textarea
                    value={form.actual_result}
                    onChange={(e) => handleChange("actual_result", e.target.value)}
                    rows={3}
                    placeholder="What actually happened?"
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Steps to reproduce (optional)</label>
                <textarea
                  value={form.steps_to_reproduce}
                  onChange={(e) => handleChange("steps_to_reproduce", e.target.value)}
                  rows={3}
                  placeholder="Example: Open NFL → pick a game → click Analysis → scroll to Trends."
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all resize-none"
                />
              </div>

              {/* Context (read-only, but visible for trust) */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Page path</label>
                  <input
                    value={form.page_path}
                    onChange={(e) => handleChange("page_path", e.target.value)}
                    className="w-full px-4 py-2 bg-black/20 border border-white/10 rounded-lg text-gray-300 text-sm"
                    placeholder="/some/page"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">Page URL</label>
                  <input
                    value={form.page_url}
                    onChange={(e) => handleChange("page_url", e.target.value)}
                    className="w-full px-4 py-2 bg-black/20 border border-white/10 rounded-lg text-gray-300 text-sm"
                    placeholder="https://..."
                  />
                </div>
              </div>

              {status === "success" && (
                <div className="flex items-center gap-2 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                  <CheckCircle className="h-5 w-5" />
                  <p>Thanks — your report was sent.</p>
                </div>
              )}

              {status === "error" && (
                <div className="flex items-center gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300">
                  <AlertCircle className="h-5 w-5" />
                  <p>{errorMessage}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={!canSubmit}
                className="w-full py-4 px-6 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {status === "sending" ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Sending…
                  </>
                ) : (
                  <>
                    <Send className="h-5 w-5" />
                    Send report
                  </>
                )}
              </button>
            </form>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

// Wrap the content in Suspense to handle useSearchParams() during build/prerender.
export default function ReportBugPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex flex-col bg-[#0a0a0f]">
          <Header />
          <main className="flex-1 flex items-center justify-center p-4">
            <Loader2 className="h-8 w-8 animate-spin text-emerald-400" />
          </main>
          <Footer />
        </div>
      }
    >
      <ReportBugContent />
    </Suspense>
  )
}



