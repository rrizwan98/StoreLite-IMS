/**
 * Item Search Component (FR-006, FR-007)
 * Allows salesperson to search for items and add them to bill
 * Displays dropdown with matching items
 */

'use client';

import { useState, useCallback } from 'react';
import { Item } from '@/lib/types';
import { useSearch } from '@/lib/hooks';
import { api } from '@/lib/api';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

export interface ItemSearchProps {
  onAddItem?: (item: Item) => void;
}

export default function ItemSearch({ onAddItem }: ItemSearchProps) {
  const [showDropdown, setShowDropdown] = useState(false);

  // Search function to be used by useSearch hook
  const searchFunction = useCallback(async (query: string) => {
    try {
      return await api.getItems({ name: query });
    } catch {
      return [];
    }
  }, []);

  const { query, setQuery, results, loading, error } = useSearch(searchFunction);

  const handleSelectItem = useCallback(
    (item: Item) => {
      // Check stock
      if (item.stock_qty === 0) {
        alert(`⚠️  "${item.name}" is out of stock`);
        return;
      }

      // Callback to parent
      if (onAddItem) {
        onAddItem(item);
      }

      // Reset search
      setQuery('');
      setShowDropdown(false);
    },
    [onAddItem, setQuery]
  );

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setShowDropdown(true);
  };

  const handleInputFocus = () => {
    setShowDropdown(true);
  };

  const handleInputBlur = () => {
    // Delay to allow click on dropdown item
    setTimeout(() => {
      setShowDropdown(false);
    }, 200);
  };

  return (
    <div className="relative">
      <div className="mb-4">
        <label htmlFor="itemSearch" className="block text-sm font-medium text-gray-700 mb-2">
          Search Items
        </label>
        <div className="relative">
          <input
            type="text"
            id="itemSearch"
            value={query}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
            placeholder="Search by item name..."
            className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
          />
          {loading && (
            <div className="absolute right-4 top-3">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>
      </div>

      {/* Dropdown Results */}
      {showDropdown && (
        <div className="absolute z-10 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-64 overflow-y-auto">
          {loading && (
            <div className="p-4 text-center">
              <LoadingSpinner size="sm" message="Searching..." />
            </div>
          )}

          {!loading && error && (
            <div className="p-4 text-center text-error">
              <p className="text-sm">⚠️ Search error: {error}</p>
            </div>
          )}

          {!loading && results.length === 0 && query.length > 0 && (
            <div className="p-4 text-center text-gray-600">
              <p className="text-sm">No items found matching &quot;{query}&quot;</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <ul className="divide-y divide-gray-200">
              {results.map((item) => (
                <li key={item.id}>
                  <button
                    onClick={() => handleSelectItem(item)}
                    disabled={item.stock_qty === 0}
                    className="w-full px-4 py-3 text-left hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex justify-between items-center group"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{item.name}</p>
                      <p className="text-sm text-gray-600">
                        ₹{(parseFloat(item.unit_price as any) || 0).toFixed(2)} / {item.unit}
                      </p>
                    </div>
                    <div className="text-right ml-4">
                      {item.stock_qty === 0 ? (
                        <span className="text-xs font-medium text-error">Out of Stock</span>
                      ) : item.stock_qty < 10 ? (
                        <span className="text-xs font-medium text-warning">
                          {item.stock_qty} left
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-success">In Stock</span>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}

          {!loading && query.length === 0 && (
            <div className="p-4 text-center text-gray-600">
              <p className="text-sm">Start typing to search for items...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
