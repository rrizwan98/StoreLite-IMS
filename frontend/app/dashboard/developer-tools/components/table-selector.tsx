/**
 * Table Selector Component
 *
 * Multi-select component for choosing database tables.
 */

'use client';

import { useState, useMemo } from 'react';
import { Search, Check, Database, Columns } from 'lucide-react';
import { TableSummary } from '@/lib/developer-tools-api';

interface TableSelectorProps {
  tables: TableSummary[];
  selectedTables: string[];
  onChange: (tables: string[]) => void;
}

export default function TableSelector({ tables, selectedTables, onChange }: TableSelectorProps) {
  const [search, setSearch] = useState('');

  // Filter tables by search
  const filteredTables = useMemo(() => {
    if (!search.trim()) return tables;
    const query = search.toLowerCase();
    return tables.filter(t =>
      t.name.toLowerCase().includes(query) ||
      t.column_preview.toLowerCase().includes(query)
    );
  }, [tables, search]);

  // Check if a table is selected
  const isSelected = (tableName: string) => selectedTables.includes(tableName);

  // Toggle table selection
  const toggleTable = (tableName: string) => {
    if (isSelected(tableName)) {
      onChange(selectedTables.filter(t => t !== tableName));
    } else {
      onChange([...selectedTables, tableName]);
    }
  };

  // Select/deselect all
  const handleSelectAll = () => {
    if (selectedTables.length === tables.length) {
      onChange([]);
    } else {
      onChange(tables.map(t => t.name));
    }
  };

  return (
    <div className="space-y-4">
      {/* Search & Actions */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tables..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
        <button
          onClick={handleSelectAll}
          className="px-3 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
        >
          {selectedTables.length === tables.length ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      {/* Selection Summary */}
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {selectedTables.length} of {tables.length} tables selected
      </div>

      {/* Table List */}
      <div className="border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-200 dark:divide-gray-700 max-h-[300px] overflow-y-auto">
        {filteredTables.length === 0 ? (
          <div className="p-4 text-center text-gray-500 dark:text-gray-400">
            No tables found matching &quot;{search}&quot;
          </div>
        ) : (
          filteredTables.map((table) => (
            <div
              key={table.name}
              onClick={() => toggleTable(table.name)}
              className={`flex items-start gap-3 p-3 cursor-pointer transition-colors ${
                isSelected(table.name)
                  ? 'bg-blue-50 dark:bg-blue-900/20'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              <div className="pt-0.5">
                <div
                  className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                    isSelected(table.name)
                      ? 'bg-blue-600 border-blue-600'
                      : 'border-gray-300 dark:border-gray-600'
                  }`}
                >
                  {isSelected(table.name) && (
                    <Check className="h-3 w-3 text-white" />
                  )}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-gray-400 flex-shrink-0" />
                  <span className="font-medium text-gray-900 dark:text-white truncate">
                    {table.name}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400">
                  <Columns className="h-3 w-3" />
                  <span>{table.column_count} columns</span>
                </div>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400 truncate">
                  {table.column_preview}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Selected Tables Preview */}
      {selectedTables.length > 0 && (
        <div className="pt-2">
          <div className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Selected Tables:
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedTables.map((tableName) => (
              <span
                key={tableName}
                className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-sm rounded-full"
              >
                {tableName}
                <button
                  onClick={() => toggleTable(tableName)}
                  className="hover:text-blue-900 dark:hover:text-blue-200"
                >
                  <span className="sr-only">Remove {tableName}</span>
                  &times;
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
