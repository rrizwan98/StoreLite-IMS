/**
 * Scheduler API Client
 *
 * Functions for interacting with task scheduler endpoints.
 * Allows users to schedule agent tasks to run at specific times.
 */

import { API_BASE_URL } from './constants';
import { getAccessToken } from './auth-api';

/**
 * Available tool for scheduling
 */
export interface SchedulerTool {
  id: string;
  name: string;
  description: string;
  icon: string;
  available: boolean;
}

/**
 * Scheduled task definition
 */
export interface ScheduledTask {
  id: string;
  query: string;
  selected_tools: string[];
  scheduled_time: string; // ISO 8601 datetime
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  thread_id: string | null;
  result_summary: string | null;
  error_message: string | null;
  created_at: string;
  executed_at: string | null;
}

/**
 * Request to create a scheduled task
 */
export interface CreateTaskRequest {
  query: string;
  selected_tools: string[];
  scheduled_time: string; // ISO 8601 datetime
}

/**
 * Response after creating a task
 */
export interface CreateTaskResponse {
  task_id: string;
  status: string;
  scheduled_time: string;
  message: string;
}

/**
 * Response for listing tasks
 */
export interface TaskListResponse {
  tasks: ScheduledTask[];
  total: number;
}

/**
 * Helper function to make authenticated API requests
 */
async function schedulerFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAccessToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

/**
 * Get available tools for scheduling
 *
 * Returns list of tools user can select for scheduled tasks
 */
export async function getAvailableTools(): Promise<SchedulerTool[]> {
  const response = await schedulerFetch<{ tools: SchedulerTool[] }>('/scheduler/tools');
  return response.tools;
}

/**
 * Create a new scheduled task
 *
 * @param request - Task configuration (query, tools, time)
 * @returns Created task info
 */
export async function createScheduledTask(
  request: CreateTaskRequest
): Promise<CreateTaskResponse> {
  return schedulerFetch<CreateTaskResponse>('/scheduler/tasks', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

/**
 * Get all scheduled tasks for current user
 *
 * @param statusFilter - Optional filter by status
 * @param limit - Max tasks to return (default 50)
 * @param offset - Pagination offset (default 0)
 */
export async function getScheduledTasks(
  statusFilter?: string,
  limit: number = 50,
  offset: number = 0
): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  if (statusFilter) params.append('status_filter', statusFilter);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return schedulerFetch<TaskListResponse>(`/scheduler/tasks?${params.toString()}`);
}

/**
 * Get details of a specific task
 *
 * @param taskId - Task identifier
 */
export async function getTaskDetails(taskId: string): Promise<ScheduledTask> {
  return schedulerFetch<ScheduledTask>(`/scheduler/tasks/${taskId}`);
}

/**
 * Cancel a pending scheduled task
 *
 * @param taskId - Task identifier
 */
export async function cancelScheduledTask(
  taskId: string
): Promise<{ message: string; task_id: string }> {
  return schedulerFetch<{ message: string; task_id: string }>(
    `/scheduler/tasks/${taskId}`,
    { method: 'DELETE' }
  );
}

/**
 * Helper to format scheduled time for display
 */
export function formatScheduledTime(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

/**
 * Helper to get status display info
 */
export function getStatusInfo(status: ScheduledTask['status']): {
  label: string;
  color: string;
  bgColor: string;
} {
  const statusMap: Record<ScheduledTask['status'], { label: string; color: string; bgColor: string }> = {
    pending: { label: 'Pending', color: 'text-yellow-700', bgColor: 'bg-yellow-100' },
    running: { label: 'Running', color: 'text-blue-700', bgColor: 'bg-blue-100' },
    completed: { label: 'Completed', color: 'text-green-700', bgColor: 'bg-green-100' },
    failed: { label: 'Failed', color: 'text-red-700', bgColor: 'bg-red-100' },
    cancelled: { label: 'Cancelled', color: 'text-gray-700', bgColor: 'bg-gray-100' },
  };
  return statusMap[status];
}

/**
 * Helper to get tool icon name
 */
export function getToolIcon(icon: string): string {
  const iconMap: Record<string, string> = {
    chart: 'BarChart3',
    globe: 'Globe',
    notebook: 'FileSearch',
    mail: 'Mail',
    cube: 'Box',
    cloud: 'Cloud',
    phone: 'Phone',
  };
  return iconMap[icon] || 'Settings';
}
