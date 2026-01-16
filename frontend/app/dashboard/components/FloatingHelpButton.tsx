/**
 * Floating Help Button Component
 *
 * A floating action button (FAB) in the bottom-right corner
 * that provides quick access to help resources.
 *
 * v1.1: New component for quick help access
 * v1.3: Added Replay Tour option
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import { HelpCircle, ExternalLink, Mail, Keyboard, X, Play } from 'lucide-react';
import { restartOnboardingTour } from './OnboardingTour';

interface HelpMenuItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
}

export default function FloatingHelpButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
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

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        setShowShortcuts(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);

  // Handle replay tour
  const handleReplayTour = () => {
    restartOnboardingTour();
    setIsOpen(false);
    // Small delay to allow menu to close, then force page reload to restart tour
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };

  const menuItems: HelpMenuItem[] = [
    {
      id: 'tour',
      label: 'Replay Tour',
      icon: <Play className="h-4 w-4" />,
      onClick: handleReplayTour,
    },
    {
      id: 'docs',
      label: 'Documentation',
      icon: <ExternalLink className="h-4 w-4" />,
      href: 'https://github.com/your-repo/docs',
    },
    {
      id: 'support',
      label: 'Contact Support',
      icon: <Mail className="h-4 w-4" />,
      href: 'mailto:support@example.com',
    },
    {
      id: 'shortcuts',
      label: 'Keyboard Shortcuts',
      icon: <Keyboard className="h-4 w-4" />,
      onClick: () => setShowShortcuts(true),
    },
  ];

  return (
    <>
      {/* Floating Button and Menu */}
      <div ref={menuRef} className="fixed bottom-6 right-6 z-50">
        {/* Dropdown Menu */}
        {isOpen && (
          <div
            className="absolute bottom-14 right-0 w-52 bg-white dark:bg-gray-800
                       rounded-xl shadow-xl border border-gray-200 dark:border-gray-700
                       py-2 animate-fade-in-up overflow-hidden"
          >
            <div className="px-3 py-2 border-b border-gray-100 dark:border-gray-700">
              <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
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
                  className="flex items-center px-4 py-2.5 text-sm text-gray-700 dark:text-gray-200
                             hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  <span className="text-gray-500 dark:text-gray-400 mr-3">{item.icon}</span>
                  {item.label}
                </a>
              ) : (
                <button
                  key={item.id}
                  onClick={() => {
                    item.onClick?.();
                    setIsOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-2.5 text-sm text-gray-700
                             dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <span className="text-gray-500 dark:text-gray-400 mr-3">{item.icon}</span>
                  {item.label}
                </button>
              )
            )}
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
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={() => setShowShortcuts(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md mx-4
                       border border-gray-200 dark:border-gray-700 animate-fade-in-up"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Keyboard Shortcuts
              </h3>
              <button
                onClick={() => setShowShortcuts(false)}
                className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200
                           hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="px-5 py-4 space-y-3">
              <ShortcutRow keys={['/']} description="Focus on chat input" />
              <ShortcutRow keys={['Esc']} description="Close dialogs and menus" />
              <ShortcutRow keys={['Ctrl', 'K']} description="Open command palette" />
              <ShortcutRow keys={['Ctrl', 'Enter']} description="Send message" />
              <ShortcutRow keys={['Tab']} description="Navigate between elements" />
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
    </>
  );
}

// Helper component for keyboard shortcut display
function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600 dark:text-gray-400">{description}</span>
      <div className="flex items-center space-x-1">
        {keys.map((key, index) => (
          <span key={index}>
            <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600
                           rounded text-xs font-mono text-gray-700 dark:text-gray-300">
              {key}
            </kbd>
            {index < keys.length - 1 && <span className="text-gray-400 mx-0.5">+</span>}
          </span>
        ))}
      </div>
    </div>
  );
}
