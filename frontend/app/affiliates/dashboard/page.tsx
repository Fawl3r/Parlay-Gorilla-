"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Users, DollarSign, TrendingUp, Copy, ExternalLink,
  BarChart2, Clock, CheckCircle, XCircle, AlertCircle,
  ChevronRight, Wallet, ArrowUpRight, RefreshCcw, FileText
} from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { TaxForm } from "@/components/TaxForm";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

interface AffiliateAccount {
  id: string;
  referral_code: string;
  referral_url: string;
  tier: string;
  commission_rates: {
    subscription_first: number;
    subscription_recurring: number;
    credits: number;
  };
  stats: {
    total_clicks: number;
    total_referrals: number;
    total_referred_revenue: number;
    total_commission_earned: number;
    total_commission_paid: number;
    pending_commission: number;
  };
  payout_email: string | null;
  payout_method: string | null;
  created_at: string;
}

interface AffiliateStats {
  total_clicks: number;
  total_referrals: number;
  total_revenue: number;
  total_commission_earned: number;
  total_commission_paid: number;
  pending_commission: number;
  conversion_rate: number;
  last_30_days: {
    clicks: number;
    referrals: number;
    revenue: number;
  };
}

interface Referral {
  id: string;
  username: string | null;
  email: string;
  created_at: string;
  has_subscription: boolean;
}

interface Commission {
  id: string;
  sale_type: string;
  base_amount: number;
  amount: number;
  status: string;
  days_until_ready: number;
  created_at: string;
  subscription_plan: string | null;
  credit_pack_id: string | null;
}

const STATUS_COLORS: Record<string, { bg: string; text: string; icon: typeof CheckCircle }> = {
  pending: { bg: "bg-yellow-500/20", text: "text-yellow-400", icon: Clock },
  ready: { bg: "bg-emerald-500/20", text: "text-emerald-400", icon: CheckCircle },
  paid: { bg: "bg-blue-500/20", text: "text-blue-400", icon: CheckCircle },
  cancelled: { bg: "bg-red-500/20", text: "text-red-400", icon: XCircle },
};

const TIER_COLORS: Record<string, string> = {
  rookie: "#9ca3af",
  pro: "#3b82f6",
  all_star: "#8b5cf6",
  hall_of_fame: "#f59e0b",
};

export default function AffiliateDashboardPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [affiliate, setAffiliate] = useState<AffiliateAccount | null>(null);
  const [stats, setStats] = useState<AffiliateStats | null>(null);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [commissions, setCommissions] = useState<Commission[]>([]);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "referrals" | "commissions">("overview");
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
                label: "Total Earned",
                value: `$${(stats?.total_commission_earned || 0).toFixed(2)}`,
                icon: DollarSign,
                color: "text-emerald-400",
              },
              {
                label: "Pending",
                value: `$${(stats?.pending_commission || 0).toFixed(2)}`,
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

          {/* Tabs */}
          <div className="flex gap-2 mb-6">
            {[
              { id: "overview", label: "Overview" },
              { id: "referrals", label: "Referrals" },
              { id: "commissions", label: "Commissions" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab.id
                    ? "bg-amber-500 text-black"
                    : "bg-white/5 text-gray-400 hover:text-white"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Recent Referrals */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Recent Referrals</h3>
                  <button
                    onClick={() => setActiveTab("referrals")}
                    className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  >
                    View All <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {referrals.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">
                    No referrals yet. Share your link to start earning!
                  </p>
                ) : (
                  <div className="space-y-3">
                    {referrals.slice(0, 5).map((referral) => (
                      <div
                        key={referral.id}
                        className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                      >
                        <div>
                          <div className="font-medium text-white">
                            {referral.username || "Anonymous"}
                          </div>
                          <div className="text-xs text-gray-400">{referral.email}</div>
                        </div>
                        <div className="text-right">
                          {referral.has_subscription && (
                            <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
                              Subscribed
                            </span>
                          )}
                          <div className="text-xs text-gray-400 mt-1">
                            {new Date(referral.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>

              {/* Recent Commissions */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                className="p-6 rounded-xl bg-white/5 border border-white/10"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Recent Commissions</h3>
                  <button
                    onClick={() => setActiveTab("commissions")}
                    className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
                  >
                    View All <ChevronRight className="w-4 h-4" />
                  </button>
                </div>

                {commissions.length === 0 ? (
                  <p className="text-gray-400 text-center py-8">
                    No commissions yet. Keep sharing your link!
                  </p>
                ) : (
                  <div className="space-y-3">
                    {commissions.slice(0, 5).map((commission) => {
                      const statusConfig = STATUS_COLORS[commission.status] || STATUS_COLORS.pending;
                      const StatusIcon = statusConfig.icon;

                      return (
                        <div
                          key={commission.id}
                          className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${statusConfig.bg}`}>
                              <StatusIcon className={`w-4 h-4 ${statusConfig.text}`} />
                            </div>
                            <div>
                              <div className="font-medium text-white">
                                ${commission.amount.toFixed(2)}
                              </div>
                              <div className="text-xs text-gray-400 capitalize">
                                {commission.sale_type.replace("_", " ")}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className={`text-xs ${statusConfig.text}`}>
                              {commission.status === "pending" && commission.days_until_ready > 0
                                ? `${commission.days_until_ready}d until ready`
                                : commission.status}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </motion.div>
            </div>
          )}

          {activeTab === "referrals" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 rounded-xl bg-white/5 border border-white/10"
            >
              <h3 className="text-lg font-bold text-white mb-4">All Referrals</h3>

              {referrals.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                  No referrals yet. Share your link to start earning!
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-gray-400 border-b border-white/10">
                        <th className="pb-3 pr-4">User</th>
                        <th className="pb-3 pr-4">Status</th>
                        <th className="pb-3">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {referrals.map((referral) => (
                        <tr key={referral.id} className="border-b border-white/5">
                          <td className="py-3 pr-4">
                            <div className="font-medium text-white">
                              {referral.username || "Anonymous"}
                            </div>
                            <div className="text-xs text-gray-400">{referral.email}</div>
                          </td>
                          <td className="py-3 pr-4">
                            {referral.has_subscription ? (
                              <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
                                Subscribed
                              </span>
                            ) : (
                              <span className="px-2 py-1 bg-gray-500/20 text-gray-400 text-xs rounded-full">
                                Free
                              </span>
                            )}
                          </td>
                          <td className="py-3 text-gray-400 text-sm">
                            {new Date(referral.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </motion.div>
          )}

          {activeTab === "commissions" && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-6 rounded-xl bg-white/5 border border-white/10"
            >
              <h3 className="text-lg font-bold text-white mb-4">Commission History</h3>

              {commissions.length === 0 ? (
                <p className="text-gray-400 text-center py-8">
                  No commissions yet. Keep sharing your link!
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left text-sm text-gray-400 border-b border-white/10">
                        <th className="pb-3 pr-4">Type</th>
                        <th className="pb-3 pr-4">Amount</th>
                        <th className="pb-3 pr-4">Status</th>
                        <th className="pb-3">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {commissions.map((commission) => {
                        const statusConfig = STATUS_COLORS[commission.status] || STATUS_COLORS.pending;

                        return (
                          <tr key={commission.id} className="border-b border-white/5">
                            <td className="py-3 pr-4">
                              <div className="font-medium text-white capitalize">
                                {commission.sale_type.replace("_", " ")}
                              </div>
                              <div className="text-xs text-gray-400">
                                ${commission.base_amount.toFixed(2)} sale
                              </div>
                            </td>
                            <td className="py-3 pr-4">
                              <span className="font-bold text-emerald-400">
                                ${commission.amount.toFixed(2)}
                              </span>
                            </td>
                            <td className="py-3 pr-4">
                              <span
                                className={`px-2 py-1 rounded-full text-xs ${statusConfig.bg} ${statusConfig.text}`}
                              >
                                {commission.status}
                              </span>
                              {commission.status === "pending" && commission.days_until_ready > 0 && (
                                <div className="text-xs text-gray-400 mt-1">
                                  {commission.days_until_ready} days until ready
                                </div>
                              )}
                            </td>
                            <td className="py-3 text-gray-400 text-sm">
                              {new Date(commission.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </motion.div>
          )}
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

