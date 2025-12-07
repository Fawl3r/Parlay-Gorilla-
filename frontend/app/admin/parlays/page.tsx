"use client";

import { useEffect, useState } from 'react';
import { adminApi } from '@/lib/admin-api';
import { MetricCard } from '../components/MetricCard';
import { BarChart, PieChart, AreaChart } from '../components/charts';
import {
  Ticket,
  Layers,
  TrendingUp,
  Activity,
  Zap,
  Calculator,
} from 'lucide-react';

interface ParlayStats {
  total_parlays: number;
  avg_legs: number;
  min_legs: number;
  max_legs: number;
  by_type: Record<string, number>;
  by_method: Record<string, number>;
  recent_parlays: Array<{
    id: string;
    parlay_type: string;
    legs_count: number;
    expected_value: number | null;
    hit_probability: number | null;
    build_method: string | null;
    created_at: string;
  }>;
}

export default function AdminParlaysPage() {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30d');
  const [parlayEvents, setParlayEvents] = useState<any[]>([]);
  const [usageMetrics, setUsageMetrics] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [eventsData, usageData] = await Promise.all([
          adminApi.getEvents({ eventType: 'build_parlay', limit: 100 }).catch(() => []),
          adminApi.getUsageMetrics(timeRange),
        ]);
        setParlayEvents(eventsData);
        setUsageMetrics(usageData);
      } catch (err: any) {
        console.error('Failed to fetch parlay data:', err);
        setError(err.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [timeRange]);

  // Calculate stats from usage metrics
  const totalParlays = Object.values(usageMetrics?.parlays_by_type || {}).reduce((a: number, b: any) => a + b, 0) as number;
  
  // Transform for pie chart
  const typeDistribution = Object.entries(usageMetrics?.parlays_by_type || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
  }));

  // Legs distribution mock data (would come from parlay_events)
  const legsDistribution = [
    { name: '2-3 legs', value: Math.floor(totalParlays * 0.25) },
    { name: '4-5 legs', value: Math.floor(totalParlays * 0.35) },
    { name: '6-8 legs', value: Math.floor(totalParlays * 0.25) },
    { name: '9-12 legs', value: Math.floor(totalParlays * 0.10) },
    { name: '13+ legs', value: Math.floor(totalParlays * 0.05) },
  ];

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
          <h1 className="text-2xl font-bold text-white">Parlay Analytics</h1>
          <p className="text-gray-400 mt-1">
            Parlay generation statistics and trends
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
          title="Total Parlays"
          value={totalParlays.toLocaleString()}
          icon={Ticket}
          loading={loading}
        />
        <MetricCard
          title="Avg Legs"
          value={usageMetrics?.avg_legs?.avg?.toFixed(1) || '0'}
          icon={Layers}
          loading={loading}
        />
        <MetricCard
          title="Min Legs"
          value={usageMetrics?.avg_legs?.min?.toString() || '0'}
          icon={Activity}
          loading={loading}
        />
        <MetricCard
          title="Max Legs"
          value={usageMetrics?.avg_legs?.max?.toString() || '0'}
          icon={TrendingUp}
          loading={loading}
        />
        <MetricCard
          title="Upset Finder Used"
          value={usageMetrics?.upset_finder_usage?.toLocaleString() || '0'}
          icon={Zap}
          loading={loading}
        />
        <MetricCard
          title="Builder Sessions"
          value={usageMetrics?.parlay_sessions?.toLocaleString() || '0'}
          icon={Calculator}
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Type distribution */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Parlay Type Distribution</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : typeDistribution.length > 0 ? (
            <PieChart
              data={typeDistribution}
              height={300}
              colors={['#10b981', '#06b6d4', '#f59e0b', '#8b5cf6']}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No parlay type data available
            </div>
          )}
        </div>

        {/* Legs distribution */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Legs Distribution</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : totalParlays > 0 ? (
            <BarChart
              data={legsDistribution}
              dataKey="value"
              xAxisKey="name"
              height={300}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No legs distribution data available
            </div>
          )}
        </div>
      </div>

      {/* Type breakdown with progress bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Risk Profile Breakdown</h3>
          {loading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3, 4].map(i => (
                <div key={i}>
                  <div className="flex justify-between mb-1">
                    <div className="w-20 h-4 bg-emerald-900/20 rounded" />
                    <div className="w-12 h-4 bg-emerald-900/20 rounded" />
                  </div>
                  <div className="h-3 bg-emerald-900/20 rounded-full" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {['safe', 'balanced', 'degen', 'custom'].map((type) => {
                const count = (usageMetrics?.parlays_by_type?.[type] as number) || 0;
                const percentage = totalParlays > 0 ? (count / totalParlays * 100) : 0;
                const colors: Record<string, string> = {
                  safe: 'from-emerald-600 to-emerald-400',
                  balanced: 'from-cyan-600 to-cyan-400',
                  degen: 'from-orange-600 to-orange-400',
                  custom: 'from-purple-600 to-purple-400',
                };
                
                return (
                  <div key={type}>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-300 capitalize">{type}</span>
                      <span className="text-emerald-400 font-medium">
                        {count.toLocaleString()} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-3 bg-emerald-900/20 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${colors[type]} rounded-full transition-all duration-500`}
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
          <h3 className="text-lg font-semibold text-white mb-4">Build Method</h3>
          {loading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                  <div className="w-32 h-4 bg-emerald-900/20 rounded" />
                  <div className="w-16 h-4 bg-emerald-900/20 rounded" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-1">
              {[
                { label: 'Auto Generated', key: 'auto_generated', color: 'text-emerald-400' },
                { label: 'User Built', key: 'user_built', color: 'text-cyan-400' },
                { label: 'AI Assisted', key: 'ai_assisted', color: 'text-purple-400' },
              ].map((method) => (
                <div key={method.key} className="flex justify-between items-center py-3 border-b border-emerald-900/10">
                  <span className="text-gray-300">{method.label}</span>
                  <span className={`font-medium ${method.color}`}>
                    {/* Mock values - would come from actual data */}
                    {method.key === 'auto_generated' ? Math.floor(totalParlays * 0.6).toLocaleString() :
                     method.key === 'user_built' ? Math.floor(totalParlays * 0.3).toLocaleString() :
                     Math.floor(totalParlays * 0.1).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recent parlays table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Parlay Activity</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-emerald-900/20">
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Type</th>
                <th className="text-center py-3 px-4 text-gray-400 text-sm">Legs</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">EV</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Hit Prob</th>
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Method</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Created</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="py-3 px-4"><div className="w-16 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-center"><div className="w-8 h-4 bg-emerald-900/20 rounded mx-auto" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-12 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-12 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                    <td className="py-3 px-4"><div className="w-20 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-24 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                  </tr>
                ))
              ) : parlayEvents.length > 0 ? (
                parlayEvents.slice(0, 10).map((event, i) => (
                  <tr key={i} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        event.metadata?.parlay_type === 'safe' ? 'bg-emerald-500/20 text-emerald-400' :
                        event.metadata?.parlay_type === 'balanced' ? 'bg-cyan-500/20 text-cyan-400' :
                        event.metadata?.parlay_type === 'degen' ? 'bg-orange-500/20 text-orange-400' :
                        'bg-purple-500/20 text-purple-400'
                      }`}>
                        {event.metadata?.parlay_type || 'unknown'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center text-white">{event.metadata?.legs || '-'}</td>
                    <td className="py-3 px-4 text-right text-emerald-400">
                      {event.metadata?.expected_value ? `${(event.metadata.expected_value * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-400">
                      {event.metadata?.hit_probability ? `${(event.metadata.hit_probability * 100).toFixed(1)}%` : '-'}
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-sm">
                      {event.metadata?.build_method?.replace(/_/g, ' ') || '-'}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-500 text-sm">
                      {new Date(event.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-gray-500">
                    No recent parlay activity
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

