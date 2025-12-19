"use client"

import { motion } from "framer-motion"
import { ChevronRight } from "lucide-react"

import type { Commission, DashboardTabId, Referral } from "@/app/affiliates/dashboard/_lib/types"
import { STATUS_COLORS } from "@/app/affiliates/dashboard/_lib/constants"

type Props = {
  activeTab: DashboardTabId
  onChangeTab: (tab: DashboardTabId) => void
  referrals: Referral[]
  commissions: Commission[]
}

export function DashboardTabsSection({ activeTab, onChangeTab, referrals, commissions }: Props) {
  return (
    <>
      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { id: "overview", label: "Overview" },
          { id: "referrals", label: "Referrals" },
          { id: "commissions", label: "Commissions" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => onChangeTab(tab.id as DashboardTabId)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              activeTab === tab.id ? "bg-amber-500 text-black" : "bg-white/5 text-gray-400 hover:text-white"
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
                onClick={() => onChangeTab("referrals")}
                className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
              >
                View All <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {referrals.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No referrals yet. Share your link to start earning!</p>
            ) : (
              <div className="space-y-3">
                {referrals.slice(0, 5).map((referral) => (
                  <div
                    key={referral.id}
                    className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                  >
                    <div>
                      <div className="font-medium text-white">{referral.username || "Anonymous"}</div>
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
                onClick={() => onChangeTab("commissions")}
                className="text-sm text-amber-400 hover:text-amber-300 flex items-center gap-1"
              >
                View All <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            {commissions.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No commissions yet. Keep sharing your link!</p>
            ) : (
              <div className="space-y-3">
                {commissions.slice(0, 5).map((commission) => {
                  const statusConfig = STATUS_COLORS[commission.status] || STATUS_COLORS.pending
                  const StatusIcon = statusConfig.icon

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
                          <div className="font-medium text-white">${commission.amount.toFixed(2)}</div>
                          <div className="text-xs text-gray-400 capitalize">
                            {commission.sale_type.replace("_", " ")} •{" "}
                            {commission.settlement_provider === "lemonsqueezy"
                              ? "Card payout (LemonSqueezy)"
                              : "Crypto payout"}
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
                  )
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
            <p className="text-gray-400 text-center py-8">No referrals yet. Share your link to start earning!</p>
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
                        <div className="font-medium text-white">{referral.username || "Anonymous"}</div>
                        <div className="text-xs text-gray-400">{referral.email}</div>
                      </td>
                      <td className="py-3 pr-4">
                        {referral.has_subscription ? (
                          <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
                            Subscribed
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-500/20 text-gray-400 text-xs rounded-full">Free</span>
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
            <p className="text-gray-400 text-center py-8">No commissions yet. Keep sharing your link!</p>
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
                    const statusConfig = STATUS_COLORS[commission.status] || STATUS_COLORS.pending

                    return (
                      <tr key={commission.id} className="border-b border-white/5">
                        <td className="py-3 pr-4">
                          <div className="font-medium text-white capitalize">{commission.sale_type.replace("_", " ")}</div>
                          <div className="text-xs text-gray-400">${commission.base_amount.toFixed(2)} sale</div>
                          <div className="text-xs text-gray-500 mt-0.5">
                            {commission.settlement_provider === "lemonsqueezy"
                              ? "Paid via LemonSqueezy (card)"
                              : "Paid by Parlay Gorilla (crypto)"}
                          </div>
                        </td>
                        <td className="py-3 pr-4">
                          <span className="font-bold text-emerald-400">${commission.amount.toFixed(2)}</span>
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`px-2 py-1 rounded-full text-xs ${statusConfig.bg} ${statusConfig.text}`}>
                            {commission.status}
                          </span>
                          {commission.status === "pending" && commission.days_until_ready > 0 && (
                            <div className="text-xs text-gray-400 mt-1">{commission.days_until_ready} days until ready</div>
                          )}
                        </td>
                        <td className="py-3 text-gray-400 text-sm">
                          {new Date(commission.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </motion.div>
      )}
    </>
  )
}


