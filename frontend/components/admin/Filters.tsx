/**
 * Filters Component (FR-004)
 * Provides search and filter controls for inventory items
 * Supports name search (debounced, case-insensitive) and category filter
 */

'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { CATEGORIES } from '@/lib/constants';

export interface FiltersProps {
  onFilterChange?: (filters: { name?: string; category?: string }) => void;
  isLoading?: boolean;
}

const DEBOUNCE_DELAY = 300; // ms

export default function Filters({ onFilterChange, isLoading = false }: FiltersProps) {
  const [nameSearch, setNameSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Debounced filter change handler
  useEffect(() => {
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // Set new timer
    debounceTimer.current = setTimeout(() => {
      if (onFilterChange) {
        onFilterChange({
          name: nameSearch || undefined,
          category: categoryFilter || undefined,
        });
      }
    }, DEBOUNCE_DELAY);

    // Cleanup on unmount
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [nameSearch, categoryFilter, onFilterChange]);

  const handleClearFilters = useCallback(() => {
    setNameSearch('');
    setCategoryFilter('');
    if (onFilterChange) {
      onFilterChange({});
    }
  }, [onFilterChange]);

  const hasActiveFilters = nameSearch !== '' || categoryFilter !== '';

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h3 className="text-lg font-bold mb-4">Search & Filter</h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Name Search */}
        <div>
          <label htmlFor="nameSearch" className="block text-sm font-medium text-gray-700 mb-2">
            Search by Name
          </label>
          <input
            type="text"
            id="nameSearch"
            value={nameSearch}
            onChange={(e) => setNameSearch(e.target.value)}
            placeholder="Type item name..."
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          {nameSearch && (
            <p className="text-xs text-gray-500 mt-1">
              {nameSearch.length} character{nameSearch.length !== 1 ? 's' : ''}
            </p>
          )}
        </div>

        {/* Category Filter */}
        <div>
          <label htmlFor="categoryFilter" className="block text-sm font-medium text-gray-700 mb-2">
            Filter by Category
          </label>
          <select
            id="categoryFilter"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            disabled={isLoading}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          >
            <option value="">All Categories</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Clear Button */}
        <div className="flex items-end">
          <button
            onClick={handleClearFilters}
            disabled={!hasActiveFilters || isLoading}
            className="w-full px-4 py-2 bg-gray-200 text-gray-900 font-medium rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <p className="text-sm text-blue-900">
            <strong>Active filters:</strong> {[nameSearch && `name: "${nameSearch}"`, categoryFilter && `category: ${categoryFilter}`].filter(Boolean).join(', ')}
          </p>
        </div>
      )}
    </div>
  );
}
