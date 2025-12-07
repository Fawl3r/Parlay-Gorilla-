"use client";

import { LucideIcon, TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  change?: number;
  changeLabel?: string;
  suffix?: string;
  loading?: boolean;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  change,
  changeLabel,
  suffix,
  loading = false,
}: MetricCardProps) {
  const isPositiveChange = change !== undefined && change >= 0;
  
  if (loading) {
    return (
      <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="w-10 h-10 bg-emerald-900/20 rounded-lg" />
          <div className="w-20 h-4 bg-emerald-900/20 rounded" />
        </div>
        <div className="w-24 h-8 bg-emerald-900/20 rounded mb-2" />
        <div className="w-16 h-4 bg-emerald-900/20 rounded" />
      </div>
    );
  }
  
  return (
    <div className="bg-[#111118] rounded-xl border border-emerald-900/30 p-6 hover:border-emerald-500/30 transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="w-10 h-10 bg-emerald-500/10 rounded-lg flex items-center justify-center">
          <Icon className="w-5 h-5 text-emerald-400" />
        </div>
        {change !== undefined && (
          <div
            className={`flex items-center gap-1 text-sm ${
              isPositiveChange ? 'text-emerald-400' : 'text-red-400'
            }`}
          >
            {isPositiveChange ? (
              <TrendingUp className="w-4 h-4" />
            ) : (
              <TrendingDown className="w-4 h-4" />
            )}
            <span>
              {isPositiveChange ? '+' : ''}
              {change.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
      
      <div className="text-2xl font-bold text-white mb-1">
        {value}
        {suffix && <span className="text-lg text-gray-400 ml-1">{suffix}</span>}
      </div>
      
      <div className="text-sm text-gray-400">{title}</div>
      
      {changeLabel && (
        <div className="text-xs text-gray-500 mt-1">{changeLabel}</div>
      )}
    </div>
  );
}

