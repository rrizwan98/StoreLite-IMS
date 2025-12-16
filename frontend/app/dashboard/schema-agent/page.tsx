/**
 * Schema Agent Chat Page with ChatKit UI
 *
 * Full-page AI chat interface for querying user's database
 * with natural language. Uses OpenAI ChatKit web component
 * for the chat UI.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Script from 'next/script';
import { ROUTES, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

// Track selected tool globally for the fetch interceptor
// Tool selection comes from ChatKit's + button (composer tools)
let selectedToolId: string | null = null;

// Declare ChatKit element type for TypeScript
declare global {
  namespace JSX {
    interface IntrinsicElements {
      'openai-chatkit': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & { id?: string },
        HTMLElement
      >;
    }
  }
}

export default function SchemaAgentPage() {
  const { user, connectionStatus, isLoading, isAuthenticated } = useAuth();
  const router = useRouter();

  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState('');
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);
  const checkIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Redirect if not authenticated or wrong connection type
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(ROUTES.LOGIN);
    }
  }, [isAuthenticated, isLoading, router]);

  // Redirect if not schema_query_only or schema not ready
  useEffect(() => {
    if (!isLoading && connectionStatus) {
      if (connectionStatus.connection_type !== 'schema_query_only') {
        router.push(ROUTES.DASHBOARD);
      } else if (connectionStatus.schema_status !== 'ready') {
        router.push(ROUTES.SCHEMA_CONNECT);
      }
    }
  }, [connectionStatus, isLoading, router]);

  // Configure ChatKit when loaded
  useEffect(() => {
    if (!isLoaded || configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit) {
        setTimeout(initChatKit, 100);
        return;
      }

      // Wait for setOptions to be available (custom element upgraded)
      if (typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      console.log('Configuring Schema Agent ChatKit');
      configuredRef.current = true;

      const token = getAccessToken();
      const apiUrl = `${API_BASE_URL}/schema-agent/chatkit`;

      try {
        // Pure OpenAI ChatKit SDK configuration (correct format per type definitions)
        chatkit.setOptions({
          // Custom backend API configuration (CustomApiConfig)
          api: {
            url: apiUrl,
            // domainKey is required for custom API - using empty string for development
            domainKey: '',
            // Custom fetch for auth token and tool injection
            fetch: async (url: string, options: RequestInit) => {
              try {
                // Check if this is a message request and we have a selected tool
                if (options.body && selectedToolId) {
                  try {
                    const body = JSON.parse(options.body as string);
                    console.log('[ChatKit] Original body:', JSON.stringify(body).substring(0, 200));

                    // Add tool metadata to the request
                    body.metadata = {
                      ...body.metadata,
                      selected_tool: selectedToolId,
                    };

                    // Prefix the message content for the agent to understand
                    // ChatKit sends messages in different formats, handle all cases
                    if (body.input && typeof body.input === 'string') {
                      body.input = `[TOOL:${selectedToolId.toUpperCase()}] ${body.input}`;
                      console.log('[ChatKit] Modified input:', body.input.substring(0, 100));
                    }

                    // Also check for messages array (alternative format)
                    if (body.messages && Array.isArray(body.messages)) {
                      const lastUserMsg = body.messages.findLast((m: any) => m.role === 'user');
                      if (lastUserMsg && lastUserMsg.content) {
                        if (typeof lastUserMsg.content === 'string') {
                          lastUserMsg.content = `[TOOL:${selectedToolId.toUpperCase()}] ${lastUserMsg.content}`;
                        } else if (Array.isArray(lastUserMsg.content)) {
                          // Handle content array format
                          for (const part of lastUserMsg.content) {
                            if (part.type === 'text' && part.text) {
                              part.text = `[TOOL:${selectedToolId.toUpperCase()}] ${part.text}`;
                              break;
                            }
                          }
                        }
                        console.log('[ChatKit] Modified message in messages array');
                      }
                    }

                    options.body = JSON.stringify(body);
                    console.log('[ChatKit] Tool applied:', selectedToolId);

                    // Reset tool after use - user can reselect from + button for next message
                    selectedToolId = null;
                  } catch (parseError) {
                    console.error('[ChatKit] Parse error:', parseError);
                  }
                }

                return fetch(url, {
                  ...options,
                  headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                  },
                });
              } catch (e) {
                console.error('ChatKit fetch error:', e);
                throw e;
              }
            },
          },
          // Theme (ColorScheme or ThemeOption)
          theme: 'light',
          // Header configuration (HeaderOption)
          header: {
            enabled: true,
            title: {
              enabled: true,
              text: 'AI Data Assistant',
            },
          },
          // Start screen configuration (StartScreenOption)
          startScreen: {
            greeting: 'Hello! I can help you explore and analyze your database. Ask me anything about your data!',
            prompts: [
              { label: 'List Tables', prompt: 'What tables are in my database?' },
              { label: 'Show Sample', prompt: 'Show me the top 10 records from the largest table' },
              { label: 'Relationships', prompt: 'What are the relationships between tables?' },
              { label: 'Data Summary', prompt: 'Give me a summary of the data' },
            ],
          },
          // Composer configuration (ComposerOption)
          composer: {
            placeholder: 'Ask about your data... (Type / for tools)',
            // Tools menu - appears when user clicks tool button or types /
            tools: [
              {
                id: 'gmail',
                label: 'Send via Gmail',
                shortLabel: 'Gmail',
                icon: 'mail',
                placeholderOverride: 'What would you like to email? (Results will be formatted and sent)',
                persistent: false,
              },
              // Future tools can be added here:
              // {
              //   id: 'export-csv',
              //   label: 'Export to CSV',
              //   shortLabel: 'CSV',
              //   icon: 'document',
              //   placeholderOverride: 'What data would you like to export?',
              // },
            ],
          },
          // Disclaimer configuration (DisclaimerOption)
          disclaimer: {
            text: 'Read-only mode - Only SELECT queries are executed. AI may make mistakes.',
          },
        });

        // Official ChatKit event listeners
        chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
          console.log('ChatKit message event:', e.detail);
        });

        chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
          console.error('ChatKit error event:', e.detail);
          setError(e.detail?.message || 'An error occurred');
        });

        // Track tool selection via log events from ChatKit's + button
        chatkit.addEventListener('chatkit.log', (e: CustomEvent) => {
          const { name, data } = e.detail || {};
          console.log('[ChatKit Log]', name, JSON.stringify(data));

          // Detect tool selection from various log event formats
          // ChatKit may emit different event names for tool selection
          if (name === 'tool_selected' || name === 'composer.tool.selected' || name === 'tool.selected') {
            const toolId = data?.toolId || data?.tool || data?.id || null;
            if (toolId) {
              selectedToolId = toolId;
              console.log('[Tool] Selected from ChatKit:', toolId);
            }
          }
          // Also check for composer tool changes
          if (name?.includes('tool') || name?.includes('composer')) {
            if (data?.id || data?.toolId) {
              selectedToolId = data.id || data.toolId;
              console.log('[Tool] Selected from ChatKit:', selectedToolId);
            }
          }
          // Check for tool deselection
          if (name === 'tool_deselected' || name === 'composer.tool.deselected') {
            selectedToolId = null;
            console.log('[Tool] Deselected from ChatKit');
          }
        });

        // Also listen for any custom events that might indicate tool selection
        chatkit.addEventListener('chatkit.composer.tool', (e: CustomEvent) => {
          console.log('[ChatKit] Composer tool event:', e.detail);
          if (e.detail?.id) {
            selectedToolId = e.detail.id;
            console.log('[Tool] Selected from composer event:', selectedToolId);
          }
        });

      } catch (err) {
        console.error('Failed to configure ChatKit:', err);
        setError('Failed to configure chat interface');
      }
    };

    // Initialize with delay for element to be ready
    setTimeout(initChatKit, 300);
  }, [isLoaded]);

  // Check if ChatKit is already registered (from cache or previous page)
  useEffect(() => {
    // Check immediately if already registered (cached/previous load)
    if (customElements.get('openai-chatkit')) {
      console.log('[SchemaAgent] ChatKit element already registered on mount');
      setIsLoaded(true);
      return;
    }

    // Start polling for element registration
    let attempts = 0;
    const maxAttempts = 200; // 10 seconds max (50ms * 200)

    const checkElement = () => {
      attempts++;
      if (customElements.get('openai-chatkit')) {
        console.log('[SchemaAgent] ChatKit element registered after', attempts, 'attempts');
        setIsLoaded(true);
        if (checkIntervalRef.current) {
          clearInterval(checkIntervalRef.current);
          checkIntervalRef.current = null;
        }
      } else if (attempts >= maxAttempts) {
        console.error('[SchemaAgent] ChatKit element not registered after max attempts');
        setError('ChatKit failed to initialize. Please refresh the page.');
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

  const handleScriptLoad = () => {
    console.log('[SchemaAgent] ChatKit script loaded from CDN');
    // Check immediately after script loads
    if (customElements.get('openai-chatkit')) {
      console.log('[SchemaAgent] ChatKit element registered immediately after script load');
      setIsLoaded(true);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!user || connectionStatus?.connection_type !== 'schema_query_only') {
    return null;
  }

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Load ChatKit from OpenAI CDN */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => {
          console.error('Failed to load ChatKit:', e);
          setError('Failed to load chat interface');
        }}
      />

      {/* Header */}
      <header className="bg-white shadow-sm flex-shrink-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl">🧠</span>
              </div>
              <span className="text-xl font-bold text-gray-900">AI Agent</span>
            </Link>
            <span className="text-gray-400">|</span>
            <span className="text-gray-600 text-sm">Query your database with natural language</span>
          </div>
          <div className="flex items-center space-x-4">
            {connectionStatus?.tables_count !== undefined && (
              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                {connectionStatus.tables_count} tables
              </span>
            )}
            <Link
              href={ROUTES.SCHEMA_CONNECT}
              className="text-gray-600 hover:text-gray-900 text-sm"
            >
              View Schema
            </Link>
            <Link
              href={ROUTES.DASHBOARD}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <span className="text-red-700 text-sm">{error}</span>
            <button
              onClick={() => setError('')}
              className="text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* ChatKit Container */}
      <div className="flex-grow overflow-hidden relative">
        {!isLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading chat interface...</p>
            </div>
          </div>
        )}

        {/* ChatKit Web Component - always render but hide until loaded */}
        <openai-chatkit
          ref={chatkitRef as any}
          id="schema-chatkit"
          style={{
            width: '100%',
            height: '100%',
            display: isLoaded ? 'block' : 'none',
          }}
        />
      </div>

      {/* Footer info */}
      <div className="bg-white border-t border-gray-200 px-4 py-2 flex-shrink-0">
        <div className="max-w-7xl mx-auto text-center text-xs text-gray-500">
          Read-only mode - Only SELECT queries are executed on your database
        </div>
      </div>
    </div>
  );
}
