/**
 * Scheduler Page
 *
 * Task scheduling interface for schema_query_only users.
 * Allows users to:
 * - Select tools (max 3)
 * - Enter a query
 * - Pick a date/time
 * - Schedule the task to run automatically
 * - View scheduled/completed tasks
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Calendar, Clock, Play, X, Eye, Trash2,
  BarChart3, Globe, FileSearch, Mail, Box, Cloud, Phone,
  CheckCircle, AlertCircle, Loader2, Timer
} from 'lucide-react';
import { ROUTES } from '@/lib/constants';
import AnalogClockPicker from '@/components/ui/AnalogClockPicker';
import { useAuth } from '@/lib/auth-context';
import { ThemeToggle } from '@/components/theme-toggle';
import {
  getAvailableTools,
  createScheduledTask,
  getScheduledTasks,
  cancelScheduledTask,
  formatScheduledTime,
  getStatusInfo,
  SchedulerTool,
  ScheduledTask,
} from '@/lib/scheduler-api';

// Icon mapping for tools
const toolIcons: Record<string, React.ReactNode> = {
  chart: <BarChart3 className="h-5 w-5" />,
  globe: <Globe className="h-5 w-5" />,
  notebook: <FileSearch className="h-5 w-5" />,
  mail: <Mail className="h-5 w-5" />,
  cube: <Box className="h-5 w-5" />,
  cloud: <Cloud className="h-5 w-5" />,
  phone: <Phone className="h-5 w-5" />,
};

export default function SchedulerPage() {
  const { user, connectionStatus, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  // Form state
  const [availableTools, setAvailableTools] = useState<SchedulerTool[]>([]);
  const [selectedTools, setSelectedTools] = useState<string[]>([]);
  const [query, setQuery] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledTime, setScheduledTime] = useState('');
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Tasks state
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pending' | 'completed'>('pending');

  // Redirect if not authenticated or wrong connection type
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Redirect if not schema_query_only
  useEffect(() => {
    if (!isLoading && connectionStatus) {
      if (connectionStatus.connection_type !== 'schema_query_only') {
        router.push(ROUTES.DASHBOARD);
      } else if (connectionStatus.schema_status !== 'ready') {
        router.push(ROUTES.SCHEMA_CONNECT);
      }
    }
  }, [connectionStatus, isLoading, router]);

  // Load available tools
  useEffect(() => {
    const loadTools = async () => {
      try {
        const tools = await getAvailableTools();
        setAvailableTools(tools);
      } catch (err) {
        console.error('Failed to load tools:', err);
      }
    };
    if (isAuthenticated) {
      loadTools();
    }
  }, [isAuthenticated]);

  // Load tasks
  useEffect(() => {
    const loadTasks = async () => {
      setTasksLoading(true);
      try {
        const response = await getScheduledTasks();
        setTasks(response.tasks);
      } catch (err) {
        console.error('Failed to load tasks:', err);
      } finally {
        setTasksLoading(false);
      }
    };
    if (isAuthenticated) {
      loadTasks();
    }
  }, [isAuthenticated]);

  // Handle tool selection (max 3)
  const handleToolToggle = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      setSelectedTools(prev => prev.filter(t => t !== toolId));
    } else if (selectedTools.length < 3) {
      setSelectedTools(prev => [...prev, toolId]);
    }
  };

  // Handle schedule submission
  const handleSchedule = async () => {
    setError('');
    setSuccess('');

    // Validate
    if (selectedTools.length === 0) {
      setError('Please select at least one tool');
      return;
    }
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }
    if (!scheduledDate || !scheduledTime) {
      setError('Please select a date and time');
      return;
    }

    // Create ISO datetime
    const scheduledDateTime = new Date(`${scheduledDate}T${scheduledTime}`);
    if (scheduledDateTime <= new Date()) {
      setError('Scheduled time must be in the future');
      return;
    }

    setCreating(true);
    try {
      const response = await createScheduledTask({
        query: query.trim(),
        selected_tools: selectedTools,
        scheduled_time: scheduledDateTime.toISOString(),
      });

      setSuccess(`Task scheduled! ${response.message}`);

      // Reset form
      setQuery('');
      setSelectedTools([]);
      setScheduledDate('');
      setScheduledTime('');

      // Reload tasks
      const tasksResponse = await getScheduledTasks();
      setTasks(tasksResponse.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to schedule task');
    } finally {
      setCreating(false);
    }
  };

  // Handle task cancellation
  const handleCancelTask = async (taskId: string) => {
    try {
      await cancelScheduledTask(taskId);
      // Reload tasks
      const response = await getScheduledTasks();
      setTasks(response.tasks);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel task');
    }
  };

  // View task result in ChatKit
  const handleViewResult = (task: ScheduledTask) => {
    if (task.thread_id) {
      router.push(`${ROUTES.SCHEMA_AGENT}?thread=${task.thread_id}`);
    }
  };

  // Filter tasks by tab
  const filteredTasks = tasks.filter(task => {
    if (activeTab === 'pending') {
      return task.status === 'pending' || task.status === 'running';
    }
    return task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled';
  });

  // Get minimum date/time for picker (now)
  const now = new Date();
  const minDate = now.toISOString().split('T')[0];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 dark:border-emerald-400"></div>
      </div>
    );
  }

  if (!user || connectionStatus?.connection_type !== 'schema_query_only') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm dark:shadow-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 sm:gap-0">
            <div className="flex items-center space-x-2 sm:space-x-3">
              <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-2 sm:space-x-3">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-purple-600 dark:bg-purple-500 rounded-lg flex items-center justify-center">
                  <Timer className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
                </div>
                <span className="text-lg sm:text-xl font-bold text-gray-900 dark:text-white">Scheduler</span>
              </Link>
              <span className="hidden md:inline text-gray-400 dark:text-gray-500">|</span>
              <span className="hidden md:inline text-gray-600 dark:text-gray-400 text-sm">Automate your queries</span>
            </div>
            <div className="flex items-center space-x-3 sm:space-x-4 text-sm">
              <Link
                href={ROUTES.SCHEMA_AGENT}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              >
                Agent
              </Link>
              <Link
                href={ROUTES.DASHBOARD}
                className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium"
              >
                Dashboard
              </Link>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column - Create Task Form */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Schedule New Task</h2>

            {/* Error/Success Messages */}
            {error && (
              <div className="mb-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg flex items-center">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                {error}
              </div>
            )}
            {success && (
              <div className="mb-4 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg flex items-center">
                <CheckCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                {success}
              </div>
            )}

            {/* Tool Selection */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Tools (max 3)
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {availableTools.map(tool => (
                  <button
                    key={tool.id}
                    onClick={() => handleToolToggle(tool.id)}
                    disabled={!tool.available || (!selectedTools.includes(tool.id) && selectedTools.length >= 3)}
                    className={`
                      flex items-center p-3 rounded-lg border-2 transition-all text-left
                      ${selectedTools.includes(tool.id)
                        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 text-gray-700 dark:text-gray-300'
                      }
                      ${!tool.available || (!selectedTools.includes(tool.id) && selectedTools.length >= 3)
                        ? 'opacity-50 cursor-not-allowed'
                        : 'cursor-pointer'
                      }
                    `}
                  >
                    <span className="mr-2">{toolIcons[tool.icon] || <Box className="h-5 w-5" />}</span>
                    <span className="text-sm font-medium truncate">{tool.name}</span>
                    {selectedTools.includes(tool.id) && (
                      <CheckCircle className="h-4 w-4 ml-auto text-emerald-600 dark:text-emerald-400" />
                    )}
                  </button>
                ))}
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                Selected: {selectedTools.length}/3 tools
              </p>
            </div>

            {/* Query Input */}
            <div className="mb-6">
              <label htmlFor="query" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Query
              </label>
              <textarea
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What would you like the agent to do? e.g., 'Generate a sales report for this week and email it to me'"
                rows={4}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            {/* Date/Time Selection */}
            <div className="mb-6 grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Calendar className="h-4 w-4 inline mr-1" />
                  Date
                </label>
                <input
                  type="date"
                  id="date"
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  min={minDate}
                  className="w-full px-4 py-2.5 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  <Clock className="h-4 w-4 inline mr-1" />
                  Time
                </label>
                <AnalogClockPicker
                  value={scheduledTime}
                  onChange={(time) => setScheduledTime(time)}
                />
              </div>
            </div>

            {/* Schedule Button */}
            <button
              onClick={handleSchedule}
              disabled={creating || selectedTools.length === 0 || !query.trim() || !scheduledDate || !scheduledTime}
              className="w-full flex items-center justify-center px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-semibold"
            >
              {creating ? (
                <>
                  <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                  Scheduling...
                </>
              ) : (
                <>
                  <Play className="h-5 w-5 mr-2" />
                  Schedule Task
                </>
              )}
            </button>
          </div>

          {/* Right Column - Task List */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Scheduled Tasks</h2>

            {/* Tab Buttons */}
            <div className="flex border-b border-gray-200 dark:border-gray-700 mb-4">
              <button
                onClick={() => setActiveTab('pending')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === 'pending'
                    ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Pending
              </button>
              <button
                onClick={() => setActiveTab('completed')}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === 'completed'
                    ? 'border-emerald-500 text-emerald-600 dark:text-emerald-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                Completed
              </button>
            </div>

            {/* Task List */}
            {tasksLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <Timer className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>No {activeTab} tasks</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto">
                {filteredTasks.map(task => {
                  const statusInfo = getStatusInfo(task.status);
                  return (
                    <div
                      key={task.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 flex-1 mr-2">
                          {task.query}
                        </p>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusInfo.bgColor} ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                      </div>

                      <div className="flex items-center text-xs text-gray-500 dark:text-gray-400 mb-2">
                        <Clock className="h-3 w-3 mr-1" />
                        {formatScheduledTime(task.scheduled_time)}
                      </div>

                      <div className="flex items-center flex-wrap gap-1 mb-3">
                        {task.selected_tools.map(toolId => (
                          <span
                            key={toolId}
                            className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded"
                          >
                            {toolId}
                          </span>
                        ))}
                      </div>

                      <div className="flex items-center justify-end space-x-2">
                        {task.status === 'pending' && (
                          <button
                            onClick={() => handleCancelTask(task.id)}
                            className="flex items-center px-3 py-1.5 text-xs text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                          >
                            <Trash2 className="h-3.5 w-3.5 mr-1" />
                            Cancel
                          </button>
                        )}
                        {task.status === 'completed' && task.thread_id && (
                          <button
                            onClick={() => handleViewResult(task)}
                            className="flex items-center px-3 py-1.5 text-xs bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-400 hover:bg-emerald-200 dark:hover:bg-emerald-900/70 rounded-lg transition-colors"
                          >
                            <Eye className="h-3.5 w-3.5 mr-1" />
                            View Result
                          </button>
                        )}
                        {task.status === 'failed' && task.error_message && (
                          <span className="text-xs text-red-600 dark:text-red-400 truncate max-w-[200px]" title={task.error_message}>
                            {task.error_message}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Info Notice */}
        <div className="mt-6 bg-purple-50 dark:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Timer className="h-5 w-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-purple-800 dark:text-purple-300">How Scheduler Works</h4>
              <p className="text-sm text-purple-700 dark:text-purple-400 mt-1">
                Select up to 3 tools, write your query, and pick a time. At the scheduled time,
                the AI Agent will run your query using only the selected tools. View results
                in the chat interface when complete.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
