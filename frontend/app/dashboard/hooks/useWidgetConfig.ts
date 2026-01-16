/**
 * Widget Configuration Hook
 *
 * Manages dashboard widget visibility and order with localStorage persistence.
 * NO backend changes - all state stored client-side.
 *
 * v1.4: Phase 8 - Customizable Dashboard Widgets
 */

import { useState, useEffect, useCallback } from 'react';

// Widget identifiers
export type WidgetId =
  | 'checklist'
  | 'kpiStats'
  | 'recentActivity'
  | 'featureCards'
  | 'connectedTools';

// Widget metadata for UI
export interface WidgetMeta {
  id: WidgetId;
  label: string;
  description: string;
  alwaysVisible?: boolean;
}

// All available widgets with metadata
export const WIDGET_METADATA: WidgetMeta[] = [
  {
    id: 'checklist',
    label: 'Onboarding Checklist',
    description: 'Track your setup progress',
  },
  {
    id: 'kpiStats',
    label: 'KPI Stats',
    description: 'Quick overview of tables and tools',
  },
  {
    id: 'recentActivity',
    label: 'Recent Activity',
    description: 'See your recent actions',
  },
  {
    id: 'featureCards',
    label: 'Feature Cards',
    description: 'Quick access to main features',
    alwaysVisible: true,
  },
  {
    id: 'connectedTools',
    label: 'Connected Tools',
    description: 'Manage your integrations',
  },
];

// Configuration structure
export interface WidgetConfig {
  visibility: Record<WidgetId, boolean>;
  order: WidgetId[];
}

// Default configuration
export const DEFAULT_WIDGET_CONFIG: WidgetConfig = {
  visibility: {
    checklist: true,
    kpiStats: true,
    recentActivity: true,
    featureCards: true,
    connectedTools: true,
  },
  order: ['checklist', 'kpiStats', 'recentActivity', 'featureCards', 'connectedTools'],
};

// localStorage key
const STORAGE_KEY = 'ims_dashboard_widget_config';

// Validate and sanitize config (handle corrupted data)
function sanitizeConfig(config: unknown): WidgetConfig {
  const defaultConfig = { ...DEFAULT_WIDGET_CONFIG };

  if (!config || typeof config !== 'object') {
    return defaultConfig;
  }

  const parsed = config as Partial<WidgetConfig>;

  // Validate visibility
  const visibility = { ...defaultConfig.visibility };
  if (parsed.visibility && typeof parsed.visibility === 'object') {
    for (const key of Object.keys(defaultConfig.visibility) as WidgetId[]) {
      if (typeof parsed.visibility[key] === 'boolean') {
        visibility[key] = parsed.visibility[key];
      }
    }
  }
  // Feature cards always visible
  visibility.featureCards = true;

  // Validate order
  let order = [...defaultConfig.order];
  if (Array.isArray(parsed.order)) {
    const validIds = new Set(defaultConfig.order);
    const newOrder = parsed.order.filter(
      (id): id is WidgetId => typeof id === 'string' && validIds.has(id as WidgetId)
    );
    // Only use if all widgets are present
    if (newOrder.length === defaultConfig.order.length) {
      order = newOrder;
    }
  }

  return { visibility, order };
}

// Hook return type
export interface UseWidgetConfigReturn {
  config: WidgetConfig;
  isLoaded: boolean;
  toggleWidget: (widgetId: WidgetId) => void;
  setWidgetVisibility: (widgetId: WidgetId, visible: boolean) => void;
  reorderWidgets: (newOrder: WidgetId[]) => void;
  moveWidget: (fromIndex: number, toIndex: number) => void;
  resetToDefault: () => void;
  getVisibleWidgets: () => WidgetId[];
}

export function useWidgetConfig(): UseWidgetConfigReturn {
  const [config, setConfig] = useState<WidgetConfig>(DEFAULT_WIDGET_CONFIG);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load config from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        const sanitized = sanitizeConfig(parsed);
        setConfig(sanitized);
      }
    } catch (error) {
      console.error('[useWidgetConfig] Failed to load config:', error);
    }
    setIsLoaded(true);
  }, []);

  // Save config to localStorage whenever it changes (after initial load)
  useEffect(() => {
    if (isLoaded) {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
      } catch (error) {
        console.error('[useWidgetConfig] Failed to save config:', error);
      }
    }
  }, [config, isLoaded]);

  // Toggle widget visibility
  const toggleWidget = useCallback((widgetId: WidgetId) => {
    // Can't toggle feature cards
    if (widgetId === 'featureCards') return;

    setConfig((prev) => ({
      ...prev,
      visibility: {
        ...prev.visibility,
        [widgetId]: !prev.visibility[widgetId],
      },
    }));
  }, []);

  // Set widget visibility explicitly
  const setWidgetVisibility = useCallback((widgetId: WidgetId, visible: boolean) => {
    // Can't hide feature cards
    if (widgetId === 'featureCards' && !visible) return;

    setConfig((prev) => ({
      ...prev,
      visibility: {
        ...prev.visibility,
        [widgetId]: visible,
      },
    }));
  }, []);

  // Reorder widgets with new order array
  const reorderWidgets = useCallback((newOrder: WidgetId[]) => {
    // Validate that all widgets are present
    const allPresent = DEFAULT_WIDGET_CONFIG.order.every((id) => newOrder.includes(id));
    if (!allPresent || newOrder.length !== DEFAULT_WIDGET_CONFIG.order.length) {
      console.error('[useWidgetConfig] Invalid order array');
      return;
    }

    setConfig((prev) => ({
      ...prev,
      order: newOrder,
    }));
  }, []);

  // Move widget from one position to another
  const moveWidget = useCallback((fromIndex: number, toIndex: number) => {
    if (fromIndex === toIndex) return;

    setConfig((prev) => {
      const newOrder = [...prev.order];
      const [removed] = newOrder.splice(fromIndex, 1);
      newOrder.splice(toIndex, 0, removed);
      return {
        ...prev,
        order: newOrder,
      };
    });
  }, []);

  // Reset to default configuration
  const resetToDefault = useCallback(() => {
    setConfig({ ...DEFAULT_WIDGET_CONFIG });
  }, []);

  // Get list of visible widgets in order
  const getVisibleWidgets = useCallback(() => {
    return config.order.filter((id) => config.visibility[id]);
  }, [config]);

  return {
    config,
    isLoaded,
    toggleWidget,
    setWidgetVisibility,
    reorderWidgets,
    moveWidget,
    resetToDefault,
    getVisibleWidgets,
  };
}
