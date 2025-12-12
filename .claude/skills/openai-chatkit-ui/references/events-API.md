# ChatKit Events and API

Official events and methods for the ChatKit web component.

## ⚠️ CRITICAL: Load from CDN, NOT npm

```html
<!-- ✅ CORRECT: Load from CDN -->
<script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"></script>

<!-- ❌ WRONG: npm package is types only, not the actual component -->
<!-- import '@openai/chatkit'; -->
```

## Wait for Custom Element Registration

```javascript
// ✅ CORRECT: Wait for custom element
await customElements.whenDefined('openai-chatkit');

// OR check if registered
if (customElements.get('openai-chatkit')) {
  // ChatKit is ready
}

// ❌ WRONG: window.openai.ChatKit doesn't exist!
// if (window.openai?.ChatKit) { ... }
```

---

## Event Listeners

### Available Events

```javascript
const chatkit = document.getElementById('chat');

// Message events
chatkit.addEventListener('chatkit.message', (e) => {
  console.log('New message:', e.detail);
});

chatkit.addEventListener('chatkit.message-start', (e) => {
  console.log('Message started:', e.detail);
});

chatkit.addEventListener('chatkit.message-end', (e) => {
  console.log('Message completed:', e.detail);
});

// Error events
chatkit.addEventListener('chatkit.error', (e) => {
  console.error('ChatKit error:', e.detail);
});

// Thread events
chatkit.addEventListener('chatkit.thread-change', (e) => {
  console.log('Thread changed:', e.detail);
});
```

---

## setOptions() - CORRECT Format

### ⚠️ CRITICAL: theme is a STRING, not object!

```javascript
chatkit.setOptions({
  // API configuration (required for custom backend)
  api: {
    url: 'http://localhost:8000/agent/chatkit',
    domainKey: '',  // Empty string for localhost dev
    
    // Optional: Custom fetch for auth/session
    fetch: async (url, options) => {
      const body = options.body ? JSON.parse(options.body) : {};
      body.session_id = sessionId;
      return fetch(url, {
        ...options,
        body: JSON.stringify(body),
        headers: { ...options.headers, 'Content-Type': 'application/json' },
      });
    },
  },
  
  // ✅ CORRECT: theme is a string literal
  theme: 'light',  // 'light' | 'dark' | 'auto'
  
  // ❌ WRONG: theme as object causes "Invalid input" error
  // theme: { colorScheme: 'light' },
  
  // Header configuration
  header: {
    enabled: true,
    title: {
      enabled: true,
      text: 'AI Assistant',  // ✅ Use 'text', not 'content'
    },
  },
  
  // Start screen configuration
  startScreen: {
    greeting: 'Hello! How can I help?',
    prompts: [
      // ✅ CORRECT: Use 'label' and 'prompt'
      { label: 'Get Started', prompt: 'Help me get started' },
      { label: 'Features', prompt: 'What can you do?' },
      
      // ❌ WRONG: 'text' instead of 'label'
      // { text: 'Get Started', prompt: '...' },
    ],
  },
  
  // Composer configuration
  composer: {
    placeholder: 'Type a message...',
    // Attachments disabled by default, no config needed
  },
  
  // Disclaimer
  disclaimer: {
    text: 'AI may make mistakes. Verify important information.',
  },
});
```

### Complete Configuration Reference

```javascript
chatkit.setOptions({
  // Required for custom backend
  api: {
    url: string,           // Your backend URL
    domainKey: string,     // Empty '' for localhost
    fetch?: Function,      // Custom fetch wrapper
  },
  
  // Theme
  theme: 'light' | 'dark' | 'auto',
  
  // Header
  header: {
    enabled: boolean,
    title: {
      enabled: boolean,
      text: string,
    },
  },
  
  // Start screen
  startScreen: {
    greeting: string,
    prompts: Array<{
      label: string,   // Button text
      prompt: string,  // Message to send
    }>,
  },
  
  // Input composer
  composer: {
    placeholder: string,
  },
  
  // Footer disclaimer
  disclaimer: {
    text: string,
  },
});
```

---

## Methods

### sendMessage()

Send a message programmatically:

```javascript
chatkit.sendMessage('Hello, how are you?');
```

### clearThread()

Start a new conversation:

```javascript
chatkit.clearThread();
```

### focus()

Focus the input:

```javascript
chatkit.focus();
```

---

## Complete Working Example (Next.js)

```tsx
'use client';

import { useEffect, useState, useRef } from 'react';
import Script from 'next/script';

export default function ChatKitWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);
  const chatkitRef = useRef<HTMLElement | null>(null);
  const configuredRef = useRef(false);

  // Configure when ready
  useEffect(() => {
    if (!isOpen || !isLoaded || configuredRef.current) return;

    const initChatKit = () => {
      const chatkit = chatkitRef.current as any;
      if (!chatkit || typeof chatkit.setOptions !== 'function') {
        setTimeout(initChatKit, 100);
        return;
      }

      configuredRef.current = true;

      chatkit.setOptions({
        api: {
          url: 'http://localhost:8000/agent/chatkit',
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
            { label: 'Get Started', prompt: 'Help me get started' },
          ],
        },
      });

      // Event listeners
      chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
        console.log('Message:', e.detail);
      });
      chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
        console.error('Error:', e.detail);
      });
    };

    setTimeout(initChatKit, 300);
  }, [isOpen, isLoaded]);

  const handleScriptLoad = () => {
    const checkElement = () => {
      if (customElements.get('openai-chatkit')) {
        setIsLoaded(true);
      } else {
        setTimeout(checkElement, 100);
      }
    };
    checkElement();
  };

  return (
    <>
      {/* CDN Script */}
      <Script
        src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js"
        strategy="afterInteractive"
        onLoad={handleScriptLoad}
        onError={(e) => console.error('Failed:', e)}
      />

      {/* Toggle Button */}
      <button onClick={() => setIsOpen(!isOpen)}>
        {isOpen ? 'Close' : 'Chat'}
      </button>

      {/* ChatKit */}
      {isOpen && isLoaded && (
        <openai-chatkit
          ref={chatkitRef as any}
          style={{ width: '400px', height: '500px' }}
        />
      )}
    </>
  );
}

// Type declaration
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

## Common Errors

### Error: "Invalid input" on api config

**Cause:** Wrong structure for api object.

**Fix:** Use correct structure:
```javascript
api: {
  url: 'http://...',
  domainKey: '',  // Required, even if empty
}
```

### Error: "Invalid input" on theme

**Cause:** `theme` is an object instead of string.

**Fix:** Use string:
```javascript
theme: 'light'  // NOT { colorScheme: 'light' }
```

### Error: Prompts not showing

**Cause:** Using `text` instead of `label`.

**Fix:** Use correct field names:
```javascript
prompts: [
  { label: 'Button Text', prompt: 'Message to send' }
]
```
