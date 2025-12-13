/**
 * Dashboard POS Page
 * Point of Sale for users using our database
 */

'use client';

import { useCallback, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Item, Bill } from '@/lib/types';
import { useBill, useStockMonitor } from '@/lib/hooks';
import { ROUTES, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import ItemSearch from '@/components/pos/ItemSearch';
import BillItems from '@/components/pos/BillItems';
import BillSummary from '@/components/pos/BillSummary';
import GenerateBillButton from '@/components/pos/GenerateBillButton';
import InvoiceView from '@/components/pos/InvoiceView';
import StockWarning from '@/components/pos/StockWarning';
import ErrorBoundary from '@/components/shared/ErrorBoundary';

export default function DashboardPOSPage() {
  const { user, connectionStatus, logout, isLoading } = useAuth();
  const router = useRouter();

  const { items, addItem, updateQuantity, removeItem, subtotal, total, clearBill } = useBill();
  const { warning: stockWarning } = useStockMonitor(items);
  const [generatedBill, setGeneratedBill] = useState<Bill | null>(null);

  // Check if user should have access to this page
  useEffect(() => {
    if (!isLoading && connectionStatus?.connection_type === 'own_database') {
      router.push(ROUTES.DASHBOARD);
    }
  }, [connectionStatus, isLoading, router]);

  const handleAddItem = useCallback((item: Item) => {
    addItem(item);
  }, [addItem]);

  const handleUpdateQuantity = useCallback((index: number, quantity: number) => {
    updateQuantity(index, quantity);
  }, [updateQuantity]);

  const handleRemoveItem = useCallback((index: number) => {
    removeItem(index);
  }, [removeItem]);

  const handleBillGenerated = useCallback((billId: number) => {
    setGeneratedBill({
      id: billId,
      total_amount: total,
      created_at: new Date().toISOString(),
    });
  }, [total]);

  const handleNewBill = useCallback(() => {
    clearBill();
    setGeneratedBill(null);
  }, [clearBill]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Show invoice view if bill is generated
  if (generatedBill) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-6">
              <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl font-bold">S</span>
                </div>
                <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
              </Link>
            </div>
            <span className="text-gray-600 text-sm">{user?.email}</span>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <ErrorBoundary>
            <InvoiceView
              bill={generatedBill}
              billItems={items}
              onNewBill={handleNewBill}
              storeName={APP_METADATA.NAME}
            />
          </ErrorBoundary>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
            </Link>
            <nav className="hidden md:flex space-x-4">
              <Link href={ROUTES.ADMIN} className="text-gray-600 hover:text-gray-900">Admin</Link>
              <Link href={ROUTES.POS} className="text-blue-600 font-medium">POS</Link>
              <Link href={ROUTES.ANALYTICS} className="text-gray-600 hover:text-gray-900">Analytics</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600 text-sm">{user?.email}</span>
            <button onClick={logout} className="text-gray-600 hover:text-gray-900 text-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ErrorBoundary>
          <StockWarning warning={stockWarning} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Bill Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Search Section */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold mb-4">Search Items</h2>
                <ItemSearch onAddItem={handleAddItem} />
              </div>

              {/* Bill Items Section */}
              <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-900">Bill Items</h2>
                <BillItems
                  items={items}
                  onUpdateQuantity={handleUpdateQuantity}
                  onRemoveItem={handleRemoveItem}
                />
              </div>
            </div>

            {/* Bill Summary Sidebar */}
            <div className="lg:col-span-1 space-y-4">
              <div className="sticky top-6">
                <BillSummary items={items} subtotal={subtotal} total={total} />

                <div className="mt-4">
                  <GenerateBillButton
                    billItems={items}
                    onSuccess={handleBillGenerated}
                  />
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
                  <p className="font-semibold mb-2">Next Steps:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Edit quantities if needed</li>
                    <li>Remove any unwanted items</li>
                    <li>Click &quot;Generate Bill&quot; to create invoice</li>
                    <li>Review and print the invoice</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </ErrorBoundary>
      </main>
    </div>
  );
}
