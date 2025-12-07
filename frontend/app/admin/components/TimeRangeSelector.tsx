"use client";

interface TimeRangeSelectorProps {
  value: string;
  onChange: (range: string) => void;
}

const ranges = [
  { value: '24h', label: 'Last 24h' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: '90d', label: 'Last 90 days' },
];

export function TimeRangeSelector({ value, onChange }: TimeRangeSelectorProps) {
  return (
    <div className="flex items-center bg-[#0a0a0f] rounded-lg p-1 border border-emerald-900/30">
      {ranges.map((range) => (
        <button
          key={range.value}
          onClick={() => onChange(range.value)}
          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
            value === range.value
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'text-gray-400 hover:text-emerald-300'
          }`}
        >
          {range.label}
        </button>
      ))}
    </div>
  );
}

