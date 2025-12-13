/**
 * DataTable Component (Task T040)
 *
 * Sortable table for detailed data display
 * Includes sorting and basic filtering
 */

'use client';

import { useState, useMemo } from 'react';

interface Column {
  key: string;
  header: string;
  sortable?: boolean;
  align?: 'left' | 'center' | 'right';
  format?: (value: any, row: any) => React.ReactNode;
}

interface DataTableProps {
  data: Record<string, any>[];
  columns: Column[];
  title?: string;
  maxRows?: number;
  emptyMessage?: string;
}

type SortDirection = 'asc' | 'desc' | null;

export default function DataTable({
  data,
  columns,
  title,
  maxRows,
  emptyMessage = 'No data available',
}: DataTableProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (key: string, sortable?: boolean) => {
    if (!sortable) return;

    if (sortKey === key) {
      if (sortDirection === 'asc') {
        setSortDirection('desc');
      } else if (sortDirection === 'desc') {
        setSortKey(null);
        setSortDirection(null);
      }
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey || !sortDirection) return data;

    return [...data].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;
      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      const comparison = aVal < bVal ? -1 : 1;
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [data, sortKey, sortDirection]);

  const displayData = maxRows ? sortedData.slice(0, maxRows) : sortedData;

  const alignClass = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {title && (
        <div className="px-4 py-3 border-b border-gray-200">
          <h3 className="text-sm font-semibold text-gray-700">{title}</h3>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider
                    ${alignClass[col.align || 'left']}
                    ${col.sortable ? 'cursor-pointer hover:bg-gray-100 select-none' : ''}`}
                  onClick={() => handleSort(col.key, col.sortable)}
                >
                  <div className="flex items-center gap-1">
                    {col.header}
                    {col.sortable && (
                      <span className="text-gray-400">
                        {sortKey === col.key
                          ? sortDirection === 'asc'
                            ? '↑'
                            : '↓'
                          : '↕'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {displayData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-gray-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              displayData.map((row, rowIndex) => (
                <tr key={rowIndex} className="hover:bg-gray-50">
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`px-4 py-3 text-sm text-gray-700 whitespace-nowrap
                        ${alignClass[col.align || 'left']}`}
                    >
                      {col.format ? col.format(row[col.key], row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {maxRows && data.length > maxRows && (
        <div className="px-4 py-2 border-t border-gray-200 bg-gray-50 text-xs text-gray-500">
          Showing {maxRows} of {data.length} rows
        </div>
      )}
    </div>
  );
}
