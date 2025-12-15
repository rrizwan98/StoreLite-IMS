/**
 * Invoice View Component (FR-013, FR-014)
 * Displays printable invoice after bill generation
 * Shows store info, items, totals, and print/new bill buttons
 */

'use client';

import { useCallback } from 'react';
import { Bill, BillItem } from '@/lib/types';

export interface InvoiceViewProps {
  bill: Bill | null;
  billItems: BillItem[];
  onNewBill?: () => void;
  storeName?: string;
}

export default function InvoiceView({
  bill,
  billItems,
  onNewBill,
  storeName = 'StoreLite IMS',
}: InvoiceViewProps) {
  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  if (!bill) {
    return null;
  }

  const subtotal = billItems.reduce((sum, item) => {
    const lineTotal = item.line_total || item.quantity * item.unit_price;
    return sum + lineTotal;
  }, 0);

  const total = subtotal;

  return (
    <div className="space-y-6">
      {/* Invoice Card */}
      <div className="bg-white rounded-lg shadow-md p-8">
        {/* Header */}
        <div className="text-center mb-8 pb-8 border-b-2 border-gray-300">
          <h1 className="text-3xl font-bold text-gray-900">{storeName}</h1>
          <p className="text-gray-600 mt-2">Invoice / Receipt</p>
        </div>

        {/* Bill Details */}
        <div className="grid grid-cols-2 gap-8 mb-8">
          <div>
            <p className="text-sm text-gray-600">Invoice #</p>
            <p className="text-xl font-bold text-gray-900">{bill.id}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Date & Time</p>
            <p className="text-xl font-bold text-gray-900">
              {new Date(bill.created_at).toLocaleDateString('en-IN')}
            </p>
            <p className="text-sm text-gray-600">
              {new Date(bill.created_at).toLocaleTimeString('en-IN')}
            </p>
          </div>
        </div>

        {/* Customer */}
        {bill.customer_name && (
          <div className="mb-8 pb-8 border-b border-gray-200">
            <p className="text-sm text-gray-600">Customer</p>
            <p className="text-lg font-semibold text-gray-900">{bill.customer_name}</p>
          </div>
        )}

        {/* Items Table */}
        <div className="mb-8">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-gray-300">
                <th className="text-left py-2 font-bold text-gray-900">Item Name</th>
                <th className="text-center py-2 font-bold text-gray-900">Unit</th>
                <th className="text-right py-2 font-bold text-gray-900">Qty</th>
                <th className="text-right py-2 font-bold text-gray-900">Price</th>
                <th className="text-right py-2 font-bold text-gray-900">Total</th>
              </tr>
            </thead>
            <tbody>
              {billItems.map((item, index) => {
                const unitPrice = parseFloat(item.unit_price as any) || 0;
                const lineTotal = item.line_total || item.quantity * unitPrice;
                return (
                  <tr key={index} className="border-b border-gray-200">
                    <td className="py-2 text-gray-900">{item.item_name}</td>
                    <td className="text-center py-2 text-gray-600">{item.unit || '-'}</td>
                    <td className="text-right py-2 text-gray-900">{item.quantity}</td>
                    <td className="text-right py-2 text-gray-900">
                      ₹{unitPrice.toFixed(2)}
                    </td>
                    <td className="text-right py-2 font-semibold text-gray-900">
                      ₹{(parseFloat(lineTotal as any) || 0).toFixed(2)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="mb-8 pb-8 border-t-2 border-gray-300 space-y-2">
          <div className="flex justify-between text-lg">
            <span className="text-gray-700">Subtotal:</span>
            <span className="font-semibold text-gray-900">₹{subtotal.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-2xl pt-4">
            <span className="font-bold text-gray-900">Grand Total:</span>
            <span className="font-bold text-primary">₹{total.toFixed(2)}</span>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-600 pt-8 border-t border-gray-200">
          <p>Thank you for your purchase!</p>
          <p className="mt-2">Please keep this receipt for your records</p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4 no-print">
        <button
          onClick={handlePrint}
          className="flex-1 px-4 py-3 bg-primary text-white font-bold rounded-md hover:bg-opacity-90 transition-colors"
        >
          🖨️ Print Invoice
        </button>
        {onNewBill && (
          <button
            onClick={onNewBill}
            className="flex-1 px-4 py-3 bg-gray-200 text-gray-900 font-bold rounded-md hover:bg-gray-300 transition-colors"
          >
            ➕ New Bill
          </button>
        )}
      </div>
    </div>
  );
}
