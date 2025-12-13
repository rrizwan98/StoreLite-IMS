/**
 * MetricCard Component (Task T041)
 *
 * Displays a single KPI metric with optional trend indicator
 */

'use client';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: string;
  trend?: {
    direction: 'up' | 'down' | 'flat';
    value: string;
    isPositive?: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const variantStyles = {
  default: 'bg-white border-gray-200',
  success: 'bg-green-50 border-green-200',
  warning: 'bg-yellow-50 border-yellow-200',
  danger: 'bg-red-50 border-red-200',
};

const trendColors = {
  up: 'text-green-600',
  down: 'text-red-600',
  flat: 'text-gray-500',
};

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
}: MetricCardProps) {
  const trendArrow = trend?.direction === 'up' ? '↑' : trend?.direction === 'down' ? '↓' : '→';
  const trendColorClass = trend
    ? trend.isPositive !== undefined
      ? trend.isPositive
        ? 'text-green-600'
        : 'text-red-600'
      : trendColors[trend.direction]
    : '';

  return (
    <div className={`rounded-lg border p-4 shadow-sm ${variantStyles[variant]}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <div className="mt-1 flex items-baseline">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {trend && (
              <span className={`ml-2 text-sm font-medium ${trendColorClass}`}>
                {trendArrow} {trend.value}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
        {icon && (
          <span className="text-2xl">{icon}</span>
        )}
      </div>
    </div>
  );
}
