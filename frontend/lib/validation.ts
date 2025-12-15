/**
 * Client-side validation rules for forms
 * Validates before sending to API (FR-017)
 */

import { ItemForm, BillItem, ValidationError } from './types';
import { VALIDATION_RULES, CATEGORIES, UNITS } from './constants';

/**
 * Validate item form data (used in Add Item and Edit Item forms)
 * Returns object with field names as keys and error messages as values
 * Empty object means validation passed
 */
export const validateItem = (item: ItemForm): ValidationError => {
  const errors: ValidationError = {};

  // Validate name
  if (!item.name || item.name.trim().length === 0) {
    errors.name = 'Item name is required';
  } else if (item.name.length > VALIDATION_RULES.ITEM_NAME_MAX_LENGTH) {
    errors.name = `Item name must be ${VALIDATION_RULES.ITEM_NAME_MAX_LENGTH} characters or less`;
  }

  // Validate category
  if (!item.category || item.category.trim().length === 0) {
    errors.category = 'Category is required';
  } else if (!CATEGORIES.includes(item.category)) {
    errors.category = `Category must be one of: ${CATEGORIES.join(', ')}`;
  }

  // Validate unit
  if (!item.unit || item.unit.trim().length === 0) {
    errors.unit = 'Unit is required';
  } else if (!UNITS.includes(item.unit)) {
    errors.unit = `Unit must be one of: ${UNITS.join(', ')}`;
  }

  // Validate unit price
  if (item.unit_price === undefined || item.unit_price === null) {
    errors.unit_price = 'Unit price is required';
  } else if (typeof item.unit_price !== 'number') {
    errors.unit_price = 'Unit price must be a number';
  } else if (item.unit_price < VALIDATION_RULES.UNIT_PRICE_MIN) {
    errors.unit_price = `Unit price must be at least ${VALIDATION_RULES.UNIT_PRICE_MIN}`;
  } else if (item.unit_price > VALIDATION_RULES.UNIT_PRICE_MAX) {
    errors.unit_price = `Unit price must not exceed ${VALIDATION_RULES.UNIT_PRICE_MAX}`;
  }

  // Validate stock quantity
  if (item.stock_qty === undefined || item.stock_qty === null) {
    errors.stock_qty = 'Stock quantity is required';
  } else if (typeof item.stock_qty !== 'number') {
    errors.stock_qty = 'Stock quantity must be a number';
  } else if (item.stock_qty < VALIDATION_RULES.STOCK_QTY_MIN) {
    errors.stock_qty = `Stock quantity cannot be negative`;
  } else if (item.stock_qty > VALIDATION_RULES.STOCK_QTY_MAX) {
    errors.stock_qty = `Stock quantity must not exceed ${VALIDATION_RULES.STOCK_QTY_MAX}`;
  }

  return errors;
};

/**
 * Validate bill item (line item in a bill)
 * Checks quantity against available stock
 */
export const validateBillItem = (item: BillItem, availableStock: number): ValidationError => {
  const errors: ValidationError = {};

  // Validate quantity
  if (!item.quantity || item.quantity <= 0) {
    errors.quantity = 'Quantity must be greater than 0';
  } else if (item.quantity > availableStock) {
    errors.quantity = `Cannot add more than ${availableStock} units (available stock)`;
  }

  return errors;
};

/**
 * Validate bill before generation
 * Checks that bill has items and all items have valid quantities
 */
export const validateBillForGeneration = (items: BillItem[]): ValidationError => {
  const errors: ValidationError = {};

  if (!items || items.length === 0) {
    errors.items = 'Bill must contain at least one item';
  } else {
    // Check each item has valid quantity
    const invalidItems = items.filter((item) => !item.quantity || item.quantity <= 0);
    if (invalidItems.length > 0) {
      errors.items = 'All items must have quantity greater than 0';
    }
  }

  return errors;
};

/**
 * Validate search input (prevent malicious input)
 * Simple trimming and length check
 */
export const validateSearchInput = (input: string): ValidationError => {
  const errors: ValidationError = {};

  if (input && input.length > 255) {
    errors.search = 'Search input too long';
  }

  return errors;
};

/**
 * Check if there are any validation errors
 * Returns true if errors object is empty
 */
export const isValid = (errors: ValidationError): boolean => {
  return Object.keys(errors).length === 0;
};

/**
 * Get first error message (for simple toast notifications)
 */
export const getFirstErrorMessage = (errors: ValidationError): string | null => {
  const keys = Object.keys(errors);
  return keys.length > 0 ? errors[keys[0]] : null;
};

/**
 * Format price for display and input
 */
export const formatPrice = (price: number): string => {
  return `$${price.toFixed(2)}`;
};

/**
 * Parse price from input (remove $ and commas)
 */
export const parsePrice = (input: string): number | null => {
  const cleaned = input.replace(/[$,]/g, '');
  const parsed = parseFloat(cleaned);
  return isNaN(parsed) ? null : parsed;
};

/**
 * Round to 2 decimal places (for currency)
 */
export const roundPrice = (price: number): number => {
  return Math.round(price * 100) / 100;
};
