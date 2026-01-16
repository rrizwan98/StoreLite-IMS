/**
 * Keyboard Shortcuts Provider
 *
 * Global keyboard shortcut handler that:
 * - Registers system-wide keyboard shortcuts
 * - Shows visual feedback when shortcuts are triggered
 * - Respects input focus (doesn't trigger when typing)
 * - Supports both Windows (Ctrl) and Mac (Cmd) modifiers
 *
 * v1.0: Initial implementation
 */

'use client';

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { Keyboard, Search, HelpCircle, FileText } from 'lucide-react';

// Types for keyboard shortcuts
interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  description: string;
  action: () => void;
}

interface ShortcutToast {
  id: string;
  message: string;
  icon?: ReactNode;
}

interface KeyboardShortcutsContextType {
  registerShortcut: (shortcut: KeyboardShortcut) => void;
  unregisterShortcut: (key: string) => void;
  shortcuts: KeyboardShortcut[];
  openDocumentation: () => void;
  openShortcutsModal: () => void;
  openCommandPalette: () => void;
  focusChatInput: () => void;
}

const KeyboardShortcutsContext = createContext<KeyboardShortcutsContextType | null>(null);

export function useKeyboardShortcuts() {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error('useKeyboardShortcuts must be used within KeyboardShortcutsProvider');
  }
  return context;
}

interface KeyboardShortcutsProviderProps {
  children: ReactNode;
  onOpenDocumentation?: () => void;
  onOpenShortcuts?: () => void;
  onOpenCommandPalette?: () => void;
}

export default function KeyboardShortcutsProvider({
  children,
  onOpenDocumentation,
  onOpenShortcuts,
  onOpenCommandPalette,
}: KeyboardShortcutsProviderProps) {
  const [shortcuts, setShortcuts] = useState<KeyboardShortcut[]>([]);
  const [toasts, setToasts] = useState<ShortcutToast[]>([]);

  // Show a toast notification
  const showToast = useCallback((message: string, icon?: ReactNode) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, icon }]);

    // Auto-remove after 2 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 2000);
  }, []);

  // Focus chat input
  const focusChatInput = useCallback(() => {
    // Try to find chat input by various selectors
    const selectors = [
      '[data-chat-input]',
      'openai-chatkit textarea',
      'openai-chatkit input',
      '.chat-input',
      '#chat-input',
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector) as HTMLElement;
      if (element) {
        element.focus();
        showToast('Chat input focused', <Search className="h-4 w-4" />);
        return;
      }
    }

    // If on schema-agent page, try to focus the chatkit
    const chatkit = document.querySelector('openai-chatkit');
    if (chatkit) {
      // Try to access shadow DOM or dispatch focus event
      chatkit.dispatchEvent(new FocusEvent('focus'));
      showToast('Chat focused', <Search className="h-4 w-4" />);
    }
  }, [showToast]);

  // Open documentation
  const openDocumentation = useCallback(() => {
    if (onOpenDocumentation) {
      onOpenDocumentation();
      showToast('Documentation opened', <FileText className="h-4 w-4" />);
    }
  }, [onOpenDocumentation, showToast]);

  // Open shortcuts modal
  const openShortcutsModal = useCallback(() => {
    if (onOpenShortcuts) {
      onOpenShortcuts();
      showToast('Shortcuts reference', <Keyboard className="h-4 w-4" />);
    }
  }, [onOpenShortcuts, showToast]);

  // Open command palette
  const openCommandPalette = useCallback(() => {
    if (onOpenCommandPalette) {
      onOpenCommandPalette();
      showToast('Command palette', <Search className="h-4 w-4" />);
    }
  }, [onOpenCommandPalette, showToast]);

  // Register a new shortcut
  const registerShortcut = useCallback((shortcut: KeyboardShortcut) => {
    setShortcuts((prev) => {
      // Remove existing shortcut with same key combo
      const filtered = prev.filter((s) => s.key !== shortcut.key);
      return [...filtered, shortcut];
    });
  }, []);

  // Unregister a shortcut
  const unregisterShortcut = useCallback((key: string) => {
    setShortcuts((prev) => prev.filter((s) => s.key !== key));
  }, []);

  // Check if user is in an input field
  const isInInputField = useCallback(() => {
    const activeElement = document.activeElement;
    if (!activeElement) return false;

    const tagName = activeElement.tagName.toLowerCase();
    const isEditable = activeElement.getAttribute('contenteditable') === 'true';

    return (
      tagName === 'input' ||
      tagName === 'textarea' ||
      tagName === 'select' ||
      isEditable
    );
  }, []);

  // Main keyboard event handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

      // Handle Escape - always works
      if (e.key === 'Escape') {
        // Let individual modals handle their own escape
        return;
      }

      // Handle '?' for shortcuts (only if not in input)
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !e.altKey && !isInInputField()) {
        e.preventDefault();
        openShortcutsModal();
        return;
      }

      // Handle '/' for chat focus (only if not in input)
      if (e.key === '/' && !e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey && !isInInputField()) {
        e.preventDefault();
        focusChatInput();
        return;
      }

      // Handle Shift+/ for documentation (only if not in input)
      if (e.key === '/' && e.shiftKey && !e.ctrlKey && !e.metaKey && !isInInputField()) {
        e.preventDefault();
        openDocumentation();
        return;
      }

      // Handle Ctrl/Cmd+K for command palette
      if (e.key === 'k' && ctrlOrCmd && !e.shiftKey && !e.altKey) {
        e.preventDefault();
        openCommandPalette();
        return;
      }

      // Handle Ctrl/Cmd+/ for documentation (alternative)
      if (e.key === '/' && ctrlOrCmd) {
        e.preventDefault();
        openDocumentation();
        return;
      }

      // Check registered shortcuts
      for (const shortcut of shortcuts) {
        const matchesKey = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const matchesCtrl = shortcut.ctrl ? ctrlOrCmd : !ctrlOrCmd;
        const matchesShift = shortcut.shift ? e.shiftKey : !e.shiftKey;
        const matchesAlt = shortcut.alt ? e.altKey : !e.altKey;

        if (matchesKey && matchesCtrl && matchesShift && matchesAlt) {
          // Skip if in input field unless explicitly allowed
          if (isInInputField() && !shortcut.ctrl && !shortcut.alt) {
            continue;
          }
          e.preventDefault();
          shortcut.action();
          showToast(shortcut.description);
          return;
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [
    shortcuts,
    isInInputField,
    openDocumentation,
    openShortcutsModal,
    openCommandPalette,
    focusChatInput,
    showToast,
  ]);

  const contextValue: KeyboardShortcutsContextType = {
    registerShortcut,
    unregisterShortcut,
    shortcuts,
    openDocumentation,
    openShortcutsModal,
    openCommandPalette,
    focusChatInput,
  };

  return (
    <KeyboardShortcutsContext.Provider value={contextValue}>
      {children}

      {/* Toast Notifications */}
      <div className="fixed bottom-24 right-6 z-[200] flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className="flex items-center gap-2 px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900
                       rounded-lg shadow-lg animate-fade-in-up text-sm font-medium"
          >
            {toast.icon}
            {toast.message}
          </div>
        ))}
      </div>
    </KeyboardShortcutsContext.Provider>
  );
}

// Export a simple hook for checking if a key is pressed
export function useKeyPress(targetKey: string, callback: () => void) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === targetKey) {
        callback();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [targetKey, callback]);
}
