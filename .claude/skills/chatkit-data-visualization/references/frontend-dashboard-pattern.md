# Frontend Dashboard Pattern for Data Visualization

> This reference explains how to create split-panel dashboards with ChatKit + visualization panel using Next.js and Recharts.

---

## Overview

The dashboard pattern consists of:
1. **Left Panel**: ChatKit widget for AI conversation
2. **Right Panel**: Live visualizations (metrics + charts)
3. **Stream Capture**: Intercept AI response to trigger visualization
4. **Chart Rendering**: Recharts components for different chart types

---

## Complete Page Template

```tsx
// frontend/app/your-domain/page.tsx

'use client';

import { useEffect, useState, useRef, useCallback } from 'react';
import Script from 'next/script';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// ============================================
// TYPES
// ============================================

interface MetricData {
  title: string;
  value: string;
  subtitle?: string;
  status?: 'success' | 'warning' | 'danger' | 'neutral';
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

// ============================================
// CONSTANTS
// ============================================

const COLORS = [
  '#3B82F6', // Blue
  '#10B981', // Green
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#EC4899', // Pink
  '#06B6D4', // Cyan
  '#84CC16', // Lime
];

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================
// SESSION ID GENERATOR
// ============================================

const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session-${timestamp}-${random}`;
};

// ============================================
// MAIN COMPONENT
// ============================================

export default function YourDomainDashboard() {
  // State
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [charts, setCharts] = useState<ChartConfig[]>([]);
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [lastQuery, setLastQuery] = useState<string>('');
  const [isLoadingViz, setIsLoadingViz] = useState(false);

  // Refs
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Session ID (persistent per tab)
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('your-domain-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('your-domain-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  // ============================================
  // FETCH VISUALIZATION
  // ============================================

  const fetchVisualization = useCallback(async (
    query: string,
    responseText?: string
  ) => {
    if (!query) return;

    setIsLoadingViz(true);
    console.log('[Dashboard] Fetching visualization for:', query);

    try {
      const response = await fetch(`${API_BASE_URL}/your-domain/visualize`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`, // Add if needed
        },
        body: JSON.stringify({
          query: query,
          response_text: responseText || '',
        })
      });

      const data: VisualizationResponse = await response.json();
      console.log('[Dashboard] Visualization response:', data);

      if (data.success) {
        setMetrics(data.metrics || []);
        setCharts(data.charts || []);
        setLastQuery(query);
      }
    } catch (error) {
      console.error('[Dashboard] Visualization fetch error:', error);
    } finally {
      setIsLoadingViz(false);
    }
  }, []);

  // ============================================
  // CONFIGURE CHATKIT
  // ============================================

  useEffect(() => {
    if (!isChatkitLoaded) return;
    if (configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      console.log('[Dashboard] Configuring ChatKit');
      configuredRef.current = true;

      let currentQuery = '';

      chatkit.setOptions({
        api: {
          url: `${API_BASE_URL}/agent/chatkit`,
          domainKey: '',
          fetch: async (url: string, options: RequestInit) => {
            try {
              const body = options.body ? JSON.parse(options.body as string) : {};
              body.session_id = sessionId;

              // Capture user query from input
              if (body.params?.input?.content) {
                const inputText = body.params.input.content.find(
                  (c: any) => c.type === 'input_text'
                )?.text;
                if (inputText) {
                  currentQuery = inputText;
                }
              }

              // Make request
              const response = await fetch(url, {
                ...options,
                body: JSON.stringify(body),
                headers: {
                  ...options.headers,
                  'Content-Type': 'application/json',
                },
              });

              // Clone response to read for visualization
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

                            // Capture text content
                            if (data.type === 'assistant_message.content_part.text_delta' &&
                                data.delta) {
                              responseText += data.delta;
                            }

                            // When response complete, trigger visualization
                            if (data.type === 'thread.item.done' &&
                                data.item?.type === 'assistant_message') {
                              // Small delay to ensure full response
                              setTimeout(() => {
                                fetchVisualization(currentQuery, responseText);
                              }, 200);
                            }
                          } catch (e) {
                            // Ignore JSON parse errors
                          }
                        }
                      }
                    }
                  } catch (e) {
                    console.error('[Dashboard] Stream read error:', e);
                  }
                })();
              }

              return response;
            } catch (e) {
              console.error('[Dashboard] ChatKit fetch error:', e);
              throw e;
            }
          },
        },
        theme: 'light',
        header: {
          enabled: true,
          title: {
            enabled: true,
            text: 'AI Assistant',
          },
        },
        startScreen: {
          greeting: 'Ask me anything! Charts will appear automatically.',
          prompts: [
            { label: 'Overview', prompt: 'Show me an overview' },
            { label: 'Trends', prompt: 'Show me trends' },
            { label: 'Top Items', prompt: 'What are the top items?' },
            { label: 'Alerts', prompt: 'Are there any alerts?' },
          ],
        },
        composer: {
          placeholder: 'Ask about your data...',
        },
        disclaimer: {
          text: 'Charts are generated from your actual data.',
        },
      });
    };

    setTimeout(initChatKit, 300);
  }, [isChatkitLoaded, sessionId, fetchVisualization]);

  // ============================================
  // CHECK CHATKIT ELEMENT REGISTRATION
  // ============================================

  useEffect(() => {
    // Check if already registered
    if (customElements.get('openai-chatkit')) {
      console.log('[Dashboard] ChatKit already registered');
      setIsChatkitLoaded(true);
      setScriptLoaded(true);
      return;
    }

    // Poll for element registration
    let attempts = 0;
    const maxAttempts = 200; // 10 seconds

    const checkElement = () => {
      attempts++;
      if (customElements.get('openai-chatkit')) {
        console.log('[Dashboard] ChatKit registered after', attempts, 'attempts');
        setIsChatkitLoaded(true);
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
      } else if (attempts >= maxAttempts) {
        console.error('[Dashboard] ChatKit not registered after max attempts');
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
      }
    };

    checkIntervalRef.current = setInterval(checkElement, 50);

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
    };
  }, []);

  // ============================================
  // SCRIPT LOAD HANDLER
  // ============================================

  const handleScriptLoad = () => {
    console.log('[Dashboard] ChatKit script loaded');
    setScriptLoaded(true);

    if (customElements.get('openai-chatkit')) {
      setIsChatkitLoaded(true);
    }
  };

  // ============================================
  // VALUE FORMATTERS
  // ============================================

  const formatValue = (value: number, format?: string) => {
    if (format === 'currency') return `$${value.toLocaleString()}`;
    if (format === 'percentage') return `${value}%`;
    return value.toLocaleString();
  };

  // ============================================
  // CHART RENDERERS
  // ============================================

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
                <XAxis
                  type="number"
                  tick={{ fontSize: 11 }}
                  tickFormatter={(v) => formatValue(v, chart.formatValue)}
                />
                <YAxis
                  type="category"
                  dataKey={chart.xAxisKey}
                  tick={{ fontSize: 11 }}
                  width={95}
                />
                <Tooltip
                  formatter={(value: number) => [
                    formatValue(value, chart.formatValue),
                    'Value'
                  ]}
                />
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
              <LineChart
                data={chart.data}
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey={chart.xAxisKey}
                  tick={{ fontSize: 10 }}
                />
                <YAxis
                  tick={{ fontSize: 10 }}
                  tickFormatter={(v) => formatValue(v, chart.formatValue)}
                />
                <Tooltip
                  formatter={(value: number) => [
                    formatValue(value, chart.formatValue),
                    'Value'
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey={chart.dataKey}
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ r: 3 }}
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
                  label={({ name, value }) =>
                    `${name}: ${formatValue(value, chart.formatValue)}`
                  }
                >
                  {chart.data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number) =>
                    formatValue(value, chart.formatValue)
                  }
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  // ============================================
  // RENDER
  // ============================================

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Load ChatKit Script */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
      />

      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">Your Domain Dashboard</h1>
          {/* Add navigation, user info, etc. */}
        </div>
      </header>

      {/* Main Content - Split Panel */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <div className="h-[calc(100vh-180px)] flex gap-4">
          {/* Left Panel: ChatKit */}
          <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Panel Header */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3">
              <h2 className="font-semibold flex items-center">
                <span className="mr-2">🤖</span>
                AI Assistant
              </h2>
              <p className="text-xs text-blue-100 mt-1">
                Ask questions - charts appear automatically
              </p>
            </div>

            {/* ChatKit Container */}
            <div className="flex-1 relative">
              {!isChatkitLoaded ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3" />
                    <p className="text-gray-500">Loading ChatKit...</p>
                  </div>
                </div>
              ) : (
                <openai-chatkit
                  ref={chatkitRef as any}
                  id="dashboard-chatkit"
                  style={{ width: '100%', height: '100%', display: 'block' }}
                />
              )}
            </div>
          </div>

          {/* Right Panel: Visualizations */}
          <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Panel Header */}
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-3">
              <h2 className="font-semibold flex items-center">
                <span className="mr-2">📊</span>
                Live Visualizations
              </h2>
              <p className="text-xs text-purple-100 mt-1">
                {lastQuery ? `Query: "${lastQuery}"` : 'Charts from your data'}
              </p>
            </div>

            {/* Visualizations Container */}
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
              {isLoadingViz ? (
                <div className="flex items-center justify-center h-32">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
                  <span className="ml-3 text-gray-500">Loading charts...</span>
                </div>
              ) : charts.length === 0 && metrics.length === 0 ? (
                <div className="text-center py-8">
                  <div className="text-6xl mb-4 opacity-50">📈</div>
                  <p className="text-gray-500 mb-2">Charts appear here automatically</p>
                  <p className="text-gray-400 text-sm">
                    Ask a question and charts will be
                    <br />
                    generated from your data!
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
                            m.status === 'danger'
                              ? 'bg-red-50 border-red-200'
                              : m.status === 'warning'
                              ? 'bg-yellow-50 border-yellow-200'
                              : m.status === 'success'
                              ? 'bg-green-50 border-green-200'
                              : 'bg-white border-gray-200'
                          }`}
                        >
                          <div className="text-xs text-gray-500 mb-1 truncate">
                            {m.title}
                          </div>
                          <div
                            className={`text-xl font-bold ${
                              m.status === 'danger'
                                ? 'text-red-600'
                                : m.status === 'warning'
                                ? 'text-yellow-600'
                                : m.status === 'success'
                                ? 'text-green-600'
                                : 'text-gray-800'
                            }`}
                          >
                            {m.value}
                          </div>
                          {m.subtitle && (
                            <div className="text-xs text-gray-400 mt-1">
                              {m.subtitle}
                            </div>
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
      </main>

      {/* ChatKit CSS Variables */}
      <style jsx global>{`
        openai-chatkit {
          --chatkit-primary-color: #2563eb;
          --chatkit-background: #ffffff;
          --chatkit-text-color: #1f2937;
          --chatkit-border-radius: 8px;
        }
      `}</style>
    </div>
  );
}

// TypeScript declaration for openai-chatkit custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'openai-chatkit': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement>,
        HTMLElement
      >;
    }
  }
}
```

---

## Key Components Explained

### 1. Session ID Management

```tsx
const [sessionId] = useState(() => {
  if (typeof window !== 'undefined') {
    let id = sessionStorage.getItem('your-domain-session-id');
    if (!id) {
      id = generateSessionId();
      sessionStorage.setItem('your-domain-session-id', id);
    }
    return id;
  }
  return generateSessionId();
});
```

- Uses `sessionStorage` for tab-lifetime persistence
- Same tab = same session (keeps conversation history)
- New tab = new session

### 2. Stream Response Capture

```tsx
// Clone response to read for visualization
const clonedResponse = response.clone();
const reader = clonedResponse.body?.getReader();

// Read in background
(async () => {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    // Parse SSE events to capture response text
    // Trigger visualization on completion
  }
})();

return response; // Return original (not cloned)
```

- Clone response before reading (so ChatKit still gets original)
- Parse SSE events to extract text content
- Trigger visualization when `thread.item.done` received

### 3. Metrics Cards with Status

```tsx
<div className={`p-4 rounded-lg border shadow-sm ${
  m.status === 'danger' ? 'bg-red-50 border-red-200' :
  m.status === 'warning' ? 'bg-yellow-50 border-yellow-200' :
  m.status === 'success' ? 'bg-green-50 border-green-200' :
  'bg-white border-gray-200'
}`}>
```

- Conditional styling based on metric status
- Green for success, yellow for warning, red for danger

---

## Dependencies

```json
{
  "dependencies": {
    "next": "^14.x",
    "react": "^18.x",
    "recharts": "^2.x"
  }
}
```

---

## Customization Points

1. **Panel widths**: Change `w-1/2` to adjust split ratio
2. **Colors**: Modify `COLORS` array for brand colors
3. **Chart heights**: Adjust `chartHeight` calculation
4. **Start prompts**: Customize `startScreen.prompts` for your domain
5. **Header gradients**: Change gradient classes for branding
