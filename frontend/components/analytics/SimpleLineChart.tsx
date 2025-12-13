/**
 * SimpleLineChart Component (Task T038)
 *
 * CSS/SVG-based sparkline chart for sales trends
 * No external charting library required
 */

'use client';

interface DataPoint {
  label: string;
  value: number;
}

interface SimpleLineChartProps {
  data: DataPoint[];
  title?: string;
  height?: number;
  color?: string;
  showLabels?: boolean;
  formatValue?: (value: number) => string;
}

export default function SimpleLineChart({
  data,
  title,
  height = 120,
  color = '#3B82F6',
  showLabels = true,
  formatValue = (v) => v.toLocaleString(),
}: SimpleLineChartProps) {
  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        {title && <h3 className="text-sm font-semibold text-gray-700 mb-4">{title}</h3>}
        <p className="text-gray-500 text-center py-4">No data available</p>
      </div>
    );
  }

  const values = data.map(d => d.value);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;

  // SVG dimensions
  const width = 100;
  const chartHeight = 60;
  const padding = 5;

  // Generate path points
  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1 || 1)) * (width - 2 * padding);
    const y = chartHeight - padding - ((d.value - minValue) / range) * (chartHeight - 2 * padding);
    return `${x},${y}`;
  });

  // Create line path
  const linePath = `M ${points.join(' L ')}`;

  // Create area path (for fill)
  const areaPath = `${linePath} L ${width - padding},${chartHeight - padding} L ${padding},${chartHeight - padding} Z`;

  // Summary statistics
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  const trend = values.length > 1 ? values[values.length - 1] - values[0] : 0;
  const trendPercent = values[0] !== 0 ? ((trend / values[0]) * 100).toFixed(1) : 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      {title && (
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
          <div className="text-right">
            <p className={`text-sm font-medium ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend >= 0 ? '↑' : '↓'} {trendPercent}%
            </p>
          </div>
        </div>
      )}

      {/* SVG Chart */}
      <div style={{ height }}>
        <svg
          viewBox={`0 0 ${width} ${chartHeight}`}
          className="w-full h-full"
          preserveAspectRatio="none"
        >
          {/* Area fill */}
          <path
            d={areaPath}
            fill={color}
            fillOpacity="0.1"
          />
          {/* Line */}
          <path
            d={linePath}
            fill="none"
            stroke={color}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Data points */}
          {data.map((d, i) => {
            const x = padding + (i / (data.length - 1 || 1)) * (width - 2 * padding);
            const y = chartHeight - padding - ((d.value - minValue) / range) * (chartHeight - 2 * padding);
            return (
              <circle
                key={i}
                cx={x}
                cy={y}
                r="1.5"
                fill={color}
              />
            );
          })}
        </svg>
      </div>

      {/* Summary Stats */}
      {showLabels && (
        <div className="mt-4 grid grid-cols-3 gap-2 text-center">
          <div>
            <p className="text-xs text-gray-500">Min</p>
            <p className="text-sm font-medium">{formatValue(minValue)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Avg</p>
            <p className="text-sm font-medium">{formatValue(avg)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Max</p>
            <p className="text-sm font-medium">{formatValue(maxValue)}</p>
          </div>
        </div>
      )}

      {/* X-axis labels (first and last) */}
      {data.length > 1 && (
        <div className="flex justify-between mt-2 text-xs text-gray-400">
          <span>{data[0].label}</span>
          <span>{data[data.length - 1].label}</span>
        </div>
      )}
    </div>
  );
}
