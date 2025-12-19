"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Users,
  DollarSign,
  Copy,
  BarChart2,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCcw,
  FileText,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { TaxForm } from "@/components/TaxForm";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

import { DashboardTabsSection } from "@/app/affiliates/dashboard/_components/DashboardTabsSection";
import { TIER_COLORS } from "@/app/affiliates/dashboard/_lib/constants";
import type {
  AffiliateAccount,
  AffiliateStats,
  Commission,
  DashboardTabId,
  Referral,
} from "@/app/affiliates/dashboard/_lib/types";

export default function AffiliateDashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [affiliate, setAffiliate] = useState<AffiliateAccount | null>(null);
  const [stats, setStats] = useState<AffiliateStats | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [commissions, setCommissions] = useState<Commission[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<DashboardTabId>("overview");
  const [showTaxForm, setShowTaxForm] = useState(false);
  const [taxStatus, setTaxStatus] = useState<any>(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);

      // Load affiliate account
      const accountRes = await api.get("/api/affiliates/me");
      setAffiliate(accountRes.data);

      // Load stats
      const statsRes = await api.get("/api/affiliates/me/stats");
      setStats(statsRes.data);

      // Load referrals
      const referralsRes = await api.get("/api/affiliates/me/referrals?limit=10");
      setReferrals(referralsRes.data.referrals || []);

      // Load commissions
      const commissionsRes = await api.get("/api/affiliates/me/commissions?limit=10");
      setCommissions(commissionsRes.data.commissions || []);

      // Load tax status
      try {
        const taxRes = await api.getTaxFormStatus();
        setTaxStatus(taxRes);
      } catch (err) {
        console.error("Failed to load tax status:", err);
      }
    } catch (err: any) {
      console.error("Error loading dashboard:", err);
      if (err.response?.status === 404) {
        // Not an affiliate, redirect to join page
        router.push("/affiliates/join");
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/auth/login?redirect=/affiliates/dashboard");
      return;
    }

    if (user) {
      loadDashboardData();
    }
  }, [user, authLoading, router, loadDashboardData]);

  const copyReferralLink = () => {
    if (affiliate?.referral_url) {
      navigator.clipboard.writeText(affiliate.referral_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (authLoading || loading) {
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

  if (!affiliate) {
    return null;
  }

  const tierColor = TIER_COLORS[affiliate.tier] || "#9ca3af";
  const MIN_PAYOUT_USD = 25;

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
      <Header />

      <main className="flex-1 py-8">
        <div className="container mx-auto px-4 max-w-6xl">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl md:text-3xl font-black text-white mb-2">
                Affiliate Dashboard
              </h1>
              <div className="flex items-center gap-3">
                <span
                  className="px-3 py-1 rounded-full text-sm font-medium"
                  style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
                >
                  {affiliate.tier.replace("_", " ").toUpperCase()}
                </span>
                <span className="text-gray-400 text-sm">
                  Member since {new Date(affiliate.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            <button
              onClick={loadDashboardData}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <RefreshCcw className="w-4 h-4" />
              Refresh
            </button>
          </div>

          {/* Referral Link Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-6 rounded-xl bg-gradient-to-r from-amber-900/20 to-yellow-900/10 border border-amber-500/20 mb-8"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-white mb-1">Your Referral Link</h2>
                <p className="text-sm text-gray-400">Share this link to earn commissions</p>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1 md:flex-none px-4 py-2 bg-black/30 rounded-lg text-amber-400 font-mono text-sm truncate max-w-xs">
                  {affiliate.referral_url}
                </div>
                <button
                  onClick={copyReferralLink}
                  className={`px-4 py-2 rounded-lg font-medium flex items-center gap-2 transition-all ${
                    copied
                      ? "bg-emerald-500 text-white"
                      : "bg-amber-500 text-black hover:bg-amber-400"
                  }`}
                >
                  {copied ? (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>

          {/* Tax Status Card */}
          {taxStatus && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-6 rounded-xl border mb-8 ${
                taxStatus.requires_form && !taxStatus.form_complete
                  ? "bg-yellow-900/10 border-yellow-500/30"
                  : taxStatus.form_complete
                  ? "bg-emerald-900/10 border-emerald-500/30"
                  : "bg-white/5 border-white/10"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  {taxStatus.requires_form && !taxStatus.form_complete ? (
                    <AlertCircle className="w-6 h-6 text-yellow-400 mt-0.5" />
                  ) : taxStatus.form_complete ? (
                    <CheckCircle className="w-6 h-6 text-emerald-400 mt-0.5" />
                  ) : (
                    <FileText className="w-6 h-6 text-gray-400 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-1">Tax Information</h3>
                    {taxStatus.requires_form && !taxStatus.form_complete ? (
                      <>
                        <p className="text-sm text-yellow-300 mb-3">
                          You've earned ${taxStatus.earnings.toFixed(2)} in commissions. 
                          A tax form is required for earnings over ${taxStatus.threshold.toFixed(2)}.
                        </p>
                        <button
                          onClick={() => setShowTaxForm(true)}
                          className="px-4 py-2 bg-yellow-500 text-black font-semibold rounded-lg hover:bg-yellow-400 transition-colors flex items-center gap-2"
                        >
                          <FileText className="w-4 h-4" />
                          Submit Tax Form
                        </button>
                      </>
                    ) : taxStatus.form_complete ? (
                      <p className="text-sm text-emerald-300">
                        Your {taxStatus.form_type?.toUpperCase()} tax form has been verified.
                      </p>
                    ) : taxStatus.form_status === "submitted" ? (
                      <p className="text-sm text-gray-300">
                        Your tax form is under review. We'll notify you once it's verified.
                      </p>
                    ) : (
                      <p className="text-sm text-gray-400">
                        Tax form will be required when you reach ${taxStatus.threshold.toFixed(2)} in earnings.
                        Current earnings: ${taxStatus.earnings.toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
                {taxStatus.requires_form && !taxStatus.form_complete && (
                  <button
                    onClick={() => setShowTaxForm(true)}
                    className="px-4 py-2 bg-white/5 border border-white/10 text-white rounded-lg hover:bg-white/10 transition-colors"
                  >
                    Update
                  </button>
                )}
              </div>
            </motion.div>
          )}

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              {
                label: "Total Clicks",
                value: stats?.total_clicks || 0,
                icon: BarChart2,
                color: "text-blue-400",
              },
              {
                label: "Referrals",
                value: stats?.total_referrals || 0,
                icon: Users,
                color: "text-purple-400",
              },
              {
                label: "Crypto (Payable)",
                value: `$${(stats?.settlement_breakdown?.internal?.pending || 0).toFixed(2)}`,
                icon: DollarSign,
                color: "text-emerald-400",
              },
              {
                label: "Card (LemonSqueezy)",
                value: `$${(stats?.settlement_breakdown?.lemonsqueezy?.earned || 0).toFixed(2)}`,
                icon: Clock,
                color: "text-amber-400",
              },
            ].map((stat, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="p-4 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color}`} />
                  <span className="text-xs text-gray-400">{stat.label}</span>
                </div>
                <div className="text-2xl font-bold text-white">{stat.value}</div>
              </motion.div>
            ))}
          </div>

          {/* Payout Minimum */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="p-6 rounded-xl bg-white/5 border border-white/10 mb-8"
          >
            <div className="flex items-start gap-3">
              <DollarSign className="w-6 h-6 text-emerald-400 mt-0.5" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-white mb-1">Minimum payout</h3>
                <p className="text-sm text-gray-400">
                  Payouts are processed once you have{" "}
                  <span className="text-white font-semibold">${MIN_PAYOUT_USD}</span> or more in payout-ready
                  commissions (after the hold period).
                </p>
              </div>
            </div>
          </motion.div>

          {/* Commission Rates */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="p-6 rounded-xl bg-white/5 border border-white/10 mb-8"
          >
            <h3 className="text-lg font-bold text-white mb-4">Your Commission Rates</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-black text-emerald-400">
                  {(affiliate.commission_rates.subscription_first * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-400">First Subscription</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-black text-emerald-400">
                  {(affiliate.commission_rates.subscription_recurring * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-400">Recurring</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-black text-amber-400">
                  {(affiliate.commission_rates.credits * 100).toFixed(0)}%
                </div>
                <div className="text-sm text-gray-400">Credit Packs</div>
              </div>
            </div>
          </motion.div>
          <DashboardTabsSection
            activeTab={activeTab}
            onChangeTab={setActiveTab}
            referrals={referrals}
            commissions={commissions}
          />
        </div>
      </main>

      <Footer />
      {showTaxForm && (
        <TaxForm
          onClose={() => setShowTaxForm(false)}
          onSuccess={() => {
            loadDashboardData();
            setShowTaxForm(false);
          }}
        />
      )}
    </div>
  );
}

