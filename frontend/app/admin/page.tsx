"use client";

import { useEffect, useState } from 'react';
import { adminApi, OverviewMetrics, UserMetrics, TemplateMetrics } from '@/lib/admin-api';
import { MetricCard } from './components/MetricCard';
import { AreaChart, BarChart } from './components/charts';
import {
  Users,
  Activity,
  Ticket,
  TrendingUp,
  DollarSign,
  Server,
  LayoutTemplate,
} from 'lucide-react';

const TEMPLATE_IDS = ['safer_2', 'solid_3', 'longshot_4'] as const;
const TEMPLATE_LABELS: Record<string, string> = {
  safer_2: 'Safer 2-Pick',
  solid_3: 'Solid 3-Pick',
  longshot_4: 'Longshot 4-Pick',
};

export default function AdminOverviewPage() {
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<OverviewMetrics | null>(null);
  const [userMetrics, setUserMetrics] = useState<UserMetrics | null>(null);
  const [templateMetrics, setTemplateMetrics] = useState<TemplateMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      setError(null);
      try {
        const [overviewData, userData, templateData] = await Promise.allSettled([
          adminApi.getOverviewMetrics('7d'),
          adminApi.getUserMetrics('30d'),
          adminApi.getTemplateMetrics('30d'),
        ]);
        if (overviewData.status === 'fulfilled') setOverview(overviewData.value);
        if (userData.status === 'fulfilled') setUserMetrics(userData.value);
        if (templateData.status === 'fulfilled') setTemplateMetrics(templateData.value);
        const failed = [
          overviewData.status === 'rejected' && 'overview',
          userData.status === 'rejected' && 'user metrics',
          templateData.status === 'rejected' && 'templates',
        ].filter(Boolean) as string[];
        if (failed.length === 3) {
          setError('Failed to load metrics. Check server logs and try again.');
        } else if (failed.length > 0) {
          console.warn('Admin metrics partial load:', failed.join(', '), 'failed');
        }
      } catch (err: any) {
        console.error('Failed to fetch admin metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

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

  // Transform user signups data for chart
  const signupsData = userMetrics?.signups_over_time?.map(item => ({
    date: item.date,
    value: item.count,
  })) || [];

  // Mock parlay data for chart (will be replaced with real data)
  const parlayData = [
    { name: 'Safe', value: overview?.total_parlays ? Math.floor(overview.total_parlays * 0.3) : 0 },
    { name: 'Balanced', value: overview?.total_parlays ? Math.floor(overview.total_parlays * 0.45) : 0 },
    { name: 'Degen', value: overview?.total_parlays ? Math.floor(overview.total_parlays * 0.2) : 0 },
    { name: 'Custom', value: overview?.total_parlays ? Math.floor(overview.total_parlays * 0.05) : 0 },
  ];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard Overview</h1>
        <p className="text-gray-400 mt-1">
          Key metrics and performance indicators for Parlay Gorilla
        </p>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Users"
          value={overview?.total_users?.toLocaleString() || '0'}
          icon={Users}
          loading={loading}
        />
        <MetricCard
          title="Daily Active Users"
          value={overview?.dau?.toLocaleString() || '0'}
          icon={Activity}
          loading={loading}
        />
        <MetricCard
          title="Parlays Generated"
          value={overview?.total_parlays?.toLocaleString() || '0'}
          icon={Ticket}
          loading={loading}
        />
        <MetricCard
          title="Model Accuracy"
          value={overview?.model_accuracy ? `${overview.model_accuracy}%` : 'N/A'}
          icon={TrendingUp}
          loading={loading}
        />
        <MetricCard
          title="Total Revenue"
          value={`$${overview?.total_revenue?.toLocaleString() || '0'}`}
          icon={DollarSign}
          loading={loading}
        />
        <MetricCard
          title="API Health"
          value={overview?.api_health?.status === 'healthy' ? 'Healthy' : 'Degraded'}
          icon={Server}
          loading={loading}
          suffix={overview?.api_health ? `${overview.api_health.error_rate}% errors` : undefined}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User signups chart */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">User Signups</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : signupsData.length > 0 ? (
            <AreaChart
              data={signupsData}
              dataKey="value"
              xAxisKey="date"
              color="#10b981"
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No signup data available
            </div>
          )}
        </div>

        {/* Parlays by type chart */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Parlays by Type</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : (
            <BarChart
              data={parlayData}
              dataKey="value"
              xAxisKey="name"
            />
          )}
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User breakdown */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Users by Plan</h3>
          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex justify-between items-center">
                  <div className="w-20 h-4 bg-emerald-900/20 rounded" />
                  <div className="w-12 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(userMetrics?.users_by_plan || {}).map(([plan, count]) => (
                <div key={plan} className="flex justify-between items-center">
                  <span className="text-gray-400 capitalize">{plan}</span>
                  <span className="text-white font-medium">{count.toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active vs Inactive */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">User Status</h3>
          {loading ? (
            <div className="space-y-3 animate-pulse">
              <div className="flex justify-between items-center">
                <div className="w-20 h-4 bg-emerald-900/20 rounded" />
                <div className="w-12 h-4 bg-emerald-900/20 rounded" />
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-emerald-400">Active</span>
                <span className="text-white font-medium">
                  {userMetrics?.active_vs_inactive?.active?.toLocaleString() || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-red-400">Inactive</span>
                <span className="text-white font-medium">
                  {userMetrics?.active_vs_inactive?.inactive?.toLocaleString() || 0}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Engagement metrics */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Engagement</h3>
          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex justify-between items-center">
                  <div className="w-20 h-4 bg-emerald-900/20 rounded" />
                  <div className="w-12 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">DAU</span>
                <span className="text-white font-medium">{userMetrics?.dau?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">WAU</span>
                <span className="text-white font-medium">{userMetrics?.wau?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">MAU</span>
                <span className="text-white font-medium">{userMetrics?.mau?.toLocaleString() || 0}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Templates (Custom Builder QuickStart) */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <LayoutTemplate className="h-5 w-5 text-emerald-400" />
          Templates
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          Custom Builder QuickStart: clicks, applied, partial rate by template (30d).
        </p>
        {loading ? (
          <div className="overflow-x-auto">
            <div className="min-w-[400px] space-y-2 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex gap-4">
                  <div className="w-24 h-6 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-6 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-6 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-6 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          </div>
        ) : templateMetrics ? (
          <div className="overflow-x-auto">
            <table className="min-w-[400px] w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-white/10">
                  <th className="py-2 pr-4">Template</th>
                  <th className="py-2 pr-4">Clicks</th>
                  <th className="py-2 pr-4">Applied</th>
                  <th className="py-2 pr-4">Partial rate</th>
                </tr>
              </thead>
              <tbody>
                {TEMPLATE_IDS.map(tid => (
                  <tr key={tid} className="border-b border-white/5">
                    <td className="py-2 pr-4 text-white font-medium">
                      {TEMPLATE_LABELS[tid] || tid}
                    </td>
                    <td className="py-2 pr-4 text-white">
                      {(templateMetrics.clicks_by_template?.[tid] ?? 0).toLocaleString()}
                    </td>
                    <td className="py-2 pr-4 text-white">
                      {(templateMetrics.applied_by_template?.[tid] ?? 0).toLocaleString()}
                    </td>
                    <td className="py-2 pr-4 text-emerald-400">
                      {(templateMetrics.partial_rate_by_template?.[tid] ?? 0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No template data.</p>
        )}
      </div>
    </div>
  );
}

