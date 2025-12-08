/**
 * Type definitions for StoreLite IMS Frontend
 * All data structures used across the application
 */

// Item entity from backend
export interface Item {
  id: number;
  name: string;
  category: string;
  unit: string;
  unit_price: number;
  stock_qty: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

// Bill entity from backend
export interface Bill {
  id: number;
  customer_name?: string;
  store_name?: string;
  total_amount: number;
  created_at: string;
}

// Bill item (line item in a bill)
export interface BillItem {
  id?: number;
  bill_id?: number;
  item_id: number;
  item_name: string;
  unit?: string;
  unit_price: number;
  stock_qty?: number; // Original stock quantity from database (for validation)
  quantity: number;
  line_total?: number;
}

// Form data for adding/editing items
export interface ItemForm {
  name: string;
  category: string;
  unit: string;
  unit_price: number;
  stock_qty: number;
}

// Form data for creating bills
export interface BillForm {
  customer_name?: string;
  items: BillItem[];
}

// API error response
export interface APIError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

// API response wrapper (optional, for standardized responses)
export interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
}

// Validation error object
export interface ValidationError {
  [field: string]: string;
}

// Current bill state in POS
export interface CurrentBill {
  items: BillItem[];
  subtotal: number;
  total: number;
}

// Stock level warning
export interface StockWarning {
  itemId: number;
  itemName: string;
  currentStock: number;
  status: 'warning' | 'out-of-stock';
}

// Retry configuration
export interface RetryConfig {
  maxRetries: number;
  initialDelayMs: number;
  backoffMultiplier: number;
  maxDelayMs: number;
}

// API client configuration
export interface APIClientConfig {
  baseURL: string;
  timeout?: number;
  retryConfig?: RetryConfig;
}
