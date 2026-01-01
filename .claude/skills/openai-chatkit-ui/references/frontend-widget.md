# Frontend Widget Reference

> Complete guide for integrating OpenAI ChatKit web component in frontend applications.

---

## Core Principles

1. **Pure Web Component**: Use only `<openai-chatkit>` custom element
2. **CDN Loading**: Load script from OpenAI CDN
3. **Configuration via setOptions()**: All settings through official API
4. **No React Wrapper**: Never use `@openai/chatkit-react`
5. **No Custom UI**: Never create custom message components

---

## Basic Implementation

### Next.js (React with Script Loader)

```tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import Script from 'next/script';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Generate unique session ID (tab-lifetime persistence)
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

  // Session ID persisted in sessionStorage
  const [sessionId] = useState(() => {
    if (typeof window !== 'undefined') {
      let id = sessionStorage.getItem('chatkit-session-id');
      if (!id) {
        id = generateSessionId();
        sessionStorage.setItem('chatkit-session-id', id);
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

      console.log('Configuring ChatKit');
      configuredRef.current = true;

      chatkit.setOptions({
        // Custom backend API
        api: {
          url: `${API_BASE_URL}/chatkit`,
          domainKey: '', // Empty for development/custom backend
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
                  'Authorization': `Bearer ${getAuthToken()}`, // Add auth if needed
                },
              });
            } catch (e) {
              console.error('ChatKit fetch error:', e);
              throw e;
            }
          },
        },
        // Theme
        theme: 'light', // or 'dark'
        // Header
        header: {
          enabled: true,
          title: {
            enabled: true,
            text: 'AI Assistant',
          },
        },
        // Start screen
        startScreen: {
          greeting: 'Hello! How can I help you today?',
          prompts: [
            { label: 'Get Started', prompt: 'Help me get started' },
            { label: 'Examples', prompt: 'Show me some examples' },
            { label: 'Help', prompt: 'What can you do?' },
          ],
        },
        // Composer
        composer: {
          placeholder: 'Type your message...',
        },
        // Disclaimer
        disclaimer: {
          text: 'AI may make mistakes. Verify important information.',
        },
      });

      // Event listeners
      chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
        console.log('Message event:', e.detail);
      });

      chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
        console.error('Error event:', e.detail);
      });
    };

    setTimeout(initChatKit, 300);
  }, [isOpen, isLoaded, sessionId]);

  // Reset configured flag when closed
  useEffect(() => {
    if (!isOpen) {
      configuredRef.current = false;
    }
  }, [isOpen]);

  const handleScriptLoad = () => {
    console.log('ChatKit script loaded');
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        console.log('ChatKit custom element registered');
        setIsLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  return (
    <>
      {/* Load ChatKit from CDN */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('Failed to load ChatKit:', e)}
      />

      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full shadow-lg
                   bg-blue-600 hover:bg-blue-700 text-white"
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? 'X' : 'Chat'}
      </button>

      {/* ChatKit Container */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 h-[500px] rounded-xl
                       shadow-2xl border border-gray-200 overflow-hidden bg-white">
          {isLoaded ? (
            <openai-chatkit
              ref={chatkitRef as any}
              style={{ width: '100%', height: '100%', display: 'block' }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          )}
        </div>
      )}
    </>
  );
}

// TypeScript declaration for custom element
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
```

---

## setOptions() Configuration

### Complete Options Reference

```typescript
interface ChatKitOptions {
  // API Configuration
  api: {
    url: string;              // Your backend endpoint
    domainKey: string;        // Empty for custom backend
    fetch?: (url: string, options: RequestInit) => Promise<Response>;
  };

  // Theme
  theme: 'light' | 'dark';

  // Header
  header: {
    enabled: boolean;
    title?: {
      enabled: boolean;
      text: string;
    };
  };

  // Start Screen (shown when no messages)
  startScreen?: {
    greeting: string;
    prompts?: Array<{
      label: string;    // Button label
      prompt: string;   // Message to send
    }>;
  };

  // Message Composer
  composer?: {
    placeholder?: string;
    attachments?: {
      enabled: boolean;
      allowedTypes?: string[];  // e.g., ['image/*', 'application/pdf']
    };
  };

  // Disclaimer Footer
  disclaimer?: {
    text: string;
  };
}
```

### Configuration Examples

#### Minimal Configuration

```typescript
chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/chatkit',
    domainKey: '',
  },
  theme: 'light',
});
```

#### Full Featured Configuration

```typescript
chatkit.setOptions({
  api: {
    url: `${API_BASE_URL}/chatkit`,
    domainKey: '',
    fetch: customFetch,
  },
  theme: 'dark',
  header: {
    enabled: true,
    title: { enabled: true, text: 'Support Bot' },
  },
  startScreen: {
    greeting: 'Welcome! I can help with:\n- Product questions\n- Order tracking\n- Returns',
    prompts: [
      { label: 'Track Order', prompt: 'Help me track my order' },
      { label: 'Return Item', prompt: 'I want to return an item' },
      { label: 'Contact Human', prompt: 'I need to speak with a human' },
    ],
  },
  composer: {
    placeholder: 'Ask me anything...',
    attachments: {
      enabled: true,
      allowedTypes: ['image/*', 'application/pdf'],
    },
  },
  disclaimer: {
    text: 'This bot uses AI. Please verify important details.',
  },
});
```

---

## Custom Fetch Handler

The custom fetch handler allows you to:
1. Inject session IDs
2. Add authentication headers
3. Modify request body
4. Handle tool prefixes

```typescript
const customFetch = async (url: string, options: RequestInit) => {
  try {
    const body = options.body ? JSON.parse(options.body as string) : {};

    // Inject session ID
    body.session_id = sessionId;

    // Inject tool prefix if selected
    if (selectedToolPrefix && body.messages) {
      const lastMessage = body.messages[body.messages.length - 1];
      if (lastMessage?.role === 'user' && !lastMessage.content.startsWith('[TOOL:')) {
        lastMessage.content = `${selectedToolPrefix} ${lastMessage.content}`;
      }
    }

    // Make request
    return fetch(url, {
      ...options,
      body: JSON.stringify(body),
      headers: {
        ...options.headers,
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
      },
    });
  } catch (e) {
    console.error('ChatKit fetch error:', e);
    throw e;
  }
};
```

---

## Session Management

### Tab-Lifetime Session

```typescript
// Generate unique session ID
const generateSessionId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  return `session-${timestamp}-${random}`;
};

// Initialize in component
const [sessionId] = useState(() => {
  if (typeof window !== 'undefined') {
    let id = sessionStorage.getItem('chatkit-session-id');
    if (!id) {
      id = generateSessionId();
      sessionStorage.setItem('chatkit-session-id', id);
    }
    return id;
  }
  return generateSessionId();
});
```

### Persistent Session (localStorage)

```typescript
const [sessionId] = useState(() => {
  if (typeof window !== 'undefined') {
    let id = localStorage.getItem('chatkit-session-id');
    if (!id) {
      id = generateSessionId();
      localStorage.setItem('chatkit-session-id', id);
    }
    return id;
  }
  return generateSessionId();
});
```

---

## Tool Selection Integration

Add a tool selector that injects prefixes into messages:

```tsx
import { useState } from 'react';

interface Tool {
  id: string;
  name: string;
  prefix: string;
}

const tools: Tool[] = [
  { id: 'sql', name: 'SQL Query', prefix: '[TOOL:SQL]' },
  { id: 'search', name: 'Web Search', prefix: '[TOOL:SEARCH]' },
  { id: 'email', name: 'Email', prefix: '[TOOL:EMAIL]' },
];

function ToolSelector({ onSelect }: { onSelect: (prefix: string | null) => void }) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div className="flex gap-2">
      {tools.map((tool) => (
        <button
          key={tool.id}
          className={`px-3 py-1 rounded ${
            selected === tool.id ? 'bg-blue-600 text-white' : 'bg-gray-100'
          }`}
          onClick={() => {
            if (selected === tool.id) {
              setSelected(null);
              onSelect(null);
            } else {
              setSelected(tool.id);
              onSelect(tool.prefix);
            }
          }}
        >
          {tool.name}
        </button>
      ))}
    </div>
  );
}
```

---

## Embedding Patterns

### Floating Widget (Bottom Right)

```tsx
<div className="fixed bottom-24 right-6 z-50 w-96 h-[500px]">
  <openai-chatkit style={{ width: '100%', height: '100%' }} />
</div>
```

### Full Page

```tsx
<div className="h-screen w-full">
  <openai-chatkit style={{ width: '100%', height: '100%' }} />
</div>
```

### Sidebar

```tsx
<div className="fixed right-0 top-0 h-full w-[400px] border-l">
  <openai-chatkit style={{ width: '100%', height: '100%' }} />
</div>
```

### Modal

```tsx
{isOpen && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div className="w-[600px] h-[700px] bg-white rounded-xl overflow-hidden">
      <openai-chatkit style={{ width: '100%', height: '100%' }} />
    </div>
  </div>
)}
```

---

## Vanilla HTML Implementation

```html
<!DOCTYPE html>
<html>
<head>
  <title>ChatKit Demo</title>
  <style>
    #chat-container {
      width: 400px;
      height: 600px;
      border: 1px solid #ddd;
      border-radius: 12px;
      overflow: hidden;
    }
    openai-chatkit {
      width: 100%;
      height: 100%;
      display: block;
    }
  </style>
</head>
<body>
  <div id="chat-container">
    <openai-chatkit id="my-chatkit"></openai-chatkit>
  </div>

  <script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"></script>
  <script>
    // Wait for custom element to be defined
    customElements.whenDefined('openai-chatkit').then(() => {
      const chatkit = document.getElementById('my-chatkit');

      chatkit.setOptions({
        api: {
          url: 'http://localhost:8000/chatkit',
          domainKey: '',
        },
        theme: 'light',
        header: {
          enabled: true,
          title: { enabled: true, text: 'AI Assistant' },
        },
        startScreen: {
          greeting: 'Hello! How can I help?',
          prompts: [
            { label: 'Help', prompt: 'Help me get started' },
          ],
        },
      });

      chatkit.addEventListener('chatkit.message', (e) => {
        console.log('Message:', e.detail);
      });
    });
  </script>
</body>
</html>
```

---

## Common Issues & Solutions

### 1. ChatKit Not Rendering

**Problem**: `<openai-chatkit>` shows nothing

**Solution**: Ensure script is loaded and custom element is registered

```typescript
const checkElement = () => {
  if (customElements.get('openai-chatkit')) {
    setIsLoaded(true);
  } else {
    setTimeout(checkElement, 100);
  }
};
```

### 2. setOptions Not Available

**Problem**: `chatkit.setOptions is not a function`

**Solution**: Wait for custom element to upgrade

```typescript
if (typeof chatkit.setOptions !== 'function') {
  setTimeout(initChatKit, 100);
  return;
}
```

### 3. CORS Errors

**Problem**: Request blocked by CORS

**Solution**: Configure backend CORS properly

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. Streaming Not Working

**Problem**: Messages appear all at once

**Solution**: Ensure SSE headers are set correctly

```python
return StreamingResponse(
    generate(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Important for nginx
    }
)
```

---

## Best Practices

1. **Load script lazily** - Use `strategy="afterInteractive"` in Next.js
2. **Wait for registration** - Always wait for `customElements.get('openai-chatkit')`
3. **Configure once** - Use `configuredRef` to prevent multiple configurations
4. **Handle errors** - Add event listeners for `chatkit.error`
5. **Session persistence** - Use sessionStorage for tab-lifetime, localStorage for persistent
6. **Auth tokens** - Inject in custom fetch, not in URL
