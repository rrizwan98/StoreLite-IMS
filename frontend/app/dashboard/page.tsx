/**
 * Dashboard Page
 *
 * Main dashboard after login:
 * - First-time users see service selection
 * - Returning users see their dashboard based on connection type
 * - Floating chat button for MCP-connected users (ChatKit)
 */

'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
import { ROUTES, APP_METADATA, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

export default function DashboardPage() {
  const {
    user,
    connectionStatus,
    isLoading,
    isAuthenticated,
    chooseConnection,
    disconnectDatabase,
    refreshConnectionStatus,
  } = useAuth();
  const router = useRouter();

  const [databaseUri, setDatabaseUri] = useState('');
  const [choosing, setChoosing] = useState(false);
  const [error, setError] = useState('');

  // Chat state for floating chat
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isChatkitLoaded, setIsChatkitLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Derived state for MCP
  const isOwnDatabase = connectionStatus?.connection_type === 'own_database';
  const mcpConnected = connectionStatus?.mcp_status === 'connected';
  const mcpSessionId = connectionStatus?.mcp_session_id;

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Handle choosing own database
  const handleChooseOwnDatabase = async () => {
    if (!databaseUri.trim()) {
      setError('Please enter a database URI');
      return;
    }

    setChoosing(true);
    setError('');

    try {
      await chooseConnection({
        connection_type: 'own_database',
        database_uri: databaseUri,
      });
      // Redirect to DB connect page to establish MCP connection
      router.push(ROUTES.DB_CONNECT);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set connection');
    } finally {
      setChoosing(false);
    }
  };

  // Handle choosing our database
  const handleChooseOurDatabase = async () => {
    setChoosing(true);
    setError('');

    try {
      await chooseConnection({
        connection_type: 'our_database',
      });
      await refreshConnectionStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set connection');
    } finally {
      setChoosing(false);
    }
  };

  // Handle disconnect
  const handleDisconnect = async () => {
    try {
      await disconnectDatabase();
    } catch (err) {
      console.error('Disconnect failed:', err);
    }
  };

  // Configure ChatKit for MCP Agent
  const configureChatKit = useCallback(() => {
    if (!isChatkitLoaded || !mcpSessionId) return;
    if (configuredRef.current) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit || typeof chatkit.setOptions !== 'function') {
      setTimeout(() => configureChatKit(), 100);
      return;
    }

    configuredRef.current = true;
    console.log('[Dashboard] Configuring ChatKit with session:', mcpSessionId);

    chatkit.setOptions({
      api: {
        url: `${API_BASE_URL}/inventory-agent/chatkit`,
        domainKey: '',
        fetch: async (url: string, options: RequestInit) => {
          try {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = mcpSessionId;
            body.user_id = user?.id;

            return await fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: {
                ...options.headers,
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'x-session-id': mcpSessionId,
              },
            });
          } catch (e) {
            console.error('[Dashboard] ChatKit fetch error:', e);
            throw e;
          }
        },
      },
      theme: 'light',
      header: {
        enabled: true,
        title: { enabled: true, text: 'AI Assistant' },
      },
      startScreen: {
        greeting: 'Ask me anything about your inventory!',
        prompts: [
          { label: 'View Products', prompt: 'Show all products in my inventory' },
          { label: 'Low Stock', prompt: 'Which products are running low on stock?' },
          { label: 'Sales Summary', prompt: 'Show me a summary of recent sales' },
          { label: 'Add Product', prompt: 'Help me add a new product to inventory' },
        ],
      },
      composer: { placeholder: 'Ask about your inventory...' },
      disclaimer: { text: 'Connected to your database via MCP' },
    });
  }, [isChatkitLoaded, mcpSessionId, user?.id]);

  // Configure ChatKit when loaded and MCP connected
  useEffect(() => {
    if (isChatkitLoaded && mcpConnected && mcpSessionId) {
      configureChatKit();
    }
  }, [isChatkitLoaded, mcpConnected, mcpSessionId, configureChatKit]);

  // Reset configuration when chat is closed
  useEffect(() => {
    if (!isChatOpen) {
      configuredRef.current = false;
    }
  }, [isChatOpen]);

  // Handle ChatKit script load
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

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // First-time user - show service selection
  const needsSetup = !connectionStatus || connectionStatus.needs_setup;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">S</span>
            </div>
            <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">
              {user.full_name || user.email}
            </span>
            <button
              onClick={() => {
                localStorage.removeItem('ims_auth_tokens');
                window.location.href = ROUTES.HOME;
              }}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {needsSetup ? (
          /* Service Selection for First-Time Users */
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-10">
              <h1 className="text-3xl font-bold text-gray-900 mb-3">
                Welcome, {user.full_name || 'there'}!
              </h1>
              <p className="text-xl text-gray-600">
                How would you like to use {APP_METADATA.NAME}?
              </p>
            </div>

            {error && (
              <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-center">
                {error}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Option 1: Connect Own Database */}
              <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-blue-200">
                <div className="text-center mb-6">
                  <div className="text-6xl mb-4">🔌</div>
                  <h2 className="text-2xl font-bold text-gray-900">Connect Your Database</h2>
                  <p className="text-gray-600 mt-2">
                    Use your own PostgreSQL database with our AI tools
                  </p>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      PostgreSQL Database URI
                    </label>
                    <input
                      type="text"
                      value={databaseUri}
                      onChange={(e) => setDatabaseUri(e.target.value)}
                      placeholder="postgresql://user:pass@host:5432/db"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                    />
                  </div>

                  <button
                    onClick={handleChooseOwnDatabase}
                    disabled={choosing || !databaseUri.trim()}
                    className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-semibold"
                  >
                    {choosing ? 'Setting up...' : 'Connect My Database'}
                  </button>
                </div>

                <ul className="mt-6 space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Your data stays in your database
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    AI Analytics on your data
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    MCP Protocol for secure access
                  </li>
                </ul>
              </div>

              {/* Option 2: Use Our Database */}
              <div className="bg-white rounded-2xl shadow-lg p-8 border-2 border-purple-200">
                <div className="text-center mb-6">
                  <div className="text-6xl mb-4">☁️</div>
                  <h2 className="text-2xl font-bold text-gray-900">Use Our Platform</h2>
                  <p className="text-gray-600 mt-2">
                    Start immediately with our hosted database
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <p className="text-purple-800">
                      No setup required! Start managing inventory right away with
                      full Admin, POS, and Analytics features.
                    </p>
                  </div>

                  <button
                    onClick={handleChooseOurDatabase}
                    disabled={choosing}
                    className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 disabled:bg-purple-400 transition-colors font-semibold"
                  >
                    {choosing ? 'Setting up...' : 'Use Our Database'}
                  </button>
                </div>

                <ul className="mt-6 space-y-2 text-sm text-gray-600">
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    No database setup needed
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    Full Admin & POS features
                  </li>
                  <li className="flex items-center">
                    <span className="text-green-500 mr-2">✓</span>
                    AI Analytics included
                  </li>
                </ul>
              </div>
            </div>
          </div>
        ) : connectionStatus?.connection_type === 'own_database' ? (
          /* User with Own Database */
          <div>
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Your Database Dashboard</h1>
                <p className="text-gray-600">Connected to your PostgreSQL database via MCP</p>
              </div>
              <button
                onClick={handleDisconnect}
                className="text-red-600 hover:text-red-700 font-medium"
              >
                Disconnect
              </button>
            </div>

            {/* Status Card */}
            <div className="bg-white rounded-xl shadow-md p-6 mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`w-4 h-4 rounded-full ${
                    connectionStatus.mcp_status === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <div>
                    <h3 className="font-semibold text-gray-900">MCP Server Status</h3>
                    <p className="text-sm text-gray-600 capitalize">{connectionStatus.mcp_status || 'Unknown'}</p>
                  </div>
                </div>
                {connectionStatus.mcp_status !== 'connected' && (
                  <Link
                    href={ROUTES.DB_CONNECT}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Connect MCP
                  </Link>
                )}
              </div>
            </div>

            {/* Feature Cards - Full Features for Own Database Users */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.MCP_ADMIN : ROUTES.DB_CONNECT}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📦</div>
                  <h2 className="text-xl font-semibold mb-2">Inventory Admin</h2>
                  <p className="text-gray-600">
                    Manage products, stock levels, and categories in your database.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.MCP_POS : ROUTES.DB_CONNECT}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">💳</div>
                  <h2 className="text-xl font-semibold mb-2">Point of Sale</h2>
                  <p className="text-gray-600">
                    Create bills, search products, and process sales.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.ANALYTICS : ROUTES.DB_CONNECT}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📊</div>
                  <h2 className="text-xl font-semibold mb-2">AI Analytics</h2>
                  <p className="text-gray-600">
                    Ask questions about YOUR data and get smart visualizations.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={ROUTES.DB_CONNECT}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-blue-200">
                  <div className="text-4xl mb-4">🔌</div>
                  <h2 className="text-xl font-semibold mb-2">DB Connection</h2>
                  <p className="text-gray-600">
                    Manage MCP connection and run direct queries.
                  </p>
                </div>
              </Link>
            </div>
          </div>
        ) : (
          /* User with Our Database */
          <div>
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-gray-600">Manage your inventory with {APP_METADATA.NAME}</p>
              </div>
              <button
                onClick={handleDisconnect}
                className="text-gray-600 hover:text-gray-900 font-medium"
              >
                Change Service
              </button>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Link href={ROUTES.ADMIN}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📦</div>
                  <h2 className="text-xl font-semibold mb-2">Inventory Admin</h2>
                  <p className="text-gray-600">
                    Manage items, categories, and stock levels.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.POS}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">💳</div>
                  <h2 className="text-xl font-semibold mb-2">Point of Sale</h2>
                  <p className="text-gray-600">
                    Process sales and generate invoices.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.ANALYTICS}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📊</div>
                  <h2 className="text-xl font-semibold mb-2">AI Analytics</h2>
                  <p className="text-gray-600">
                    Ask questions and get smart visualizations.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.DB_CONNECT}>
                <div className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 border-dashed border-gray-300">
                  <div className="text-4xl mb-4">🔌</div>
                  <h2 className="text-xl font-semibold mb-2">Connect Own DB</h2>
                  <p className="text-gray-600">
                    Switch to your own PostgreSQL database.
                  </p>
                </div>
              </Link>
            </div>
          </div>
        )}
      </main>

      {/* Floating Chat Button - Only show for MCP connected users */}
      {isOwnDatabase && mcpConnected && mcpSessionId && (
        <>
          {/* ChatKit Script - Same as Analytics page */}
          <Script
            src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
            strategy="afterInteractive"
            onLoad={handleScriptLoad}
          />

          {/* Floating Chat Button */}
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-300 z-50 hover:scale-110"
            title="Chat with AI Assistant"
          >
            {isChatOpen ? (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            )}
          </button>

          {/* Chat Modal */}
          {isChatOpen && (
            <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-white rounded-xl shadow-2xl z-50 overflow-hidden border border-gray-200">
              {!isChatkitLoaded ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-gray-500">Loading ChatKit...</p>
                  </div>
                </div>
              ) : (
                <openai-chatkit
                  ref={chatkitRef as any}
                  style={{ width: '100%', height: '100%', display: 'block' }}
                />
              )}
            </div>
          )}

          {/* ChatKit CSS Variables */}
          <style jsx global>{`
            openai-chatkit {
              --chatkit-primary-color: #2563eb;
              --chatkit-background: #ffffff;
              --chatkit-text-color: #1f2937;
              --chatkit-border-radius: 8px;
            }
          `}</style>
        </>
      )}
    </div>
  );
}
