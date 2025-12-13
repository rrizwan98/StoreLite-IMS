'use client';

/**
 * Pure OpenAI ChatKit SDK Integration
 * 
 * Uses the official OpenAI ChatKit web component (<openai-chatkit>)
 * loaded from OpenAI's CDN
 * No custom React chat UI - pure ChatKit SDK only
 */

import { useEffect, useState, useRef } from 'react';
import Script from 'next/script';
import { API_BASE_URL } from '@/lib/constants';

// Generate unique session ID
const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session-${timestamp}-${random}`;
};

export default function ChatKitWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);
  
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('ims-chatkit-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('ims-chatkit-session-id', id);
      }
      return id;
    }
    return generateSessionId();
  });

  // Configure ChatKit when opened and loaded
  useEffect(() => {
    if (!isOpen || !isLoaded || configuredRef.current) return;

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

      console.log('✓ Configuring pure OpenAI ChatKit');
      configuredRef.current = true;

      // Pure OpenAI ChatKit SDK configuration (correct format per type definitions)
      chatkit.setOptions({
        // Custom backend API configuration (CustomApiConfig)
        api: {
          url: `${API_BASE_URL}/agent/chatkit`,
          // domainKey is required for custom API - using empty string for development
          domainKey: '',
          // Custom fetch for session management
          fetch: async (url: string, options: RequestInit) => {
            try {
              const body = options.body ? JSON.parse(options.body as string) : {};
              body.session_id = sessionId;

              return fetch(url, {
                ...options,
                body: JSON.stringify(body),
                headers: {
                  ...options.headers,
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
            text: 'IMS AI Assistant',
          },
        },
        // Start screen configuration (StartScreenOption)
        startScreen: {
          greeting: 'Hello! I can help you manage inventory and create bills.',
          prompts: [
            { label: 'Add Item', prompt: 'Help me add a new inventory item' },
            { label: 'Create Bill', prompt: 'I need to create a new bill' },
            { label: 'Check Stock', prompt: 'Show me current inventory' },
          ],
        },
        // Composer configuration (ComposerOption)
        composer: {
          placeholder: 'Type your message...',
          // No attachments config = disabled by default
        },
        // Disclaimer configuration (DisclaimerOption)
        disclaimer: {
          text: 'AI may make mistakes. Verify important information.',
        },
      });

      // Official ChatKit event listeners
      chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
        console.log('ChatKit message event:', e.detail);
      });

      chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
        console.error('ChatKit error event:', e.detail);
      });
    };

    // Initialize with delay for element to be ready
    setTimeout(initChatKit, 300);
  }, [isOpen, isLoaded, sessionId]);

  // Reset configured flag when closed
  useEffect(() => {
    if (!isOpen) {
      configuredRef.current = false;
    }
  }, [isOpen]);

  const handleScriptLoad = () => {
    console.log('✓ ChatKit script loaded from CDN');
    // Check if custom element is registered
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        console.log('✓ ChatKit custom element registered');
        setIsLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  return (
    <>
      {/* Load ChatKit from OpenAI CDN */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('Failed to load ChatKit:', e)}
      />

      {/* Toggle Button - Only custom element */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg 
                   bg-blue-600 hover:bg-blue-700 text-white transition-all duration-200
                   flex items-center justify-center focus:outline-none focus:ring-2 
                   focus:ring-blue-500 focus:ring-offset-2"
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        ) : (
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        )}
      </button>

      {/* Pure OpenAI ChatKit Web Component */}
      {isOpen && (
        <div 
          className="fixed bottom-24 right-6 z-50 w-96 h-[500px] rounded-xl 
                     shadow-2xl border border-gray-200 overflow-hidden bg-white"
        >
          {isLoaded ? (
            <openai-chatkit
              ref={chatkitRef as any}
              id="ims-chatkit"
              style={{ 
                width: '100%', 
                height: '100%',
                display: 'block',
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          )}
        </div>
      )}
    </>
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
