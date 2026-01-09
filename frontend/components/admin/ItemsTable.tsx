/**
 * Items Table Component (FR-003, FR-018)
 * Displays all inventory items in a sortable, pageable table
 * Shows name, category, unit, price, stock, and actions
 */

'use client';

import { Item } from '@/lib/types';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

export interface ItemsTableProps {
  items: Item[];
  loading?: boolean;
  onEdit?: (item: Item) => void;
  onDelete?: (item: Item) => void;
}

export default function ItemsTable({ items, loading = false, onEdit, onDelete }: ItemsTableProps) {
  if (loading) {
    return <LoadingSpinner message="Loading inventory..." />;
  }

  if (!items || items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 sm:p-8 text-center">
        <div className="text-4xl mb-3">📭</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">No items found</h3>
        <p className="text-gray-600 text-sm sm:text-base">Start by adding your first inventory item using the form above.</p>
      </div>
    );
  }

  // Helper to get stock status
  const getStockStatus = (stockQty: any) => {
    const qty = parseFloat(stockQty as any);
    if (qty <= 0) return { text: 'Out of Stock', className: 'text-error' };
    if (qty < 10) return { text: `${Math.floor(qty)} (Low)`, className: 'text-warning' };
    return { text: `${Math.floor(qty)}`, className: 'text-success' };
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      {/* Mobile Card View */}
      <div className="sm:hidden">
        {items.map((item, index) => {
          const stockStatus = getStockStatus(item.stock_qty);
          return (
            <div key={item.id || index} className="p-4 border-b border-gray-200 last:border-b-0">
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1 min-w-0">
                  <h4 className="font-medium text-gray-900 truncate">{item.name}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="inline-block bg-gray-100 px-2 py-0.5 rounded text-xs font-medium">
                      {item.category.charAt(0).toUpperCase() + item.category.slice(1)}
                    </span>
                    <span className="text-xs text-gray-500">{item.unit}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex items-center gap-4">
                  <div>
                    <span className="text-xs text-gray-500 block">Price</span>
                    <span className="text-sm font-medium">₹{(parseFloat(item.unit_price as any) || 0).toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-xs text-gray-500 block">Stock</span>
                    <span className={`text-sm font-medium ${stockStatus.className}`}>{stockStatus.text}</span>
                  </div>
                </div>
                <div className="flex gap-2">
                  {onEdit && (
                    <button
                      onClick={() => onEdit(item)}
                      className="px-3 py-1.5 bg-primary text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
                    >
                      Edit
                    </button>
                  )}
                  {onDelete && (
                    <button
                      onClick={() => {
                        if (window.confirm(`Are you sure you want to delete "${item.name}"?`)) {
                          onDelete(item);
                        }
                      }}
                      className="px-3 py-1.5 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Desktop Table View */}
      <div className="hidden sm:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-100 border-b border-gray-300">
              <th className="px-4 lg:px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
              <th className="px-4 lg:px-6 py-3 text-left text-sm font-semibold text-gray-900">Category</th>
              <th className="px-4 lg:px-6 py-3 text-left text-sm font-semibold text-gray-900">Unit</th>
              <th className="px-4 lg:px-6 py-3 text-right text-sm font-semibold text-gray-900">Price</th>
              <th className="px-4 lg:px-6 py-3 text-right text-sm font-semibold text-gray-900">Stock</th>
              <th className="px-4 lg:px-6 py-3 text-center text-sm font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr
                key={item.id || index}
                className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-900 font-medium">{item.name}</td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-600">
                  <span className="inline-block bg-gray-100 px-2 py-1 rounded text-xs font-medium">
                    {item.category.charAt(0).toUpperCase() + item.category.slice(1)}
                  </span>
                </td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-600">{item.unit}</td>
                <td className="px-4 lg:px-6 py-4 text-sm text-gray-900 text-right font-medium">
                  ₹{(parseFloat(item.unit_price as any) || 0).toFixed(2)}
                </td>
                <td className="px-4 lg:px-6 py-4 text-sm text-right">
                  {parseFloat(item.stock_qty as any) <= 0 ? (
                    <span className="text-error font-medium">Out of Stock</span>
                  ) : parseFloat(item.stock_qty as any) < 10 ? (
                    <span className="text-warning font-medium">{Math.floor(parseFloat(item.stock_qty as any))} (Low)</span>
                  ) : (
                    <span className="text-success font-medium">{Math.floor(parseFloat(item.stock_qty as any))}</span>
                  )}
                </td>
                <td className="px-4 lg:px-6 py-4 text-sm text-center">
                  <div className="flex items-center justify-center gap-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(item)}
                        className="px-3 py-1 bg-primary text-white text-xs font-medium rounded hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Edit
                      </button>
                    )}
                    {onDelete && (
                      <button
                        onClick={() => {
                          if (
                            window.confirm(
                              `Are you sure you want to delete "${item.name}"? This action cannot be undone.`
                            )
                          ) {
                            onDelete(item);
                          }
                        }}
                        className="px-3 py-1 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table Footer - Summary */}
      <div className="bg-gray-50 border-t border-gray-200 px-4 sm:px-6 py-3 text-sm text-gray-600">
        <p>
          Showing <strong>{items.length}</strong> item{items.length !== 1 ? 's' : ''} in inventory
        </p>
      </div>
    </div>
  );
}
