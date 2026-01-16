/**
 * Recent Activity Panel Component
 *
 * Displays recent user activities aggregated from existing API data.
 * NO backend changes required - uses existing APIs.
 *
 * v1.2: New component for activity timeline
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  CalendarPlus,
  CheckCircle,
  XCircle,
  Plug,
  Shield,
  Clock,
  Activity,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { ROUTES } from '@/lib/constants';
import { getScheduledTasks, ScheduledTask } from '@/lib/scheduler-api';
import { getConnectors, Connector } from '@/lib/connectors-api';

interface RecentActivityPanelProps {
  className?: string;
}

// Activity types
type ActivityType =
  | 'task_created'
  | 'task_completed'
  | 'task_failed'
  | 'task_running'
  | 'connector_added'
  | 'connector_verified';

interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: Date;
  route?: string;
}

// Activity type configurations
const activityConfig: Record<ActivityType, {
  icon: React.ReactNode;
  bgColor: string;
  textColor: string;
}> = {
  task_created: {
    icon: <CalendarPlus className="h-4 w-4" />,
    bgColor: 'bg-blue-100 dark:bg-blue-900/40',
    textColor: 'text-blue-600 dark:text-blue-400',
  },
  task_completed: {
    icon: <CheckCircle className="h-4 w-4" />,
    bgColor: 'bg-emerald-100 dark:bg-emerald-900/40',
    textColor: 'text-emerald-600 dark:text-emerald-400',
  },
  task_failed: {
    icon: <XCircle className="h-4 w-4" />,
    bgColor: 'bg-red-100 dark:bg-red-900/40',
    textColor: 'text-red-600 dark:text-red-400',
  },
  task_running: {
    icon: <Loader2 className="h-4 w-4 animate-spin" />,
    bgColor: 'bg-amber-100 dark:bg-amber-900/40',
    textColor: 'text-amber-600 dark:text-amber-400',
  },
  connector_added: {
    icon: <Plug className="h-4 w-4" />,
    bgColor: 'bg-purple-100 dark:bg-purple-900/40',
    textColor: 'text-purple-600 dark:text-purple-400',
  },
  connector_verified: {
    icon: <Shield className="h-4 w-4" />,
    bgColor: 'bg-emerald-100 dark:bg-emerald-900/40',
    textColor: 'text-emerald-600 dark:text-emerald-400',
  },
};

// Convert tasks to activities
function tasksToActivities(tasks: ScheduledTask[]): Activity[] {
  const activities: Activity[] = [];

  tasks.forEach((task) => {
    // Task created activity
    if (task.created_at) {
      activities.push({
        id: `task-created-${task.id}`,
        type: 'task_created',
        title: 'Scheduled task created',
        description: task.query.length > 50 ? task.query.slice(0, 50) + '...' : task.query,
        timestamp: new Date(task.created_at),
        route: ROUTES.SCHEDULER,
      });
    }

    // Task execution activity (if executed)
    if (task.executed_at && task.status !== 'pending') {
      let type: ActivityType = 'task_completed';
      let title = 'Task completed successfully';

      if (task.status === 'failed') {
        type = 'task_failed';
        title = 'Task failed';
      } else if (task.status === 'running') {
        type = 'task_running';
        title = 'Task is running';
      }

      activities.push({
        id: `task-executed-${task.id}`,
        type,
        title,
        description: task.result_summary || task.error_message || task.query.slice(0, 50),
        timestamp: new Date(task.executed_at),
        route: ROUTES.SCHEDULER,
      });
    }
  });

  return activities;
}

// Convert connectors to activities
function connectorsToActivities(connectors: Connector[]): Activity[] {
  const activities: Activity[] = [];

  connectors.forEach((connector) => {
    // Connector added activity
    if (connector.created_at) {
      activities.push({
        id: `connector-added-${connector.id}`,
        type: 'connector_added',
        title: `Connected ${connector.name}`,
        description: connector.email || connector.description || `${connector.tool_count} tools available`,
        timestamp: new Date(connector.created_at),
        route: '/dashboard/settings',
      });
    }

    // Connector verified activity (if different from created)
    if (connector.last_verified_at && connector.is_verified) {
      const verifiedDate = new Date(connector.last_verified_at);
      const createdDate = new Date(connector.created_at);

      // Only show if verified more than 1 minute after creation
      if (verifiedDate.getTime() - createdDate.getTime() > 60000) {
        activities.push({
          id: `connector-verified-${connector.id}-${connector.last_verified_at}`,
          type: 'connector_verified',
          title: `${connector.name} verified`,
          description: `Connection healthy with ${connector.tool_count} tools`,
          timestamp: verifiedDate,
          route: '/dashboard/settings',
        });
      }
    }
  });

  return activities;
}

// Format relative time
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  } else {
    return date.toLocaleDateString();
  }
}

export default function RecentActivityPanel({ className = '' }: RecentActivityPanelProps) {
  const router = useRouter();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch activity data from existing APIs
  const fetchActivities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch data from existing APIs (no new endpoints)
      const [tasksResponse, connectors] = await Promise.all([
        getScheduledTasks(undefined, 20, 0).catch(() => ({ tasks: [], total: 0 })),
        getConnectors(true).catch(() => []),
      ]);

      // Convert to activities
      const taskActivities = tasksToActivities(tasksResponse.tasks || []);
      const connectorActivities = connectorsToActivities(connectors || []);

      // Combine, sort by timestamp (most recent first), and limit
      const allActivities = [...taskActivities, ...connectorActivities]
        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime())
        .slice(0, 10);

      setActivities(allActivities);
    } catch (err) {
      console.error('Failed to fetch activities:', err);
      setError('Failed to load recent activity');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  // Handle activity click
  const handleActivityClick = (activity: Activity) => {
    if (activity.route) {
      router.push(activity.route);
    }
  };

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 overflow-hidden ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-700">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h2>
        </div>
        {activities.length > 0 && (
          <button
            onClick={() => router.push(ROUTES.SCHEDULER)}
            className="text-sm text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 font-medium flex items-center transition-colors"
          >
            View All
            <ChevronRight className="h-4 w-4 ml-1" />
          </button>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          /* Loading Skeleton */
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center space-x-3 animate-pulse">
                <div className="w-8 h-8 bg-gray-200 dark:bg-gray-700 rounded-full" />
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                </div>
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16" />
              </div>
            ))}
          </div>
        ) : error ? (
          /* Error State */
          <div className="text-center py-6">
            <XCircle className="h-8 w-8 text-red-400 mx-auto mb-2" />
            <p className="text-sm text-gray-600 dark:text-gray-400">{error}</p>
            <button
              onClick={fetchActivities}
              className="mt-2 text-sm text-emerald-600 dark:text-emerald-400 hover:underline"
            >
              Try again
            </button>
          </div>
        ) : activities.length === 0 ? (
          /* Empty State */
          <div className="text-center py-8">
            <Clock className="h-10 w-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
            <p className="text-gray-600 dark:text-gray-400 font-medium mb-1">No recent activity yet</p>
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Start by asking the AI Agent a question or scheduling a task!
            </p>
          </div>
        ) : (
          /* Activity List */
          <div className="space-y-2">
            {activities.map((activity, index) => {
              const config = activityConfig[activity.type];
              return (
                <button
                  key={activity.id}
                  onClick={() => handleActivityClick(activity)}
                  className={`
                    w-full flex items-center space-x-3 p-3 rounded-lg
                    hover:bg-gray-50 dark:hover:bg-gray-700/50
                    transition-colors text-left
                    animate-fade-in-up opacity-0
                  `}
                  style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'forwards' }}
                >
                  {/* Icon */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${config.bgColor} ${config.textColor}`}>
                    {config.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 dark:text-white text-sm truncate">
                      {activity.title}
                    </p>
                    {activity.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {activity.description}
                      </p>
                    )}
                  </div>

                  {/* Timestamp */}
                  <div className="flex-shrink-0 text-xs text-gray-400 dark:text-gray-500">
                    {formatRelativeTime(activity.timestamp)}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
