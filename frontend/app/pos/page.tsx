/**
 * POS Page
 * Main point of sale interface for processing customer purchases
 * Implements US4-US8: Search, Add, Edit, Remove, Total, Generate Bill, Print Invoice
 */

'use client';

import { useCallback, useState } from 'react';
import { Item, Bill } from '@/lib/types';
import { useBill, useStockMonitor } from '@/lib/hooks';
import ItemSearch from '@/components/pos/ItemSearch';
import BillItems from '@/components/pos/BillItems';
import BillSummary from '@/components/pos/BillSummary';
import GenerateBillButton from '@/components/pos/GenerateBillButton';
import InvoiceView from '@/components/pos/InvoiceView';
import StockWarning from '@/components/pos/StockWarning';
import ErrorBoundary from '@/components/shared/ErrorBoundary';

export default function POSPage() {
  const { items, addItem, updateQuantity, removeItem, subtotal, total, clearBill } = useBill();
  const { warning: stockWarning } = useStockMonitor(items);
  const [generatedBill, setGeneratedBill] = useState<Bill | null>(null);

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

  const handleBillGenerated = useCallback((billId: number) => {
    // For now, create a temporary bill object
    // In production, you'd fetch the full bill from the API
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

  // Show invoice view if bill is generated
  if (generatedBill) {
    return (
      <ErrorBoundary>
        <InvoiceView
          bill={generatedBill}
          billItems={items}
          onNewBill={handleNewBill}
          storeName="StoreLite IMS"
        />
      </ErrorBoundary>
    );
  }

  // Show bill entry form
  return (
    <ErrorBoundary>
      {/* Stock Warning Overlay */}
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

            {/* Generate Bill Button */}
            <div className="mt-4">
              <GenerateBillButton
                billItems={items}
                onSuccess={handleBillGenerated}
              />
            </div>

            {/* Info */}
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
              <p className="font-semibold mb-2">📝 Next Steps:</p>
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
  );
}
