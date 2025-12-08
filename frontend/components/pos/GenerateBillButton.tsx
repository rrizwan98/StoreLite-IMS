/**
 * Generate Bill Button Component (FR-012, FR-018, FR-020)
 * Validates bill and calls API to create bill record
 * Handles errors with retry capability
 */

'use client';

import { useCallback, useState } from 'react';
import { BillItem } from '@/lib/types';
import { validateBillBeforeSubmission } from '@/lib/calculations';
import { api } from '@/lib/api';
import LoadingSpinner from '@/components/shared/LoadingSpinner';
import ErrorMessage from '@/components/shared/ErrorMessage';

export interface GenerateBillButtonProps {
  billItems: BillItem[];
  onSuccess?: (billId: number) => void;
  customerName?: string;
}

export default function GenerateBillButton({
  billItems,
  onSuccess,
  customerName,
}: GenerateBillButtonProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateBill = useCallback(async () => {
    setError(null);

    // Validate bill
    const validationError = validateBillBeforeSubmission(billItems);
    if (validationError) {
      setError(validationError);
      return;
    }

    // Create bill
    try {
      setLoading(true);
      const bill = await api.createBill({
        customer_name: customerName,
        items: billItems.map((item) => ({
          item_id: item.item_id,
          quantity: item.quantity,
        })),
      });

      // Success
      if (onSuccess) {
        onSuccess(bill.id);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate bill';
      setError(errorMessage);
      setLoading(false);
    }
  }, [billItems, customerName, onSuccess]);

  const handleRetry = useCallback(() => {
    handleGenerateBill();
  }, [handleGenerateBill]);

  const isDisabled = billItems.length === 0 || loading;

  return (
    <div className="space-y-4">
      {error && (
        <ErrorMessage message={error} onRetry={handleRetry} showRetry />
      )}

      <button
        onClick={handleGenerateBill}
        disabled={isDisabled}
        className="w-full px-4 py-3 bg-primary text-white font-bold rounded-md hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <LoadingSpinner size="sm" />
            <span>Generating Bill...</span>
          </>
        ) : (
          <>
            <span>💳</span>
            <span>Generate Bill</span>
          </>
        )}
      </button>

      {billItems.length === 0 && (
        <p className="text-sm text-gray-600 text-center">
          Add items to bill before generating
        </p>
      )}
    </div>
  );
}
