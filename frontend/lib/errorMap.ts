/**
 * Error Message Mapping Service (FR-019)
 * Maps backend error codes to user-friendly messages
 * Technical details logged for debugging, not exposed to user
 */

/**
 * User-friendly error messages
 * Maps backend error codes to simple, actionable messages
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Validation errors
  VALIDATION_ERROR: 'Please check your input and try again',
  INVALID_INPUT: 'One or more fields have invalid values',
  MISSING_REQUIRED_FIELD: 'Please fill in all required fields',

  // Item errors
  ITEM_NOT_FOUND: 'Item no longer exists or was deleted',
  ITEM_ALREADY_EXISTS: 'An item with this name already exists',
  INVALID_ITEM_DATA: 'Item data is invalid, please check the form',

  // Stock errors
  INSUFFICIENT_STOCK: 'Not enough stock available for this item',
  STOCK_NEGATIVE: 'Stock cannot be negative',
  INVALID_QUANTITY: 'Quantity must be greater than zero',

  // Bill errors
  BILL_NOT_FOUND: 'Bill not found or was deleted',
  EMPTY_BILL: 'Cannot create a bill with no items',
  INVALID_BILL_DATA: 'Bill data is invalid',

  // Network/Server errors
  NETWORK_ERROR: 'Connection lost. Please check your internet connection',
  TIMEOUT: 'Request took too long. Please try again',
  SERVER_ERROR: 'Server error occurred. Please try again later',
  SERVICE_UNAVAILABLE: 'Service temporarily unavailable. Please try again later',
  BAD_GATEWAY: 'Bad gateway. Please try again later',

  // API errors
  API_ERROR: 'API error occurred. Please try again',
  UNAUTHORIZED: 'You do not have permission to perform this action',
  FORBIDDEN: 'Access forbidden',

  // Generic errors
  UNKNOWN: 'Something went wrong. Please try again',
  RETRY_FAILED: 'Operation failed after multiple retries. Please try again later',
};

/**
 * Log technical error details for debugging
 * Called internally, never shown to user
 */
export const logError = (errorCode: string, details?: Record<string, unknown>) => {
  if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
    console.error(`[Error: ${errorCode}]`, details);
  }
};

/**
 * Get user-friendly message for error code
 */
export const getUserFriendlyMessage = (errorCode: string): string => {
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.UNKNOWN;
};

/**
 * Get error message and log technical details
 */
export const handleError = (errorCode: string, details?: Record<string, unknown>): string => {
  // Log technical details for debugging
  logError(errorCode, details);

  // Return user-friendly message
  return getUserFriendlyMessage(errorCode);
};

/**
 * Handle multiple errors (form validation, etc.)
 */
export const handleMultipleErrors = (
  errors: Record<string, string>
): { userMessage: string; fieldErrors: Record<string, string> } => {
  const fieldErrors = { ...errors };
  const firstError = Object.values(fieldErrors)[0];

  return {
    userMessage: firstError || ERROR_MESSAGES.UNKNOWN,
    fieldErrors,
  };
};
