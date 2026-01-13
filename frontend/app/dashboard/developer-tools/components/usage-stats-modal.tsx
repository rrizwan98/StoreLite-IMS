/**
 * Usage Stats Modal Component
 *
 * Modal showing usage statistics for a published agent.
 */

'use client';

import { useState, useEffect } from 'react';
import { X, Loader2, BarChart3, AlertCircle, TrendingUp, Clock, CheckCircle, XCircle } from 'lucide-react';
import { getUsageStats, UsageStatsResponse, formatNumber } from '@/lib/developer-tools-api';

interface UsageStatsModalProps {
  agentId: string;
  agentName: string;
  onClose: () => void;
}

export default function UsageStatsModal({ agentId, agentName, onClose }: UsageStatsModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState<UsageStatsResponse | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const loadStats = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await getUsageStats(agentId, days);
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load statistics');
      } finally {
        setLoading(false);
      }
    };
    loadStats();
  }, [agentId, days]);

  const maxQueries = stats?.daily_breakdown.length
    ? Math.max(...stats.daily_breakdown.map(d => d.queries))
    : 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BarChart3 className="h-6 w-6 text-purple-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Usage Statistics - {agentName}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Period Selector */}
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Period:</span>
          {[7, 14, 30, 60, 90].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1 text-sm rounded-lg transition-colors ${
                days === d
                  ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 font-medium'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {d} days
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-600 dark:text-red-400 flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              {error}
            </div>
          ) : stats && (
            <div className="space-y-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-1">
                    <TrendingUp className="h-4 w-4" />
                    <span className="text-sm">Total Queries</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatNumber(stats.total_queries)}
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400 mb-1">
                    <CheckCircle className="h-4 w-4" />
                    <span className="text-sm">Success Rate</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.success_rate.toFixed(1)}%
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 mb-1">
                    <Clock className="h-4 w-4" />
                    <span className="text-sm">Avg Response</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {stats.avg_response_time_ms.toFixed(0)}ms
                  </div>
                </div>

                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-600 dark:text-red-400 mb-1">
                    <XCircle className="h-4 w-4" />
                    <span className="text-sm">Failed</span>
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatNumber(stats.failed_queries)}
                  </div>
                </div>
              </div>

              {/* Daily Chart */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                  Daily Usage
                </h3>
                {stats.daily_breakdown.length === 0 ? (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    No usage data for this period
                  </div>
                ) : (
                  <div className="space-y-2">
                    {stats.daily_breakdown.slice(0, 14).reverse().map((day) => {
                      const width = maxQueries > 0 ? (day.queries / maxQueries) * 100 : 0;
                      const successWidth = day.queries > 0 ? (day.successful / day.queries) * width : 0;

                      return (
                        <div key={day.date} className="flex items-center gap-3">
                          <div className="w-20 text-xs text-gray-500 dark:text-gray-400 text-right">
                            {new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </div>
                          <div className="flex-1 h-6 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden relative">
                            <div
                              className="absolute inset-y-0 left-0 bg-green-500/30 dark:bg-green-500/20"
                              style={{ width: `${width}%` }}
                            />
                            <div
                              className="absolute inset-y-0 left-0 bg-green-500"
                              style={{ width: `${successWidth}%` }}
                            />
                          </div>
                          <div className="w-16 text-xs text-gray-600 dark:text-gray-400 text-right">
                            {formatNumber(day.queries)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Detailed Table */}
              {stats.daily_breakdown.length > 0 && (
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
                    Detailed Breakdown
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200 dark:border-gray-700">
                          <th className="px-3 py-2 text-left text-gray-600 dark:text-gray-400 font-medium">Date</th>
                          <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400 font-medium">Queries</th>
                          <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400 font-medium">Success</th>
                          <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400 font-medium">Failed</th>
                          <th className="px-3 py-2 text-right text-gray-600 dark:text-gray-400 font-medium">Avg Time</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {stats.daily_breakdown.slice(0, 14).map((day) => (
                          <tr key={day.date} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                            <td className="px-3 py-2 text-gray-900 dark:text-white">
                              {new Date(day.date).toLocaleDateString()}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-900 dark:text-white">
                              {formatNumber(day.queries)}
                            </td>
                            <td className="px-3 py-2 text-right text-green-600 dark:text-green-400">
                              {formatNumber(day.successful)}
                            </td>
                            <td className="px-3 py-2 text-right text-red-600 dark:text-red-400">
                              {formatNumber(day.failed)}
                            </td>
                            <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-400">
                              {day.avg_response_ms.toFixed(0)}ms
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
