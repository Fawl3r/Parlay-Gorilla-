"use client";

import { useEffect, useState } from 'react';
import { adminApi, RevenueMetrics, PaymentRecord } from '@/lib/admin-api';
import { MetricCard } from '../components/MetricCard';
import { AreaChart, PieChart, BarChart } from '../components/charts';
import {
  DollarSign,
  CreditCard,
  Users,
  TrendingUp,
  TrendingDown,
  Percent,
  RefreshCcw,
} from 'lucide-react';

export default function AdminRevenuePage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<RevenueMetrics | null>(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const data = await adminApi.getRevenueMetrics(timeRange);
        setMetrics(data);
      } catch (err: any) {
        console.error('Failed to fetch revenue metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [timeRange]);

  // Transform revenue by plan for pie chart
  const planDistribution = Object.entries(metrics?.revenue_by_plan || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
  }));

  // Transform revenue over time for area chart
  const revenueTimeline = metrics?.revenue_over_time?.map(item => ({
    date: item.date,
    value: item.amount,
  })) || [];

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-xl p-6 text-center">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Revenue Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Payment and subscription analytics
          </p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
        >
          <option value="24h">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
        </select>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Revenue"
          value={`$${metrics?.total_revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}`}
          icon={DollarSign}
          loading={loading}
        />
        <MetricCard
          title="Active Subs"
          value={metrics?.active_subscriptions?.toLocaleString() || '0'}
          icon={Users}
          loading={loading}
        />
        <MetricCard
          title="New Subs"
          value={metrics?.new_subscriptions?.toLocaleString() || '0'}
          icon={TrendingUp}
          loading={loading}
        />
        <MetricCard
          title="Churned"
          value={metrics?.churned_subscriptions?.toLocaleString() || '0'}
          icon={TrendingDown}
          loading={loading}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${metrics?.conversion_rate?.toFixed(1) || '0'}%`}
          icon={Percent}
          loading={loading}
        />
        <MetricCard
          title="Total Payments"
          value={metrics?.recent_payments?.length?.toString() || '0'}
          icon={CreditCard}
          loading={loading}
        />
      </div>

      {/* Revenue trend chart */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Revenue Trend</h3>
        {loading ? (
          <div className="h-[300px] flex items-center justify-center">
            <div className="text-emerald-400 animate-pulse">Loading chart...</div>
          </div>
        ) : revenueTimeline.length > 0 ? (
          <AreaChart
            data={revenueTimeline}
            dataKey="value"
            xAxisKey="date"
            color="#10b981"
            height={300}
            formatValue={(v) => `$${v.toLocaleString()}`}
          />
        ) : (
          <div className="h-[300px] flex items-center justify-center text-gray-500">
            No revenue data available for this period
          </div>
        )}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue by plan */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Revenue by Plan</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : planDistribution.length > 0 ? (
            <PieChart
              data={planDistribution}
              height={300}
              colors={['#10b981', '#f59e0b', '#8b5cf6']}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No plan revenue data available
            </div>
          )}
        </div>

        {/* Subscription metrics */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Subscription Overview</h3>
          {loading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                  <div className="w-32 h-4 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              <div className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                <span className="text-gray-300">Active Subscriptions</span>
                <span className="text-emerald-400 font-medium">{metrics?.active_subscriptions || 0}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                <span className="text-gray-300">New This Period</span>
                <span className="text-cyan-400 font-medium">{metrics?.new_subscriptions || 0}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                <span className="text-gray-300">Churned</span>
                <span className="text-red-400 font-medium">{metrics?.churned_subscriptions || 0}</span>
              </div>
              <div className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                <span className="text-gray-300">Net Growth</span>
                <span className={`font-medium ${
                  (metrics?.new_subscriptions || 0) - (metrics?.churned_subscriptions || 0) >= 0 
                    ? 'text-emerald-400' 
                    : 'text-red-400'
                }`}>
                  {((metrics?.new_subscriptions || 0) - (metrics?.churned_subscriptions || 0)).toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between items-center py-3">
                <span className="text-gray-300">Conversion Rate</span>
                <span className="text-purple-400 font-medium">{metrics?.conversion_rate?.toFixed(2) || 0}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Recent payments table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Payments</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-emerald-900/20">
                <th className="text-left py-3 px-4 text-gray-400 text-sm">User ID</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Amount</th>
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Plan</th>
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Provider</th>
                <th className="text-center py-3 px-4 text-gray-400 text-sm">Status</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="py-3 px-4"><div className="w-24 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-16 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                    <td className="py-3 px-4"><div className="w-16 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4"><div className="w-20 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-center"><div className="w-16 h-4 bg-emerald-900/20 rounded mx-auto" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-24 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                  </tr>
                ))
              ) : metrics?.recent_payments && metrics.recent_payments.length > 0 ? (
                metrics.recent_payments.map((payment) => (
                  <tr key={payment.id} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                    <td className="py-3 px-4 text-gray-400 font-mono text-sm">
                      {payment.user_id.substring(0, 8)}...
                    </td>
                    <td className="py-3 px-4 text-right text-emerald-400 font-medium">
                      ${payment.amount.toFixed(2)} {payment.currency}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        payment.plan === 'elite' ? 'bg-amber-500/20 text-amber-400' :
                        payment.plan === 'standard' ? 'bg-emerald-500/20 text-emerald-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {payment.plan}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-400 capitalize">
                      {payment.provider.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        payment.status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' :
                        payment.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                        payment.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-gray-500/20 text-gray-400'
                      }`}>
                        {payment.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-gray-500 text-sm">
                      {new Date(payment.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No payments recorded yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

