/**
 * Dashboard Analytics Page
 *
 * AI Analytics Dashboard that connects to:
 * - User's MCP server (if user has own_database)
 * - Our database (if user has our_database)
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
import { ROUTES, APP_METADATA, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// Types for visualization
interface MetricData {
  title: string;
  value: string;
  subtitle?: string;
  status?: 'success' | 'warning' | 'danger';
}

interface ChartConfig {
  type: 'bar' | 'line' | 'pie';
  title: string;
  data: Array<{ name: string; value: number; [key: string]: any }>;
  dataKey: string;
  xAxisKey: string;
  color?: string;
  formatValue?: 'currency' | 'number' | 'percentage';
}

interface VisualizationResponse {
  success: boolean;
  query: string;
  metrics: MetricData[];
  charts: ChartConfig[];
  error?: string;
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `analytics-${timestamp}-${random}`;
};

export default function DashboardAnalyticsPage() {
  const { user, connectionStatus, logout, isLoading } = useAuth();
  const router = useRouter();

  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [isLoadingViz, setIsLoadingViz] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Determine which API endpoint to use based on user's connection type
  const isOwnDatabase = connectionStatus?.connection_type === 'own_database';
  const mcpConnected = connectionStatus?.mcp_status === 'connected';

  // For own_database users, use the MCP session_id from connection status
  // For our_database users, use a generated session ID
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('dashboard-analytics-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('dashboard-analytics-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  // Get the actual MCP session ID for own_database users
  const mcpSessionId = connectionStatus?.mcp_session_id;

  // Check if user with own database needs to connect MCP first
  // Also redirect if MCP is "connected" but session ID is missing (incomplete state)
  useEffect(() => {
    if (!isLoading && isOwnDatabase) {
      if (!mcpConnected || (mcpConnected && !mcpSessionId)) {
        console.log('[Dashboard Analytics] Redirecting to connect - mcpConnected:', mcpConnected, 'mcpSessionId:', mcpSessionId);
        // Redirect to connect page to establish MCP connection first
        router.push(ROUTES.DB_CONNECT);
      }
    }
  }, [isLoading, isOwnDatabase, mcpConnected, mcpSessionId, router]);

  // Fetch visualization data
  const fetchVisualization = useCallback(async (query: string, responseText?: string) => {
    if (!query) return;

    setIsLoadingViz(true);
    console.log('[Dashboard Analytics] Fetching visualization for:', query);

    try {
      const response = await fetch(`${API_BASE_URL}/analytics/visualize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
          query: query,
          response_text: responseText || '',
          user_id: user?.id,
          use_mcp: isOwnDatabase && mcpConnected,
        })
      });

      const data: VisualizationResponse = await response.json();
      console.log('[Dashboard Analytics] Visualization response:', data);

      if (data.success) {
        setMetrics(data.metrics || []);
        setCharts(data.charts || []);
        setLastQuery(query);
      }
    } catch (error) {
      console.error('[Dashboard Analytics] Failed to fetch visualization:', error);
    } finally {
      setIsLoadingViz(false);
    }
  }, [user?.id, isOwnDatabase, mcpConnected]);

  // Configure ChatKit when loaded
  // For own_database users, wait until mcpSessionId is available
  useEffect(() => {
    // Don't configure if not loaded yet
    if (!isChatkitLoaded) return;

    // For own_database users, don't configure until we have the MCP session ID
    if (isOwnDatabase && (!mcpConnected || !mcpSessionId)) {
      console.log('[Dashboard Analytics] Waiting for MCP session before configuring ChatKit');
      return;
    }

    // Allow reconfiguration when session changes
    // Reset configuredRef when key params change
    configuredRef.current = false;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      console.log('[Dashboard Analytics] Configuring ChatKit');
      console.log('[Dashboard Analytics] Connection status:', {
        isOwnDatabase,
        mcpConnected,
        mcpSessionId,
        sessionId
      });

      configuredRef.current = true;

      let currentQuery = '';

      // Determine the API URL based on connection type
      const apiUrl = isOwnDatabase && mcpConnected
        ? `${API_BASE_URL}/inventory-agent/chatkit`  // User's MCP
        : `${API_BASE_URL}/agent/chatkit`;  // Our database

      chatkit.setOptions({
        api: {
          url: apiUrl,
          domainKey: '',
          fetch: async (url: string, options: RequestInit) => {
            try {
              const body = options.body ? JSON.parse(options.body as string) : {};
              // For own_database users with MCP, use the MCP session ID
              const bodySessionId = isOwnDatabase && mcpConnected && mcpSessionId
                ? mcpSessionId
                : sessionId;
              body.session_id = bodySessionId;
              body.user_id = user?.id;

              // Capture user message
              if (body.params?.input?.content) {
                const inputText = body.params.input.content.find((c: any) => c.type === 'input_text')?.text;
                if (inputText) {
                  currentQuery = inputText;
                }
              }

              // For own_database users with MCP connected, use the MCP session ID
              // Otherwise use the generated session ID for our_database users
              const effectiveSessionId = isOwnDatabase && mcpConnected && mcpSessionId
                ? mcpSessionId
                : sessionId;

              console.log('[Dashboard Analytics] Using session ID:', effectiveSessionId,
                'isOwnDatabase:', isOwnDatabase, 'mcpConnected:', mcpConnected);

              const response = await fetch(url, {
                ...options,
                body: JSON.stringify(body),
                headers: {
                  ...options.headers,
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${getAccessToken()}`,
                  'x-session-id': effectiveSessionId,
                },
              });

              // Clone response to read for visualization trigger
              const clonedResponse = response.clone();
              const reader = clonedResponse.body?.getReader();

              if (reader && currentQuery) {
                const decoder = new TextDecoder();
                let responseText = '';

                (async () => {
                  try {
                    while (true) {
                      const { done, value } = await reader.read();
                      if (done) break;

                      const chunk = decoder.decode(value, { stream: true });
                      const lines = chunk.split('\n');

                      for (const line of lines) {
                        if (line.startsWith('data: ')) {
                          try {
                            const data = JSON.parse(line.slice(6));
                            if (data.type === 'assistant_message.content_part.text_delta' && data.delta) {
                              responseText += data.delta;
                            }
                            if (data.type === 'thread.item.done' && data.item?.type === 'assistant_message') {
                              setTimeout(() => {
                                fetchVisualization(currentQuery, responseText);
                              }, 200);
                            }
                          } catch (e) { }
                        }
                      }
                    }
                  } catch (e) {
                    console.error('[Dashboard Analytics] Stream read error:', e);
                  }
                })();
              }

              return response;
            } catch (e) {
              console.error('ChatKit fetch error:', e);
              throw e;
            }
          },
        },
        theme: 'light',
        header: {
          enabled: true,
          title: {
            enabled: true,
            text: isOwnDatabase ? 'Your Database Analytics' : 'AI Analytics Assistant',
          },
        },
        startScreen: {
          greeting: isOwnDatabase
            ? 'Connected to YOUR database! Ask me anything about your data.'
            : 'Ask me anything about your inventory! Charts will appear automatically.',
          prompts: [
            { label: 'Stock Check', prompt: 'Show me current stock levels' },
            { label: 'Overview', prompt: 'Show me inventory overview' },
            { label: 'Low Stock', prompt: 'Which items are low on stock?' },
            { label: 'Sales Trend', prompt: 'Show me sales trend' },
          ],
        },
        composer: {
          placeholder: 'Ask about inventory, sales, products...',
        },
        disclaimer: {
          text: isOwnDatabase
            ? 'Connected to your own PostgreSQL database via MCP.'
            : 'Charts are generated from your actual database.',
        },
      });
    };

    setTimeout(initChatKit, 300);
  }, [isChatkitLoaded, sessionId, mcpSessionId, user?.id, isOwnDatabase, mcpConnected, fetchVisualization]);

  // Handle script load
  const handleScriptLoad = () => {
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        setIsChatkitLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  // Format value for display
  const formatValue = (value: number, format?: string) => {
    if (format === 'currency') return `$${value.toLocaleString()}`;
    if (format === 'percentage') return `${value}%`;
    return value.toLocaleString();
  };

  // Render chart
  const renderChart = (chart: ChartConfig, index: number) => {
    const chartHeight = Math.max(200, chart.data.length * 35);

    switch (chart.type) {
      case 'bar':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-3">{chart.title}</h4>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <BarChart data={chart.data} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => formatValue(v, chart.formatValue)} />
                <YAxis type="category" dataKey={chart.xAxisKey} tick={{ fontSize: 11 }} width={95} />
                <Tooltip formatter={(value: number) => [formatValue(value, chart.formatValue), 'Value']} />
                <Bar dataKey={chart.dataKey} radius={[0, 4, 4, 0]}>
                  {chart.data.map((_, i) => (
                    <Cell key={i} fill={chart.color || COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'line':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-3">{chart.title}</h4>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chart.data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey={chart.xAxisKey} tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => formatValue(v, chart.formatValue)} />
                <Tooltip formatter={(value: number) => [formatValue(value, chart.formatValue), 'Value']} />
                <Line type="monotone" dataKey={chart.dataKey} stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'pie':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-3">{chart.title}</h4>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={chart.data}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey={chart.dataKey}
                  label={({ name, value }) => `${name}: ${formatValue(value, chart.formatValue)}`}
                >
                  {chart.data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatValue(value, chart.formatValue)} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        {/* Load ChatKit */}
        <Script
          src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
          strategy="afterInteractive"
          onLoad={handleScriptLoad}
        />

        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-6">
              <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl font-bold">S</span>
                </div>
                <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
              </Link>
              <nav className="hidden md:flex space-x-4">
                {!isOwnDatabase && (
                  <>
                    <Link href={ROUTES.ADMIN} className="text-gray-600 hover:text-gray-900">Admin</Link>
                    <Link href={ROUTES.POS} className="text-gray-600 hover:text-gray-900">POS</Link>
                  </>
                )}
                <Link href={ROUTES.ANALYTICS} className="text-blue-600 font-medium">Analytics</Link>
                {isOwnDatabase && (
                  <Link href={ROUTES.DB_CONNECT} className="text-gray-600 hover:text-gray-900">Connection</Link>
                )}
              </nav>
            </div>
            <div className="flex items-center space-x-4">
              {isOwnDatabase && (
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                  Your Database
                </span>
              )}
              <span className="text-gray-600 text-sm">{user?.email}</span>
              <button onClick={logout} className="text-gray-600 hover:text-gray-900 text-sm">
                Logout
              </button>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="h-[calc(100vh-180px)] flex gap-4">
            {/* Left: ChatKit Panel */}
            <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className={`${isOwnDatabase ? 'bg-gradient-to-r from-blue-600 to-cyan-600' : 'bg-gradient-to-r from-blue-600 to-indigo-600'} text-white px-4 py-3`}>
                <h2 className="font-semibold flex items-center">
                  <span className="mr-2">{isOwnDatabase ? '🔗' : '🤖'}</span>
                  {isOwnDatabase ? 'Your Database Analytics' : 'IMS AI Analytics Assistant'}
                </h2>
                <p className="text-xs text-blue-100 mt-1">
                  {isOwnDatabase
                    ? 'Connected to your PostgreSQL via MCP'
                    : 'Ask questions - charts appear automatically'}
                </p>
              </div>

              <div className="flex-1 relative">
                {/* Show loading if ChatKit not loaded OR if own_database but no MCP session yet */}
                {!isChatkitLoaded ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
                      <p className="text-gray-500">Loading ChatKit...</p>
                    </div>
                  </div>
                ) : isOwnDatabase && (!mcpConnected || !mcpSessionId) ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-cyan-600 mx-auto mb-3"></div>
                      <p className="text-gray-500 mb-2">Connecting to your database...</p>
                      <p className="text-gray-400 text-sm">Please wait or go to Connection page</p>
                    </div>
                  </div>
                ) : (
                  <openai-chatkit
                    ref={chatkitRef as any}
                    id="dashboard-analytics-chatkit"
                    style={{ width: '100%', height: '100%', display: 'block' }}
                  />
                )}
              </div>
            </div>

            {/* Right: Visualization Panel */}
            <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-3">
                <h2 className="font-semibold flex items-center">
                  <span className="mr-2">📊</span>
                  Live Visualizations
                </h2>
                <p className="text-xs text-purple-100 mt-1">
                  {lastQuery ? `Query: "${lastQuery}"` : 'Charts from your data'}
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
                {isLoadingViz ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                    <span className="ml-3 text-gray-500">Loading charts...</span>
                  </div>
                ) : charts.length === 0 && metrics.length === 0 ? (
                  <div className="text-center py-8">
                    <div className="text-6xl mb-4 opacity-50">📈</div>
                    <p className="text-gray-500 mb-2">Charts appear here automatically</p>
                    <p className="text-gray-400 text-sm mb-4">
                      Ask a question and charts will be<br />
                      generated from your {isOwnDatabase ? 'database' : 'inventory'}!
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Metrics Cards */}
                    {metrics.length > 0 && (
                      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {metrics.map((m, i) => (
                          <div
                            key={i}
                            className={`p-4 rounded-lg border shadow-sm ${
                              m.status === 'danger' ? 'bg-red-50 border-red-200' :
                              m.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
                              m.status === 'success' ? 'bg-green-50 border-green-200' :
                              'bg-white border-gray-200'
                            }`}
                          >
                            <div className="text-xs text-gray-500 mb-1 truncate">{m.title}</div>
                            <div className={`text-xl font-bold ${
                              m.status === 'danger' ? 'text-red-600' :
                              m.status === 'warning' ? 'text-yellow-600' :
                              m.status === 'success' ? 'text-green-600' :
                              'text-gray-800'
                            }`}>
                              {m.value}
                            </div>
                            {m.subtitle && <div className="text-xs text-gray-400 mt-1">{m.subtitle}</div>}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Charts */}
                    {charts.map((chart, i) => renderChart(chart, i))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* ChatKit CSS Variables */}
      <style jsx global>{`
        openai-chatkit {
          --chatkit-primary-color: #2563eb;
          --chatkit-background: #ffffff;
          --chatkit-text-color: #1f2937;
          --chatkit-border-radius: 8px;
        }
      `}</style>
    </ErrorBoundary>
  );
}

// Note: TypeScript declaration for openai-chatkit is in db-connect/page.tsx
