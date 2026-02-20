"use client"

import { useState, useEffect, useMemo } from "react"
import { CheckCircle, Loader2 } from "lucide-react"
import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react"
import { WalletAdapterNetwork } from "@solana/wallet-adapter-base"
import { PhantomWalletAdapter, SolflareWalletAdapter } from "@solana/wallet-adapter-wallets"
import { clusterApiUrl } from "@solana/web3.js"
import { useWallet } from "@solana/wallet-adapter-react"
import { api } from "@/lib/api"

export interface AdminWalletSectionProps {
  walletError: string | null
  setWalletError: (s: string | null) => void
}

function WalletBlockInner({ setWalletError }: AdminWalletSectionProps) {
  const { publicKey, connected, disconnect, wallets, select, connect } = useWallet()
  const [verifying, setVerifying] = useState(false)
  const [walletSuccess, setWalletSuccess] = useState(false)

  const phantomOrSolflare = useMemo(() => {
    const byName = new Map<string, (typeof wallets)[number]>()
    for (const w of wallets) {
      const name = w.adapter.name
      if ((name === "Phantom" || name === "Solflare") && !byName.has(name)) byName.set(name, w)
    }
    return Array.from(byName.values())
  }, [wallets])

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
      } catch (err: unknown) {
        if (!cancelled) {
          const msg = err && typeof err === "object" && "response" in err
            ? (err as { response?: { data?: { detail?: string } }; message?: string }).response?.data?.detail
              ?? (err as { message?: string }).message
            : "Wallet login failed"
          setWalletError(String(msg))
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

export default function AdminWalletSection(props: AdminWalletSectionProps) {
  const network = WalletAdapterNetwork.Mainnet
  const endpoint = useMemo(() => clusterApiUrl(network), [network])
  const wallets = useMemo(
    () => [new PhantomWalletAdapter(), new SolflareWalletAdapter()],
    []
  )
  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect={false}>
        <WalletBlockInner {...props} />
      </WalletProvider>
    </ConnectionProvider>
  )
}
