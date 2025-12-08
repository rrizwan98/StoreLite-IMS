/**
 * Custom React hooks for StoreLite IMS
 * Encapsulate state management and API calls
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Item, BillItem } from './types';
import { api } from './api';
import { CATEGORIES } from './constants';

const SEARCH_DEBOUNCE_DELAY = 300;

/**
 * useItems - Fetch and manage items list
 * Handles loading, error states, and filtering
 */
export const useItems = (filters?: { name?: string; category?: string }) => {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getItems(filters);
      setItems(data || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch items');
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchItems();
  }, [fetchItems]);

  return {
    items,
    loading,
    error,
    refetch: fetchItems,
  };
};

/**
 * useBill - Manage bill state and operations
 * Handles adding items, removing items, updating quantities
 */
export const useBill = () => {
  const [items, setItems] = useState<BillItem[]>([]);

  /**
   * Add item to bill or increment quantity if already present
   */
  const addItem = useCallback(
    (item: Item) => {
      setItems((prevItems) => {
        // Check if item already in bill
        const existingIndex = prevItems.findIndex((bi) => bi.item_id === item.id);

        if (existingIndex >= 0) {
          // Item exists, increment quantity
          const updated = [...prevItems];
          updated[existingIndex] = {
            ...updated[existingIndex],
            quantity: updated[existingIndex].quantity + 1,
            line_total: (updated[existingIndex].quantity + 1) * item.unit_price,
          };
          return updated;
        }

        // New item
        return [
          ...prevItems,
          {
            item_id: item.id,
            item_name: item.name,
            unit: item.unit,
            unit_price: item.unit_price,
            quantity: 1,
            line_total: item.unit_price,
          },
        ];
      });
    },
    []
  );

  /**
   * Update quantity of item in bill
   */
  const updateQuantity = useCallback((index: number, quantity: number) => {
    setItems((prevItems) => {
      const updated = [...prevItems];
      if (quantity <= 0) {
        // Remove item if quantity is 0 or negative
        updated.splice(index, 1);
      } else {
        updated[index] = {
          ...updated[index],
          quantity,
          line_total: quantity * updated[index].unit_price,
        };
      }
      return updated;
    });
  }, []);

  /**
   * Remove item from bill
   */
  const removeItem = useCallback((index: number) => {
    setItems((prevItems) => {
      const updated = [...prevItems];
      updated.splice(index, 1);
      return updated;
    });
  }, []);

  /**
   * Clear all items from bill
   */
  const clearBill = useCallback(() => {
    setItems([]);
  }, []);

  /**
   * Calculate subtotal
   */
  const subtotal = items.reduce((sum, item) => sum + (item.line_total || 0), 0);

  /**
   * Calculate total (same as subtotal for Phase 3 - no taxes/discounts)
   */
  const total = subtotal;

  return {
    items,
    subtotal,
    total,
    addItem,
    updateQuantity,
    removeItem,
    clearBill,
  };
};

/**
 * useSearch - Debounced search hook
 * Prevents excessive API calls during user typing
 */
export const useSearch = (
  searchFn: (query: string) => Promise<Item[]>,
  delay: number = SEARCH_DEBOUNCE_DELAY
) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const debounceTimer = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Clear previous timer
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    // If query is empty, clear results
    if (!query.trim()) {
      setResults([]);
      setError(null);
      return;
    }

    // Set new timer for debounced search
    debounceTimer.current = setTimeout(async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await searchFn(query);
        setResults(data || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, delay);

    // Cleanup timer on unmount
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, [query, searchFn, delay]);

  return {
    query,
    setQuery,
    results,
    loading,
    error,
  };
};

/**
 * useLocalStorage - Persist data in browser local storage
 * Useful for saving bill draft or user preferences
 */
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = typeof window !== 'undefined' ? window.localStorage.getItem(key) : null;
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(key, JSON.stringify(valueToStore));
      }
    } catch {
      console.error(`Error storing value in localStorage for key: ${key}`);
    }
  };

  return [storedValue, setValue] as const;
};

/**
 * useAsync - Generic hook for async operations
 * Handles loading, error, and data states
 */
export const useAsync = <T,>(
  asyncFunction: () => Promise<T>,
  immediate: boolean = true
) => {
  const [status, setStatus] = useState<'idle' | 'pending' | 'success' | 'error'>('idle');
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async () => {
    setStatus('pending');
    setData(null);
    setError(null);

    try {
      const response = await asyncFunction();
      setData(response);
      setStatus('success');
      return response;
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
      setStatus('error');
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { execute, status, data, error };
};

/**
 * useStockMonitor - Monitor stock levels of items in current bill (FR-021)
 * Polls items every 5-10 seconds to detect if any become unavailable
 * Returns warning messages and unavailable items list
 */
export const useStockMonitor = (billItems: BillItem[], pollIntervalMs: number = 5000) => {
  const [warning, setWarning] = useState<string | null>(null);
  const [unavailableItems, setUnavailableItems] = useState<number[]>([]);
  const pollTimerRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    // Don't poll if bill is empty
    if (billItems.length === 0) {
      setWarning(null);
      setUnavailableItems([]);
      return;
    }

    const pollStockLevels = async () => {
      try {
        // Fetch fresh item data to check stock levels
        const itemIds = billItems.map((bi) => bi.item_id);
        const freshItems = await api.getItems();

        // Check if any items in bill are now out of stock
        const nowUnavailable: number[] = [];
        const itemsInBill = new Map(billItems.map((bi) => [bi.item_id, bi]));

        freshItems.forEach((item) => {
          if (itemsInBill.has(item.id) && item.stock_qty <= 0) {
            nowUnavailable.push(item.id);
          }
        });

        setUnavailableItems(nowUnavailable);

        // Generate warning message if items became unavailable
        if (nowUnavailable.length > 0) {
          const unavailableNames = freshItems
            .filter((item) => nowUnavailable.includes(item.id))
            .map((item) => item.name)
            .join(', ');

          setWarning(
            `⚠️ ${unavailableNames} ${nowUnavailable.length === 1 ? 'is' : 'are'} now out of stock`
          );
        } else {
          setWarning(null);
        }
      } catch (err) {
        // Silently fail on polling errors to avoid disrupting user workflow
        console.debug('Stock monitor polling error:', err);
      }
    };

    // Initial poll
    pollStockLevels();

    // Set up polling interval
    pollTimerRef.current = setInterval(pollStockLevels, pollIntervalMs);

    // Cleanup
    return () => {
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
      }
    };
  }, [billItems, pollIntervalMs]);

  return {
    warning,
    unavailableItems,
  };
};
