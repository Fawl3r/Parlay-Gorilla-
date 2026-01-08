"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Shield, AlertCircle, CheckCircle, Loader2 } from "lucide-react"

import { api } from "@/lib/api"

export default function AdminLoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const canSubmit = Boolean(email.trim()) && Boolean(password) && !loading

  const submit = async () => {
    if (!canSubmit) return
    try {
      setLoading(true)
      setError(null)
      const resp = await api.adminLogin(email.trim(), password)
      if (!resp?.success || !resp?.token) {
        setError(resp?.detail || "Authentication failed")
        return
      }
      localStorage.setItem("admin_token", String(resp.token))
      setSuccess(true)
      setTimeout(() => {
        window.location.href = "/admin"
      }, 300)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || "Failed to log in")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-8 shadow-2xl">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
              <Shield className="w-8 h-8 text-emerald-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Admin Login</h1>
            <p className="text-gray-400 text-sm">Enter your admin credentials to continue.</p>
          </div>

          {error ? (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-400 text-sm font-medium">Login failed</p>
                <p className="text-red-300 text-xs mt-1">{error}</p>
              </div>
            </div>
          ) : null}

          {success ? (
            <div className="mb-6 p-4 bg-emerald-900/20 border border-emerald-500/30 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-emerald-400 text-sm font-medium">Authenticated</p>
                <p className="text-emerald-300 text-xs mt-1">Redirecting…</p>
              </div>
            </div>
          ) : null}

          <div className="space-y-4">
            <label className="block text-xs text-white/70">
              Email
              <input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                autoComplete="email"
                className="mt-1 w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-white placeholder-white/30"
                placeholder="admin@parlaygorilla.com"
              />
            </label>

            <label className="block text-xs text-white/70">
              Password
              <input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                type="password"
                autoComplete="current-password"
                className="mt-1 w-full bg-black/40 border border-white/10 rounded px-3 py-2 text-white placeholder-white/30"
                placeholder="••••••••"
                onKeyDown={(e) => {
                  if (e.key === "Enter") void submit()
                }}
              />
            </label>

            <button
              onClick={() => void submit()}
              disabled={!canSubmit}
              className="w-full py-3 px-6 bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-black font-bold rounded-xl transition-all inline-flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
              {loading ? "Signing in..." : "Sign in"}
            </button>

            <button
              onClick={() => router.push("/")}
              className="w-full px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Back to site
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

