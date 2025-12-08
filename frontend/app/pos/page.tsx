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
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-6">
            <h3 className="text-xl font-bold mb-4 text-gray-900">Bill Summary</h3>

            {/* Bill Details */}
            <div className="space-y-3 mb-6 pb-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Items Count:</span>
                <span className="font-semibold text-gray-900">{items.length}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-700">Subtotal:</span>
                <span className="font-semibold text-gray-900">₹{subtotal.toFixed(2)}</span>
              </div>
            </div>

            {/* Grand Total */}
            <div className="flex justify-between items-center mb-6 text-lg">
              <span className="font-bold text-gray-900">Grand Total:</span>
              <span className="font-bold text-primary text-2xl">₹{total.toFixed(2)}</span>
            </div>

            {/* Coming Soon - Generate Bill Button */}
            <button
              disabled={items.length === 0}
              className="w-full px-4 py-3 bg-primary text-white font-bold rounded-md hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              💳 Generate Bill
            </button>

            {/* Info */}
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
              <p className="font-semibold mb-2">📝 Next Steps:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Finish adding items to bill</li>
                <li>Click "Generate Bill" to create invoice</li>
                <li>Review and print the invoice</li>
                <li>Start a new bill for next customer</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
