# ChatKit Theming (Official Options Only)

Style ChatKit using ONLY official configuration options and CSS.

## ⚠️ CRITICAL: Theme is a String, NOT Object

```javascript
// ✅ CORRECT: theme is a string literal
chatkit.setOptions({
  theme: 'light',  // 'light' | 'dark' | 'auto'
});

// ❌ WRONG: theme as object causes "Invalid input" error
chatkit.setOptions({
  theme: {
    colorScheme: 'light',  // This won't work!
  },
});
```

---

## Theme Options

| Value | Description |
|-------|-------------|
| `'light'` | Light theme with white background |
| `'dark'` | Dark theme with dark background |
| `'auto'` | Follows system preference |

---

## Container Styling

Style the container around ChatKit, NOT ChatKit internals:

```css
/* Style the container, not internal ChatKit elements */
.chatkit-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 400px;
  height: 500px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

.chatkit-container openai-chatkit {
  width: 100%;
  height: 100%;
  display: block;
}
```

---

## Responsive Sizing

```css
/* Mobile */
@media (max-width: 640px) {
  .chatkit-container {
    position: fixed;
    inset: 0;
    width: 100%;
    height: 100%;
    border-radius: 0;
  }
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  .chatkit-container {
    width: 350px;
    height: 450px;
  }
}

/* Desktop */
@media (min-width: 1025px) {
  .chatkit-container {
    width: 400px;
    height: 500px;
  }
}
```

---

## Embedding Layouts

### Floating Widget (Bottom Right)

```html
<button id="chat-toggle" class="chat-button">💬</button>

<div id="chat-container" class="chatkit-container hidden">
  <openai-chatkit id="chatkit"></openai-chatkit>
</div>

<style>
  .chat-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: #2563EB;
    color: white;
    border: none;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
  }
  
  .chatkit-container {
    position: fixed;
    bottom: 96px;
    right: 24px;
    width: 400px;
    height: 500px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    overflow: hidden;
    background: white;
    z-index: 1000;
  }
  
  .chatkit-container.hidden {
    display: none;
  }
  
  .chatkit-container openai-chatkit {
    width: 100%;
    height: 100%;
    display: block;
  }
</style>

<script>
  document.getElementById('chat-toggle').onclick = () => {
    document.getElementById('chat-container').classList.toggle('hidden');
  };
</script>
```

### Sidebar Layout

```html
<div class="app-layout">
  <main class="content">
    <!-- Your app content -->
  </main>
  <aside class="chat-sidebar">
    <openai-chatkit id="chatkit"></openai-chatkit>
  </aside>
</div>

<style>
  .app-layout {
    display: flex;
    height: 100vh;
  }
  
  .content {
    flex: 1;
    overflow: auto;
  }
  
  .chat-sidebar {
    width: 400px;
    border-left: 1px solid #e5e7eb;
    background: white;
  }
  
  .chat-sidebar openai-chatkit {
    width: 100%;
    height: 100%;
    display: block;
  }
</style>
```

### Fullscreen Modal

```html
<div id="chat-modal" class="modal hidden">
  <div class="modal-content">
    <button class="close-btn" onclick="closeModal()">&times;</button>
    <openai-chatkit id="chatkit"></openai-chatkit>
  </div>
</div>

<style>
  .modal {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal.hidden {
    display: none;
  }
  
  .modal-content {
    background: white;
    border-radius: 12px;
    width: 600px;
    height: 80vh;
    max-width: 90vw;
    position: relative;
    overflow: hidden;
  }
  
  .modal-content openai-chatkit {
    width: 100%;
    height: 100%;
    display: block;
  }
  
  .close-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
    background: rgba(0, 0, 0, 0.1);
    border: none;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    font-size: 20px;
    cursor: pointer;
  }
</style>

<script>
  function openModal() {
    document.getElementById('chat-modal').classList.remove('hidden');
  }
  function closeModal() {
    document.getElementById('chat-modal').classList.add('hidden');
  }
</script>
```

---

## Next.js / React Styling

```tsx
'use client';

export default function ChatKitWidget() {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full 
                   bg-blue-600 hover:bg-blue-700 text-white shadow-lg
                   flex items-center justify-center transition-colors"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* ChatKit Container */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-50 w-96 h-[500px] 
                        rounded-xl shadow-2xl border overflow-hidden bg-white">
          <openai-chatkit
            ref={chatkitRef as any}
            style={{ 
              width: '100%', 
              height: '100%',
              display: 'block',
            }}
          />
        </div>
      )}
    </>
  );
}
```

---

## DO NOT

❌ Override internal ChatKit styles with `!important`
❌ Use browser dev tools to find and override internal classes
❌ Inject custom CSS into ChatKit shadow DOM
❌ Replace ChatKit components with custom implementations
❌ Use `theme: { colorScheme: '...' }` object format

## DO

✅ Use `theme: 'light'` | `'dark'` | `'auto'` string format
✅ Style the container element around ChatKit
✅ Use media queries on container for responsiveness
✅ Set width/height on the `<openai-chatkit>` element itself
