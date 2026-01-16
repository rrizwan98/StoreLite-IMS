/**
 * Usage Stats Modal Component (Redesigned)
 *
 * Enhanced modal showing usage statistics with:
 * - KPI cards with sparklines and trend indicators
 * - Radial progress for success rate
 * - Human-readable response times
 * - Area chart for daily trends
 * - Color-coded performance states
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import {
  X,
  Loader2,
  BarChart3,
  AlertCircle,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  Activity,
  Zap,
} from 'lucide-react';
import {
  getUsageStats,
  UsageStatsResponse,
  formatNumber,
  formatResponseTime,
  getSuccessRateStatus,
  calculateTrend,
} from '@/lib/developer-tools-api';
import MiniSparkline from '@/components/analytics/MiniSparkline';
import RadialProgress from '@/components/analytics/RadialProgress';

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

  // Calculate derived metrics
  const metrics = useMemo(() => {
    if (!stats || stats.daily_breakdown.length === 0) return null;

    const breakdown = stats.daily_breakdown;
    const halfIndex = Math.floor(breakdown.length / 2);

    // Split data for trend comparison
    const recentHalf = breakdown.slice(0, halfIndex);
    const previousHalf = breakdown.slice(halfIndex);

    const recentQueries = recentHalf.reduce((sum, d) => sum + d.queries, 0);
    const previousQueries = previousHalf.reduce((sum, d) => sum + d.queries, 0);

    const recentFailed = recentHalf.reduce((sum, d) => sum + d.failed, 0);
    const previousFailed = previousHalf.reduce((sum, d) => sum + d.failed, 0);

    // Sparkline data (most recent 7 days, reversed for chronological order)
    const sparklineQueries = breakdown.slice(0, 7).map(d => d.queries).reverse();
    const sparklineSuccess = breakdown.slice(0, 7).map(d => d.successful).reverse();
    const sparklineResponse = breakdown.slice(0, 7).map(d => d.avg_response_ms).reverse();
    const sparklineFailed = breakdown.slice(0, 7).map(d => d.failed).reverse();

    return {
      queryTrend: calculateTrend(recentQueries, previousQueries),
      failedTrend: calculateTrend(recentFailed, previousFailed),
      sparklineQueries,
      sparklineSuccess,
      sparklineResponse,
      sparklineFailed,
    };
  }, [stats]);

  const responseTimeInfo = stats ? formatResponseTime(stats.avg_response_time_ms) : null;
  const successRateInfo = stats ? getSuccessRateStatus(stats.success_rate) : null;

  // Find max for chart scaling
  const maxQueries = stats?.daily_breakdown.length
    ? Math.max(...stats.daily_breakdown.map(d => d.queries), 1)
    : 1;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between bg-gradient-to-r from-purple-500/10 to-blue-500/10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/50 rounded-lg">
              <BarChart3 className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Usage Statistics
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">{agentName}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Period Selector */}
        <div className="px-6 py-3 border-b border-gray-200 dark:border-gray-800 flex items-center gap-2 bg-gray-50 dark:bg-gray-800/50">
          <span className="text-sm text-gray-600 dark:text-gray-400 mr-2">Period:</span>
          <div className="flex bg-white dark:bg-gray-800 rounded-lg p-1 shadow-sm border border-gray-200 dark:border-gray-700">
            {[7, 14, 30, 60, 90].map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={`px-3 py-1.5 text-sm rounded-md transition-all ${
                  days === d
                    ? 'bg-purple-500 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50 dark:bg-gray-900/50">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="h-10 w-10 animate-spin text-purple-500 mb-4" />
              <p className="text-gray-500 dark:text-gray-400">Loading statistics...</p>
            </div>
          ) : error ? (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 dark:text-red-400 flex items-center gap-3">
              <AlertCircle className="h-5 w-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : stats && (
            <div className="space-y-6">
              {/* KPI Cards Grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Total Queries Card */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Activity className="h-4 w-4" />
                      <span className="text-xs font-medium uppercase tracking-wide">Queries</span>
                    </div>
                    {metrics?.queryTrend && (
                      <div
                        className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{
                          color: metrics.queryTrend.color,
                          backgroundColor: metrics.queryTrend.isPositive ? '#10B98115' : '#EF444415',
                        }}
                      >
                        {metrics.queryTrend.direction === 'up' ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : metrics.queryTrend.direction === 'down' ? (
                          <TrendingDown className="h-3 w-3" />
                        ) : null}
                        {metrics.queryTrend.display}
                      </div>
                    )}
                  </div>
                  <div className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    {formatNumber(stats.total_queries)}
                  </div>
                  {metrics?.sparklineQueries && metrics.sparklineQueries.length > 1 && (
                    <MiniSparkline
                      data={metrics.sparklineQueries}
                      color="#8B5CF6"
                      height={28}
                      width={100}
                    />
                  )}
                </div>

                {/* Success Rate Card */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400 mb-2">
                    <CheckCircle className="h-4 w-4" style={{ color: successRateInfo?.color }} />
                    <span className="text-xs font-medium uppercase tracking-wide">Success Rate</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <div
                        className="text-2xl font-bold"
                        style={{ color: successRateInfo?.color }}
                      >
                        {stats.success_rate.toFixed(1)}%
                      </div>
                      <div
                        className="text-xs font-medium mt-1"
                        style={{ color: successRateInfo?.color }}
                      >
                        {successRateInfo?.label}
                      </div>
                    </div>
                    <RadialProgress
                      value={stats.success_rate}
                      size={52}
                      strokeWidth={4}
                      showValue={false}
                    />
                  </div>
                </div>

                {/* Response Time Card */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <Clock className="h-4 w-4" />
                      <span className="text-xs font-medium uppercase tracking-wide">Avg Response</span>
                    </div>
                    {responseTimeInfo && (
                      <div
                        className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{
                          color: responseTimeInfo.color,
                          backgroundColor: responseTimeInfo.color + '15',
                        }}
                      >
                        <Zap className="h-3 w-3" />
                        {responseTimeInfo.status === 'fast' ? 'Fast' : responseTimeInfo.status === 'normal' ? 'Normal' : 'Slow'}
                      </div>
                    )}
                  </div>
                  <div
                    className="text-2xl font-bold mb-2"
                    style={{ color: responseTimeInfo?.color }}
                  >
                    {responseTimeInfo?.display}
                  </div>
                  {metrics?.sparklineResponse && metrics.sparklineResponse.length > 1 && (
                    <MiniSparkline
                      data={metrics.sparklineResponse}
                      color={responseTimeInfo?.color || '#3B82F6'}
                      height={28}
                      width={100}
                    />
                  )}
                </div>

                {/* Failed Queries Card */}
                <div className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                      <XCircle className="h-4 w-4 text-red-500" />
                      <span className="text-xs font-medium uppercase tracking-wide">Failed</span>
                    </div>
                    {metrics?.failedTrend && stats.failed_queries > 0 && (
                      <div
                        className="flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full"
                        style={{
                          // For failed, down is good
                          color: !metrics.failedTrend.isPositive ? '#10B981' : '#EF4444',
                          backgroundColor: !metrics.failedTrend.isPositive ? '#10B98115' : '#EF444415',
                        }}
                      >
                        {metrics.failedTrend.direction === 'up' ? (
                          <TrendingUp className="h-3 w-3" />
                        ) : metrics.failedTrend.direction === 'down' ? (
                          <TrendingDown className="h-3 w-3" />
                        ) : null}
                        {metrics.failedTrend.display}
                      </div>
                    )}
                  </div>
                  <div className={`text-2xl font-bold mb-2 ${stats.failed_queries > 0 ? 'text-red-500' : 'text-gray-900 dark:text-white'}`}>
                    {formatNumber(stats.failed_queries)}
                  </div>
                  {metrics?.sparklineFailed && metrics.sparklineFailed.some(v => v > 0) && (
                    <MiniSparkline
                      data={metrics.sparklineFailed}
                      color="#EF4444"
                      height={28}
                      width={100}
                    />
                  )}
                  {stats.failed_queries === 0 && (
                    <div className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      No failures
                    </div>
                  )}
                </div>
              </div>

              {/* Daily Usage Trend Chart */}
              <div className="bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-500" />
                  Daily Usage Trend
                </h3>
                {stats.daily_breakdown.length === 0 ? (
                  <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                    <Activity className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No usage data for this period</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {stats.daily_breakdown.slice(0, 10).reverse().map((day, index) => {
                      const width = (day.queries / maxQueries) * 100;
                      const successWidth = day.queries > 0 ? (day.successful / day.queries) * 100 : 0;
                      const isToday = index === stats.daily_breakdown.slice(0, 10).length - 1;

                      return (
                        <div
                          key={day.date}
                          className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                            isToday ? 'bg-purple-50 dark:bg-purple-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-700/30'
                          }`}
                        >
                          <div className="w-16 text-xs text-gray-500 dark:text-gray-400 font-medium">
                            {new Date(day.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </div>
                          <div className="flex-1 h-7 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden relative">
                            {/* Background bar (total) */}
                            <div
                              className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-200 to-purple-100 dark:from-purple-900/50 dark:to-purple-800/30 rounded-full transition-all duration-500"
                              style={{ width: `${width}%` }}
                            />
                            {/* Success portion */}
                            <div
                              className="absolute inset-y-0 left-0 bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-500"
                              style={{ width: `${(width * successWidth) / 100}%` }}
                            />
                            {/* Query count inside bar */}
                            {day.queries > 0 && (
                              <span className="absolute inset-0 flex items-center justify-end pr-3 text-xs font-medium text-gray-700 dark:text-gray-300">
                                {formatNumber(day.queries)}
                              </span>
                            )}
                          </div>
                          <div className="w-20 flex items-center gap-2 justify-end text-xs">
                            <span className="text-green-600 dark:text-green-400">{day.successful}</span>
                            <span className="text-gray-400">/</span>
                            <span className="text-red-500">{day.failed}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
                {/* Legend */}
                {stats.daily_breakdown.length > 0 && (
                  <div className="flex items-center justify-end gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <div className="w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-purple-400" />
                      <span>Success</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                      <div className="w-3 h-3 rounded-full bg-purple-200 dark:bg-purple-900/50" />
                      <span>Total</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Detailed Breakdown Table */}
              {stats.daily_breakdown.length > 0 && (
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
                  <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center gap-2">
                      <Activity className="h-4 w-4 text-purple-500" />
                      Detailed Breakdown
                    </h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-gray-50 dark:bg-gray-800/50">
                          <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Date</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Queries</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Success</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Failed</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Avg Time</th>
                          <th className="px-4 py-3 text-right text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                        {stats.daily_breakdown.slice(0, 14).map((day) => {
                          const dayResponseInfo = formatResponseTime(day.avg_response_ms);
                          const daySuccessRate = day.queries > 0 ? (day.successful / day.queries) * 100 : 100;
                          const dayStatus = getSuccessRateStatus(daySuccessRate);

                          return (
                            <tr key={day.date} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                              <td className="px-4 py-3 text-gray-900 dark:text-white font-medium">
                                {new Date(day.date).toLocaleDateString(undefined, {
                                  weekday: 'short',
                                  month: 'short',
                                  day: 'numeric',
                                })}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-900 dark:text-white font-semibold">
                                {formatNumber(day.queries)}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
                                  <CheckCircle className="h-3 w-3" />
                                  {formatNumber(day.successful)}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span className={`inline-flex items-center gap-1 ${day.failed > 0 ? 'text-red-500' : 'text-gray-400'}`}>
                                  {day.failed > 0 && <XCircle className="h-3 w-3" />}
                                  {formatNumber(day.failed)}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span
                                  className="font-medium"
                                  style={{ color: dayResponseInfo.color }}
                                >
                                  {dayResponseInfo.shortDisplay}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right">
                                <span
                                  className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                                  style={{
                                    color: dayStatus.color,
                                    backgroundColor: dayStatus.color + '15',
                                  }}
                                >
                                  {daySuccessRate.toFixed(0)}%
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 flex justify-end bg-white dark:bg-gray-900">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-100 rounded-lg transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
