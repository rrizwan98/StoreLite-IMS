/**
 * RadialProgress Component
 *
 * Circular progress indicator for percentage values.
 * Perfect for success rates and completion metrics.
 */

'use client';

interface RadialProgressProps {
  value: number; // 0-100
  size?: number;
  strokeWidth?: number;
  color?: string;
  trackColor?: string;
  showValue?: boolean;
  valueFormat?: (value: number) => string;
  className?: string;
}

export default function RadialProgress({
  value,
  size = 56,
  strokeWidth = 4,
  color,
  trackColor,
  showValue = true,
  valueFormat = (v) => `${v.toFixed(0)}%`,
  className = '',
}: RadialProgressProps) {
  // Clamp value between 0 and 100
  const clampedValue = Math.min(100, Math.max(0, value));

  // Calculate circle properties
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clampedValue / 100) * circumference;

  // Determine color based on value if not provided
  const getAutoColor = () => {
    if (clampedValue >= 95) return '#10B981'; // Green
    if (clampedValue >= 80) return '#F59E0B'; // Yellow/Amber
    return '#EF4444'; // Red
  };

  const progressColor = color || getAutoColor();
  const track = trackColor || (progressColor + '20'); // 20% opacity of progress color

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Track circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={track}
          strokeWidth={strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={progressColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      {/* Center value */}
      {showValue && (
        <span
          className="absolute text-xs font-semibold"
          style={{ color: progressColor }}
        >
          {valueFormat(clampedValue)}
        </span>
      )}
    </div>
  );
}
