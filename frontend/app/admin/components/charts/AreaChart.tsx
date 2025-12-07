"use client";

import {
  AreaChart as RechartsAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface AreaChartProps {
  data: Array<{ date: string; value: number; [key: string]: any }>;
  dataKey?: string;
  xAxisKey?: string;
  color?: string;
  height?: number;
  formatValue?: (value: number) => string;
  formatDate?: (date: string) => string;
}

export function AreaChart({
  data,
  dataKey = 'value',
  xAxisKey = 'date',
  color = '#10b981',
  height = 300,
  formatValue = (v) => v.toLocaleString(),
  formatDate = (d) => new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
}: AreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsAreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={color} stopOpacity={0.3} />
            <stop offset="95%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey={xAxisKey}
          tickFormatter={formatDate}
          stroke="#4b5563"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tickFormatter={formatValue}
          stroke="#4b5563"
          fontSize={12}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#111118',
            border: '1px solid #10b981',
            borderRadius: '8px',
            color: '#fff',
          }}
          labelFormatter={formatDate}
          formatter={(value: number) => [formatValue(value), dataKey]}
        />
        <Area
          type="monotone"
          dataKey={dataKey}
          stroke={color}
          strokeWidth={2}
          fillOpacity={1}
          fill={`url(#gradient-${dataKey})`}
        />
      </RechartsAreaChart>
    </ResponsiveContainer>
  );
}

