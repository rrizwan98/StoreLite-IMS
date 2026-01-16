/**
 * Floating Help Button Component
 *
 * A floating action button (FAB) in the bottom-right corner
 * that provides quick access to help resources.
 *
 * v1.1: New component for quick help access
 * v1.3: Added Replay Tour option
 * v2.0: Integrated Documentation Modal, Support Ticket Modal, and enhanced keyboard shortcuts
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { HelpCircle, ExternalLink, Mail, Keyboard, X, Play, FileText, MessageSquare } from 'lucide-react';
import { restartOnboardingTour } from './OnboardingTour';
import DocumentationModal from './DocumentationModal';
import SupportTicketModal from './SupportTicketModal';

interface HelpMenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
  description?: string;
}

export default function FloatingHelpButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showDocumentation, setShowDocumentation] = useState(false);
  const [showSupport, setShowSupport] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Global keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const ctrlOrCmd = isMac ? e.metaKey : e.ctrlKey;

      // Check if user is in an input field
      const activeElement = document.activeElement;
      const isInInput = activeElement?.tagName === 'INPUT' ||
                        activeElement?.tagName === 'TEXTAREA' ||
                        activeElement?.tagName === 'SELECT' ||
                        activeElement?.getAttribute('contenteditable') === 'true';

      // Escape key - close all modals
      if (e.key === 'Escape') {
        if (showDocumentation) {
          setShowDocumentation(false);
          return;
        }
        if (showSupport) {
          setShowSupport(false);
          return;
        }
        if (showShortcuts) {
          setShowShortcuts(false);
          return;
        }
        setIsOpen(false);
        return;
      }

      // Skip shortcuts if in input (except Escape)
      if (isInInput) return;

      // '?' key - show keyboard shortcuts
      if (e.key === '?' && !ctrlOrCmd) {
        e.preventDefault();
        setShowShortcuts(true);
        return;
      }

      // Shift+/ or Ctrl+/ - show documentation
      if (e.key === '/' && (e.shiftKey || ctrlOrCmd)) {
        e.preventDefault();
        setShowDocumentation(true);
        return;
      }

      // '/' key alone - focus chat input
      if (e.key === '/' && !e.shiftKey && !ctrlOrCmd) {
        const chatSelectors = [
          '[data-chat-input]',
          'openai-chatkit textarea',
          'openai-chatkit input',
          '.chat-input',
          '#chat-input',
        ];
        for (const selector of chatSelectors) {
          const element = document.querySelector(selector) as HTMLElement;
          if (element) {
            e.preventDefault();
            element.focus();
            return;
          }
        }
      }

      // Ctrl/Cmd+K - command palette (future feature)
      if (e.key === 'k' && ctrlOrCmd) {
        e.preventDefault();
        // TODO: Open command palette
        console.log('Command palette triggered');
        return;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showDocumentation, showSupport, showShortcuts]);

  // Handle replay tour
  const handleReplayTour = () => {
    restartOnboardingTour();
    setIsOpen(false);
    // Small delay to allow menu to close, then force page reload to restart tour
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };

  // Handle opening documentation
  const handleOpenDocumentation = () => {
    setShowDocumentation(true);
    setIsOpen(false);
  };

  // Handle opening support
  const handleOpenSupport = () => {
    setShowSupport(true);
    setIsOpen(false);
  };

  // Handle opening shortcuts
  const handleOpenShortcuts = () => {
    setShowShortcuts(true);
    setIsOpen(false);
  };

  const menuItems: HelpMenuItem[] = [
    {
      id: 'tour',
      label: 'Replay Tour',
      icon: <Play className="h-4 w-4" />,
      onClick: handleReplayTour,
      description: 'Start the onboarding tour again',
    },
    {
      id: 'docs',
      label: 'Documentation',
      icon: <FileText className="h-4 w-4" />,
      onClick: handleOpenDocumentation,
      description: 'View help documentation',
    },
    {
      id: 'support',
      label: 'Contact Support',
      icon: <MessageSquare className="h-4 w-4" />,
      onClick: handleOpenSupport,
      description: 'Submit a support ticket',
    },
    {
      id: 'shortcuts',
      label: 'Keyboard Shortcuts',
      icon: <Keyboard className="h-4 w-4" />,
      onClick: handleOpenShortcuts,
      description: 'View all keyboard shortcuts',
    },
  ];

  return (
    <>
      {/* Floating Button and Menu */}
      <div ref={menuRef} className="fixed bottom-6 right-6 z-50" data-tour="help-button">
        {/* Dropdown Menu */}
        {isOpen && (
          <div
            className="absolute bottom-14 right-0 w-64 bg-white dark:bg-gray-800
                       rounded-xl shadow-xl border border-gray-200 dark:border-gray-700
                       py-2 animate-fade-in-up overflow-hidden"
          >
            <div className="px-4 py-2 border-b border-gray-100 dark:border-gray-700">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Help & Resources
              </p>
            </div>
            {menuItems.map((item) =>
              item.href ? (
                <a
                  key={item.id}
                  href={item.href}
                  target={item.href.startsWith('mailto:') ? undefined : '_blank'}
                  rel={item.href.startsWith('mailto:') ? undefined : 'noopener noreferrer'}
                  className="flex items-center px-4 py-3 text-sm text-gray-700 dark:text-gray-200
                             hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-gray-500 dark:text-gray-400 mr-3 group-hover:text-emerald-500 transition-colors">
                    {item.icon}
                  </span>
                  <div>
                    <p className="font-medium">{item.label}</p>
                    {item.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{item.description}</p>
                    )}
                  </div>
                  {!item.href.startsWith('mailto:') && (
                    <ExternalLink className="h-3 w-3 ml-auto text-gray-400" />
                  )}
                </a>
              ) : (
                <button
                  key={item.id}
                  onClick={() => {
                    item.onClick?.();
                  }}
                  className="flex items-center w-full px-4 py-3 text-sm text-gray-700
                             dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
                >
                  <span className="text-gray-500 dark:text-gray-400 mr-3 group-hover:text-emerald-500 transition-colors">
                    {item.icon}
                  </span>
                  <div className="text-left">
                    <p className="font-medium">{item.label}</p>
                    {item.description && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">{item.description}</p>
                    )}
                  </div>
                </button>
              )
            )}

            {/* Shortcut hint */}
            <div className="px-4 py-2 border-t border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Press <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">?</kbd> for shortcuts
              </p>
            </div>
          </div>
        )}

        {/* FAB Button */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`
            w-12 h-12 sm:w-14 sm:h-14 rounded-full shadow-lg
            flex items-center justify-center
            transition-all duration-200 click-feedback
            ${isOpen
              ? 'bg-gray-700 dark:bg-gray-600 text-white rotate-45'
              : 'bg-emerald-600 dark:bg-emerald-500 text-white hover:bg-emerald-700 dark:hover:bg-emerald-600 hover:shadow-xl'
            }
          `}
          aria-label={isOpen ? 'Close help menu' : 'Open help menu'}
          aria-expanded={isOpen}
        >
          {isOpen ? (
            <X className="h-5 w-5 sm:h-6 sm:w-6 -rotate-45" />
          ) : (
            <HelpCircle className="h-5 w-5 sm:h-6 sm:w-6" />
          )}
        </button>
      </div>

      {/* Keyboard Shortcuts Modal */}
      {showShortcuts && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
          onClick={() => setShowShortcuts(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4
                       border border-gray-200 dark:border-gray-700 animate-fade-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <Keyboard className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Keyboard Shortcuts
                </h3>
              </div>
              <button
                onClick={() => setShowShortcuts(false)}
                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200
                           hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="px-5 py-4">
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  Navigation
                </h4>
                <div className="space-y-2">
                  <ShortcutRow keys={['/']} description="Focus on chat input" />
                  <ShortcutRow keys={['?']} description="Show keyboard shortcuts" />
                  <ShortcutRow keys={['Shift', '/']} description="Open documentation" />
                  <ShortcutRow keys={['Esc']} description="Close dialogs and menus" />
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  Actions
                </h4>
                <div className="space-y-2">
                  <ShortcutRow keys={['Ctrl', 'K']} description="Open command palette" />
                  <ShortcutRow keys={['Ctrl', 'Enter']} description="Send message" />
                  <ShortcutRow keys={['Tab']} description="Navigate between elements" />
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-5 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 rounded-b-xl">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Press <kbd className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded text-xs font-mono">Esc</kbd> to close
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Documentation Modal */}
      <DocumentationModal
        isOpen={showDocumentation}
        onClose={() => setShowDocumentation(false)}
      />

      {/* Support Ticket Modal */}
      <SupportTicketModal
        isOpen={showSupport}
        onClose={() => setShowSupport(false)}
      />
    </>
  );
}

// Helper component for keyboard shortcut display
function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-gray-600 dark:text-gray-400">{description}</span>
      <div className="flex items-center space-x-1">
        {keys.map((key, index) => (
          <span key={index} className="flex items-center">
            <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600
                           rounded text-xs font-mono text-gray-700 dark:text-gray-300 min-w-[24px] text-center">
              {key}
            </kbd>
            {index < keys.length - 1 && <span className="text-gray-400 mx-0.5">+</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
