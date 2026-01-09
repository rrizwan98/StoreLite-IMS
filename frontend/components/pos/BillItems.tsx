/**
 * Bill Items Component (FR-008)
 * Displays items in the current bill
 * Shows item details, quantity, and line total
 * Allows editing quantity and removing items (from US5)
 */

'use client';

import { BillItem } from '@/lib/types';

export interface BillItemsProps {
  items: BillItem[];
  onUpdateQuantity?: (index: number, quantity: number) => void;
  onRemoveItem?: (index: number) => void;
}

export default function BillItems({
  items,
  onUpdateQuantity,
  onRemoveItem,
}: BillItemsProps) {
  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 sm:p-8 text-center">
        <div className="text-4xl mb-3">🛒</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">No items in bill yet</h3>
        <p className="text-gray-600 text-sm sm:text-base">Search and add items from the list above</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Mobile Card View */}
      <div className="sm:hidden">
        {items.map((item, index) => (
          <div key={index} className="p-4 border-b border-gray-200 last:border-b-0">
            <div className="flex justify-between items-start mb-2">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-gray-900 truncate">{item.item_name}</h4>
                <p className="text-xs text-gray-500">{item.unit || '-'} • ₹{(parseFloat(item.unit_price as any) || 0).toFixed(2)}</p>
              </div>
              {onRemoveItem && (
                <button
                  onClick={() => onRemoveItem(index)}
                  className="ml-2 px-2 py-1 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
                >
                  Remove
                </button>
              )}
            </div>
            <div className="flex items-center justify-between mt-3">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Qty:</span>
                {onUpdateQuantity ? (
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min="1"
                      max={Math.floor(parseFloat(item.stock_qty as any) || 0)}
                      value={item.quantity}
                      onChange={(e) => {
                        const newQty = parseInt(e.target.value) || 1;
                        const maxQty = Math.floor(parseFloat(item.stock_qty as any) || 0);
                        if (newQty > maxQty) return;
                        onUpdateQuantity(index, newQty);
                      }}
                      className="w-14 px-2 py-1 border border-gray-300 rounded text-center text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                    {item.stock_qty !== undefined && (
                      <span className="text-xs text-gray-400">/{Math.floor(parseFloat(item.stock_qty as any) || 0)}</span>
                    )}
                  </div>
                ) : (
                  <span className="text-sm font-medium">{item.quantity}</span>
                )}
              </div>
              <div className="text-right">
                <span className="text-sm font-semibold text-gray-900">
                  ₹{((item.line_total || 0) || item.quantity * parseFloat(item.unit_price as any)).toFixed(2)}
                </span>
              </div>
            </div>
            {item.quantity > parseFloat(item.stock_qty as any || 0) && (
              <span className="text-xs text-error font-medium mt-1 block">⚠️ Exceeds stock</span>
            )}
          </div>
        ))}
      </div>

      {/* Desktop Table View */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-100 border-b border-gray-300">
              <th className="px-4 lg:px-6 py-3 text-left text-sm font-semibold text-gray-900">
                Item Name
              </th>
              <th className="px-4 lg:px-6 py-3 text-left text-sm font-semibold text-gray-900">Unit</th>
              <th className="px-4 lg:px-6 py-3 text-right text-sm font-semibold text-gray-900">Price</th>
              <th className="px-4 lg:px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Quantity
              </th>
              <th className="px-4 lg:px-6 py-3 text-right text-sm font-semibold text-gray-900">
                Line Total
              </th>
              <th className="px-4 lg:px-6 py-3 text-center text-sm font-semibold text-gray-900">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr
                key={index}
                className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-900 font-medium">{item.item_name}</td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-600">{item.unit || '-'}</td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-900 text-right font-medium">
                  ₹{(parseFloat(item.unit_price as any) || 0).toFixed(2)}
                </td>
                <td className="px-4 lg:px-6 py-4 text-center">
                  {onUpdateQuantity ? (
                    <div className="flex flex-col items-center gap-1">
                      <input
                        type="number"
                        min="1"
                        max={Math.floor(parseFloat(item.stock_qty as any) || 0)}
                        value={item.quantity}
                        onChange={(e) => {
                          const newQty = parseInt(e.target.value) || 1;
                          const maxQty = Math.floor(parseFloat(item.stock_qty as any) || 0);

                          // Only allow quantity up to available stock
                          if (newQty > maxQty) {
                            return; // Reject if exceeds stock
                          }

                          onUpdateQuantity(index, newQty);
                        }}
                        className="w-16 px-2 py-1 border border-gray-300 rounded-md text-center text-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                      />
                      {item.stock_qty !== undefined && (
                        <span className="text-xs text-gray-500">
                          max: {Math.floor(parseFloat(item.stock_qty as any) || 0)}
                        </span>
                      )}
                      {item.quantity > parseFloat(item.stock_qty as any || 0) && (
                        <span className="text-xs text-error font-medium">⚠️ Exceeds stock</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-sm font-medium">{item.quantity}</span>
                  )}
                </td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-900 text-right font-medium">
                  ₹{((item.line_total || 0) || item.quantity * parseFloat(item.unit_price as any)).toFixed(2)}
                </td>
                <td className="px-4 lg:px-6 py-4 text-center">
                  {onRemoveItem && (
                    <button
                      onClick={() => onRemoveItem(index)}
                      className="px-3 py-1 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
                    >
                      Remove
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer - Summary */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 sm:px-6 py-3 text-sm text-gray-600">
        <p>
          <strong>{items.length}</strong> item{items.length !== 1 ? 's' : ''} in bill
        </p>
      </div>
    </div>
  );
}
