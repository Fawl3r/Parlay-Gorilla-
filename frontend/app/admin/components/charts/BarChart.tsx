"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

interface BarChartProps {
  data: Array<{ name: string; value: number; [key: string]: any }>;
  dataKey?: string;
  xAxisKey?: string;
  color?: string;
  height?: number;
  formatValue?: (value: number) => string;
  showLabels?: boolean;
}

const COLORS = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444'];

export function BarChart({
  data,
  dataKey = 'value',
  xAxisKey = 'name',
  color,
  height = 300,
  formatValue = (v) => v.toLocaleString(),
  showLabels = true,
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis
          dataKey={xAxisKey}
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
          formatter={(value?: number) => [formatValue(typeof value === "number" ? value : 0), dataKey]}
        />
        <Bar dataKey={dataKey} radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={color || COLORS[index % COLORS.length]}
            />
          ))}
        </Bar>
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}

