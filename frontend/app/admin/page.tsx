/**
 * Admin Page
 * Main admin interface for inventory management
 * Implements US1 (Add New Item) and US2 (View and Search Inventory)
 */

'use client';

import { useState, useCallback } from 'react';
import { Item } from '@/lib/types';
import { useItems } from '@/lib/hooks';
import AddItemForm from '@/components/admin/AddItemForm';
import ItemsTable from '@/components/admin/ItemsTable';
import Filters from '@/components/admin/Filters';
import EditItemModal from '@/components/admin/EditItemModal';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import ErrorMessage from '@/components/shared/ErrorMessage';

export default function AdminPage() {
  const [filters, setFilters] = useState<{ name?: string; category?: string }>({});
  const { items, loading, error, refetch } = useItems(filters);
  const [selectedItemForEdit, setSelectedItemForEdit] = useState<Item | null>(null);

  const handleItemAdded = useCallback(
    (item: Item) => {
      // Refresh inventory table after new item is added
      refetch();
    },
    [refetch]
  );

  const handleFilterChange = useCallback((newFilters: { name?: string; category?: string }) => {
    setFilters(newFilters);
  }, []);

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleEditItem = useCallback((item: Item) => {
    setSelectedItemForEdit(item);
  }, []);

  const handleSaveItem = useCallback(
    (updatedItem: Item) => {
      // Update items list with the updated item
      refetch();
      setSelectedItemForEdit(null);
    },
    [refetch]
  );

  const handleCloseModal = useCallback(() => {
    setSelectedItemForEdit(null);
  }, []);

  return (
    <ErrorBoundary>
      <div className="space-y-6">
        {/* Add Item Form Section */}
        <div>
          <AddItemForm onItemAdded={handleItemAdded} />
        </div>

        {/* Inventory View Section */}
        <div>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-1">Inventory Items</h2>
            <p className="text-gray-600">Search and manage all your inventory items</p>
          </div>

          {/* Filters */}
          <Filters onFilterChange={handleFilterChange} isLoading={loading} />

          {/* Error Message */}
          {error && (
            <div className="mb-6">
              <ErrorMessage message={error} onRetry={handleRetry} showRetry />
            </div>
          )}

          {/* Items Table */}
          <ItemsTable items={items} loading={loading} onEdit={handleEditItem} />

          {/* Summary */}
          {!loading && items.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
              <strong>{items.length}</strong> item{items.length !== 1 ? 's' : ''} in inventory
              {filters.name && <span>, filtered by name: <strong>&quot;{filters.name}&quot;</strong></span>}
              {filters.category && <span>, filtered by category: <strong>{filters.category}</strong></span>}
            </div>
          )}
        </div>
      </div>

      {/* Edit Item Modal */}
      <EditItemModal
        item={selectedItemForEdit}
        onSave={handleSaveItem}
        onCancel={handleCloseModal}
      />
    </ErrorBoundary>
  );
}
