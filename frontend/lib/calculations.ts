/**
 * Bill Calculation Utilities (FR-011)
 * Functions for calculating line totals, subtotals, and grand totals
 */

import { BillItem } from './types';

/**
 * Calculate line total for a bill item
 * @param unitPrice - Price per unit
 * @param quantity - Quantity ordered
 * @returns Line total (unitPrice * quantity)
 */
export const calculateLineTotal = (unitPrice: number, quantity: number): number => {
  return unitPrice * quantity;
};

/**
 * Calculate subtotal from all bill items
 * @param billItems - Array of bill items
 * @returns Sum of all line totals
 */
export const calculateSubtotal = (billItems: BillItem[]): number => {
  return billItems.reduce((sum, item) => {
    const lineTotal = item.line_total || calculateLineTotal(item.unit_price, item.quantity);
    return sum + lineTotal;
  }, 0);
};

/**
 * Calculate grand total (currently same as subtotal - no taxes/discounts in Phase 3)
 * @param subtotal - Bill subtotal
 * @returns Grand total
 */
export const calculateGrandTotal = (subtotal: number): number => {
  // Phase 3: No taxes, discounts, or other charges
  // This function exists as placeholder for future tax/discount logic
  return subtotal;
};

/**
 * Format currency for display
 * @param amount - Amount to format
 * @param currency - Currency code (default: INR)
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number, currency: string = 'INR'): string => {
  const formatter = new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return formatter.format(amount);
};

/**
 * Validate bill before submission
 * @param billItems - Items in bill
 * @returns Error message if invalid, null if valid
 */
export const validateBillBeforeSubmission = (billItems: BillItem[]): string | null => {
  if (!billItems || billItems.length === 0) {
    return 'Bill must contain at least one item';
  }

  for (const item of billItems) {
    if (item.quantity <= 0) {
      return `Invalid quantity for item "${item.item_name}"`;
    }
    if (item.unit_price < 0) {
      return `Invalid price for item "${item.item_name}"`;
    }
  }

  return null;
};
