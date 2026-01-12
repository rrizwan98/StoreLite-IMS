/**
 * Dashboard Admin Page
 * Inventory management for users using our database
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Item } from '@/lib/types';
import { useItems } from '@/lib/hooks';
import { ROUTES, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { ThemeToggle } from '@/components/theme-toggle';
import AddItemForm from '@/components/admin/AddItemForm';
import ItemsTable from '@/components/admin/ItemsTable';
import Filters from '@/components/admin/Filters';
import EditItemModal from '@/components/admin/EditItemModal';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import ErrorMessage from '@/components/shared/ErrorMessage';

export default function DashboardAdminPage() {
  const { user, connectionStatus, logout, isLoading } = useAuth();
  const router = useRouter();

  const [filters, setFilters] = useState<{ name?: string; category?: string }>({});
  const { items, loading, error, refetch } = useItems(filters);
  const [selectedItemForEdit, setSelectedItemForEdit] = useState<Item | null>(null);

  // Check if user should have access to this page
  useEffect(() => {
    if (!isLoading && connectionStatus?.connection_type === 'own_database') {
      // User with own database should use their MCP-connected features
      router.push(ROUTES.DASHBOARD);
    }
  }, [connectionStatus, isLoading, router]);

  const handleItemAdded = useCallback((item: Item) => {
    refetch();
  }, [refetch]);

  const handleFilterChange = useCallback((newFilters: { name?: string; category?: string }) => {
    setFilters(newFilters);
  }, []);

  const handleRetry = useCallback(() => {
    refetch();
  }, [refetch]);

  const handleEditItem = useCallback((item: Item) => {
    setSelectedItemForEdit(item);
  }, []);

  const handleSaveItem = useCallback((updatedItem: Item) => {
    refetch();
    setSelectedItemForEdit(null);
  }, [refetch]);

  const handleCloseModal = useCallback(() => {
    setSelectedItemForEdit(null);
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm dark:shadow-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 dark:bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">{APP_METADATA.NAME}</span>
            </Link>
            <nav className="hidden md:flex space-x-4">
              <Link href={ROUTES.ADMIN} className="text-blue-600 dark:text-blue-400 font-medium">Admin</Link>
              <Link href={ROUTES.POS} className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">POS</Link>
              <Link href={ROUTES.ANALYTICS} className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white">Analytics</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600 dark:text-gray-300 text-sm">{user?.email}</span>
            <ThemeToggle />
            <button onClick={logout} className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white text-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorBoundary>
          <div className="space-y-6">
            {/* Add Item Form Section */}
            <div>
              <AddItemForm onItemAdded={handleItemAdded} />
            </div>

            {/* Inventory View Section */}
            <div>
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">Inventory Items</h2>
                <p className="text-gray-600 dark:text-gray-400">Search and manage all your inventory items</p>
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
                <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-900 dark:text-blue-300">
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
      </main>
    </div>
  );
}
