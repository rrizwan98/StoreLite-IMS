/**
 * Analytics Dashboard Page (Task T035)
 *
 * AI-powered analytics dashboard with:
 * - Natural language query interface via ChatKit
 * - Quick action buttons for common analytics queries
 * - Metrics display cards
 * - Rate limit status indicator
 */

'use client';

import { useEffect, useState, useRef } from 'react';
import Script from 'next/script';
import { API_BASE_URL } from '@/lib/constants';
import ErrorBoundary from '@/components/shared/ErrorBoundary';
import ChatVisualization from '@/components/analytics/ChatVisualization';

// Generate unique session ID for analytics
const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `analytics-${timestamp}-${random}`;
};

// Quick analytics queries
const QUICK_QUERIES = [
  {
    label: 'Sales This Month',
    prompt: 'What were our sales this month? Show me total revenue, top products, and daily trends.',
    icon: '📈',
  },
  {
    label: 'Compare Periods',
    prompt: 'Compare this month to last month. What changed in sales?',
    icon: '📊',
  },
  {
    label: 'Sales Trends',
    prompt: 'Show me sales trends for the last 30 days with best and worst performing days.',
    icon: '📉',
  },
  {
    label: 'Inventory Health',
    prompt: 'What\'s our inventory health? Show me out of stock items and low stock alerts.',
    icon: '📦',
  },
  {
    label: 'Top Products',
    prompt: 'What are our top 5 selling products by revenue?',
    icon: '🏆',
  },
  {
    label: 'Restock Alerts',
    prompt: 'Which items need restocking? Give me recommendations.',
    icon: '⚠️',
  },
];

interface RateLimitStatus {
  used: number;
  remaining: number;
  limit: number;
  percentage_used: number;
  warning: boolean;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export default function AnalyticsPage() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [rateLimitStatus, setRateLimitStatus] = useState<RateLimitStatus | null>(null);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Fallback chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('ims-analytics-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('ims-analytics-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  // Fetch rate limit status
  useEffect(() => {
    const fetchRateLimitStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/agent/chatkit/rate-limit/${sessionId}`);
        if (response.ok) {
          const data = await response.json();
          setRateLimitStatus(data.rate_limit);
        }
      } catch (error) {
        console.error('Failed to fetch rate limit status:', error);
      }
    };

    fetchRateLimitStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchRateLimitStatus, 30000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // Configure ChatKit when loaded
  useEffect(() => {
    if (!isLoaded || configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      console.log('✓ Configuring Analytics ChatKit');
      configuredRef.current = true;

      chatkit.setOptions({
        api: {
          url: `${API_BASE_URL}/agent/chatkit`,
          domainKey: '',
          fetch: async (url: string, options: RequestInit) => {
            try {
              const body = options.body ? JSON.parse(options.body as string) : {};
              body.session_id = sessionId;

              const response = await fetch(url, {
                ...options,
                body: JSON.stringify(body),
                headers: {
                  ...options.headers,
                  'Content-Type': 'application/json',
                },
              });

              // Refresh rate limit status after each request
              setTimeout(() => {
                fetch(`${API_BASE_URL}/agent/chatkit/rate-limit/${sessionId}`)
                  .then(res => res.json())
                  .then(data => setRateLimitStatus(data.rate_limit))
                  .catch(console.error);
              }, 1000);

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
          greeting: 'Ask me anything about your sales data, inventory status, or business performance!',
          prompts: [
            { label: 'Monthly Sales', prompt: 'Show me this month\'s sales summary' },
            { label: 'Inventory Status', prompt: 'What\'s the current inventory health?' },
            { label: 'Trends', prompt: 'Show me sales trends for the last 30 days' },
          ],
        },
        composer: {
          placeholder: 'Ask about sales, inventory, trends...',
        },
        disclaimer: {
          text: 'AI analytics powered by Gemini. Data refreshed on each query.',
        },
      });
    };

    setTimeout(initChatKit, 300);
  }, [isLoaded, sessionId]);

  // Timeout for ChatKit loading (fallback to simple chat after 5s)
  useEffect(() => {
    const timeout = setTimeout(() => {
      if (!isLoaded && !loadError) {
        console.log('ChatKit CDN not available, using fallback chat');
        setLoadError('ChatKit CDN not available - using built-in chat');
        setIsLoaded(true); // Show fallback UI
      }
    }, 5000);
    return () => clearTimeout(timeout);
  }, [isLoaded, loadError]);

  const handleScriptLoad = () => {
    console.log('ChatKit script loaded, checking for custom element...');
    let attempts = 0;
    const maxAttempts = 30; // 3 seconds max
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        console.log('ChatKit custom element registered');
        setIsLoaded(true);
        setLoadError(null);
      } else if (attempts < maxAttempts) {
        attempts++;
        setTimeout(checkElement, 100);
      } else {
        console.log('ChatKit element not registered after timeout');
        setLoadError('ChatKit not available - using built-in chat');
        setIsLoaded(true);
      }
    };
    checkElement();
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Send message using simple chat API (fallback)
  const sendFallbackMessage = async (prompt: string) => {
    if (!prompt.trim() || isTyping) return;

    // Add user message
    const userMessage: ChatMessage = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    try {
      // Use the legacy chat endpoint (works without ChatKit SDK)
      const response = await fetch(`${API_BASE_URL}/agent/chat-legacy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: prompt,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (response.status === 429) {
          throw new Error(errorData.message || 'Rate limit exceeded. Please wait and try again.');
        }
        throw new Error(errorData.error || errorData.detail || `Error: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: data.response || data.content || 'No response received',
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Refresh rate limit status
      fetch(`${API_BASE_URL}/agent/chatkit/rate-limit/${sessionId}`)
        .then(res => res.json())
        .then(rateData => {
          if (rateData.rate_limit) {
            setRateLimitStatus(rateData.rate_limit);
          }
        })
        .catch(console.error);
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  // Send quick query - use ChatKit if available, otherwise fallback
  const sendQuickQuery = (prompt: string) => {
    if (loadError) {
      // Use fallback chat
      sendFallbackMessage(prompt);
    } else {
      const chatkit = chatkitRef.current as any;
      if (chatkit && typeof chatkit.sendMessage === 'function') {
        chatkit.sendMessage(prompt);
      } else {
        // Fallback to built-in chat
        sendFallbackMessage(prompt);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendFallbackMessage(inputValue);
    }
  };

  return (
    <ErrorBoundary>
      {/* Load ChatKit from CDN */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('Failed to load ChatKit:', e)}
      />

      <div className="space-y-6">
        {/* Rate Limit Status Banner */}
        {rateLimitStatus && rateLimitStatus.warning && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-yellow-600 mr-2">⚠️</span>
              <div>
                <p className="text-yellow-800 font-medium">
                  Approaching rate limit: {rateLimitStatus.remaining}/{rateLimitStatus.limit} queries remaining
                </p>
                <p className="text-yellow-600 text-sm">
                  {rateLimitStatus.percentage_used.toFixed(0)}% of hourly limit used
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Analytics</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {QUICK_QUERIES.map((query, index) => (
              <button
                key={index}
                onClick={() => sendQuickQuery(query.prompt)}
                className="flex flex-col items-center p-4 rounded-lg border border-gray-200
                         hover:border-blue-500 hover:bg-blue-50 transition-all duration-200
                         focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <span className="text-2xl mb-2">{query.icon}</span>
                <span className="text-sm text-gray-700 text-center">{query.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Main Analytics Interface */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* ChatKit Panel - Main */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="h-[600px] flex flex-col">
              {!isLoaded ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading AI Analytics...</p>
                  </div>
                </div>
              ) : loadError ? (
                /* Fallback Chat Interface */
                <>
                  {/* Header */}
                  <div className="bg-blue-600 text-white px-4 py-3 flex items-center">
                    <span className="text-lg mr-2">AI</span>
                    <span className="font-medium">Analytics Assistant</span>
                  </div>

                  {/* Messages Area */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                    {messages.length === 0 ? (
                      <div className="text-center py-8">
                        <div className="text-4xl mb-4">AI</div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                          AI Analytics Assistant
                        </h3>
                        <p className="text-gray-600 mb-4">
                          Ask me anything about your sales data, inventory status, or business performance!
                        </p>
                        <div className="flex flex-wrap justify-center gap-2">
                          {['Monthly Sales', 'Inventory Status', 'Trends'].map((label) => (
                            <button
                              key={label}
                              onClick={() => sendFallbackMessage(`Show me ${label.toLowerCase()}`)}
                              className="px-3 py-1.5 bg-white border border-gray-300 rounded-full text-sm text-gray-700 hover:bg-gray-100"
                            >
                              {label}
                            </button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      messages.map((message, index) => (
                        <div
                          key={index}
                          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`rounded-lg px-4 py-3 ${
                              message.role === 'user'
                                ? 'max-w-[80%] bg-blue-600 text-white'
                                : 'max-w-[90%] bg-white border border-gray-200 text-gray-800 shadow-sm'
                            }`}
                          >
                            {message.role === 'user' ? (
                              <p className="whitespace-pre-wrap text-sm">{message.content}</p>
                            ) : (
                              <ChatVisualization content={message.content} role={message.role} />
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    {isTyping && (
                      <div className="flex justify-start">
                        <div className="bg-white border border-gray-200 rounded-lg px-4 py-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input Area */}
                  <div className="border-t border-gray-200 p-4 bg-white">
                    <div className="flex space-x-2">
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about sales, inventory, trends..."
                        className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        disabled={isTyping}
                      />
                      <button
                        onClick={() => sendFallbackMessage(inputValue)}
                        disabled={!inputValue.trim() || isTyping}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                      >
                        Send
                      </button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      AI analytics powered by Gemini. Data refreshed on each query.
                    </p>
                  </div>
                </>
              ) : (
                <openai-chatkit
                  ref={chatkitRef as any}
                  id="analytics-chatkit"
                  style={{
                    width: '100%',
                    height: '100%',
                    display: 'block',
                  }}
                />
              )}
            </div>
          </div>

          {/* Side Panel - Tips & Status */}
          <div className="space-y-4">
            {/* Rate Limit Card */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Query Quota</h3>
              {rateLimitStatus ? (
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-600">Used</span>
                    <span className="font-medium">
                      {rateLimitStatus.used}/{rateLimitStatus.limit}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full transition-all duration-300 ${
                        rateLimitStatus.percentage_used > 80
                          ? 'bg-red-500'
                          : rateLimitStatus.percentage_used > 50
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                      }`}
                      style={{ width: `${rateLimitStatus.percentage_used}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {rateLimitStatus.remaining} queries remaining this hour
                  </p>
                </div>
              ) : (
                <div className="animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
                  <div className="h-2.5 bg-gray-200 rounded w-full"></div>
                </div>
              )}
            </div>

            {/* Example Queries */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Try Asking</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  "What were our sales in November 2025?"
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  "Compare October and November sales"
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  "Show me 30-day sales trends"
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  "Which products need restocking?"
                </li>
                <li className="flex items-start">
                  <span className="text-blue-500 mr-2">•</span>
                  "What's our total inventory value?"
                </li>
              </ul>
            </div>

            {/* Features */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-100 p-4">
              <h3 className="text-sm font-semibold text-blue-900 mb-3">AI Features</h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li className="flex items-center">
                  <span className="mr-2">✨</span>
                  Natural language queries
                </li>
                <li className="flex items-center">
                  <span className="mr-2">📊</span>
                  Sales analytics & trends
                </li>
                <li className="flex items-center">
                  <span className="mr-2">📦</span>
                  Inventory health reports
                </li>
                <li className="flex items-center">
                  <span className="mr-2">🔄</span>
                  Period comparisons
                </li>
                <li className="flex items-center">
                  <span className="mr-2">💡</span>
                  AI recommendations
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}

// Type declaration for the custom element
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'openai-chatkit': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          id?: string;
        },
        HTMLElement
      >;
    }
  }
}
