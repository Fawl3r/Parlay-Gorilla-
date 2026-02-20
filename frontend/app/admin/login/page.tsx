"use client"

import { useState, useEffect, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Shield, AlertCircle, CheckCircle, Loader2 } from "lucide-react"
import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react"
import { WalletAdapterNetwork } from "@solana/wallet-adapter-base"
import { PhantomWalletAdapter, SolflareWalletAdapter } from "@solana/wallet-adapter-wallets"
import { clusterApiUrl } from "@solana/web3.js"
import { useWallet } from "@solana/wallet-adapter-react"

import { api } from "@/lib/api"

function AdminEmailForm({ setError }: { setError: (s: string | null) => void }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
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
        {loading ? "Signing in..." : "Sign in with email"}
      </button>
    </div>
  )
}

function AdminWalletBlock({
  walletError,
  setWalletError,
}: {
  walletError: string | null
  setWalletError: (s: string | null) => void
}) {
  const { publicKey, connected, disconnect } = useWallet()
  const [verifying, setVerifying] = useState(false)
  const [walletSuccess, setWalletSuccess] = useState(false)

  useEffect(() => {
    if (!connected || !publicKey) return
    let cancelled = false
    const run = async () => {
      const address = publicKey.toBase58()
      setVerifying(true)
      setWalletError(null)
      try {
        const resp = await api.adminWalletLogin(address)
        if (cancelled) return
        if (resp?.success && resp?.token) {
          localStorage.setItem("admin_token", String(resp.token))
          setWalletSuccess(true)
          setTimeout(() => {
            window.location.href = "/admin"
          }, 500)
        } else {
          setWalletError(resp?.detail || "Wallet not authorized for admin")
          disconnect()
        }
      } catch (err: any) {
        if (!cancelled) {
          setWalletError(
            (err?.response?.data?.detail as string) || err?.message || "Wallet login failed"
          )
          disconnect()
        }
      } finally {
        if (!cancelled) setVerifying(false)
      }
    }
    run()
    return () => {
      cancelled = true
    }
  }, [connected, publicKey, disconnect, setWalletError])

  if (walletSuccess) {
    return (
      <div className="p-4 bg-emerald-900/20 border border-emerald-500/30 rounded-lg flex items-center gap-2">
        <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
        <span className="text-emerald-400 text-sm">Redirecting to admin…</span>
      </div>
    )
  }

  if (connected && publicKey) {
    return (
      <div className="space-y-2">
        <div className="p-3 bg-black/40 rounded-lg border border-emerald-900/20 text-center">
          <span className="text-gray-400 text-xs">Connected: </span>
          <span className="text-emerald-400 font-mono text-xs">
            {publicKey.toBase58().slice(0, 6)}…{publicKey.toBase58().slice(-4)}
          </span>
        </div>
        {verifying && (
          <div className="flex items-center justify-center gap-2 text-emerald-400 text-sm">
            <Loader2 className="w-4 h-4 animate-spin" />
            Verifying…
          </div>
        )}
        {!verifying && (
          <button
            type="button"
            onClick={() => disconnect()}
            className="w-full py-2 text-sm text-gray-400 hover:text-white"
          >
            Disconnect wallet
          </button>
        )}
      </div>
    )
  }

  const { wallets, select, connect } = useWallet()
  const phantomOrSolflare = useMemo(() => {
    const byName = new Map<string, (typeof wallets)[number]>()
    for (const w of wallets) {
      const name = w.adapter.name
      if ((name === "Phantom" || name === "Solflare") && !byName.has(name)) byName.set(name, w)
    }
    return Array.from(byName.values())
  }, [wallets])

  return (
    <div className="space-y-2">
      <p className="text-gray-400 text-sm text-center">Connect Phantom or Solflare</p>
      <div className="flex flex-col gap-2">
        {phantomOrSolflare.map((w) => (
          <button
            key={w.adapter.name}
            type="button"
            onClick={async () => {
              select(w.adapter.name)
              await connect()
            }}
            className="w-full py-3 px-6 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-medium"
          >
            {w.adapter.name}
          </button>
        ))}
        {phantomOrSolflare.length === 0 && (
          <p className="text-gray-500 text-sm text-center">Install Phantom or Solflare extension to continue.</p>
        )}
      </div>
    </div>
  )
}

function AdminLoginContent() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const [walletError, setWalletError] = useState<string | null>(null)
  const anyError = error ?? walletError

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-8 shadow-2xl">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
              <Shield className="w-8 h-8 text-emerald-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Admin Login</h1>
            <p className="text-gray-400 text-sm">
              Sign in with email or connect your Phantom wallet.
            </p>
          </div>

          {anyError ? (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-400 text-sm font-medium">Login failed</p>
                <p className="text-red-300 text-xs mt-1">{anyError}</p>
              </div>
            </div>
          ) : null}

          <AdminEmailForm
            setError={(s) => {
              setError(s)
              if (s) setWalletError(null)
            }}
          />

          <div className="my-6 flex items-center gap-3">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-gray-500 text-xs">or</span>
            <div className="flex-1 h-px bg-white/10" />
          </div>

          <AdminWalletBlock
            walletError={walletError}
            setWalletError={(s) => {
              setWalletError(s)
              if (s) setError(null)
            }}
          />

          <button
            onClick={() => router.push("/")}
            className="mt-6 w-full px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Back to site
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AdminLoginPage() {
  const network = WalletAdapterNetwork.Mainnet
  const endpoint = useMemo(() => clusterApiUrl(network), [network])
  const wallets = useMemo(
    () => [new PhantomWalletAdapter(), new SolflareWalletAdapter()],
    []
  )

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect={false}>
        <AdminLoginContent />
      </WalletProvider>
    </ConnectionProvider>
  )
}
