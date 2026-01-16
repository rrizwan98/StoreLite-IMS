/**
 * MiniSparkline Component
 *
 * Compact SVG sparkline for KPI cards.
 * Lightweight, no labels, just trend visualization.
 */

'use client';

interface MiniSparklineProps {
  data: number[];
  color?: string;
  height?: number;
  width?: number;
  strokeWidth?: number;
  showArea?: boolean;
  className?: string;
}

export default function MiniSparkline({
  data,
  color = '#10B981',
  height = 24,
  width = 80,
  strokeWidth = 1.5,
  showArea = true,
  className = '',
}: MiniSparklineProps) {
  if (data.length < 2) {
    return (
      <div
        className={`flex items-center justify-center text-gray-400 ${className}`}
        style={{ height, width }}
      >
        <svg viewBox="0 0 24 24" className="w-4 h-4 opacity-50">
          <line x1="2" y1="12" x2="22" y2="12" stroke="currentColor" strokeWidth="2" strokeDasharray="4 2" />
        </svg>
      </div>
    );
  }

  const padding = 2;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  const minValue = Math.min(...data);
  const maxValue = Math.max(...data);
  const range = maxValue - minValue || 1;

  // Generate points
  const points = data.map((value, i) => {
    const x = padding + (i / (data.length - 1)) * chartWidth;
    const y = padding + chartHeight - ((value - minValue) / range) * chartHeight;
    return { x, y };
  });

  // Create line path
  const linePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ');

  // Create area path
  const areaPath = `${linePath} L ${points[points.length - 1].x},${height - padding} L ${padding},${height - padding} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      style={{ width, height }}
      preserveAspectRatio="none"
    >
      {/* Area fill */}
      {showArea && (
        <path
          d={areaPath}
          fill={color}
          fillOpacity="0.15"
        />
      )}
      {/* Line */}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      <circle
        cx={points[points.length - 1].x}
        cy={points[points.length - 1].y}
        r="2"
        fill={color}
      />
    </svg>
  );
}
