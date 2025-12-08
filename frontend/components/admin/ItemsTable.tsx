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
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-4xl mb-3">📭</div>
        <h3 className="text-lg font-semibold text-gray-900 mb-1">No items found</h3>
        <p className="text-gray-600">Start by adding your first inventory item using the form above.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-100 border-b border-gray-300">
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Name</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Category</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Unit</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Price</th>
              <th className="px-6 py-3 text-right text-sm font-semibold text-gray-900">Stock</th>
              <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item, index) => (
              <tr
                key={item.id || index}
                className="border-b border-gray-200 hover:bg-gray-50 transition-colors"
              >
                <td className="px-6 py-4 text-sm text-gray-900 font-medium">{item.name}</td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  <span className="inline-block bg-gray-100 px-2 py-1 rounded text-xs font-medium">
                    {item.category.charAt(0).toUpperCase() + item.category.slice(1)}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">{item.unit}</td>
                <td className="px-6 py-4 text-sm text-gray-900 text-right font-medium">
                  ₹{(item.unit_price || 0).toFixed(2)}
                </td>
                <td className="px-6 py-4 text-sm text-right">
                  {item.stock_qty === 0 ? (
                    <span className="text-error font-medium">Out of Stock</span>
                  ) : item.stock_qty < 10 ? (
                    <span className="text-warning font-medium">{item.stock_qty} (Low)</span>
                  ) : (
                    <span className="text-success font-medium">{item.stock_qty}</span>
                  )}
                </td>
                <td className="px-6 py-4 text-sm text-center">
                  <div className="flex items-center justify-center gap-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(item)}
                        className="px-3 py-1 bg-primary text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
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
                        className="px-3 py-1 bg-error text-white text-xs font-medium rounded hover:bg-opacity-90 transition-colors"
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
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-3 text-sm text-gray-600">
        <p>
          Showing <strong>{items.length}</strong> item{items.length !== 1 ? 's' : ''} in inventory
        </p>
      </div>
    </div>
  );
}
