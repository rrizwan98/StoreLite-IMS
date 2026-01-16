/**
 * Customize Dashboard Modal Component
 *
 * Modal for customizing dashboard widget visibility and order.
 * Uses HTML5 drag-and-drop for reordering (no external libraries).
 *
 * v1.4: Phase 8 - Customizable Dashboard Widgets
 */

'use client';

import { useState, useRef, useCallback } from 'react';
import {
  X,
  GripVertical,
  RotateCcw,
  Settings,
  Eye,
  EyeOff,
  Lock,
} from 'lucide-react';
import {
  WidgetId,
  WidgetConfig,
  WIDGET_METADATA,
} from '../hooks/useWidgetConfig';

interface CustomizeDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: WidgetConfig;
  onToggleWidget: (widgetId: WidgetId) => void;
  onReorderWidgets: (newOrder: WidgetId[]) => void;
  onResetToDefault: () => void;
}

export default function CustomizeDashboardModal({
  isOpen,
  onClose,
  config,
  onToggleWidget,
  onReorderWidgets,
  onResetToDefault,
}: CustomizeDashboardModalProps) {
  // Drag state
  const [draggedId, setDraggedId] = useState<WidgetId | null>(null);
  const [dragOverId, setDragOverId] = useState<WidgetId | null>(null);
  const dragCounter = useRef(0);

  // Handle drag start
  const handleDragStart = useCallback(
    (e: React.DragEvent<HTMLDivElement>, widgetId: WidgetId) => {
      setDraggedId(widgetId);
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', widgetId);

      // Add dragging class after a short delay for visual feedback
      requestAnimationFrame(() => {
        (e.target as HTMLElement).classList.add('opacity-50');
      });
    },
    []
  );

  // Handle drag end
  const handleDragEnd = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    (e.target as HTMLElement).classList.remove('opacity-50');
    setDraggedId(null);
    setDragOverId(null);
    dragCounter.current = 0;
  }, []);

  // Handle drag over (allow drop)
  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  // Handle drag enter (track which item we're over)
  const handleDragEnter = useCallback(
    (e: React.DragEvent<HTMLDivElement>, widgetId: WidgetId) => {
      e.preventDefault();
      dragCounter.current++;
      if (widgetId !== draggedId) {
        setDragOverId(widgetId);
      }
    },
    [draggedId]
  );

  // Handle drag leave
  const handleDragLeave = useCallback(() => {
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setDragOverId(null);
    }
  }, []);

  // Handle drop - reorder widgets
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>, targetId: WidgetId) => {
      e.preventDefault();

      const sourceId = e.dataTransfer.getData('text/plain') as WidgetId;
      if (!sourceId || sourceId === targetId) {
        setDragOverId(null);
        return;
      }

      // Create new order
      const currentOrder = [...config.order];
      const sourceIndex = currentOrder.indexOf(sourceId);
      const targetIndex = currentOrder.indexOf(targetId);

      if (sourceIndex === -1 || targetIndex === -1) return;

      // Remove from source position and insert at target position
      currentOrder.splice(sourceIndex, 1);
      currentOrder.splice(targetIndex, 0, sourceId);

      onReorderWidgets(currentOrder);
      setDragOverId(null);
    },
    [config.order, onReorderWidgets]
  );

  // Handle keyboard close
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

  // Handle toggle
  const handleToggle = useCallback(
    (widgetId: WidgetId) => {
      const meta = WIDGET_METADATA.find((w) => w.id === widgetId);
      if (meta?.alwaysVisible) return;
      onToggleWidget(widgetId);
    },
    [onToggleWidget]
  );

  if (!isOpen) return null;

  // Get widgets in current order with metadata
  const orderedWidgets = config.order.map((id) => {
    const meta = WIDGET_METADATA.find((w) => w.id === id)!;
    return {
      ...meta,
      isVisible: config.visibility[id],
    };
  });

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onKeyDown={handleKeyDown}
      role="dialog"
      aria-modal="true"
      aria-labelledby="customize-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Settings className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            <h2
              id="customize-modal-title"
              className="text-lg font-semibold text-gray-900 dark:text-white"
            >
              Customize Dashboard
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600
                       dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700
                       transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Drag to reorder widgets. Toggle visibility with the eye icon.
          </p>

          {/* Widget List */}
          <div className="space-y-2">
            {orderedWidgets.map((widget) => {
              const isDragging = draggedId === widget.id;
              const isDragOver = dragOverId === widget.id;

              return (
                <div
                  key={widget.id}
                  draggable={!widget.alwaysVisible}
                  onDragStart={(e) => handleDragStart(e, widget.id)}
                  onDragEnd={handleDragEnd}
                  onDragOver={handleDragOver}
                  onDragEnter={(e) => handleDragEnter(e, widget.id)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, widget.id)}
                  className={`
                    flex items-center p-3 rounded-lg border
                    transition-all duration-200
                    ${isDragOver && !isDragging
                      ? 'border-emerald-400 dark:border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30'
                      : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50'
                    }
                    ${widget.alwaysVisible ? '' : 'cursor-grab active:cursor-grabbing'}
                    ${!widget.isVisible ? 'opacity-60' : ''}
                  `}
                >
                  {/* Drag Handle */}
                  <div
                    className={`flex-shrink-0 mr-3 ${
                      widget.alwaysVisible
                        ? 'text-gray-300 dark:text-gray-600'
                        : 'text-gray-400 dark:text-gray-500'
                    }`}
                  >
                    {widget.alwaysVisible ? (
                      <Lock className="h-4 w-4" />
                    ) : (
                      <GripVertical className="h-4 w-4" />
                    )}
                  </div>

                  {/* Widget Info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                      {widget.label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {widget.description}
                    </p>
                  </div>

                  {/* Toggle Button */}
                  <button
                    onClick={() => handleToggle(widget.id)}
                    disabled={widget.alwaysVisible}
                    className={`
                      flex-shrink-0 p-2 rounded-lg transition-colors
                      ${widget.alwaysVisible
                        ? 'text-gray-300 dark:text-gray-600 cursor-not-allowed'
                        : widget.isVisible
                        ? 'text-emerald-600 dark:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/30'
                        : 'text-gray-400 dark:text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                    aria-label={`${widget.isVisible ? 'Hide' : 'Show'} ${widget.label}`}
                    title={
                      widget.alwaysVisible
                        ? 'This widget is always visible'
                        : widget.isVisible
                        ? 'Click to hide'
                        : 'Click to show'
                    }
                  >
                    {widget.isVisible ? (
                      <Eye className="h-5 w-5" />
                    ) : (
                      <EyeOff className="h-5 w-5" />
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 rounded-b-xl">
          <button
            onClick={onResetToDefault}
            className="flex items-center text-sm text-gray-600 dark:text-gray-400
                       hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <RotateCcw className="h-4 w-4 mr-1.5" />
            Reset to Default
          </button>

          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium bg-emerald-600 text-white
                       rounded-lg hover:bg-emerald-700 transition-colors click-feedback"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
