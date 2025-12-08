/**
 * POS Page
 * Main point of sale interface for processing customer purchases
 * Implements US4 (Search and Add Items to Bill) with foundation for US5-US8
 */

'use client';

import { useCallback } from 'react';
import { Item } from '@/lib/types';
import { useBill } from '@/lib/hooks';
import ItemSearch from '@/components/pos/ItemSearch';
import BillItems from '@/components/pos/BillItems';
import BillSummary from '@/components/pos/BillSummary';
import ErrorBoundary from '@/components/shared/ErrorBoundary';

export default function POSPage() {
  const { items, addItem, updateQuantity, removeItem, subtotal, total } = useBill();

  const handleAddItem = useCallback(
    (item: Item) => {
      addItem(item);
    },
    [addItem]
  );

  const handleUpdateQuantity = useCallback(
    (index: number, quantity: number) => {
      updateQuantity(index, quantity);
    },
    [updateQuantity]
  );

  const handleRemoveItem = useCallback(
    (index: number) => {
      removeItem(index);
    },
    [removeItem]
  );

  return (
    <ErrorBoundary>
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

            {/* Coming Soon - Generate Bill Button */}
            <button
              disabled={items.length === 0}
              className="w-full mt-4 px-4 py-3 bg-primary text-white font-bold rounded-md hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              💳 Generate Bill
            </button>

            {/* Info */}
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
              <p className="font-semibold mb-2">📝 Next Steps:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Edit quantities if needed</li>
                <li>Remove any unwanted items</li>
                <li>Click "Generate Bill" to create invoice</li>
                <li>Review and print the invoice</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
