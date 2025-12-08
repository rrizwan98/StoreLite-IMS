/**
 * Admin Page
 * Main admin interface for inventory management
 * Implements US1 (Add New Item) with foundation for US2 (View/Search Inventory)
 */

'use client';

import { useState, useCallback } from 'react';
import { Item } from '@/lib/types';
import AddItemForm from '@/components/admin/AddItemForm';
import ErrorBoundary from '@/components/shared/ErrorBoundary';

export default function AdminPage() {
  const [lastAddedItem, setLastAddedItem] = useState<Item | null>(null);

  const handleItemAdded = useCallback((item: Item) => {
    setLastAddedItem(item);
    // Refresh inventory table in next phase (US2)
    // This will trigger refetch() on useItems hook
  }, []);

  return (
    <ErrorBoundary>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Add Item Form - Main Section */}
        <div className="lg:col-span-2">
          <AddItemForm onItemAdded={handleItemAdded} />

          {/* Success Indicator */}
          {lastAddedItem && (
            <div className="mt-4 bg-success bg-opacity-10 border border-success text-success rounded-md p-4">
              <p className="text-sm">
                <strong>Last Added:</strong> {lastAddedItem.name} ({lastAddedItem.stock_qty}{' '}
                {lastAddedItem.unit})
              </p>
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-bold mb-4">Getting Started</h3>
            <div className="space-y-3 text-sm text-gray-600">
              <div>
                <p className="font-semibold text-gray-900">Step 1</p>
                <p>Fill out the form with item details</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Step 2</p>
                <p>Select appropriate category and unit</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Step 3</p>
                <p>Set price and initial stock quantity</p>
              </div>
              <div>
                <p className="font-semibold text-gray-900">Step 4</p>
                <p>Click "Add Item" to save</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6 mt-4">
            <h3 className="text-lg font-bold mb-3">Quick Tips</h3>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
              <li>All fields are required</li>
              <li>Prices must be positive numbers</li>
              <li>Stock quantity can be zero for pre-orders</li>
              <li>Categories help organize your inventory</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Coming Soon Section - Placeholder for US2 */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h2 className="text-xl font-bold text-blue-900 mb-2">📋 Coming in Phase 4</h2>
        <p className="text-blue-800">
          View and search your inventory items in a sortable table, filter by category, and see
          real-time stock levels.
        </p>
      </div>
    </ErrorBoundary>
  );
}
