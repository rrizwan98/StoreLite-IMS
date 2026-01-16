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
import ConnectToolsSection from './components/ConnectToolsSection';
import KPIStatsRow from './components/KPIStatsRow';
import OnboardingChecklist from './components/OnboardingChecklist';
import FloatingHelpButton from './components/FloatingHelpButton';
import { ThemeToggle } from '@/components/theme-toggle';
import { InfoTooltip } from '@/components/ui/Tooltip';
import { getConnectors } from '@/lib/connectors-api';

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
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [chatLoadError, setChatLoadError] = useState<string | null>(null);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // KPI Stats state (for connectors count)
  const [connectorsCount, setConnectorsCount] = useState<number | null>(null);

  // Progressive disclosure: track if user is new (hasn't made AI query yet)
  const [isNewUser, setIsNewUser] = useState(false);

  // Check new user status on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hasFirstQuery = localStorage.getItem('ims_first_ai_query') === 'true';
      setIsNewUser(!hasFirstQuery);
    }
  }, []);

  // Derived state for connection type
  const isOwnDatabase = connectionStatus?.connection_type === 'own_database';
  const isOurDatabase = connectionStatus?.connection_type === 'our_database';
  const isSchemaQueryOnly = connectionStatus?.connection_type === 'schema_query_only';
  const mcpConnected = connectionStatus?.mcp_status === 'connected';
  const mcpSessionId = connectionStatus?.mcp_session_id;

  // For our_database users, generate a session ID based on user ID
  const ourDbSessionId = user?.id ? `our-db-session-${user.id}` : null;

  // Determine if chat should be available
  // - own_database: needs MCP connected
  // - our_database: always available after setup
  const isChatAvailable = (isOwnDatabase && mcpConnected && mcpSessionId) || (isOurDatabase && !connectionStatus?.needs_setup);
  const chatSessionId = isOwnDatabase ? mcpSessionId : ourDbSessionId;

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Fetch connectors count for KPI stats
  useEffect(() => {
    const fetchConnectorsCount = async () => {
      try {
        const connectors = await getConnectors(true);
        const activeConnectors = connectors.filter(c => c.is_verified && c.is_active);
        setConnectorsCount(activeConnectors.length);
      } catch {
        setConnectorsCount(0);
      }
    };

    if (isAuthenticated && isSchemaQueryOnly) {
      fetchConnectorsCount();
    }
  }, [isAuthenticated, isSchemaQueryOnly]);

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

  // Handle choosing schema query only (Agent + Analytics)
  const handleChooseSchemaQueryOnly = async () => {
    if (!databaseUri.trim()) {
      setError('Please enter a database URI');
      return;
    }

    setChoosing(true);
    setError('');

    try {
      // Connect and discover schema (backend tests connection first)
      await chooseConnection({
        connection_type: 'schema_query_only',
        database_uri: databaseUri,
      });

      // Connection successful - redirect to AI Agent page
      // (If connection fails, an error is thrown and caught below)
      router.push(ROUTES.SCHEMA_AGENT);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect to database');
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

  // Configure ChatKit for AI Assistant
  const configureChatKit = useCallback(() => {
    if (!isChatkitLoaded || !chatSessionId) return;
    if (configuredRef.current) return;

    const chatkit = chatkitRef.current as any;
    if (!chatkit || typeof chatkit.setOptions !== 'function') {
      setTimeout(() => configureChatKit(), 100);
      return;
    }

    configuredRef.current = true;
    console.log('[Dashboard] Configuring ChatKit with session:', chatSessionId, 'type:', isOwnDatabase ? 'own_database' : 'our_database');

    // Use different endpoint based on connection type
    // own_database: uses /inventory-agent/chatkit (connects to user's DB via MCP)
    // our_database: uses /agent/chatkit (connects to our platform DB)
    const chatEndpoint = isOwnDatabase
      ? `${API_BASE_URL}/inventory-agent/chatkit`
      : `${API_BASE_URL}/agent/chatkit`;

    chatkit.setOptions({
      api: {
        url: chatEndpoint,
        domainKey: '',
        fetch: async (url: string, options: RequestInit) => {
          try {
            const body = options.body ? JSON.parse(options.body as string) : {};
            body.session_id = chatSessionId;
            body.user_id = user?.id;

            return await fetch(url, {
              ...options,
              body: JSON.stringify(body),
              headers: {
                ...options.headers,
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'x-session-id': chatSessionId || '',
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
        greeting: isOwnDatabase
          ? 'Ask me anything about your database!'
          : 'Ask me anything about your inventory!',
        prompts: [
          { label: 'View Products', prompt: 'Show all items in my inventory' },
          { label: 'Low Stock', prompt: 'Which items are running low on stock?' },
          { label: 'Sales Summary', prompt: 'Show me a summary of recent sales' },
          { label: 'Add Item', prompt: 'Help me add a new item to inventory' },
        ],
      },
      composer: { placeholder: 'Ask about your inventory...' },
      disclaimer: {
        text: isOwnDatabase
          ? 'Connected to your database via MCP'
          : 'Connected to IMS Platform'
      },
    });
  }, [isChatkitLoaded, chatSessionId, user?.id, isOwnDatabase]);

  // Configure ChatKit when loaded and chat is available
  useEffect(() => {
    if (isChatkitLoaded && isChatAvailable && chatSessionId) {
      configureChatKit();
    }
  }, [isChatkitLoaded, isChatAvailable, chatSessionId, configureChatKit]);

  // Reset configuration when chat is closed
  useEffect(() => {
    if (!isChatOpen) {
      configuredRef.current = false;
    }
  }, [isChatOpen]);

  // Check if ChatKit is already registered (from cache or previous page)
  useEffect(() => {
    // Check immediately if already registered (cached/previous load)
    if (customElements.get('openai-chatkit')) {
      console.log('[Dashboard] ChatKit element already registered on mount');
      setIsChatkitLoaded(true);
      setScriptLoaded(true);
      return;
    }

    // Start polling for element registration
    let attempts = 0;
    const maxAttempts = 200; // 10 seconds max (50ms * 200)

    const checkElement = () => {
      attempts++;
      if (customElements.get('openai-chatkit')) {
        console.log('[Dashboard] ChatKit element registered after', attempts, 'attempts');
        setIsChatkitLoaded(true);
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
      } else if (attempts >= maxAttempts) {
        console.error('[Dashboard] ChatKit element not registered after max attempts');
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
      }
    };

    // Poll every 50ms
    checkIntervalRef.current = setInterval(checkElement, 50);

    return () => {
      if (checkIntervalRef.current) {
        clearInterval(checkIntervalRef.current);
        checkIntervalRef.current = null;
      }
    };
  }, []);

  // Handle ChatKit script load
  const handleScriptLoad = () => {
    console.log('[Dashboard] ChatKit script loaded');
    setScriptLoaded(true);

    // Check immediately after script loads
    if (customElements.get('openai-chatkit')) {
      console.log('[Dashboard] ChatKit element registered immediately after script load');
      setIsChatkitLoaded(true);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 dark:border-blue-400"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // First-time user - show service selection
  const needsSetup = !connectionStatus || connectionStatus.needs_setup;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm dark:shadow-gray-900/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row justify-between items-center gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 dark:bg-blue-500 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">S</span>
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">{APP_METADATA.NAME}</span>
          </div>
          <div className="flex items-center space-x-3 sm:space-x-4">
            <span className="text-gray-600 dark:text-gray-300 text-sm sm:text-base truncate max-w-[100px] sm:max-w-none">
              {user.full_name || user.email}
            </span>
            <ThemeToggle />
            <button
              onClick={() => {
                localStorage.removeItem('ims_auth_tokens');
                window.location.href = ROUTES.HOME;
              }}
              className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white font-medium text-sm sm:text-base"
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
            <div className="text-center mb-6 sm:mb-10">
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white mb-2 sm:mb-3">
                Welcome, {user.full_name || 'there'}!
              </h1>
              <p className="text-lg sm:text-xl text-gray-600 dark:text-gray-300">
                How would you like to use {APP_METADATA.NAME}?
              </p>
            </div>

            {error && (
              <div className="mb-6 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-lg text-center">
                {error}
              </div>
            )}

            {/* Database URI Input (shared between options 1 and 3) */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-4 sm:p-6 mb-6 sm:mb-8">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                PostgreSQL Database URI (for options 1 or 3)
              </label>
              <input
                type="text"
                value={databaseUri}
                onChange={(e) => setDatabaseUri(e.target.value)}
                placeholder="postgresql://user:pass@host:5432/db"
                className="w-full px-3 sm:px-4 py-2 sm:py-3 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-xs sm:text-sm placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {/* Option 1: Full IMS Connection */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/50 p-6 border-2 border-blue-200 dark:border-blue-800 flex flex-col">
                <div className="text-center mb-4">
                  <div className="text-5xl mb-3">🔌</div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Full IMS Connection</h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
                    Complete system with Admin, POS & AI
                  </p>
                </div>

                <div className="flex-grow">
                  <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      Inventory Admin Panel
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      Point of Sale (POS)
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      AI Analytics & Agent
                    </li>
                    <li className="flex items-center">
                      <span className="text-yellow-500 mr-2">!</span>
                      <span className="text-yellow-700 dark:text-yellow-400">Creates IMS tables</span>
                    </li>
                  </ul>
                </div>

                <button
                  onClick={handleChooseOwnDatabase}
                  disabled={choosing || !databaseUri.trim()}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors font-semibold"
                >
                  {choosing ? 'Setting up...' : 'Connect Full IMS'}
                </button>
              </div>

              {/* Option 2: Use Our Platform */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/50 p-6 border-2 border-purple-200 dark:border-purple-800 flex flex-col">
                <div className="text-center mb-4">
                  <div className="text-5xl mb-3">☁️</div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Use Our Platform</h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
                    Hosted database, no setup needed
                  </p>
                </div>

                <div className="flex-grow">
                  <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      Inventory Admin Panel
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      Point of Sale (POS)
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      AI Analytics & Agent
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      No database required
                    </li>
                  </ul>
                </div>

                <button
                  onClick={handleChooseOurDatabase}
                  disabled={choosing}
                  className="w-full bg-purple-600 text-white py-3 px-4 rounded-lg hover:bg-purple-700 disabled:bg-purple-400 transition-colors font-semibold"
                >
                  {choosing ? 'Setting up...' : 'Use Our Platform'}
                </button>
              </div>

              {/* Option 3: Agent + Analytics Only */}
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/50 p-6 border-2 border-emerald-200 dark:border-emerald-800 flex flex-col">
                <div className="text-center mb-4">
                  <div className="text-5xl mb-3">🧠</div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">Agent + Analytics</h2>
                  <p className="text-gray-600 dark:text-gray-400 mt-2 text-sm">
                    Query your existing database with AI
                  </p>
                </div>

                <div className="flex-grow">
                  <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      AI-powered queries
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      Natural language analytics
                    </li>
                    <li className="flex items-center">
                      <span className="text-green-500 mr-2">✓</span>
                      <span className="text-emerald-700 dark:text-emerald-400 font-medium">NO table modifications</span>
                    </li>
                    <li className="flex items-center">
                      <span className="text-gray-400 dark:text-gray-500 mr-2">✗</span>
                      <span className="text-gray-400 dark:text-gray-500">No Admin/POS</span>
                    </li>
                  </ul>
                </div>

                <button
                  onClick={handleChooseSchemaQueryOnly}
                  disabled={choosing || !databaseUri.trim()}
                  className="w-full bg-emerald-600 text-white py-3 px-4 rounded-lg hover:bg-emerald-700 disabled:bg-emerald-400 transition-colors font-semibold"
                >
                  {choosing ? 'Setting up...' : 'Connect Agent Only'}
                </button>
              </div>
            </div>
          </div>
        ) : connectionStatus?.connection_type === 'own_database' ? (
          /* User with Own Database */
          <div>
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Your Database Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-400">Connected to your PostgreSQL database via MCP</p>
              </div>
              <button
                onClick={handleDisconnect}
                className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
              >
                Disconnect
              </button>
            </div>

            {/* Status Card */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 mb-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className={`w-4 h-4 rounded-full ${
                    connectionStatus.mcp_status === 'connected' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">MCP Server Status</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">{connectionStatus.mcp_status || 'Unknown'}</p>
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
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.MCP_ADMIN : ROUTES.DB_CONNECT}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📦</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Inventory Admin</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Manage products, stock levels, and categories in your database.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 dark:text-yellow-400 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.MCP_POS : ROUTES.DB_CONNECT}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">💳</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Point of Sale</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Create bills, search products, and process sales.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 dark:text-yellow-400 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={connectionStatus.mcp_status === 'connected' ? ROUTES.ANALYTICS : ROUTES.DB_CONNECT}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📊</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">AI Analytics</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Ask questions about YOUR data and get smart visualizations.
                  </p>
                  {connectionStatus.mcp_status !== 'connected' && (
                    <span className="text-xs text-yellow-600 dark:text-yellow-400 mt-2 block">Connect MCP first</span>
                  )}
                </div>
              </Link>

              <Link href={ROUTES.DB_CONNECT}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer border-2 border-blue-200 dark:border-blue-800">
                  <div className="text-4xl mb-4">🔌</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">DB Connection</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Manage MCP connection and run direct queries.
                  </p>
                </div>
              </Link>
            </div>
          </div>
        ) : connectionStatus?.connection_type === 'schema_query_only' ? (
          /* User with Schema Query Only (Agent + Analytics) */
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Analytics Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-400">Query your database with natural language</p>
              </div>
              <button
                onClick={handleDisconnect}
                className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
              >
                Disconnect
              </button>
            </div>

            {/* Onboarding Checklist */}
            <OnboardingChecklist
              connectionStatus={connectionStatus}
              connectorsCount={connectorsCount ?? 0}
              className="mb-6"
            />

            {/* KPI Stats Row */}
            <KPIStatsRow
              tablesCount={connectionStatus?.tables_count ?? null}
              toolsConnected={connectorsCount}
              schemaStatus={connectionStatus?.schema_status as 'ready' | 'pending' | 'error' | null}
              className="mb-8"
            />

            {/* Feature Cards - Agent, Analytics, Scheduler, Connection */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              {/* AI Agent Card - Primary Feature */}
              <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover-lift relative ${
                isNewUser
                  ? 'border-2 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-200 dark:ring-emerald-900'
                  : 'border-2 border-emerald-300 dark:border-emerald-700'
              }`}>
                {/* New user badge */}
                {isNewUser && connectionStatus?.schema_status === 'ready' && (
                  <span className="absolute -top-2 -right-2 bg-emerald-500 text-white text-xs font-medium px-2 py-1 rounded-full shadow-sm">
                    Start here
                  </span>
                )}
                <div className="text-4xl mb-4">🧠</div>
                <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">AI Agent</h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Ask questions about your data in natural language.
                </p>
                <Link href={connectionStatus.schema_status === 'ready' ? ROUTES.SCHEMA_AGENT : ROUTES.SCHEMA_CONNECT}>
                  <button
                    className={`w-full py-2.5 px-4 rounded-lg font-medium click-feedback transition-colors ${
                      connectionStatus.schema_status === 'ready'
                        ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                    title={connectionStatus.schema_status !== 'ready' ? 'Discover schema first' : undefined}
                  >
                    {connectionStatus.schema_status === 'ready' ? 'Open Chat' : 'Setup Required'}
                  </button>
                </Link>
              </div>

              {/* Scheduler Card */}
              <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover-lift border border-gray-200 dark:border-gray-700 transition-opacity ${
                isNewUser ? 'opacity-75 hover:opacity-100' : ''
              }`}>
                <div className="text-4xl mb-4">⏰</div>
                <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Scheduler</h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Schedule automated tasks to run at specific times.
                </p>
                <Link href={connectionStatus.schema_status === 'ready' ? ROUTES.SCHEDULER : ROUTES.SCHEMA_CONNECT}>
                  <button
                    className={`w-full py-2.5 px-4 rounded-lg font-medium click-feedback transition-colors ${
                      connectionStatus.schema_status === 'ready'
                        ? 'border border-purple-300 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/30'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                    title={connectionStatus.schema_status !== 'ready' ? 'Discover schema first' : undefined}
                  >
                    {connectionStatus.schema_status === 'ready' ? 'View Tasks' : 'Setup Required'}
                  </button>
                </Link>
              </div>

              {/* Connection Card */}
              <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover-lift border border-gray-200 dark:border-gray-700 transition-opacity ${
                isNewUser ? 'opacity-75 hover:opacity-100' : ''
              }`}>
                <div className="text-4xl mb-4">🔌</div>
                <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Connection</h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  View schema, refresh metadata, or upgrade mode.
                </p>
                <Link href={ROUTES.SCHEMA_CONNECT}>
                  <button className="w-full py-2.5 px-4 rounded-lg font-medium click-feedback transition-colors border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                    View Schema
                  </button>
                </Link>
              </div>

              {/* Developer Tools Card */}
              <div className={`bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover-lift border border-gray-200 dark:border-gray-700 transition-opacity ${
                isNewUser ? 'opacity-75 hover:opacity-100' : ''
              }`}>
                <div className="text-4xl mb-4">🛠️</div>
                <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Developer Tools</h2>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Publish agents, get API keys, embed code.
                </p>
                <Link href={connectionStatus.schema_status === 'ready' ? ROUTES.DEVELOPER_TOOLS : ROUTES.SCHEMA_CONNECT}>
                  <button
                    className={`w-full py-2.5 px-4 rounded-lg font-medium click-feedback transition-colors ${
                      connectionStatus.schema_status === 'ready'
                        ? 'border border-orange-300 dark:border-orange-700 text-orange-700 dark:text-orange-300 hover:bg-orange-50 dark:hover:bg-orange-900/30'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                    }`}
                    title={connectionStatus.schema_status !== 'ready' ? 'Discover schema first' : undefined}
                  >
                    {connectionStatus.schema_status === 'ready' ? 'Manage Agents' : 'Setup Required'}
                  </button>
                </Link>
              </div>
            </div>

            {/* Connect Tools Section */}
            <ConnectToolsSection className="mt-8" />

            {/* Read-Only Notice with Tooltip and Learn More link (v1.1) */}
            <div className="mt-8 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-200 dark:border-emerald-800 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <span className="text-emerald-600 dark:text-emerald-400 text-xl">🛡️</span>
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-emerald-800 dark:text-emerald-300">Read-Only Mode</h4>
                    <InfoTooltip
                      content="Read-only mode ensures we can only SELECT data from your database. We cannot INSERT, UPDATE, DELETE, or run any DDL commands. Your data is completely safe."
                      position="right"
                    />
                  </div>
                  <p className="text-sm text-emerald-700 dark:text-emerald-400">
                    Your data is safe. This connection only allows SELECT queries - no modifications to your database.
                    <a
                      href="https://www.postgresql.org/docs/current/sql-grant.html"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 underline hover:text-emerald-600 dark:hover:text-emerald-300 transition-colors"
                    >
                      Learn more
                    </a>
                  </p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* User with Our Database */
          <div>
            <div className="flex justify-between items-center mb-8">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
                <p className="text-gray-600 dark:text-gray-400">Manage your inventory with {APP_METADATA.NAME}</p>
              </div>
              <button
                onClick={handleDisconnect}
                className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white font-medium"
              >
                Change Service
              </button>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
              <Link href={ROUTES.ADMIN}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📦</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Inventory Admin</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Manage items, categories, and stock levels.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.POS}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">💳</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Point of Sale</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Process sales and generate invoices.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.ANALYTICS}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer">
                  <div className="text-4xl mb-4">📊</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">AI Analytics</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Ask questions and get smart visualizations.
                  </p>
                </div>
              </Link>

              <Link href={ROUTES.DB_CONNECT}>
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-md dark:shadow-gray-900/50 p-6 hover:shadow-lg dark:hover:shadow-gray-900/70 transition-shadow cursor-pointer border-2 border-dashed border-gray-300 dark:border-gray-600">
                  <div className="text-4xl mb-4">🔌</div>
                  <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Connect Own DB</h2>
                  <p className="text-gray-600 dark:text-gray-400">
                    Switch to your own PostgreSQL database.
                  </p>
                </div>
              </Link>
            </div>
          </div>
        )}
      </main>

      {/* ChatKit Script - Load always for preloading, not conditionally */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => {
          console.error('[Dashboard] Failed to load ChatKit:', e);
          setChatLoadError('Failed to load ChatKit script. Please check your network connection.');
        }}
      />

      {/* Floating Chat Button - Show for both our_database and own_database users */}
      {isChatAvailable && chatSessionId && (
        <>
          {/* Floating Chat Button - Blue for own_database, Purple for our_database */}
          <button
            onClick={() => setIsChatOpen(!isChatOpen)}
            className={`fixed bottom-6 right-6 w-14 h-14 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-300 z-50 hover:scale-110 ${
              isOurDatabase
                ? 'bg-purple-600 hover:bg-purple-700'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
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
            <div className="fixed bottom-24 right-4 sm:right-6 w-[calc(100vw-2rem)] sm:w-96 max-w-md h-[60vh] sm:h-[500px] bg-white rounded-xl shadow-2xl z-50 overflow-hidden border border-gray-200">
              {chatLoadError ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center p-6">
                    <div className="text-red-500 text-4xl mb-4">⚠️</div>
                    <p className="text-red-600 font-medium mb-2">ChatKit Error</p>
                    <p className="text-gray-500 text-sm mb-4">{chatLoadError}</p>
                    <button
                      onClick={() => window.location.reload()}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                    >
                      Refresh Page
                    </button>
                  </div>
                </div>
              ) : !isChatkitLoaded ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-gray-500">Loading ChatKit...</p>
                    {scriptLoaded && <p className="text-gray-400 text-xs mt-2">Initializing component...</p>}
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

          {/* ChatKit CSS Variables - Purple for our_database, Blue for own_database */}
          <style jsx global>{`
            openai-chatkit {
              --chatkit-primary-color: ${isOurDatabase ? '#9333ea' : '#2563eb'};
              --chatkit-background: #ffffff;
              --chatkit-text-color: #1f2937;
              --chatkit-border-radius: 8px;
            }
          `}</style>
        </>
      )}

      {/* v1.1: Floating Help Button */}
      {isSchemaQueryOnly && <FloatingHelpButton />}
    </div>
  );
}
