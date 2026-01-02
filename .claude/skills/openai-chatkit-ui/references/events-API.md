# Events API Reference

> Complete guide for ChatKit event handling and API methods.

---

## Event Listeners

### Message Events

```typescript
const chatkit = document.getElementById('my-chatkit');

// Message sent or received
chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
  console.log('Message event:', e.detail);
  // detail: { type: 'user' | 'assistant', content: string, ... }
});

// Message stream started
chatkit.addEventListener('chatkit.stream.start', (e: CustomEvent) => {
  console.log('Stream started:', e.detail);
});

// Message stream chunk
chatkit.addEventListener('chatkit.stream.chunk', (e: CustomEvent) => {
  console.log('Stream chunk:', e.detail);
});

// Message stream completed
chatkit.addEventListener('chatkit.stream.end', (e: CustomEvent) => {
  console.log('Stream ended:', e.detail);
});
```

### Thread Events

```typescript
// Thread created
chatkit.addEventListener('chatkit.thread.created', (e: CustomEvent) => {
  console.log('Thread created:', e.detail.threadId);
});

// Thread switched
chatkit.addEventListener('chatkit.thread.switched', (e: CustomEvent) => {
  console.log('Switched to thread:', e.detail.threadId);
});

// Thread deleted
chatkit.addEventListener('chatkit.thread.deleted', (e: CustomEvent) => {
  console.log('Thread deleted:', e.detail.threadId);
});
```

### Error Events

```typescript
// Error occurred
chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
  console.error('ChatKit error:', e.detail);
  // detail: { code: string, message: string, allow_retry: boolean }

  // Handle specific errors
  if (e.detail.code === 'RATE_LIMIT') {
    showRateLimitWarning();
  } else if (e.detail.code === 'STREAM_ERROR') {
    showRetryButton();
  }
});
```

### UI Events

```typescript
// Widget opened
chatkit.addEventListener('chatkit.open', (e: CustomEvent) => {
  console.log('ChatKit opened');
  trackAnalytics('chatkit_opened');
});

// Widget closed
chatkit.addEventListener('chatkit.close', (e: CustomEvent) => {
  console.log('ChatKit closed');
});

// User started typing
chatkit.addEventListener('chatkit.typing.start', (e: CustomEvent) => {
  console.log('User typing');
});

// User stopped typing
chatkit.addEventListener('chatkit.typing.stop', (e: CustomEvent) => {
  console.log('User stopped typing');
});
```

### Attachment Events

```typescript
// File attached
chatkit.addEventListener('chatkit.attachment.added', (e: CustomEvent) => {
  console.log('File attached:', e.detail.file);
  // detail: { file: File, type: string, size: number }
});

// File removed
chatkit.addEventListener('chatkit.attachment.removed', (e: CustomEvent) => {
  console.log('File removed:', e.detail.fileId);
});

// File upload progress
chatkit.addEventListener('chatkit.attachment.progress', (e: CustomEvent) => {
  console.log('Upload progress:', e.detail.percent);
});
```

---

## API Methods

### setOptions()

Configure ChatKit programmatically:

```typescript
chatkit.setOptions({
  api: {
    url: 'http://localhost:8000/chatkit',
    domainKey: '',
    fetch: customFetch,
  },
  theme: 'light',
  header: {
    enabled: true,
    title: { enabled: true, text: 'AI Assistant' },
  },
  startScreen: {
    greeting: 'Hello!',
    prompts: [
      { label: 'Help', prompt: 'Help me get started' },
    ],
  },
  composer: {
    placeholder: 'Type here...',
    attachments: { enabled: true },
  },
  disclaimer: {
    text: 'AI may make mistakes.',
  },
});
```

### sendMessage()

Programmatically send a message:

```typescript
chatkit.sendMessage('Hello, I need help with my order');

// With metadata
chatkit.sendMessage('Track order #12345', {
  metadata: { orderId: '12345' }
});
```

### clearThread()

Clear current conversation:

```typescript
chatkit.clearThread();
```

### switchThread()

Switch to a different thread:

```typescript
chatkit.switchThread('thread-abc123');
```

### createThread()

Create a new thread:

```typescript
const threadId = await chatkit.createThread({
  title: 'Support Request',
  metadata: { priority: 'high' }
});
```

### deleteThread()

Delete a thread:

```typescript
await chatkit.deleteThread('thread-abc123');
```

### focus()

Focus the composer input:

```typescript
chatkit.focus();
```

### blur()

Remove focus from composer:

```typescript
chatkit.blur();
```

---

## Event Detail Types

### MessageEvent Detail

```typescript
interface MessageEventDetail {
  type: 'user' | 'assistant';
  id: string;
  threadId: string;
  content: string;
  timestamp: string;
  attachments?: Array<{
    id: string;
    type: 'file' | 'image';
    name: string;
    mimeType: string;
  }>;
}
```

### ErrorEvent Detail

```typescript
interface ErrorEventDetail {
  code: ErrorCode;
  message: string;
  allow_retry: boolean;
  details?: Record<string, any>;
}

type ErrorCode =
  | 'INVALID_REQUEST'
  | 'STREAM_ERROR'
  | 'RATE_LIMIT'
  | 'AUTHENTICATION_ERROR'
  | 'NETWORK_ERROR'
  | 'UNKNOWN';
```

### ThreadEvent Detail

```typescript
interface ThreadEventDetail {
  threadId: string;
  title?: string;
  createdAt?: string;
  metadata?: Record<string, any>;
}
```

---

## Custom Fetch Handler

Intercept and modify requests:

```typescript
chatkit.setOptions({
  api: {
    url: `${API_BASE_URL}/chatkit`,
    domainKey: '',
    fetch: async (url: string, options: RequestInit) => {
      // Parse body
      const body = options.body ? JSON.parse(options.body as string) : {};

      // Inject session ID
      body.session_id = getSessionId();

      // Inject tool prefix
      if (selectedTool) {
        const messages = body.messages || [];
        const lastMessage = messages[messages.length - 1];
        if (lastMessage?.role === 'user') {
          lastMessage.content = `[TOOL:${selectedTool}] ${lastMessage.content}`;
        }
      }

      // Add custom headers
      const headers = {
        ...options.headers,
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`,
        'X-Custom-Header': 'value',
      };

      // Make request
      const response = await fetch(url, {
        ...options,
        body: JSON.stringify(body),
        headers,
      });

      // Handle response errors
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Request failed');
      }

      return response;
    },
  },
});
```

---

## Event Handling Patterns

### Track Analytics

```typescript
chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
  if (e.detail.type === 'user') {
    trackEvent('message_sent', {
      threadId: e.detail.threadId,
      hasAttachments: e.detail.attachments?.length > 0,
    });
  }
});

chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
  trackEvent('chatkit_error', {
    code: e.detail.code,
    message: e.detail.message,
  });
});
```

### Show Custom Notifications

```typescript
chatkit.addEventListener('chatkit.message', (e: CustomEvent) => {
  if (e.detail.type === 'assistant') {
    // Show browser notification if tab is inactive
    if (document.hidden) {
      new Notification('New message from AI Assistant', {
        body: e.detail.content.substring(0, 100),
      });
    }
  }
});
```

### Handle Errors Gracefully

```typescript
chatkit.addEventListener('chatkit.error', (e: CustomEvent) => {
  const { code, message, allow_retry } = e.detail;

  switch (code) {
    case 'RATE_LIMIT':
      showToast('Too many requests. Please wait a moment.', 'warning');
      break;

    case 'AUTHENTICATION_ERROR':
      // Redirect to login
      window.location.href = '/login';
      break;

    case 'NETWORK_ERROR':
      showToast('Network error. Check your connection.', 'error');
      break;

    case 'STREAM_ERROR':
      if (allow_retry) {
        showRetryButton();
      } else {
        showToast(message, 'error');
      }
      break;

    default:
      showToast('An error occurred. Please try again.', 'error');
  }
});
```

### Sync with External State

```typescript
// Update external UI when thread changes
chatkit.addEventListener('chatkit.thread.switched', (e: CustomEvent) => {
  updateBreadcrumb(e.detail.threadId);
  loadRelatedContent(e.detail.threadId);
});

// Clear external state when thread is deleted
chatkit.addEventListener('chatkit.thread.deleted', (e: CustomEvent) => {
  clearRelatedContent(e.detail.threadId);
});
```

---

## React Integration

### Custom Hook

```tsx
import { useEffect, useRef, useCallback } from 'react';

function useChatKit(onMessage?: (detail: any) => void, onError?: (detail: any) => void) {
  const chatkitRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const chatkit = chatkitRef.current;
    if (!chatkit) return;

    const messageHandler = (e: CustomEvent) => onMessage?.(e.detail);
    const errorHandler = (e: CustomEvent) => onError?.(e.detail);

    chatkit.addEventListener('chatkit.message', messageHandler);
    chatkit.addEventListener('chatkit.error', errorHandler);

    return () => {
      chatkit.removeEventListener('chatkit.message', messageHandler);
      chatkit.removeEventListener('chatkit.error', errorHandler);
    };
  }, [onMessage, onError]);

  const sendMessage = useCallback((message: string) => {
    (chatkitRef.current as any)?.sendMessage(message);
  }, []);

  return { chatkitRef, sendMessage };
}

// Usage
function ChatWidget() {
  const { chatkitRef, sendMessage } = useChatKit(
    (detail) => console.log('Message:', detail),
    (detail) => console.error('Error:', detail)
  );

  return <openai-chatkit ref={chatkitRef} />;
}
```

---

## Best Practices

1. **Always handle errors** - Provide user feedback for failures
2. **Track important events** - For analytics and debugging
3. **Use event delegation** - Add listeners to the chatkit element directly
4. **Clean up listeners** - Remove in useEffect cleanup or component unmount
5. **Don't block events** - Keep handlers fast and non-blocking
6. **Log for debugging** - But remove in production
