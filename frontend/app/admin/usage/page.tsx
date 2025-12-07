"use client";

import { useEffect, useState } from 'react';
import { adminApi, UsageMetrics } from '@/lib/admin-api';
import { MetricCard } from '../components/MetricCard';
import { BarChart, PieChart } from '../components/charts';
import {
  Eye,
  Ticket,
  Zap,
  BarChart3,
  TrendingUp,
  Layers,
} from 'lucide-react';

export default function AdminUsagePage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<UsageMetrics | null>(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const data = await adminApi.getUsageMetrics(timeRange);
        setMetrics(data);
      } catch (err: any) {
        console.error('Failed to fetch usage metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [timeRange]);

  // Transform parlay type data for chart
  const parlayTypeData = Object.entries(metrics?.parlays_by_type || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
  }));

  // Transform feature usage data for chart
  const featureUsageData = Object.entries(metrics?.feature_usage || {})
    .slice(0, 10)
    .map(([name, value]) => ({
      name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      value: value as number,
    }));

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
          <h1 className="text-2xl font-bold text-white">Usage Analytics</h1>
          <p className="text-gray-400 mt-1">
            Feature usage and engagement metrics
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
          title="Analysis Views"
          value={metrics?.analysis_views?.toLocaleString() || '0'}
          icon={Eye}
          loading={loading}
        />
        <MetricCard
          title="Parlay Sessions"
          value={metrics?.parlay_sessions?.toLocaleString() || '0'}
          icon={Ticket}
          loading={loading}
        />
        <MetricCard
          title="Upset Finder Clicks"
          value={metrics?.upset_finder_usage?.toLocaleString() || '0'}
          icon={Zap}
          loading={loading}
        />
        <MetricCard
          title="Avg Legs/Parlay"
          value={metrics?.avg_legs?.avg?.toFixed(1) || '0'}
          icon={Layers}
          loading={loading}
        />
        <MetricCard
          title="Min Legs"
          value={metrics?.avg_legs?.min?.toString() || '0'}
          icon={BarChart3}
          loading={loading}
        />
        <MetricCard
          title="Max Legs"
          value={metrics?.avg_legs?.max?.toString() || '0'}
          icon={TrendingUp}
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Parlays by type */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Parlays by Type</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : parlayTypeData.length > 0 ? (
            <PieChart
              data={parlayTypeData}
              height={300}
              colors={['#10b981', '#06b6d4', '#f59e0b', '#8b5cf6']}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No parlay data available
            </div>
          )}
        </div>

        {/* Feature usage */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Feature Usage</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : featureUsageData.length > 0 ? (
            <BarChart
              data={featureUsageData}
              dataKey="value"
              xAxisKey="name"
              height={300}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No usage data available
            </div>
          )}
        </div>
      </div>

      {/* Detailed feature usage table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Event Breakdown</h3>
        {loading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="flex justify-between items-center py-2">
                <div className="w-32 h-4 bg-emerald-900/20 rounded" />
                <div className="w-16 h-4 bg-emerald-900/20 rounded" />
              </div>
            ))}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-emerald-900/20">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Event Type</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Count</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Percentage</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(metrics?.feature_usage || {}).map(([event, count]) => {
                  const total = Object.values(metrics?.feature_usage || {}).reduce((a, b) => a + b, 0);
                  const percentage = total > 0 ? ((count as number) / total * 100).toFixed(1) : '0';
                  return (
                    <tr key={event} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                      <td className="py-3 px-4 text-white">
                        {event.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </td>
                      <td className="py-3 px-4 text-right text-emerald-400 font-medium">
                        {(count as number).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400">
                        {percentage}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Parlay stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Parlay Type Distribution</h3>
          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex justify-between items-center py-2">
                  <div className="w-24 h-4 bg-emerald-900/20 rounded" />
                  <div className="flex-1 mx-4 h-2 bg-emerald-900/20 rounded" />
                  <div className="w-12 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(metrics?.parlays_by_type || {}).map(([type, count]) => {
                const total = Object.values(metrics?.parlays_by_type || {}).reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? ((count as number) / total * 100) : 0;
                return (
                  <div key={type}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-gray-300 capitalize">{type}</span>
                      <span className="text-emerald-400 font-medium">{(count as number).toLocaleString()}</span>
                    </div>
                    <div className="h-2 bg-emerald-900/20 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Sport Usage</h3>
          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex justify-between items-center py-2">
                  <div className="w-20 h-4 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(metrics?.parlays_by_sport || {}).length > 0 ? (
                Object.entries(metrics?.parlays_by_sport || {}).map(([sport, count]) => (
                  <div key={sport} className="flex justify-between items-center py-2 border-b border-emerald-900/10">
                    <span className="text-gray-300 uppercase">{sport}</span>
                    <span className="text-emerald-400 font-medium">{(count as number).toLocaleString()}</span>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-8">
                  Sport breakdown data not available
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

