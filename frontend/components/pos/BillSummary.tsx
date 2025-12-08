/**
 * Bill Summary Component (FR-011)
 * Displays bill totals (subtotal and grand total)
 * Updates in real-time as items are added/removed/modified
 */

'use client';

import { BillItem } from '@/lib/types';

export interface BillSummaryProps {
  items: BillItem[];
  subtotal?: number;
  total?: number;
}

export default function BillSummary({
  items,
  subtotal = 0,
  total = 0,
}: BillSummaryProps) {
  // Calculate totals if not provided
  const calculatedSubtotal =
    subtotal ||
    items.reduce((sum, item) => {
      const lineTotal = item.line_total || item.quantity * item.unit_price;
      return sum + lineTotal;
    }, 0);

  const calculatedTotal = total || calculatedSubtotal;

  return (
    <div className="space-y-4">
      {/* Summary Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-bold mb-4 text-gray-900">Bill Summary</h3>

        {/* Items Count */}
        <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200">
          <span className="text-gray-700">Items Count:</span>
          <span className="font-semibold text-gray-900">{items.length}</span>
        </div>

        {/* Subtotal */}
        <div className="flex justify-between items-center mb-4 pb-4 border-b border-gray-200">
          <span className="text-gray-700">Subtotal:</span>
          <span className="font-semibold text-gray-900">
            ₹{calculatedSubtotal.toFixed(2)}
          </span>
        </div>

        {/* Grand Total */}
        <div className="flex justify-between items-center mb-6">
          <span className="text-lg font-bold text-gray-900">Grand Total:</span>
          <span className="text-3xl font-bold text-primary">
            ₹{calculatedTotal.toFixed(2)}
          </span>
        </div>

        {/* Empty State */}
        {items.length === 0 && (
          <div className="p-4 bg-gray-50 border border-gray-200 rounded-md text-center">
            <p className="text-sm text-gray-600">
              Add items to bill to see totals
            </p>
          </div>
        )}

        {/* Summary Details */}
        {items.length > 0 && (
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
            <p className="text-sm text-blue-900">
              <strong>Bill Ready:</strong> {items.length} item{items.length !== 1 ? 's' : ''} ready for checkout
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
