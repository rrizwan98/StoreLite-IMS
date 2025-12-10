/**
 * VisualizationPanel Component (Task T037)
 *
 * Main container for rendering analytics visualizations
 * Dynamically renders charts, tables, and metrics based on data type
 */

'use client';

import MetricCard from './MetricCard';
import SimpleLineChart from './SimpleLineChart';
import SimpleBarChart from './SimpleBarChart';
import DataTable from './DataTable';

// Visualization types
type VisualizationType = 'metrics' | 'line-chart' | 'bar-chart' | 'table' | 'mixed';

interface MetricData {
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

interface ChartData {
  label: string;
  value: number;
}

interface TableColumn {
  key: string;
  header: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  format?: (value: any, row: any) => React.ReactNode;
}

interface VisualizationPanelProps {
  type: VisualizationType;
  title?: string;
  description?: string;
  // For metrics
  metrics?: MetricData[];
  // For charts
  chartData?: ChartData[];
  chartTitle?: string;
  chartColor?: string;
  // For tables
  tableData?: Record<string, any>[];
  tableColumns?: TableColumn[];
  maxRows?: number;
  // Loading state
  isLoading?: boolean;
}

export default function VisualizationPanel({
  type,
  title,
  description,
  metrics = [],
  chartData = [],
  chartTitle,
  chartColor,
  tableData = [],
  tableColumns = [],
  maxRows = 10,
  isLoading = false,
}: VisualizationPanelProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {title && <h2 className="text-lg font-semibold text-gray-900 mb-4">{title}</h2>}
        <div className="animate-pulse space-y-4">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      {/* Header */}
      {(title || description) && (
        <div className="mb-6">
          {title && <h2 className="text-lg font-semibold text-gray-900">{title}</h2>}
          {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
        </div>
      )}

      {/* Content based on type */}
      {type === 'metrics' && metrics.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric, index) => (
            <MetricCard key={index} {...metric} />
          ))}
        </div>
      )}

      {type === 'line-chart' && chartData.length > 0 && (
        <SimpleLineChart
          data={chartData}
          title={chartTitle}
          color={chartColor}
        />
      )}

      {type === 'bar-chart' && chartData.length > 0 && (
        <SimpleBarChart
          data={chartData}
          title={chartTitle}
        />
      )}

      {type === 'table' && tableColumns.length > 0 && (
        <DataTable
          data={tableData}
          columns={tableColumns}
          maxRows={maxRows}
        />
      )}

      {type === 'mixed' && (
        <div className="space-y-6">
          {/* Metrics row */}
          {metrics.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {metrics.map((metric, index) => (
                <MetricCard key={index} {...metric} />
              ))}
            </div>
          )}

          {/* Charts row */}
          {chartData.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <SimpleLineChart
                data={chartData}
                title={chartTitle || 'Trend'}
                color={chartColor}
              />
              <SimpleBarChart
                data={chartData.slice(0, 5)}
                title="Top Items"
              />
            </div>
          )}

          {/* Table */}
          {tableData.length > 0 && tableColumns.length > 0 && (
            <DataTable
              data={tableData}
              columns={tableColumns}
              title="Details"
              maxRows={maxRows}
            />
          )}
        </div>
      )}

      {/* Empty state */}
      {((type === 'metrics' && metrics.length === 0) ||
        (type === 'line-chart' && chartData.length === 0) ||
        (type === 'bar-chart' && chartData.length === 0) ||
        (type === 'table' && tableData.length === 0)) && (
        <div className="text-center py-8">
          <p className="text-gray-500">No data to display</p>
        </div>
      )}
    </div>
  );
}

// Export sub-components for individual use
export { MetricCard, SimpleLineChart, SimpleBarChart, DataTable };
