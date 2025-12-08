'use client';

import { useEffect } from 'react';

/**
 * Success Toast Component
 * Transient notification for successful operations
 */

export interface SuccessToastProps {
  message: string;
  duration?: number;
  onClose?: () => void;
}

export default function SuccessToast({
  message,
  duration = 3000,
  onClose,
}: SuccessToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      if (onClose) {
        onClose();
      }
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className="fixed bottom-4 right-4 bg-success text-white px-4 py-3 rounded shadow-lg animate-fade-in-down">
      <div className="flex items-center">
        <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
            clipRule="evenodd"
          />
        </svg>
        {message}
      </div>
    </div>
  );
}
