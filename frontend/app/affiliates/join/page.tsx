"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle, ArrowRight, Share2, Wallet, DollarSign
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

export default function AffiliateJoinPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [payoutEmail, setPayoutEmail] = useState("");
  const [payoutMethod, setPayoutMethod] = useState("paypal");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [agreed, setAgreed] = useState(false);

  // Redirect to login if not authenticated
  if (!authLoading && !user) {
    if (typeof window !== "undefined") {
      sessionStorage.setItem("redirectAfterLogin", "/affiliates/join");
      router.push("/auth/login");
    }
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!agreed) {
      setError("Please agree to the affiliate terms to continue.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await api.post("/api/affiliates/register", {
        payout_email: payoutEmail || undefined,
        payout_method: payoutMethod,
      });

      // Redirect to dashboard on success
      router.push("/affiliates/dashboard");
    } catch (err: any) {
      console.error("Error registering as affiliate:", err);
      if (err.response?.status === 400) {
        setError("You are already registered as an affiliate.");
        setTimeout(() => router.push("/affiliates/dashboard"), 2000);
      } else {
        setError(err.response?.data?.detail || "Failed to register. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full" />
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
      <Header />

      <main className="flex-1 py-12">
        <div className="container mx-auto px-4 max-w-xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-8"
          >
            <div className="text-5xl mb-4">🦍</div>
            <h1 className="text-3xl font-black text-white mb-2">
              Join the Gorilla Squad
            </h1>
            <p className="text-gray-400">
              Start earning commissions on every referral.
            </p>
          </motion.div>

          {/* Benefits Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="p-6 rounded-xl bg-gradient-to-r from-amber-900/20 to-yellow-900/10 border border-amber-500/20 mb-8"
          >
            <h2 className="text-lg font-bold text-white mb-4">What You Get</h2>
            <div className="space-y-3">
              {[
                { icon: Share2, text: "Unique referral link to share" },
                { icon: DollarSign, text: "Up to 40% commission on all purchases" },
                  { icon: Wallet, text: "Monthly payouts via PayPal (min $25)" },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/20 rounded-lg">
                    <item.icon className="w-4 h-4 text-amber-400" />
                  </div>
                  <span className="text-gray-300">{item.text}</span>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Registration Form */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-xl bg-white/5 border border-white/10"
          >
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Payout Email (Optional) */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Payout Email (Optional)
                </label>
                <input
                  type="email"
                  value={payoutEmail}
                  onChange={(e) => setPayoutEmail(e.target.value)}
                  placeholder="your@email.com"
                  className="w-full px-4 py-3 bg-black/30 border border-white/10 rounded-lg text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                />
                <p className="text-xs text-gray-500 mt-1">
                  You can add this later in your dashboard settings.
                </p>
              </div>

              {/* Payout Method */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Preferred Payout Method
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: "paypal", label: "PayPal" },
                    { id: "bank", label: "Bank" },
                  ].map((method) => (
                    <button
                      key={method.id}
                      type="button"
                      onClick={() => setPayoutMethod(method.id)}
                      className={`px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                        payoutMethod === method.id
                          ? "bg-amber-500/20 border-amber-500/50 text-amber-400"
                          : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                      }`}
                    >
                      {method.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Terms Agreement */}
              <div>
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={agreed}
                    onChange={(e) => setAgreed(e.target.checked)}
                    className="mt-1 w-4 h-4 rounded border-gray-600 bg-black/30 text-amber-500 focus:ring-amber-500/50"
                  />
                  <span className="text-sm text-gray-400">
                    I agree to the{" "}
                    <a href="/terms" className="text-amber-400 hover:underline">
                      Terms of Service
                    </a>{" "}
                    and{" "}
                    <a href="/affiliates/terms" className="text-amber-400 hover:underline">
                      Affiliate Program Terms
                    </a>
                    . I understand that commissions are subject to a 30-day hold period and a $25 minimum payout threshold.
                  </span>
                </label>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full px-6 py-4 bg-gradient-to-r from-amber-500 to-yellow-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-amber-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="animate-spin w-5 h-5 border-2 border-black border-t-transparent rounded-full" />
                ) : (
                  <>
                    Become an Affiliate
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>
          </motion.div>

          {/* Already an affiliate? */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center text-gray-400 mt-6"
          >
            Already an affiliate?{" "}
            <a href="/affiliates/dashboard" className="text-amber-400 hover:underline">
              Go to Dashboard
            </a>
          </motion.p>
        </div>
      </main>

      <Footer />
    </div>
  );
}




