"use client";

import { useEffect, useState } from 'react';
import { adminApi } from '@/lib/admin-api';
import { MetricCard } from '../components/MetricCard';
import { BarChart } from '../components/charts';
import {
  Target,
  TrendingUp,
  Activity,
  Percent,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

interface ModelMetrics {
  model_version?: string;
  current_model_version?: string;
  metrics: {
    total_predictions: number;
    correct_predictions: number;
    accuracy: number;
    brier_score: number;
    avg_edge: number;
    positive_edge_accuracy: number;
  };
  interpretation: {
    accuracy: string;
    brier_score: string;
    edge_performance: string;
  };
}

interface SportsBreakdown {
  model_version: string;
  lookback_days: number;
  sports: Array<{
    sport: string;
    total_predictions: number;
    accuracy: number;
    brier_score?: number;
  }>;
  best_performing: string | null;
}

interface TeamBias {
  team: string;
  bias_adjustment: number;
  adjustment_pct: string;
  direction: string;
}

interface TeamBiasesResponse {
  sport: string;
  total_teams: number;
  teams: TeamBias[];
  summary: string;
}

export default function AdminModelPerformancePage() {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [sportsBreakdown, setSportsBreakdown] = useState<SportsBreakdown | null>(null);
  const [teamBiases, setTeamBiases] = useState<TeamBiasesResponse | null>(null);
  const [selectedSport, setSelectedSport] = useState('NFL');
  const [lookbackDays, setLookbackDays] = useState(30);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const [metricsData, sportsData] = await Promise.all([
          adminApi.getModelMetrics({ lookbackDays }),
          adminApi.getSportsBreakdown(lookbackDays),
        ]);
        setMetrics(metricsData);
        setSportsBreakdown(sportsData);
      } catch (err: any) {
        console.error('Failed to fetch model metrics:', err);
        setError(err.message || 'Failed to load metrics');
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [lookbackDays]);

  useEffect(() => {
    async function fetchTeamBiases() {
      try {
        const data = await adminApi.getTeamBiases(selectedSport);
        setTeamBiases(data);
      } catch (err) {
        console.error('Failed to fetch team biases:', err);
      }
    }

    fetchTeamBiases();
  }, [selectedSport]);

  // Transform sports data for chart
  const sportsChartData = sportsBreakdown?.sports?.map(s => ({
    name: s.sport,
    value: s.accuracy * 100,
  })) || [];

  const handleRecalibrate = async () => {
    try {
      await adminApi.triggerRecalibration(selectedSport);
      // Refresh team biases
      const data = await adminApi.getTeamBiases(selectedSport);
      setTeamBiases(data);
      alert(`Recalibration triggered for ${selectedSport}`);
    } catch (err: any) {
      alert(err.message || 'Recalibration failed');
    }
  };

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
          <h1 className="text-2xl font-bold text-white">Model Performance</h1>
          <p className="text-gray-400 mt-1">
            Prediction accuracy and calibration metrics
          </p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">
            Model: <span className="text-emerald-400 font-mono">{metrics?.model_version ?? metrics?.current_model_version ?? 'Loading...'}</span>
          </span>
          <select
            value={lookbackDays}
            onChange={(e) => setLookbackDays(Number(e.target.value))}
            className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <MetricCard
          title="Total Predictions"
          value={metrics?.metrics?.total_predictions?.toLocaleString() || '0'}
          icon={Activity}
          loading={loading}
        />
        <MetricCard
          title="Correct Predictions"
          value={metrics?.metrics?.correct_predictions?.toLocaleString() || '0'}
          icon={CheckCircle}
          loading={loading}
        />
        <MetricCard
          title="Accuracy"
          value={metrics?.metrics?.accuracy ? `${(metrics.metrics.accuracy * 100).toFixed(1)}%` : 'N/A'}
          icon={Target}
          loading={loading}
        />
        <MetricCard
          title="Brier Score"
          value={metrics?.metrics?.brier_score?.toFixed(3) || 'N/A'}
          icon={Percent}
          loading={loading}
        />
        <MetricCard
          title="Avg Edge"
          value={metrics?.metrics?.avg_edge ? `${(metrics.metrics.avg_edge * 100).toFixed(2)}%` : 'N/A'}
          icon={TrendingUp}
          loading={loading}
        />
        <MetricCard
          title="+EV Accuracy"
          value={metrics?.metrics?.positive_edge_accuracy ? `${(metrics.metrics.positive_edge_accuracy * 100).toFixed(1)}%` : 'N/A'}
          icon={AlertTriangle}
          loading={loading}
        />
      </div>

      {/* No-data guidance */}
      {!loading && (metrics?.metrics?.total_predictions ?? 0) === 0 && (
        <div className="bg-amber-900/20 border border-amber-700/40 rounded-xl p-4">
          <p className="text-amber-200 text-sm">
            <strong>To see accuracy and calibration:</strong> the app must record predictions when generating analysis (e.g. heatmap or upset finder) and resolve them when game results are in. Once predictions are saved and resolved, metrics will appear here.
          </p>
        </div>
      )}

      {/* Interpretation */}
      {metrics?.interpretation && (
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Performance Interpretation</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Accuracy</div>
              <div className={metrics.interpretation.accuracy?.startsWith('Insufficient data') ? 'text-amber-400' : 'text-emerald-400'}>
                {metrics.interpretation.accuracy}
              </div>
            </div>
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Calibration</div>
              <div className={metrics.interpretation.brier_score?.startsWith('Insufficient data') ? 'text-amber-400' : 'text-emerald-400'}>
                {metrics.interpretation.brier_score}
              </div>
            </div>
            <div className="bg-[#0a0a0f] rounded-lg p-4">
              <div className="text-sm text-gray-400 mb-1">Edge Performance</div>
              <div className={metrics.interpretation.edge_performance?.startsWith('Insufficient data') ? 'text-amber-400' : 'text-emerald-400'}>
                {metrics.interpretation.edge_performance}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accuracy by sport */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Accuracy by Sport</h3>
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <div className="text-emerald-400 animate-pulse">Loading chart...</div>
            </div>
          ) : sportsChartData.length > 0 ? (
            <>
              <BarChart
                data={sportsChartData}
                dataKey="value"
                xAxisKey="name"
                height={280}
                formatValue={(v) => `${v.toFixed(1)}%`}
              />
              {sportsBreakdown?.best_performing && (
                <div className="mt-4 text-center text-sm text-gray-400">
                  Best performing: <span className="text-emerald-400">{sportsBreakdown.best_performing}</span>
                </div>
              )}
            </>
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No sports data available
            </div>
          )}
        </div>

        {/* Sports breakdown table */}
        <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Detailed Breakdown</h3>
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
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-emerald-900/20">
                    <th className="text-left py-2 px-3 text-gray-400 text-sm">Sport</th>
                    <th className="text-right py-2 px-3 text-gray-400 text-sm">Predictions</th>
                    <th className="text-right py-2 px-3 text-gray-400 text-sm">Accuracy</th>
                    <th className="text-right py-2 px-3 text-gray-400 text-sm">Brier</th>
                  </tr>
                </thead>
                <tbody>
                  {sportsBreakdown?.sports?.map((sport) => (
                    <tr key={sport.sport} className="border-b border-emerald-900/10">
                      <td className="py-2 px-3 text-white font-medium">{sport.sport}</td>
                      <td className="py-2 px-3 text-right text-gray-300">{sport.total_predictions}</td>
                      <td className="py-2 px-3 text-right text-emerald-400">
                        {(sport.accuracy * 100).toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-right text-gray-400">
                        {sport.brier_score?.toFixed(3) || 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Team calibration */}
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Team Calibration</h3>
          <div className="flex items-center gap-3">
            <select
              value={selectedSport}
              onChange={(e) => setSelectedSport(e.target.value)}
              className="bg-[#0a0a0f] border border-emerald-900/30 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-emerald-500/50"
            >
              <option value="NFL">NFL</option>
              <option value="NBA">NBA</option>
              <option value="NHL">NHL</option>
              <option value="MLB">MLB</option>
              <option value="SOCCER">Soccer</option>
            </select>
            <button
              onClick={handleRecalibrate}
              className="px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-colors"
            >
              Recalibrate
            </button>
          </div>
        </div>
        
        {teamBiases?.summary && (
          <p className="text-gray-400 mb-4">{teamBiases.summary}</p>
        )}

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-emerald-900/20">
                <th className="text-left py-3 px-4 text-gray-400 text-sm">Team</th>
                <th className="text-right py-3 px-4 text-gray-400 text-sm">Adjustment</th>
                <th className="text-center py-3 px-4 text-gray-400 text-sm">Direction</th>
              </tr>
            </thead>
            <tbody>
              {teamBiases?.teams?.slice(0, 15).map((team) => (
                <tr key={team.team} className="border-b border-emerald-900/10 hover:bg-emerald-900/5">
                  <td className="py-3 px-4 text-white">{team.team}</td>
                  <td className="py-3 px-4 text-right font-mono">
                    <span className={team.bias_adjustment >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                      {team.adjustment_pct}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs ${
                      team.direction === 'calibrated'
                        ? 'bg-gray-500/20 text-gray-400'
                        : team.direction === 'underrated'
                        ? 'bg-emerald-500/20 text-emerald-400'
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {team.direction}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

