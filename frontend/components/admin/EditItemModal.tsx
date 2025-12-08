/**
 * Edit Item Modal Component (FR-005, FR-017, FR-018, FR-020)
 * Modal form for editing item price and stock quantity
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { Item, ItemForm, ValidationError } from '@/lib/types';
import { validateItem, isValid } from '@/lib/validation';
import { CATEGORIES, UNITS } from '@/lib/constants';
import { api } from '@/lib/api';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import ErrorMessage from '@/components/shared/ErrorMessage';

export interface EditItemModalProps {
  item: Item | null;
  onSave?: (updatedItem: Item) => void;
  onCancel?: () => void;
}

export default function EditItemModal({ item, onSave, onCancel }: EditItemModalProps) {
  const [formData, setFormData] = useState<ItemForm>({
    name: '',
    category: '',
    unit: '',
    unit_price: 0,
    stock_qty: 0,
  });

  const [errors, setErrors] = useState<ValidationError>({});
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // Initialize form when item changes
  useEffect(() => {
    if (item) {
      setFormData({
        name: item.name,
        category: item.category,
        unit: item.unit,
        unit_price: item.unit_price,
        stock_qty: item.stock_qty,
      });
      setErrors({});
      setApiError(null);
    }
  }, [item]);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({
        ...prev,
        [name]: name === 'unit_price' || name === 'stock_qty' ? parseFloat(value) || 0 : value,
      }));
      // Clear error for this field
      if (errors[name]) {
        setErrors((prev) => {
          const updated = { ...prev };
          delete updated[name];
          return updated;
        });
      }
    },
    [errors]
  );

  const handleSave = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      if (!item) return;

      setApiError(null);

      // Validate form
      const validationErrors = validateItem(formData);
      if (!isValid(validationErrors)) {
        setErrors(validationErrors);
        return;
      }

      // Submit to API
      try {
        setLoading(true);
        const updatedItem = await api.updateItem(item.id, formData);

        // Success
        setErrors({});
        if (onSave) {
          onSave(updatedItem);
        }
        // Close modal
        if (onCancel) {
          onCancel();
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to update item';
        setApiError(errorMessage);
        setLoading(false);
      }
    },
    [item, formData, onSave, onCancel]
  );

  const handleRetry = useCallback(() => {
    setApiError(null);
    handleSave(new Event('submit', { bubbles: true }) as any);
  }, [handleSave]);

  // Don't render if no item selected
  if (!item) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="bg-gray-100 border-b border-gray-200 px-6 py-4">
          <h2 className="text-xl font-bold text-gray-900">Edit Item</h2>
          <p className="text-sm text-gray-600 mt-1">{item.name}</p>
        </div>

        {/* Body */}
        <div className="p-6">
          {apiError && (
            <div className="mb-4">
              <ErrorMessage message={apiError} onRetry={handleRetry} showRetry />
            </div>
          )}

          <form onSubmit={handleSave} className="space-y-4">
            {/* Item Name - Read Only */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Item Name</label>
              <input
                type="text"
                value={formData.name}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Read-only field</p>
            </div>

            {/* Category - Read Only */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <input
                type="text"
                value={formData.category.charAt(0).toUpperCase() + formData.category.slice(1)}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Read-only field</p>
            </div>

            {/* Unit - Read Only */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
              <input
                type="text"
                value={formData.unit}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-600 cursor-not-allowed"
              />
              <p className="text-xs text-gray-500 mt-1">Read-only field</p>
            </div>

            {/* Unit Price - Editable */}
            <div>
              <label htmlFor="unit_price" className="block text-sm font-medium text-gray-700 mb-1">
                Unit Price *
              </label>
              <input
                type="number"
                id="unit_price"
                name="unit_price"
                value={formData.unit_price === 0 ? '' : formData.unit_price}
                onChange={handleChange}
                placeholder="0.00"
                step="0.01"
                min="0.01"
                disabled={loading}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                  errors.unit_price ? 'border-error' : 'border-gray-300'
                }`}
              />
              {errors.unit_price && <p className="text-error text-sm mt-1">{errors.unit_price}</p>}
            </div>

            {/* Stock Quantity - Editable */}
            <div>
              <label htmlFor="stock_qty" className="block text-sm font-medium text-gray-700 mb-1">
                Stock Quantity *
              </label>
              <input
                type="number"
                id="stock_qty"
                name="stock_qty"
                value={formData.stock_qty === 0 ? '' : formData.stock_qty}
                onChange={handleChange}
                placeholder="0"
                step="1"
                min="0"
                disabled={loading}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
                  errors.stock_qty ? 'border-error' : 'border-gray-300'
                }`}
              />
              {errors.stock_qty && <p className="text-error text-sm mt-1">{errors.stock_qty}</p>}
            </div>

            {/* Form Actions */}
            <div className="flex gap-2 pt-4">
              <button
                type="button"
                onClick={onCancel}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 px-4 py-2 bg-primary text-white rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span className="ml-2">Saving...</span>
                  </>
                ) : (
                  'Save Changes'
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
