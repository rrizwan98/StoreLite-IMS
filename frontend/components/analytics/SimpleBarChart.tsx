/**
 * SimpleBarChart Component (Task T039)
 *
 * CSS-based horizontal bar chart for product comparisons
 * No external charting library required
 */

'use client';

interface BarData {
  label: string;
  value: number;
  color?: string;
}

interface SimpleBarChartProps {
  data: BarData[];
  title?: string;
  maxValue?: number;
  formatValue?: (value: number) => string;
  showValues?: boolean;
}

const defaultColors = [
  'bg-blue-500',
  'bg-green-500',
  'bg-purple-500',
  'bg-orange-500',
  'bg-pink-500',
  'bg-teal-500',
  'bg-indigo-500',
  'bg-red-500',
];

export default function SimpleBarChart({
  data,
  title,
  maxValue,
  formatValue = (v) => v.toLocaleString(),
  showValues = true,
}: SimpleBarChartProps) {
  const max = maxValue || Math.max(...data.map(d => d.value), 1);

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {title && (
        <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>
      )}
      <div className="space-y-3">
        {data.map((item, index) => {
          const percentage = (item.value / max) * 100;
          const colorClass = item.color || defaultColors[index % defaultColors.length];

          return (
            <div key={index}>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 truncate max-w-[60%]">{item.label}</span>
                {showValues && (
                  <span className="font-medium text-gray-900">{formatValue(item.value)}</span>
                )}
              </div>
              <div className="w-full bg-gray-100 rounded-full h-4">
                <div
                  className={`h-4 rounded-full transition-all duration-500 ${colorClass}`}
                  style={{ width: `${Math.max(percentage, 2)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      {data.length === 0 && (
        <p className="text-gray-500 text-center py-4">No data available</p>
      )}
    </div>
  );
}
