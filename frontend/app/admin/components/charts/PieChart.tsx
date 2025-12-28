"use client";

import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';

interface PieChartProps {
  data: Array<{ name: string; value: number }>;
  height?: number;
  colors?: string[];
  innerRadius?: number;
  outerRadius?: number;
  showLabels?: boolean;
}

const DEFAULT_COLORS = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899'];

export function PieChart({
  data,
  height = 300,
  colors = DEFAULT_COLORS,
  innerRadius = 60,
  outerRadius = 100,
  showLabels = true,
}: PieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={2}
          dataKey="value"
          label={showLabels ? ({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''} (${((percent ?? 0) * 100).toFixed(0)}%)` : undefined}
          labelLine={showLabels}
        >
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={colors[index % colors.length]}
              stroke="#111118"
              strokeWidth={2}
            />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: '#111118',
            border: '1px solid #10b981',
            borderRadius: '8px',
            color: '#fff',
          }}
          formatter={(value?: number, name?: string) => {
            const v = typeof value === "number" ? value : 0
            const n = typeof name === "string" ? name : ""
            return [`${v.toLocaleString()} (${total > 0 ? ((v / total) * 100).toFixed(1) : "0.0"}%)`, n]
          }}
        />
        <Legend
          verticalAlign="bottom"
          height={36}
          formatter={(value) => <span className="text-gray-300">{value}</span>}
        />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}

