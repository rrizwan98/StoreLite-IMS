/**
 * KPI Stats Row Component
 *
 * Displays key metrics at the top of the dashboard for quick visibility.
 * Data derived from existing API responses - no new endpoints needed.
 */

'use client';

import Link from 'next/link';
import { Database, Wrench, CheckCircle, AlertCircle, Loader2, Info } from 'lucide-react';
import { ROUTES } from '@/lib/constants';
import Tooltip from '@/components/ui/Tooltip';

interface KPIStatsRowProps {
  tablesCount: number | null;  // null = loading
  toolsConnected: number | null;
  schemaStatus: 'ready' | 'pending' | 'error' | null;
  className?: string;
}

interface StatWidgetProps {
  value: number | string | null;
  label: string;
  icon: React.ReactNode;
  href: string;
  colorScheme: 'emerald' | 'purple' | 'blue';
  isLoading?: boolean;
}

function StatWidget({ value, label, icon, href, colorScheme, isLoading }: StatWidgetProps) {
  const colorClasses = {
    emerald: {
      bg: 'bg-emerald-50 dark:bg-emerald-900/30',
      border: 'border-emerald-200 dark:border-emerald-800',
      icon: 'text-emerald-600 dark:text-emerald-400',
      value: 'text-emerald-700 dark:text-emerald-300',
      hover: 'hover:border-emerald-300 dark:hover:border-emerald-700',
    },
    purple: {
      bg: 'bg-purple-50 dark:bg-purple-900/30',
      border: 'border-purple-200 dark:border-purple-800',
      icon: 'text-purple-600 dark:text-purple-400',
      value: 'text-purple-700 dark:text-purple-300',
      hover: 'hover:border-purple-300 dark:hover:border-purple-700',
    },
    blue: {
      bg: 'bg-blue-50 dark:bg-blue-900/30',
      border: 'border-blue-200 dark:border-blue-800',
      icon: 'text-blue-600 dark:text-blue-400',
      value: 'text-blue-700 dark:text-blue-300',
      hover: 'hover:border-blue-300 dark:hover:border-blue-700',
    },
  };

  const colors = colorClasses[colorScheme];

  return (
    <Link href={href}>
      <div
        className={`
          ${colors.bg} ${colors.border} ${colors.hover}
          border rounded-xl p-4
          transition-all duration-200
          hover:-translate-y-0.5 hover:shadow-md
          cursor-pointer
          min-w-[140px]
        `}
      >
        <div className="flex items-center space-x-3">
          <div className={`${colors.icon}`}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            {isLoading ? (
              <div className="animate-pulse">
                <div className="h-7 w-12 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
                <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
              </div>
            ) : (
              <>
                <p className={`text-2xl font-bold ${colors.value}`}>
                  {value ?? '—'}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                  {label}
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}

function SchemaStatusWidget({ status, isLoading }: { status: 'ready' | 'pending' | 'error' | null; isLoading?: boolean }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'ready':
        return {
          icon: <CheckCircle className="h-6 w-6" />,
          value: 'Ready',
          colorScheme: 'emerald' as const,
          tooltip: 'Your database schema was discovered successfully. You can now query your data with AI.',
        };
      case 'pending':
        return {
          icon: <Loader2 className="h-6 w-6 animate-spin" />,
          value: 'Pending',
          colorScheme: 'blue' as const,
          tooltip: 'Schema discovery is in progress. This usually takes a few seconds.',
        };
      case 'error':
        return {
          icon: <AlertCircle className="h-6 w-6" />,
          value: 'Error',
          colorScheme: 'purple' as const,
          tooltip: 'There was an error discovering your schema. Click to view details and retry.',
        };
      default:
        return {
          icon: <Database className="h-6 w-6" />,
          value: '—',
          colorScheme: 'blue' as const,
          tooltip: 'Schema status unknown. Click to check connection.',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className="relative">
      <StatWidget
        value={config.value}
        label="Schema Status"
        icon={config.icon}
        href={ROUTES.SCHEMA_CONNECT}
        colorScheme={config.colorScheme}
        isLoading={isLoading}
      />
      {!isLoading && (
        <div className="absolute top-2 right-2">
          <Tooltip content={config.tooltip} position="left">
            <button
              type="button"
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors rounded-full hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="More information about schema status"
            >
              <Info className="h-4 w-4" />
            </button>
          </Tooltip>
        </div>
      )}
    </div>
  );
}

export default function KPIStatsRow({
  tablesCount,
  toolsConnected,
  schemaStatus,
  className = '',
}: KPIStatsRowProps) {
  const isLoading = tablesCount === null && toolsConnected === null && schemaStatus === null;

  return (
    <div className={`grid grid-cols-1 sm:grid-cols-3 gap-4 ${className}`}>
      {/* Tables Discovered */}
      <StatWidget
        value={tablesCount}
        label="Tables Discovered"
        icon={<Database className="h-6 w-6" />}
        href={ROUTES.SCHEMA_CONNECT}
        colorScheme="emerald"
        isLoading={isLoading}
      />

      {/* Tools Connected */}
      <StatWidget
        value={toolsConnected}
        label="Tools Connected"
        icon={<Wrench className="h-6 w-6" />}
        href="/dashboard/settings"
        colorScheme="purple"
        isLoading={isLoading}
      />

      {/* Schema Status */}
      <SchemaStatusWidget status={schemaStatus} isLoading={isLoading} />
    </div>
  );
}
