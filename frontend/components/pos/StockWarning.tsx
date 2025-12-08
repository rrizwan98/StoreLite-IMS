/**
 * Stock Warning Component (FR-021)
 * Displays alert when items in bill become unavailable due to stock depletion
 * Dismissible or auto-dismisses after configured timeout
 */

'use client';

import { useEffect, useState } from 'react';

export interface StockWarningProps {
  warning: string | null;
  onDismiss?: () => void;
  autoDismissMs?: number;
}

export default function StockWarning({
  warning,
  onDismiss,
  autoDismissMs = 5000,
}: StockWarningProps) {
  const [isVisible, setIsVisible] = useState(!!warning);

  useEffect(() => {
    if (!warning) {
      setIsVisible(false);
      return;
    }

    setIsVisible(true);

    // Auto-dismiss after configured time
    const timer = setTimeout(() => {
      setIsVisible(false);
    }, autoDismissMs);

    return () => clearTimeout(timer);
  }, [warning, autoDismissMs]);

  const handleDismiss = () => {
    setIsVisible(false);
    if (onDismiss) {
      onDismiss();
    }
  };

  if (!isVisible || !warning) {
    return null;
  }

  return (
    <div className="fixed top-4 left-4 right-4 max-w-md bg-yellow-50 border border-yellow-200 border-l-4 border-l-yellow-500 rounded-md p-4 shadow-lg z-50">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <span className="text-xl">⚠️</span>
          <div>
            <p className="font-semibold text-yellow-900">Stock Alert</p>
            <p className="text-sm text-yellow-800 mt-1">{warning}</p>
            <p className="text-xs text-yellow-700 mt-2">
              ℹ️ Remove unavailable items from bill or contact store for restocking
            </p>
          </div>
        </div>
        <button
          onClick={handleDismiss}
          className="ml-4 text-yellow-600 hover:text-yellow-900 text-xl leading-none"
          aria-label="Dismiss warning"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
