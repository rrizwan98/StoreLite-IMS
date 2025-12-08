'use client';

/**
 * Error Message Component
 * Displays user-friendly error messages with retry button
 */

export interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export default function ErrorMessage({
  message,
  onRetry,
  showRetry = true,
}: ErrorMessageProps) {
  return (
    <div className="bg-error bg-opacity-10 border border-error text-error rounded-md p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-semibold">Error</p>
          <p className="text-sm mt-1">{message}</p>
        </div>
        {showRetry && onRetry && (
          <button
            onClick={onRetry}
            className="ml-4 px-3 py-1 bg-error text-white rounded hover:bg-opacity-80 text-sm whitespace-nowrap"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
}
