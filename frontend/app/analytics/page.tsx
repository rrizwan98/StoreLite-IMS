/**
 * AI Analytics Dashboard with Pure OpenAI ChatKit + Structured Visualization API
 *
 * Architecture:
 * 1. ChatKit handles chat (unchanged)
 * 2. After response, calls /analytics/visualize API with query
 * 3. API returns structured chart data
 * 4. Frontend renders charts with Recharts
 */

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import Script from 'next/script';
import { API_BASE_URL } from '@/lib/constants';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// Types for visualization data from API
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
  intent?: {
    inventory: boolean;
    sales: boolean;
    trend: boolean;
    products: string[];
  };
  error?: string;
}

// Chart colors
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

// Generate session ID
const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `analytics-${timestamp}-${random}`;
};

export default function AnalyticsPage() {
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [isLoaded, setIsLoaded] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [isLoadingViz, setIsLoadingViz] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('analytics-chatkit-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('analytics-chatkit-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  /**
   * Fetch visualization data from the new API endpoint
   */
  const fetchVisualization = useCallback(async (query: string, responseText?: string) => {
    if (!query) return;

    setIsLoadingViz(true);
    console.log('[Analytics] Fetching visualization for:', query);

    try {
      const response = await fetch(`${API_BASE_URL}/analytics/visualize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          response_text: responseText || ''
        })
      });

      const data: VisualizationResponse = await response.json();
      console.log('[Analytics] Visualization response:', data);

      if (data.success) {
        setMetrics(data.metrics || []);
        setCharts(data.charts || []);
        setLastQuery(query);
      } else {
        console.error('[Analytics] Visualization error:', data.error);
      }
    } catch (error) {
      console.error('[Analytics] Failed to fetch visualization:', error);
    } finally {
      setIsLoadingViz(false);
    }
  }, []);

  // Configure ChatKit when loaded
  useEffect(() => {
    if (!isLoaded || configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      console.log('[Analytics] Configuring ChatKit');
      configuredRef.current = true;

      // Store the last user query
      let currentQuery = '';

      chatkit.setOptions({
        api: {
          url: `${API_BASE_URL}/agent/chatkit`,
          domainKey: '',
          fetch: async (url: string, options: RequestInit) => {
            try {
              const body = options.body ? JSON.parse(options.body as string) : {};
              body.session_id = sessionId;

              // Capture user message
              if (body.params?.input?.content) {
                const inputText = body.params.input.content.find((c: any) => c.type === 'input_text')?.text;
                if (inputText) {
                  currentQuery = inputText;
                  console.log('[Analytics] User query:', inputText);
                }
              }

              const response = await fetch(url, {
                ...options,
                body: JSON.stringify(body),
                headers: {
                  ...options.headers,
                  'Content-Type': 'application/json',
                },
              });

              // Clone response to read for visualization trigger
              const clonedResponse = response.clone();
              const reader = clonedResponse.body?.getReader();

              if (reader && currentQuery) {
                const decoder = new TextDecoder();
                let responseText = '';

                // Read stream in background
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

                            // Capture response text
                            if (data.type === 'assistant_message.content_part.text_delta' && data.delta) {
                              responseText += data.delta;
                            }

                            // When thread item is done, fetch visualization
                            if (data.type === 'thread.item.done' && data.item?.type === 'assistant_message') {
                              console.log('[Analytics] Response complete, fetching visualization');
                              // Small delay to ensure UI updates
                              setTimeout(() => {
                                fetchVisualization(currentQuery, responseText);
                              }, 200);
                            }
                          } catch (e) {
                            // Not JSON, skip
                          }
                        }
                      }
                    }
                  } catch (e) {
                    console.error('[Analytics] Stream read error:', e);
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
            text: 'AI Analytics Assistant',
          },
        },
        startScreen: {
          greeting: 'Ask me anything about your inventory! Charts will appear automatically.',
          prompts: [
            { label: 'Stock Check', prompt: 'Show me stock of Dollar pancel and oil' },
            { label: 'All Inventory', prompt: 'Show me inventory overview' },
            { label: 'Low Stock', prompt: 'Which items are low on stock?' },
            { label: 'Sales Trend', prompt: 'Show me sales trend' },
          ],
        },
        composer: {
          placeholder: 'Ask about inventory, sales, products...',
        },
        disclaimer: {
          text: 'Charts are generated from your actual database.',
        },
      });
    };

    setTimeout(initChatKit, 300);
  }, [isLoaded, sessionId, fetchVisualization]);

  // Handle script load with fast polling
  const handleScriptLoad = () => {
    console.log('[Analytics] ChatKit script loaded');
    setScriptLoaded(true);

    let attempts = 0;
    const maxAttempts = 100; // 5 seconds max (50ms * 100)

    const checkElement = () => {
      attempts++;
      if (customElements.get('openai-chatkit')) {
        console.log('[Analytics] ChatKit element registered after', attempts, 'attempts');
        setIsLoaded(true);
      } else if (attempts < maxAttempts) {
        setTimeout(checkElement, 50); // Fast polling every 50ms
      } else {
        console.error('[Analytics] ChatKit element not registered after max attempts');
        setLoadError('ChatKit failed to initialize. Please refresh the page.');
      }
    };

    // Start checking immediately
    checkElement();
  };

  // Format value for display
  const formatValue = (value: number, format?: string) => {
    if (format === 'currency') {
      return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    }
    if (format === 'percentage') {
      return `${value}%`;
    }
    return value.toLocaleString();
  };

  // Render chart based on type
  const renderChart = (chart: ChartConfig, index: number) => {
    const chartHeight = Math.max(200, chart.data.length * 35);

    switch (chart.type) {
      case 'bar':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm">
            <h4 className="font-semibold text-gray-800 mb-3">{chart.title}</h4>
            <ResponsiveContainer width="100%" height={chartHeight}>
              <BarChart
                data={chart.data}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
              >
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
                <Line
                  type="monotone"
                  dataKey={chart.dataKey}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ r: 3, fill: '#3B82F6' }}
                  activeDot={{ r: 6 }}
                />
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
                  labelLine={{ strokeWidth: 1 }}
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

  return (
    <ErrorBoundary>
      {/* Load ChatKit from OpenAI CDN - afterInteractive for faster loading */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => {
          console.error('Failed to load ChatKit:', e);
          setLoadError('Failed to load ChatKit script. Please check your network connection.');
        }}
      />

      <div className="h-[calc(100vh-120px)] flex gap-4">
        {/* Left: ChatKit Panel */}
        <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3">
            <h2 className="font-semibold flex items-center">
              <span className="mr-2">🤖</span>
              IMS AI Analytics Assistant
            </h2>
            <p className="text-xs text-blue-100 mt-1">Ask questions - charts appear automatically</p>
          </div>

          <div className="flex-1 relative">
            {loadError ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center p-6">
                  <div className="text-red-500 text-4xl mb-4">⚠️</div>
                  <p className="text-red-600 font-medium mb-2">ChatKit Error</p>
                  <p className="text-gray-500 text-sm mb-4">{loadError}</p>
                  <button
                    onClick={() => window.location.reload()}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Refresh Page
                  </button>
                </div>
              </div>
            ) : isLoaded ? (
              <openai-chatkit
                ref={chatkitRef as any}
                id="analytics-chatkit"
                style={{
                  width: '100%',
                  height: '100%',
                  display: 'block',
                }}
              />
            ) : (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
                  <p className="text-gray-500">Loading ChatKit...</p>
                  {scriptLoaded && <p className="text-gray-400 text-xs mt-2">Initializing component...</p>}
                </div>
              </div>
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
              {lastQuery ? `Query: "${lastQuery}"` : 'Charts from your database'}
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
                  Ask a question in the chat and charts will be<br />
                  generated from your actual database!
                </p>
                <div className="bg-blue-50 rounded-lg p-4 text-left max-w-sm mx-auto">
                  <p className="text-xs text-blue-700 font-medium mb-2">Try asking:</p>
                  <ul className="text-xs text-blue-600 space-y-1">
                    <li>Show me stock of Dollar pancel and oil</li>
                    <li>What is the inventory overview?</li>
                    <li>Which items are low on stock?</li>
                    <li>Show me sales trend</li>
                  </ul>
                </div>
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
                        <div className="text-xs text-gray-500 mb-1 truncate" title={m.title}>
                          {m.title}
                        </div>
                        <div className={`text-xl font-bold ${
                          m.status === 'danger' ? 'text-red-600' :
                          m.status === 'warning' ? 'text-yellow-600' :
                          m.status === 'success' ? 'text-green-600' :
                          'text-gray-800'
                        }`}>
                          {m.value}
                        </div>
                        {m.subtitle && (
                          <div className="text-xs text-gray-400 mt-1">{m.subtitle}</div>
                        )}
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
    </ErrorBoundary>
  );
}

// Note: TypeScript declaration for openai-chatkit is in ChatKitWidget.tsx
