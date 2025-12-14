/**
 * API Client with auto-retry logic (FR-020)
 * Handles all HTTP requests to FastAPI backend
 * Implements 3-attempt retry with exponential backoff
 */

import axios, { AxiosInstance, AxiosError, AxiosRequestConfig } from 'axios';
import { Item, Bill, BillItem, APIError, ValidationError } from './types';
import {
  API_BASE_URL,
  API_TIMEOUT,
  MAX_RETRIES,
  RETRY_INITIAL_DELAY,
  RETRY_BACKOFF_MULTIPLIER,
  RETRY_MAX_DELAY,
  ERROR_CODES,
  HTTP_STATUS,
} from './constants';
import { getAccessToken } from './auth-api';

/**
 * Maps backend error codes and HTTP status to user-friendly messages
 * (FR-019 - user-friendly error handling)
 */
export const ERROR_MESSAGES: Record<string, string> = {
  [ERROR_CODES.VALIDATION_ERROR]: 'Please check your input and try again',
  [ERROR_CODES.INSUFFICIENT_STOCK]: 'Not enough stock available for this item',
  [ERROR_CODES.ITEM_NOT_FOUND]: 'Item no longer exists',
  [ERROR_CODES.SERVER_ERROR]: 'System error, please try again later',
  [ERROR_CODES.NETWORK_ERROR]: 'Connection lost, retrying...',
  [ERROR_CODES.TIMEOUT]: 'Request timed out, please try again',
  [ERROR_CODES.UNKNOWN]: 'Something went wrong, please try again',
};

/**
 * Map backend error code or HTTP status to user-friendly message
 */
export const mapError = (errorCode: string | number): string => {
  if (typeof errorCode === 'number') {
    // Map HTTP status codes
    switch (errorCode) {
      case HTTP_STATUS.BAD_REQUEST:
        return ERROR_MESSAGES[ERROR_CODES.VALIDATION_ERROR];
      case HTTP_STATUS.NOT_FOUND:
        return ERROR_MESSAGES[ERROR_CODES.ITEM_NOT_FOUND];
      case HTTP_STATUS.CONFLICT:
        return ERROR_MESSAGES[ERROR_CODES.INSUFFICIENT_STOCK];
      case HTTP_STATUS.SERVER_ERROR:
      case HTTP_STATUS.SERVICE_UNAVAILABLE:
        return ERROR_MESSAGES[ERROR_CODES.SERVER_ERROR];
      default:
        return ERROR_MESSAGES[ERROR_CODES.UNKNOWN];
    }
  }

  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES[ERROR_CODES.UNKNOWN];
};

/**
 * Retry status callback type
 * Called on each retry attempt to update UI
 */
export type RetryStatusCallback = (attempt: number, maxRetries: number, error: Error) => void;

/**
 * API Client class with retry logic
 */
export class APIClient {
  private axiosInstance: AxiosInstance;
  private retryStatusCallback?: RetryStatusCallback;

  constructor(baseURL: string = API_BASE_URL, retryCallback?: RetryStatusCallback) {
    this.axiosInstance = axios.create({
      baseURL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    this.retryStatusCallback = retryCallback;

    // Add auth token interceptor - automatically include token in every request
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Make HTTP request with automatic retry on failure
   * Implements exponential backoff strategy
   */
  async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    maxRetries: number = MAX_RETRIES
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const config: AxiosRequestConfig = {
          method,
          url: endpoint,
        };

        if (data) {
          config.data = data;
        }

        const response = await this.axiosInstance.request<T>(config);
        return response.data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        // If this is the last attempt, throw the error
        if (attempt === maxRetries - 1) {
          break;
        }

        // Calculate exponential backoff delay
        const backoffDelay = Math.min(
          RETRY_INITIAL_DELAY * Math.pow(RETRY_BACKOFF_MULTIPLIER, attempt),
          RETRY_MAX_DELAY
        );

        // Call retry callback if provided (for UI feedback)
        if (this.retryStatusCallback) {
          this.retryStatusCallback(attempt + 1, maxRetries, lastError);
        }

        // Wait before retrying
        await new Promise((resolve) => setTimeout(resolve, backoffDelay));
      }
    }

    throw lastError || new Error('Request failed');
  }

  /**
   * GET /api/items - Fetch all items with optional filters
   */
  async getItems(filters?: { name?: string; category?: string }): Promise<Item[]> {
    const params = new URLSearchParams();
    if (filters?.name) params.append('name', filters.name);
    if (filters?.category) params.append('category', filters.category);

    const endpoint = `/api/items${params.toString() ? `?${params.toString()}` : ''}`;
    return this.request<Item[]>('GET', endpoint);
  }

  /**
   * GET /api/items/{id} - Fetch single item by ID
   */
  async getItem(id: number): Promise<Item> {
    return this.request<Item>('GET', `/api/items/${id}`);
  }

  /**
   * POST /api/items - Create new item (FR-002)
   */
  async addItem(item: {
    name: string;
    category: string;
    unit: string;
    unit_price: number;
    stock_qty: number;
  }): Promise<Item> {
    return this.request<Item>('POST', '/api/items', item);
  }

  /**
   * PUT /api/items/{id} - Update existing item (FR-005)
   */
  async updateItem(
    id: number,
    item: Partial<{
      name: string;
      category: string;
      unit: string;
      unit_price: number;
      stock_qty: number;
    }>
  ): Promise<Item> {
    return this.request<Item>('PUT', `/api/items/${id}`, item);
  }

  /**
   * POST /api/bills - Create bill and deduct stock (FR-012, FR-022)
   * Validates stock at generation time
   */
  async createBill(billData: {
    customer_name?: string;
    items: Array<{ item_id: number; quantity: number }>;
  }): Promise<Bill> {
    return this.request<Bill>('POST', '/api/bills', billData);
  }

  /**
   * GET /api/bills/{id} - Fetch bill for invoice (FR-013)
   */
  async getBill(id: number): Promise<Bill & { items?: BillItem[] }> {
    return this.request<Bill & { items?: BillItem[] }>('GET', `/api/bills/${id}`);
  }

  /**
   * Set retry status callback for UI feedback
   */
  setRetryStatusCallback(callback: RetryStatusCallback): void {
    this.retryStatusCallback = callback;
  }

  /**
   * Clear retry callback
   */
  clearRetryStatusCallback(): void {
    this.retryStatusCallback = undefined;
  }
}

/**
 * Singleton instance of API client
 * Used throughout the application
 */
let apiClientInstance: APIClient | null = null;

/**
 * Get or create API client instance
 */
export const getApiClient = (retryCallback?: RetryStatusCallback): APIClient => {
  if (!apiClientInstance) {
    apiClientInstance = new APIClient(API_BASE_URL, retryCallback);
  }
  return apiClientInstance;
};

/**
 * Default API client export
 */
export const api = getApiClient();

/**
 * Error extraction helper
 * Extracts meaningful error message from Axios error
 */
export const extractErrorMessage = (error: unknown): string => {
  if (error instanceof AxiosError) {
    // Try to get backend error message
    if (error.response?.data) {
      const data = error.response.data as any;
      if (typeof data === 'object' && 'detail' in data) {
        return data.detail;
      }
      if (typeof data === 'object' && 'message' in data) {
        return data.message;
      }
    }

    // Map HTTP status code
    if (error.response?.status) {
      return mapError(error.response.status);
    }

    // Network error
    if (!error.response) {
      return mapError(ERROR_CODES.NETWORK_ERROR);
    }

    // Timeout
    if (error.code === 'ECONNABORTED') {
      return mapError(ERROR_CODES.TIMEOUT);
    }
  }

  return mapError(ERROR_CODES.UNKNOWN);
};
