/**
 * Add Item Form Component (FR-002, FR-017, FR-018)
 * Allows admin users to add new inventory items with client-side validation
 */

'use client';

import { useState, useCallback } from 'react';
import { Item, ItemForm, ValidationError } from '@/lib/types';
import { validateItem, isValid, getFirstErrorMessage } from '@/lib/validation';
import { CATEGORIES, UNITS } from '@/lib/constants';
import { api } from '@/lib/api';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import ErrorMessage from '@/components/shared/ErrorMessage';
import SuccessToast from '@/components/shared/SuccessToast';

export interface AddItemFormProps {
  onItemAdded?: (item: Item) => void;
}

export default function AddItemForm({ onItemAdded }: AddItemFormProps) {
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
  const [success, setSuccess] = useState(false);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const { name, value } = e.target;
      setFormData((prev) => ({
        ...prev,
        [name]: name === 'unit_price' || name === 'stock_qty' ? parseFloat(value) || 0 : value,
      }));
      // Clear error for this field when user starts editing
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

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setApiError(null);
      setSuccess(false);

      // Validate form
      const validationErrors = validateItem(formData);
      if (!isValid(validationErrors)) {
        setErrors(validationErrors);
        return;
      }

      // Submit to API
      try {
        setLoading(true);
        const newItem = await api.addItem(formData);

        // Success
        setSuccess(true);
        setErrors({});
        setFormData({
          name: '',
          category: '',
          unit: '',
          unit_price: 0,
          stock_qty: 0,
        });

        // Callback to parent
        if (onItemAdded) {
          onItemAdded(newItem);
        }

        // Clear success message after 3 seconds
        setTimeout(() => {
          setSuccess(false);
        }, 3000);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to add item';
        setApiError(errorMessage);
        setLoading(false);
      }
    },
    [formData, onItemAdded]
  );

  const handleRetry = useCallback(() => {
    setApiError(null);
    handleSubmit(new Event('submit', { bubbles: true }) as any);
  }, [handleSubmit]);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-2xl font-bold mb-4">Add New Item</h2>

      {apiError && <ErrorMessage message={apiError} onRetry={handleRetry} showRetry />}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Item Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            Item Name *
          </label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="Enter item name"
            disabled={loading}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
              errors.name ? 'border-error' : 'border-gray-300'
            }`}
          />
          {errors.name && <p className="text-error text-sm mt-1">{errors.name}</p>}
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
            Category *
          </label>
          <select
            id="category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            disabled={loading}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
              errors.category ? 'border-error' : 'border-gray-300'
            }`}
          >
            <option value="">Select a category</option>
            {CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat.charAt(0).toUpperCase() + cat.slice(1)}
              </option>
            ))}
          </select>
          {errors.category && <p className="text-error text-sm mt-1">{errors.category}</p>}
        </div>

        {/* Unit */}
        <div>
          <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">
            Unit *
          </label>
          <select
            id="unit"
            name="unit"
            value={formData.unit}
            onChange={handleChange}
            disabled={loading}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent ${
              errors.unit ? 'border-error' : 'border-gray-300'
            }`}
          >
            <option value="">Select a unit</option>
            {UNITS.map((unit) => (
              <option key={unit} value={unit}>
                {unit}
              </option>
            ))}
          </select>
          {errors.unit && <p className="text-error text-sm mt-1">{errors.unit}</p>}
        </div>

        {/* Unit Price */}
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

        {/* Stock Quantity */}
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

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-white py-2 rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
        >
          {loading ? (
            <>
              <LoadingSpinner size="sm" />
              <span className="ml-2">Adding...</span>
            </>
          ) : (
            'Add Item'
          )}
        </button>
      </form>

      {/* Success Toast */}
      {success && (
        <SuccessToast
          message="Item added successfully!"
          duration={3000}
          onClose={() => setSuccess(false)}
        />
      )}
    </div>
  );
}
