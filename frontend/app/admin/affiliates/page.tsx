"use client";

import { useEffect, useMemo, useState } from "react";
import { adminApi, AffiliateListItem } from "@/lib/admin-api";
import { RefreshCcw, Search, Filter, DollarSign, Users, MousePointerClick } from "lucide-react";

const TIME_RANGES = [
  { value: "24h", label: "Last 24h" },
  { value: "7d", label: "Last 7d" },
  { value: "30d", label: "Last 30d" },
  { value: "90d", label: "Last 90d" },
];

const SORTS = [
  { value: "revenue_desc", label: "Revenue ↓" },
  { value: "revenue_asc", label: "Revenue ↑" },
  { value: "commission_desc", label: "Commission ↓" },
  { value: "commission_asc", label: "Commission ↑" },
  { value: "created_desc", label: "Newest" },
  { value: "created_asc", label: "Oldest" },
];

export default function AdminAffiliatesPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<AffiliateListItem[]>([]);
  const [timeRange, setTimeRange] = useState("30d");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("revenue_desc");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(25);
  const [total, setTotal] = useState(0);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await adminApi.getAffiliates({
        timeRange,
        page,
        pageSize,
        search: search.trim() || undefined,
        sort,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err: any) {
      console.error("Failed to load affiliates", err);
      setError(err?.message || "Failed to load affiliates");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeRange, sort, page]);

  const handleSearch = () => {
    setPage(1);
    fetchData();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Affiliates</h1>
          <p className="text-gray-400 mt-1">Performance by affiliate (clicks, referrals, revenue, commissions)</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <select
            className="bg-[#0a0a0f] border border-emerald-900/40 rounded-lg px-3 py-2 text-sm text-white"
            value={timeRange}
            onChange={(e) => {
              setPage(1);
              setTimeRange(e.target.value);
            }}
          >
            {TIME_RANGES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
          <select
            className="bg-[#0a0a0f] border border-emerald-900/40 rounded-lg px-3 py-2 text-sm text-white"
            value={sort}
            onChange={(e) => {
              setPage(1);
              setSort(e.target.value);
            }}
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
          <button
            onClick={fetchData}
            className="inline-flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-200 hover:text-white hover:bg-white/10 transition-colors text-sm"
          >
            <RefreshCcw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Search bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-3" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search email or referral code..."
            className="w-full bg-[#0a0a0f] border border-emerald-900/30 rounded-lg pl-10 pr-3 py-2 text-sm text-white placeholder:text-gray-600"
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSearch();
            }}
          />
        </div>
        <button
            onClick={handleSearch}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-semibold hover:bg-emerald-500 transition-colors"
          >
            <Filter className="w-4 h-4" />
            Apply
          </button>
      </div>

      {error && (
        <div className="p-4 rounded-lg border border-red-500/30 bg-red-900/20 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-gray-400 border-b border-emerald-900/30">
                <th className="px-4 py-3">Affiliate</th>
                <th className="px-4 py-3">Tier</th>
                <th className="px-4 py-3">Clicks</th>
                <th className="px-4 py-3">Referrals</th>
                <th className="px-4 py-3">Conv%</th>
                <th className="px-4 py-3">Revenue</th>
                <th className="px-4 py-3">Commission (E/P)</th>
                <th className="px-4 py-3">Pending</th>
                <th className="px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="px-4 py-6 text-center text-emerald-400">
                    Loading affiliates...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-6 text-center text-gray-500">
                    No affiliates found for this range.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr key={item.id} className="border-b border-emerald-900/20 hover:bg-emerald-900/5 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-1">
                        <div className="text-white font-semibold flex items-center gap-2">
                          {item.email || item.username || "Unknown"}
                          {item.is_active ? (
                            <span className="text-emerald-400 text-xs px-2 py-0.5 rounded-full bg-emerald-900/30">
                              Active
                            </span>
                          ) : (
                            <span className="text-gray-400 text-xs px-2 py-0.5 rounded-full bg-gray-800/60">
                              Inactive
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-gray-500">
                          Code: <span className="text-emerald-300 font-mono">{item.referral_code}</span>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-emerald-300 text-sm font-semibold">
                      {item.tier.replace("_", " ").toUpperCase()}
                    </td>
                    <td className="px-4 py-3 text-gray-200">{item.stats.clicks.toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-200">{item.stats.referrals.toLocaleString()}</td>
                    <td className="px-4 py-3 text-gray-200">{item.stats.conversion_rate.toFixed(1)}%</td>
                    <td className="px-4 py-3 text-emerald-200 font-semibold">
                      ${item.stats.revenue.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-gray-200">
                      <div className="flex flex-col text-sm">
                        <span className="text-emerald-200 font-semibold">
                          Earned ${item.stats.commission_earned.toFixed(2)}
                        </span>
                        <span className="text-blue-200">
                          Paid ${item.stats.commission_paid.toFixed(2)}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-amber-200 font-semibold">
                      ${item.stats.pending_commission.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-sm">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-emerald-900/30 text-sm text-gray-300">
          <div>
            Page {page} / {totalPages} • {total.toLocaleString()} affiliates
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg border border-emerald-900/30 bg-white/5 disabled:opacity-40"
            >
              Prev
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg border border-emerald-900/30 bg-white/5 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Quick stats row */}
      {!loading && items.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="p-4 rounded-lg bg-emerald-900/10 border border-emerald-900/20">
            <div className="flex items-center gap-2 text-emerald-300 text-sm font-semibold">
              <MousePointerClick className="w-4 h-4" /> Clicks
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              {items.reduce((sum, i) => sum + i.stats.clicks, 0).toLocaleString()}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-emerald-900/10 border border-emerald-900/20">
            <div className="flex items-center gap-2 text-emerald-300 text-sm font-semibold">
              <Users className="w-4 h-4" /> Referrals
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              {items.reduce((sum, i) => sum + i.stats.referrals, 0).toLocaleString()}
            </div>
          </div>
          <div className="p-4 rounded-lg bg-emerald-900/10 border border-emerald-900/20">
            <div className="flex items-center gap-2 text-emerald-300 text-sm font-semibold">
              <DollarSign className="w-4 h-4" /> Commission Earned
            </div>
            <div className="mt-2 text-2xl font-bold text-white">
              $
              {items
                .reduce((sum, i) => sum + i.stats.commission_earned, 0)
                .toFixed(2)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


