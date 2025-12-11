/**
 * AI Analytics Dashboard - Hybrid Approach
 *
 * 1. Uses /agent/chat-legacy for natural language AI responses
 * 2. Uses /analytics/* endpoints for structured visualization data
 * 3. Uses /inventory endpoint for product-specific queries
 *
 * This ensures both accurate AI responses AND reliable chart data
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import { API_BASE_URL } from '@/lib/constants';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Types
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

interface Visualization {
  type: 'bar' | 'line' | 'pie' | 'metric';
  title: string;
  data: ChartData[];
}

interface MetricData {
  title: string;
  value: string;
  icon?: string;
}

// Colors for charts
const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16'];

// Detect query intent
function detectQueryIntent(query: string): { type: string; endpoint: string } | null {
  const lower = query.toLowerCase();

  // Inventory/Stock queries for specific products
  if (lower.includes('pencil') || lower.includes('pancel') || lower.includes('dollar') ||
      (lower.includes('stock') && (lower.includes('show') || lower.includes('check') || lower.includes('what')))) {
    // Extract key product words - use smarter extraction
    // Remove common filler words and just get the product name
    let searchTerm = query
      .replace(/(?:show|check|what|get|find|me|the|only|please|stock|inventory|just|can you)\s*/gi, '')
      .trim();

    // If we have "pencil" in query but product is "pancel", search for "dollar" (the brand)
    if (lower.includes('dollar')) {
      searchTerm = 'dollar'; // Use brand name for more flexible search
    }

    // Fallback: use first meaningful word
    if (!searchTerm || searchTerm.length < 2) {
      const words = query.split(/\s+/).filter(w => w.length > 2 && !['show', 'check', 'what', 'get', 'find', 'me', 'the', 'only', 'stock'].includes(w.toLowerCase()));
      searchTerm = words[0] || query;
    }

    console.log('[Analytics] Product search term:', searchTerm);
    return { type: 'product', endpoint: `/api/items?name=${encodeURIComponent(searchTerm)}` };
  }

  // Inventory health/analytics
  if (lower.includes('inventory') && (lower.includes('health') || lower.includes('status') || lower.includes('analytics'))) {
    return { type: 'inventory_health', endpoint: '/analytics/inventory-health' };
  }

  // Low stock
  if (lower.includes('low stock') || lower.includes('restock') || lower.includes('running low')) {
    return { type: 'inventory_health', endpoint: '/analytics/inventory-health' };
  }

  // Top products/best sellers
  if (lower.includes('top') || lower.includes('best') || lower.includes('selling')) {
    return { type: 'top_products', endpoint: '/analytics/top-products?limit=5' };
  }

  // Sales trends
  if (lower.includes('trend') || lower.includes('daily') || lower.includes('30 day')) {
    return { type: 'sales_trends', endpoint: '/analytics/sales-trends?days=30' };
  }

  // Monthly sales
  if (lower.includes('month') || lower.includes('sale') || lower.includes('revenue')) {
    return { type: 'sales_month', endpoint: '/analytics/sales-month' };
  }

  // Category breakdown
  if (lower.includes('category') || lower.includes('breakdown')) {
    return { type: 'inventory_health', endpoint: '/analytics/inventory-health' };
  }

  // All inventory
  if (lower.includes('all') && (lower.includes('item') || lower.includes('product') || lower.includes('inventory'))) {
    return { type: 'all_inventory', endpoint: '/api/items' };
  }

  return null;
}

// Generate visualizations from API response
function generateVisualizationsFromData(type: string, data: any): { visualizations: Visualization[], metrics: MetricData[] } {
  const visualizations: Visualization[] = [];
  const metrics: MetricData[] = [];

  console.log('[Analytics] generateVisualizationsFromData called with:', { type, dataLength: Array.isArray(data) ? data.length : 'not array', data });

  switch (type) {
    case 'product':
      // Single or multiple products from /api/items
      // API returns: stock_qty, unit_price (not stock_quantity, price)
      if (Array.isArray(data) && data.length > 0) {
        console.log('[Analytics] Processing product data:', data);
        if (data.length === 1) {
          // Single product - show as metrics
          const item = data[0];
          const stockQty = parseFloat(item.stock_qty) || 0;
          const unitPrice = parseFloat(item.unit_price) || 0;
          metrics.push(
            { title: 'Product', value: (item.name || 'Unknown').trim() },
            { title: 'Stock Qty', value: String(stockQty) },
            { title: 'Price', value: `$${unitPrice.toFixed(2)}` },
            { title: 'Category', value: item.category || 'N/A' },
            { title: 'Unit', value: item.unit || 'N/A' },
            { title: 'Total Value', value: `$${(stockQty * unitPrice).toFixed(2)}` }
          );
        } else {
          // Multiple products - show as charts
          visualizations.push({
            type: 'bar',
            title: 'Stock Quantity',
            data: data.slice(0, 10).map((item: any) => ({
              name: (item.name || 'Unknown').trim().substring(0, 15),
              value: parseFloat(item.stock_qty) || 0,
            })),
          });

          visualizations.push({
            type: 'bar',
            title: 'Inventory Value ($)',
            data: data.slice(0, 10).map((item: any) => ({
              name: (item.name || 'Unknown').trim().substring(0, 15),
              value: (parseFloat(item.stock_qty) || 0) * (parseFloat(item.unit_price) || 0),
            })),
          });
        }
      }
      break;

    case 'all_inventory':
      if (Array.isArray(data) && data.length > 0) {
        visualizations.push({
          type: 'bar',
          title: 'Inventory by Stock',
          data: data.slice(0, 10).map((item: any) => ({
            name: (item.name || 'Unknown').trim().substring(0, 15),
            value: parseFloat(item.stock_qty) || 0,
          })),
        });

        // Group by category
        const categoryMap: Record<string, number> = {};
        data.forEach((item: any) => {
          const cat = item.category || 'Other';
          categoryMap[cat] = (categoryMap[cat] || 0) + ((parseFloat(item.stock_qty) || 0) * (parseFloat(item.unit_price) || 0));
        });
        visualizations.push({
          type: 'pie',
          title: 'Value by Category',
          data: Object.entries(categoryMap).map(([name, value]) => ({ name, value })),
        });
      }
      break;

    case 'inventory_health':
      if (data.metrics) {
        data.metrics.forEach((m: any) => {
          metrics.push({ title: m.title, value: m.value, icon: m.icon });
        });
      }
      if (data.visualizations) {
        data.visualizations.forEach((v: any) => {
          if (v.type === 'bar-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'bar',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          }
        });
      }
      break;

    case 'top_products':
      if (data.visualizations) {
        data.visualizations.forEach((v: any) => {
          if (v.type === 'bar-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'bar',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          }
        });
      }
      break;

    case 'sales_trends':
      if (data.metrics) {
        data.metrics.forEach((m: any) => {
          metrics.push({ title: m.title, value: m.value, icon: m.icon });
        });
      }
      if (data.visualizations) {
        data.visualizations.forEach((v: any) => {
          if (v.type === 'line-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'line',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          } else if (v.type === 'bar-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'bar',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          }
        });
      }
      break;

    case 'sales_month':
      if (data.metrics) {
        data.metrics.forEach((m: any) => {
          metrics.push({ title: m.title, value: m.value, icon: m.icon });
        });
      }
      if (data.visualizations) {
        data.visualizations.forEach((v: any) => {
          if (v.type === 'bar-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'bar',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          } else if (v.type === 'line-chart' && v.data?.length > 0) {
            visualizations.push({
              type: 'line',
              title: v.title,
              data: v.data.map((d: any) => ({ name: d.label, value: d.value })),
            });
          }
        });
      }
      break;
  }

  return { visualizations, metrics };
}

export default function AnalyticsPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [visualizations, setVisualizations] = useState<Visualization[]>([]);
  const [metrics, setMetrics] = useState<MetricData[]>([]);
  const [sessionId] = useState(() => `analytics-${Date.now()}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message - HYBRID APPROACH
  const sendMessage = async (message: string) => {
    if (!message.trim() || isTyping) return;

    const userMsg: ChatMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      // PARALLEL CALLS: AI agent + Analytics endpoint
      const intent = detectQueryIntent(message);
      console.log('[Analytics] Detected intent:', intent);

      // Start both requests in parallel
      const aiPromise = fetch(`${API_BASE_URL}/agent/chat-legacy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message }),
      }).then(r => r.json()).catch(e => ({ response: 'AI service unavailable', error: true }));

      const dataPromise = intent
        ? fetch(`${API_BASE_URL}${intent.endpoint}`).then(r => r.json()).catch(e => {
            console.error('[Analytics] Data fetch error:', e);
            return null;
          })
        : Promise.resolve(null);

      // Wait for both
      const [aiResponse, dataResponse] = await Promise.all([aiPromise, dataPromise]);
      console.log('[Analytics] AI response:', aiResponse);
      console.log('[Analytics] Data response:', dataResponse);

      // Add AI response to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: aiResponse.response || 'No response from AI.',
      }]);

      // Generate visualizations from data endpoint
      if (dataResponse && intent) {
        console.log('[Analytics] Generating visualizations for type:', intent.type);
        const { visualizations: newViz, metrics: newMetrics } = generateVisualizationsFromData(intent.type, dataResponse);
        console.log('[Analytics] Generated:', { visualizations: newViz.length, metrics: newMetrics.length });

        // Always update state - clear old and set new
        setVisualizations(newViz);
        setMetrics(newMetrics);
      } else if (intent) {
        // Clear visualizations if no data returned
        console.log('[Analytics] No data returned, clearing visualizations');
        setVisualizations([]);
        setMetrics([]);
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
    return `$${value.toFixed(0)}`;
  };

  // Render visualization
  const renderVisualization = (viz: Visualization, index: number) => {
    switch (viz.type) {
      case 'bar':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-3">{viz.title}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={viz.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                  {viz.data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'line':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-3">{viz.title}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={viz.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'pie':
        return (
          <div key={index} className="bg-white rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-800 mb-3">{viz.title}</h4>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={viz.data}
                  cx="50%"
                  cy="50%"
                  innerRadius={40}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name }) => name}
                >
                  {viz.data.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      default:
        return null;
    }
  };

  // Sample queries
  const sampleQueries = [
    'Show me Dollar Pencil stock',
    'Top 5 selling products',
    'Inventory health report',
    'Sales trends for 30 days',
    'Monthly sales report',
    'Show all products',
  ];

  return (
    <ErrorBoundary>
      <div className="h-[calc(100vh-120px)] flex gap-4">
        {/* Left: Chat Panel */}
        <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-4 py-3">
            <h2 className="font-semibold flex items-center">
              <span className="mr-2">🤖</span>
              IMS AI Analytics Assistant
            </h2>
            <p className="text-xs text-blue-100 mt-1">Ask anything about your inventory in natural language</p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-gray-50">
            {messages.length === 0 && (
              <div className="text-center py-6">
                <div className="text-5xl mb-3">📊</div>
                <p className="text-gray-600 mb-4">Ask me anything about your inventory!</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {sampleQueries.slice(0, 4).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="px-3 py-1.5 bg-white border border-gray-300 rounded-full text-sm hover:bg-blue-50 hover:border-blue-300 transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200 text-gray-800'
                }`}>
                  <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-gray-200 p-3 bg-white">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about inventory, sales, products..."
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                disabled={isTyping}
              />
              <button
                onClick={() => sendMessage(inputValue)}
                disabled={!inputValue.trim() || isTyping}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors"
              >
                Send
              </button>
            </div>
          </div>
        </div>

        {/* Right: Visualization Panel */}
        <div className="w-1/2 flex flex-col bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-3">
            <h2 className="font-semibold flex items-center">
              <span className="mr-2">📈</span>
              Dynamic Visualizations
            </h2>
            <p className="text-xs text-purple-100 mt-1">Charts update based on your queries</p>
          </div>

          <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
            {visualizations.length === 0 && metrics.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-6xl mb-4 opacity-50">📊</div>
                <p className="text-gray-500">Ask a question to see visualizations</p>
                <p className="text-gray-400 text-sm mt-2">Charts will appear here based on your queries</p>
                <div className="mt-4 space-y-2">
                  <p className="text-xs text-gray-400">Try asking:</p>
                  {sampleQueries.slice(0, 3).map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="block mx-auto text-xs text-blue-500 hover:underline"
                    >
                      "{q}"
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Metrics Grid */}
                {metrics.length > 0 && (
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <h4 className="font-semibold text-gray-800 mb-3">Details</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {metrics.map((m, i) => (
                        <div key={i} className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="text-xs text-gray-500 mb-1">{m.title}</div>
                          <div className="text-lg font-bold text-gray-800">{m.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Charts */}
                {visualizations.map((viz, i) => renderVisualization(viz, i))}
              </div>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
