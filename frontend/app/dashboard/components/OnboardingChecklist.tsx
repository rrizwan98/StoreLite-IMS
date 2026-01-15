/**
 * Onboarding Checklist Component
 *
 * Guides new users through key setup steps.
 * State derived from existing data - no new API calls needed.
 * Uses localStorage for non-API trackable items.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Database,
  MessageSquare,
  Wrench,
  CalendarClock,
  Check,
  ChevronDown,
  ChevronUp,
  X,
  Sparkles,
} from 'lucide-react';
import { ROUTES } from '@/lib/constants';

// localStorage keys (namespaced to avoid conflicts)
const STORAGE_KEYS = {
  CHECKLIST_DISMISSED: 'ims_dashboard_checklist_dismissed',
  FIRST_AI_QUERY: 'ims_first_ai_query',
  FIRST_TASK_CREATED: 'ims_first_task_created',
};

import type { ConnectionStatus } from '@/lib/auth-api';

interface OnboardingChecklistProps {
  connectionStatus: ConnectionStatus | null;
  connectorsCount: number;
  className?: string;
}

interface ChecklistItem {
  id: string;
  label: string;
  description: string;
  isComplete: boolean;
  route: string;
  icon: React.ReactNode;
}

function getChecklistItems(
  connectionStatus: ConnectionStatus | null,
  connectorsCount: number
): ChecklistItem[] {
  // Check localStorage for user actions (only on client side)
  const hasFirstAIQuery = typeof window !== 'undefined'
    ? localStorage.getItem(STORAGE_KEYS.FIRST_AI_QUERY) === 'true'
    : false;
  const hasFirstTask = typeof window !== 'undefined'
    ? localStorage.getItem(STORAGE_KEYS.FIRST_TASK_CREATED) === 'true'
    : false;

  return [
    {
      id: 'connect_db',
      label: 'Connect your database',
      description: 'Link your PostgreSQL database to discover schema',
      isComplete: connectionStatus?.schema_status === 'ready',
      route: ROUTES.SCHEMA_CONNECT,
      icon: <Database className="h-5 w-5" />,
    },
    {
      id: 'first_query',
      label: 'Ask your first AI question',
      description: 'Try asking a question about your data',
      isComplete: hasFirstAIQuery,
      route: ROUTES.SCHEMA_AGENT,
      icon: <MessageSquare className="h-5 w-5" />,
    },
    {
      id: 'connect_tool',
      label: 'Connect a tool',
      description: 'Add Gmail, Google Drive, or other integrations',
      isComplete: connectorsCount > 0,
      route: '/dashboard/settings',
      icon: <Wrench className="h-5 w-5" />,
    },
    {
      id: 'create_task',
      label: 'Create a scheduled task',
      description: 'Set up automated tasks to run on schedule',
      isComplete: hasFirstTask,
      route: ROUTES.SCHEDULER,
      icon: <CalendarClock className="h-5 w-5" />,
    },
  ];
}

export default function OnboardingChecklist({
  connectionStatus,
  connectorsCount,
  className = '',
}: OnboardingChecklistProps) {
  const router = useRouter();
  const [isDismissed, setIsDismissed] = useState(true); // Start hidden to avoid flash
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [items, setItems] = useState<ChecklistItem[]>([]);

  // Initialize state from localStorage on mount
  useEffect(() => {
    const dismissed = localStorage.getItem(STORAGE_KEYS.CHECKLIST_DISMISSED) === 'true';
    setIsDismissed(dismissed);

    // Get checklist items
    setItems(getChecklistItems(connectionStatus, connectorsCount));
  }, [connectionStatus, connectorsCount]);

  // Handle dismiss
  const handleDismiss = () => {
    localStorage.setItem(STORAGE_KEYS.CHECKLIST_DISMISSED, 'true');
    setIsDismissed(true);
  };

  // Handle show again
  const handleShow = () => {
    localStorage.setItem(STORAGE_KEYS.CHECKLIST_DISMISSED, 'false');
    setIsDismissed(false);
  };

  // Handle item click
  const handleItemClick = (item: ChecklistItem) => {
    router.push(item.route);
  };

  // Calculate progress
  const completedCount = items.filter((item) => item.isComplete).length;
  const totalCount = items.length;
  const progressPercent = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;
  const allComplete = completedCount === totalCount;

  // If dismissed, show minimal expand button
  if (isDismissed) {
    return (
      <button
        onClick={handleShow}
        className={`
          flex items-center space-x-2 px-4 py-2
          bg-emerald-50 dark:bg-emerald-900/30
          border border-emerald-200 dark:border-emerald-800
          rounded-lg text-emerald-700 dark:text-emerald-300
          hover:bg-emerald-100 dark:hover:bg-emerald-900/50
          transition-colors text-sm font-medium
          ${className}
        `}
      >
        <Sparkles className="h-4 w-4" />
        <span>Show Getting Started Guide</span>
      </button>
    );
  }

  return (
    <div
      className={`
        bg-white dark:bg-gray-800
        border border-gray-200 dark:border-gray-700
        rounded-xl shadow-sm
        overflow-hidden
        ${className}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <Sparkles className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {allComplete ? 'All set!' : 'Get Started'}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {allComplete
                ? 'You\'ve completed all setup steps'
                : `${completedCount} of ${totalCount} complete`}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Collapse/Expand button */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
            aria-label={isCollapsed ? 'Expand checklist' : 'Collapse checklist'}
          >
            {isCollapsed ? (
              <ChevronDown className="h-5 w-5" />
            ) : (
              <ChevronUp className="h-5 w-5" />
            )}
          </button>

          {/* Dismiss button */}
          <button
            onClick={handleDismiss}
            className="p-1.5 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-600 rounded-lg transition-colors"
            aria-label="Dismiss checklist"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1 bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-emerald-500 dark:bg-emerald-400 transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Checklist items */}
      {!isCollapsed && (
        <div className="divide-y divide-gray-100 dark:divide-gray-700">
          {items.map((item) => (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              disabled={item.isComplete}
              className={`
                w-full flex items-center space-x-4 px-4 py-3 text-left
                transition-colors
                ${item.isComplete
                  ? 'bg-gray-50 dark:bg-gray-800 cursor-default'
                  : 'hover:bg-emerald-50 dark:hover:bg-emerald-900/20 cursor-pointer'
                }
              `}
            >
              {/* Status icon */}
              <div
                className={`
                  flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
                  ${item.isComplete
                    ? 'bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }
                `}
              >
                {item.isComplete ? (
                  <Check className="h-5 w-5" />
                ) : (
                  item.icon
                )}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p
                  className={`
                    font-medium
                    ${item.isComplete
                      ? 'text-gray-500 dark:text-gray-500 line-through'
                      : 'text-gray-900 dark:text-white'
                    }
                  `}
                >
                  {item.label}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                  {item.description}
                </p>
              </div>

              {/* Arrow for incomplete items */}
              {!item.isComplete && (
                <div className="flex-shrink-0 text-emerald-600 dark:text-emerald-400">
                  <ChevronDown className="h-5 w-5 -rotate-90" />
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Utility function to mark first AI query complete (call from Schema Agent page)
export function markFirstAIQueryComplete() {
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEYS.FIRST_AI_QUERY, 'true');
  }
}

// Utility function to mark first task created (call from Scheduler page)
export function markFirstTaskCreated() {
  if (typeof window !== 'undefined') {
    localStorage.setItem(STORAGE_KEYS.FIRST_TASK_CREATED, 'true');
  }
}
