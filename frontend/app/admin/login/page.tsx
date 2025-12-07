"use client";

import { useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { ConnectionProvider, WalletProvider } from '@solana/wallet-adapter-react';
import { WalletAdapterNetwork } from '@solana/wallet-adapter-base';
import { WalletModalProvider } from '@solana/wallet-adapter-react-ui';
import { PhantomWalletAdapter, SolflareWalletAdapter } from '@solana/wallet-adapter-wallets';
import { clusterApiUrl } from '@solana/web3.js';
import { useWallet } from '@solana/wallet-adapter-react';
import { WalletMultiButton } from '@solana/wallet-adapter-react-ui';
import { api } from '@/lib/api';
import { Shield, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

// Import wallet adapter CSS
import '@solana/wallet-adapter-react-ui/styles.css';

// Admin wallet address
const ADMIN_WALLET_ADDRESS = '4E58m1qpnxbFRoDZ8kk9zu3GT6YLrPtPk65u8Xa2ZgBU';

function AdminLoginForm() {
  const { publicKey, connected, connecting, disconnect } = useWallet();
  const router = useRouter();
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (connected && publicKey) {
      handleVerifyWallet();
    }
  }, [connected, publicKey]);

  async function handleVerifyWallet() {
    if (!publicKey) return;

    const walletAddress = publicKey.toBase58();
    
    // Check if wallet matches admin address
    if (walletAddress !== ADMIN_WALLET_ADDRESS) {
      setError(`Access denied. This wallet (${walletAddress.substring(0, 8)}...) is not authorized.`);
      disconnect();
      return;
    }

    try {
      setVerifying(true);
      setError(null);

      // Sign a message to prove wallet ownership
      const message = `Parlay Gorilla Admin Login\nTimestamp: ${Date.now()}`;
      
      // Call the admin wallet login API
      const response = await api.adminWalletLogin(walletAddress, message);

      if (response.success) {
        setSuccess(true);
        // Store admin session token
        if (response.token) {
          localStorage.setItem('admin_token', response.token);
        }
        // Redirect to admin dashboard with a full page reload to refresh auth context
        setTimeout(() => {
          window.location.href = '/admin';
        }, 1500);
      } else {
        setError(response.detail || 'Authentication failed');
        disconnect();
      }
    } catch (err: any) {
      console.error('Admin login error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to verify wallet');
      disconnect();
    } finally {
      setVerifying(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-emerald-500/20 mb-4">
              <Shield className="w-8 h-8 text-emerald-400" />
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Admin Login</h1>
            <p className="text-gray-400 text-sm">
              Connect your Solana wallet to access the admin dashboard
            </p>
          </div>

          {/* Status Messages */}
          {error && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-400 text-sm font-medium">Access Denied</p>
                <p className="text-red-300 text-xs mt-1">{error}</p>
              </div>
            </div>
          )}

          {success && (
            <div className="mb-6 p-4 bg-emerald-900/20 border border-emerald-500/30 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-emerald-400 text-sm font-medium">Authentication Successful</p>
                <p className="text-emerald-300 text-xs mt-1">Redirecting to admin dashboard...</p>
              </div>
            </div>
          )}

          {/* Wallet Connection Status */}
          {connected && publicKey && (
            <div className="mb-6 p-4 bg-[#0a0a0f] rounded-lg border border-emerald-900/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Connected Wallet:</span>
                <span className="text-emerald-400 font-mono text-xs">
                  {publicKey.toBase58().substring(0, 8)}...{publicKey.toBase58().slice(-6)}
                </span>
              </div>
              {verifying && (
                <div className="flex items-center gap-2 mt-3">
                  <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />
                  <span className="text-emerald-400 text-sm">Verifying wallet...</span>
                </div>
              )}
            </div>
          )}

          {/* Wallet Connect Button */}
          {!connected && !verifying && (
            <div className="space-y-4">
              <p className="text-gray-400 text-sm text-center">
                Click the button below to connect your Solana wallet
              </p>
              <div className="flex justify-center">
                <WalletMultiButton className="!bg-emerald-500 hover:!bg-emerald-600 !text-white !rounded-lg !px-6 !py-3 !font-medium" />
              </div>
            </div>
          )}

          {/* Disconnect Button */}
          {connected && !verifying && !success && (
            <button
              onClick={disconnect}
              className="w-full px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Disconnect Wallet
            </button>
          )}

          {/* Info Box */}
          <div className="mt-6 p-4 bg-[#0a0a0f] rounded-lg border border-gray-800">
            <p className="text-xs text-gray-500 text-center">
              Only authorized Solana wallets can access the admin dashboard
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminLoginPage() {
  // Use mainnet for production, devnet for testing
  const network = WalletAdapterNetwork.Mainnet;
  const endpoint = useMemo(() => clusterApiUrl(network), [network]);

  const wallets = useMemo(
    () => [
      new PhantomWalletAdapter(),
      new SolflareWalletAdapter(),
    ],
    []
  );

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={wallets} autoConnect={false}>
        <WalletModalProvider>
          <AdminLoginForm />
        </WalletModalProvider>
      </WalletProvider>
    </ConnectionProvider>
  );
}

