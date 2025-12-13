/**
 * Application constants and configuration
 */

// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000');
export const MAX_RETRIES = parseInt(process.env.NEXT_PUBLIC_MAX_RETRIES || '3');
export const RETRY_INITIAL_DELAY = 1000; // 1 second
export const RETRY_BACKOFF_MULTIPLIER = 2; // Exponential backoff
export const RETRY_MAX_DELAY = 10000; // 10 seconds

// Stock Monitoring
export const STOCK_MONITOR_INTERVAL = parseInt(process.env.NEXT_PUBLIC_STOCK_MONITOR_INTERVAL || '10000');

// Categories (must match backend VALID_CATEGORIES in app/schemas.py)
export const CATEGORIES = [
  'Grocery',
  'Beauty',
  'Garments',
  'Utilities',
];

// Item units
export const UNITS = [
  'kg',
  'lbs',
  'pcs',
  'ltr',
  'ml',
  'box',
  'pack',
  'dozen',
  'meter',
  'cm',
];

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
};

// Error Codes from Backend (for mapping)
export const ERROR_CODES = {
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INSUFFICIENT_STOCK: 'INSUFFICIENT_STOCK',
  ITEM_NOT_FOUND: 'ITEM_NOT_FOUND',
  SERVER_ERROR: 'SERVER_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT: 'TIMEOUT',
  UNKNOWN: 'UNKNOWN',
};

// Routes
export const ROUTES = {
  HOME: '/',
  ADMIN: '/admin',
  POS: '/pos',
  ANALYTICS: '/analytics',
  DB_CONNECT: '/db-connect',
};

// API Endpoints
export const API_ENDPOINTS = {
  ITEMS: '/items',
  ITEM_BY_ID: (id: number) => `/items/${id}`,
  BILLS: '/bills',
  BILL_BY_ID: (id: number) => `/bills/${id}`,
};

// Toast Messages Duration (ms)
export const TOAST_DURATION = 3000;

// Debounce Delay (ms)
export const SEARCH_DEBOUNCE_DELAY = 300;

// Form Validation Rules
export const VALIDATION_RULES = {
  ITEM_NAME_MIN_LENGTH: 1,
  ITEM_NAME_MAX_LENGTH: 255,
  UNIT_PRICE_MIN: 0.01,
  UNIT_PRICE_MAX: 1000000,
  STOCK_QTY_MIN: 0,
  STOCK_QTY_MAX: 999999,
  CUSTOMER_NAME_MAX_LENGTH: 255,
};

// Performance Metrics (for monitoring)
export const PERFORMANCE_TARGETS = {
  PAGE_LOAD_MS: 3000,
  SEARCH_FILTER_MS: 1000,
  BILL_CALCULATION_MS: 100,
  API_RESPONSE_MS: 5000,
};

// Application Metadata
export const APP_METADATA = {
  NAME: 'StoreLite IMS',
  SUBTITLE: 'Inventory & Billing System',
  VERSION: '3.0.0',
  DESCRIPTION: 'Modern inventory management and point-of-sale system',
};
