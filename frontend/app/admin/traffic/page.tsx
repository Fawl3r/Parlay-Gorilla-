"use client";

import { useEffect, useState } from 'react';
import { adminApi, TrafficMetrics } from '@/lib/admin-api';
import { MetricCard } from '../components/MetricCard';
import { BarChart, PieChart } from '../components/charts';
import {
  Globe,
  Users,
  Eye,
  Link,
  Search,
  TrendingUp,
} from 'lucide-react';

export default function AdminTrafficPage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<TrafficMetrics | null>(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const data = await adminApi.getTrafficMetrics(timeRange);
        setMetrics(data);
      } catch (err: any) {
        console.error('Failed to fetch traffic metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [timeRange]);

  // Transform referrer data for pie chart
  const referrerData = Object.entries(metrics?.referrer_breakdown || {}).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: value as number,
  }));

  // Calculate totals
  const totalPageViews = Object.values(metrics?.event_counts || {}).reduce((a, b) => a + b, 0);
  const totalSessions = metrics?.unique_sessions || 0;

  // Get analysis page views
  const analysisViews = metrics?.top_pages?.filter(p => p.page?.includes('/analysis/')) || [];

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
          <h1 className="text-2xl font-bold text-white">Traffic & SEO</h1>
          <p className="text-gray-400 mt-1">
            Page views, referrers, and SEO metrics
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Unique Sessions"
          value={totalSessions.toLocaleString()}
          icon={Users}
          loading={loading}
        />
        <MetricCard
          title="Total Events"
          value={totalPageViews.toLocaleString()}
          icon={Eye}
          loading={loading}
        />
        <MetricCard
          title="Analysis Pages"
          value={analysisViews.length.toLocaleString()}
          icon={Search}
          loading={loading}
        />
        <MetricCard
          title="Avg Events/Session"
          value={totalSessions > 0 ? (totalPageViews / totalSessions).toFixed(1) : '0'}
          icon={TrendingUp}
          loading={loading}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Referrer breakdown */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Traffic Sources</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : referrerData.length > 0 ? (
            <PieChart
              data={referrerData}
              height={300}
              colors={['#10b981', '#06b6d4', '#f59e0b', '#8b5cf6', '#ef4444']}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No referrer data available
            </div>
          )}
        </div>

        {/* Event type breakdown */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Event Types</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : Object.keys(metrics?.event_counts || {}).length > 0 ? (
            <BarChart
              data={Object.entries(metrics?.event_counts || {})
                .slice(0, 8)
                .map(([name, value]) => ({
                  name: name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
                  value: value as number,
                }))}
              dataKey="value"
              xAxisKey="name"
              height={300}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No event data available
            </div>
          )}
        </div>
      </div>

      {/* Top pages table */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Top Pages</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-emerald-900/20">
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Page URL</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Views</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">% of Total</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 10 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="py-3 px-4"><div className="w-64 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-12 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-12 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                  </tr>
                ))
              ) : metrics?.top_pages && metrics.top_pages.length > 0 ? (
                metrics.top_pages.slice(0, 20).map((page, i) => {
                  const totalViews = metrics.top_pages?.reduce((a, b) => a + b.views, 0) || 1;
                  const percentage = ((page.views / totalViews) * 100).toFixed(1);
                  
                  return (
                    <tr key={i} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          {page.page?.includes('/analysis/') ? (
                            <Search className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                          ) : (
                            <Globe className="w-4 h-4 text-gray-500 flex-shrink-0" />
                          )}
                          <span className="text-gray-300 truncate max-w-[400px]" title={page.page}>
                            {page.page || '(none)'}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right text-emerald-400 font-medium">
                        {page.views.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-400">
                        {percentage}%
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={3} className="py-8 text-center text-gray-500">
                    No page data available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Analysis pages (SEO focus) */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <h3 className="text-lg font-semibold text-white mb-2">Analysis Page Performance</h3>
        <p className="text-gray-400 text-sm mb-4">
          SEO landing pages for game predictions
        </p>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-emerald-900/20">
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Matchup</th>
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Sport</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Views</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="py-3 px-4"><div className="w-48 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4"><div className="w-16 h-4 bg-emerald-900/20 rounded" /></td>
                    <td className="py-3 px-4 text-right"><div className="w-12 h-4 bg-emerald-900/20 rounded ml-auto" /></td>
                  </tr>
                ))
              ) : analysisViews.length > 0 ? (
                analysisViews.slice(0, 15).map((page, i) => {
                  // Parse matchup from URL
                  const urlParts = page.page?.split('/') || [];
                  const sport = urlParts[2]?.toUpperCase() || 'Unknown';
                  const matchup = urlParts[3]?.replace(/-prediction$/, '').replace(/-/g, ' ') || 'Unknown';
                  
                  return (
                    <tr key={i} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                      <td className="py-3 px-4 text-white capitalize">{matchup}</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-500/20 text-emerald-400">
                          {sport}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right text-emerald-400 font-medium">
                        {page.views.toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={3} className="py-8 text-center text-gray-500">
                    No analysis page views yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Referrer details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Traffic Source Breakdown</h3>
          {loading ? (
            <div className="space-y-4 animate-pulse">
              {[1, 2, 3, 4].map(i => (
                <div key={i}>
                  <div className="flex justify-between mb-1">
                    <div className="w-24 h-4 bg-emerald-900/20 rounded" />
                    <div className="w-16 h-4 bg-emerald-900/20 rounded" />
                  </div>
                  <div className="h-3 bg-emerald-900/20 rounded-full" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(metrics?.referrer_breakdown || {}).map(([source, count]) => {
                const total = Object.values(metrics?.referrer_breakdown || {}).reduce((a, b) => a + b, 0);
                const percentage = total > 0 ? ((count as number) / total * 100) : 0;
                const colors: Record<string, string> = {
                  direct: 'from-emerald-600 to-emerald-400',
                  search: 'from-cyan-600 to-cyan-400',
                  social: 'from-purple-600 to-purple-400',
                  other: 'from-gray-600 to-gray-400',
                };
                
                return (
                  <div key={source}>
                    <div className="flex justify-between mb-1">
                      <span className="text-gray-300 capitalize">{source}</span>
                      <span className="text-emerald-400 font-medium">
                        {(count as number).toLocaleString()} ({percentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-3 bg-emerald-900/20 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${colors[source] || colors.other} rounded-full`}
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
          <h3 className="text-lg font-semibold text-white mb-4">SEO Insights</h3>
          <div className="space-y-4">
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <Search className="w-5 h-5 text-emerald-400" />
                <span className="text-white font-medium">Analysis Pages</span>
              </div>
              <p className="text-gray-400 text-sm">
                {analysisViews.length} unique prediction pages receiving traffic
              </p>
            </div>
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <Link className="w-5 h-5 text-cyan-400" />
                <span className="text-white font-medium">Search Traffic</span>
              </div>
              <p className="text-gray-400 text-sm">
                {((metrics?.referrer_breakdown?.search || 0) as number).toLocaleString()} visits from search engines
              </p>
            </div>
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="flex items-center gap-3 mb-2">
                <Globe className="w-5 h-5 text-purple-400" />
                <span className="text-white font-medium">Direct Traffic</span>
              </div>
              <p className="text-gray-400 text-sm">
                {((metrics?.referrer_breakdown?.direct || 0) as number).toLocaleString()} direct/bookmark visits
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

