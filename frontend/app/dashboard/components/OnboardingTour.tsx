/**
 * Interactive Onboarding Tour Component
 *
 * Custom-built tour component using Tailwind and React.
 * NO external libraries - uses existing Tailwind/CSS animations.
 *
 * v1.3: Phase 7 - Interactive Onboarding Tour
 * v1.5: Phase 9 - Tour UX Improvements
 *   - Scroll lock during overlay
 *   - Auto-scroll to target element
 *   - Multi-step coach marks with auto-trigger on action
 *   - Event-based tour advancement
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  ChevronRight,
  ChevronLeft,
  Sparkles,
} from 'lucide-react';

interface OnboardingTourProps {
  onComplete?: () => void;
  onSkip?: () => void;
  forceStart?: boolean;
}

interface TourStep {
  target: string;
  title: string;
  description: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  /** Optional action element selector - clicking this auto-advances tour */
  actionTrigger?: string;
  /** Optional event name that triggers auto-advance */
  triggerEvent?: string;
}

// Tour steps configuration
const TOUR_STEPS: TourStep[] = [
  {
    target: '[data-tour="ai-agent-card"]',
    title: 'AI Agent',
    description: 'Start here! Ask questions about your data in natural language. The AI understands your database schema.',
    position: 'right',
    // When user clicks "Open Chat" button, auto-advance tour
    actionTrigger: '[data-tour="ai-agent-card"] a, [data-tour="ai-agent-card"] button',
  },
  {
    target: '[data-tour="kpi-stats"]',
    title: 'Quick Stats',
    description: 'See an overview of your connected tables and tools at a glance. Click any stat for more details.',
    position: 'bottom',
  },
  {
    target: '[data-tour="connected-tools"]',
    title: 'Connected Tools',
    description: 'Extend AI capabilities by connecting Gmail, Slack, Google Drive, and more MCP-compatible tools.',
    position: 'top',
  },
  {
    target: '[data-tour="scheduler-card"]',
    title: 'Scheduler',
    description: 'Automate recurring queries on a schedule. Perfect for daily reports or automated monitoring.',
    position: 'left',
    // When user clicks scheduler action, auto-advance tour
    actionTrigger: '[data-tour="scheduler-card"] a, [data-tour="scheduler-card"] button',
  },
  {
    target: '[data-tour="help-button"]',
    title: 'Need Help?',
    description: 'Find documentation, support, and keyboard shortcuts here anytime you need assistance.',
    position: 'top',
  },
];

// localStorage keys
const STORAGE_KEYS = {
  COMPLETED: 'ims_onboarding_tour_completed',
  SKIPPED: 'ims_onboarding_tour_skipped',
};

export default function OnboardingTour({ onComplete, onSkip, forceStart = false }: OnboardingTourProps) {
  const [isActive, setIsActive] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [showSkipConfirm, setShowSkipConfirm] = useState(false);
  const [mounted, setMounted] = useState(false);
  const tooltipRef = useRef<HTMLDivElement>(null);

  // Check if tour should start
  useEffect(() => {
    setMounted(true);

    if (forceStart) {
      // Forced restart - clear flags and start
      localStorage.removeItem(STORAGE_KEYS.COMPLETED);
      localStorage.removeItem(STORAGE_KEYS.SKIPPED);
      const timer = setTimeout(() => setIsActive(true), 500);
      return () => clearTimeout(timer);
    }

    // Check if already completed or skipped
    const completed = localStorage.getItem(STORAGE_KEYS.COMPLETED);
    const skipped = localStorage.getItem(STORAGE_KEYS.SKIPPED);

    if (!completed && !skipped) {
      // First time user - start tour after delay
      const timer = setTimeout(() => setIsActive(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [forceStart]);

  // v1.5: Smart scroll - scroll target element into view with space for tooltip
  useEffect(() => {
    if (!isActive) return;

    const step = TOUR_STEPS[currentStep];
    const element = document.querySelector(step.target) as HTMLElement;

    if (element) {
      // Get element's absolute position on page
      const rect = element.getBoundingClientRect();
      const viewportHeight = window.innerHeight;
      const tooltipHeight = 220; // Approximate tooltip height including footer
      const padding = 40;

      // Calculate element's absolute position (not relative to viewport)
      const elementAbsoluteTop = rect.top + window.scrollY;

      let targetScrollY = window.scrollY;

      // Calculate scroll position to ensure both element AND tooltip are visible
      switch (step.position) {
        case 'top':
          // Tooltip appears above element - need element lower in viewport
          // Scroll so element is in lower half with space above for tooltip
          targetScrollY = elementAbsoluteTop - tooltipHeight - padding - 80;
          break;
        case 'bottom':
          // Tooltip appears below element - need element higher in viewport
          // Scroll so element is near top with space below for tooltip
          targetScrollY = elementAbsoluteTop - padding - 60;
          break;
        case 'left':
        case 'right':
          // Tooltip appears to side - center element vertically
          // Account for tooltip height when centering
          targetScrollY = elementAbsoluteTop - (viewportHeight / 2) + (rect.height / 2);
          break;
      }

      // Ensure we don't scroll past document boundaries
      targetScrollY = Math.max(0, targetScrollY);
      const maxScroll = document.documentElement.scrollHeight - viewportHeight;
      targetScrollY = Math.min(targetScrollY, maxScroll);

      // Smooth scroll to calculated position
      window.scrollTo({
        top: targetScrollY,
        behavior: 'smooth',
      });

      // Update target rect after scroll animation completes
      const scrollTimeout = setTimeout(() => {
        // Get fresh rect after scroll
        const freshRect = element.getBoundingClientRect();
        setTargetRect(freshRect);
      }, 500);

      return () => clearTimeout(scrollTimeout);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive, currentStep]);

  // Update target rect when step changes
  const updateTargetRect = useCallback(() => {
    if (!isActive) return;

    const step = TOUR_STEPS[currentStep];
    const element = document.querySelector(step.target);

    if (element) {
      const rect = element.getBoundingClientRect();
      setTargetRect(rect);
    }
  }, [isActive, currentStep]);

  useEffect(() => {
    if (!isActive) return;

    // Initial update
    updateTargetRect();

    // Update on scroll/resize with throttle for performance
    let ticking = false;
    const handleUpdate = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          updateTargetRect();
          ticking = false;
        });
        ticking = true;
      }
    };

    window.addEventListener('scroll', handleUpdate, { passive: true });
    window.addEventListener('resize', handleUpdate, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleUpdate);
      window.removeEventListener('resize', handleUpdate);
    };
  }, [updateTargetRect, isActive]);

  // Handle keyboard navigation
  useEffect(() => {
    if (!isActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowSkipConfirm(true);
      } else if (e.key === 'ArrowRight' || e.key === 'Enter') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handleBack();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isActive, currentStep]);

  // v1.5: Action trigger listeners for auto-advance
  useEffect(() => {
    if (!isActive) return;

    const step = TOUR_STEPS[currentStep];
    if (!step.actionTrigger) return;

    const elements = document.querySelectorAll(step.actionTrigger);

    const handleActionClick = () => {
      // Auto-advance to next step after brief delay for visual feedback
      setTimeout(() => {
        if (currentStep < TOUR_STEPS.length - 1) {
          setCurrentStep((prev) => prev + 1);
        } else {
          handleComplete();
        }
      }, 300);
    };

    elements.forEach((el) => {
      el.addEventListener('click', handleActionClick);
    });

    return () => {
      elements.forEach((el) => {
        el.removeEventListener('click', handleActionClick);
      });
    };
  }, [isActive, currentStep]);

  const handleNext = () => {
    if (currentStep < TOUR_STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleComplete();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleComplete = () => {
    localStorage.setItem(STORAGE_KEYS.COMPLETED, 'true');
    setIsActive(false);
    onComplete?.();
  };

  const handleSkip = () => {
    localStorage.setItem(STORAGE_KEYS.SKIPPED, 'true');
    setIsActive(false);
    setShowSkipConfirm(false);
    onSkip?.();
  };

  const handleCancelSkip = () => {
    setShowSkipConfirm(false);
  };

  // Calculate tooltip position
  const getTooltipPosition = useCallback(() => {
    if (!targetRect) return { top: 0, left: 0 };

    const step = TOUR_STEPS[currentStep];
    const padding = 16;
    const tooltipWidth = 320;
    const tooltipHeight = 180;

    let top = 0;
    let left = 0;

    switch (step.position) {
      case 'top':
        top = targetRect.top - tooltipHeight - padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      case 'bottom':
        top = targetRect.bottom + padding;
        left = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
        break;
      case 'left':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.left - tooltipWidth - padding;
        break;
      case 'right':
        top = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
        left = targetRect.right + padding;
        break;
    }

    // Keep within viewport
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    if (left < padding) left = padding;
    if (left + tooltipWidth > viewportWidth - padding) {
      left = viewportWidth - tooltipWidth - padding;
    }
    if (top < padding) top = padding;
    if (top + tooltipHeight > viewportHeight - padding) {
      top = viewportHeight - tooltipHeight - padding;
    }

    return { top, left };
  }, [targetRect, currentStep]);

  // Don't render on server or if not active
  if (!mounted || !isActive) return null;

  const step = TOUR_STEPS[currentStep];
  const tooltipPosition = getTooltipPosition();
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === TOUR_STEPS.length - 1;

  return createPortal(
    <div className="fixed inset-0 z-[100]" role="dialog" aria-modal="true" aria-label="Onboarding tour">
      {/* Overlay with spotlight cutout */}
      <div className="absolute inset-0">
        {/* Semi-transparent backdrop */}
        <div className="absolute inset-0 bg-black/60 transition-opacity duration-300" />

        {/* Spotlight cutout (using box-shadow technique) */}
        {targetRect && (
          <div
            className="absolute transition-all duration-300 ease-out rounded-lg"
            style={{
              top: targetRect.top - 8,
              left: targetRect.left - 8,
              width: targetRect.width + 16,
              height: targetRect.height + 16,
              boxShadow: '0 0 0 9999px rgba(0, 0, 0, 0.6)',
            }}
          >
            {/* Pulsing ring around spotlight */}
            <div
              className="absolute inset-0 rounded-lg ring-2 ring-emerald-400 animate-pulse"
              style={{ animationDuration: '2s' }}
            />
          </div>
        )}
      </div>

      {/* Tooltip */}
      {targetRect && (
        <div
          ref={tooltipRef}
          className="absolute w-80 bg-white dark:bg-gray-800 rounded-xl shadow-2xl
                     border border-gray-200 dark:border-gray-700
                     transition-all duration-300 ease-out animate-fade-in-up"
          style={{
            top: tooltipPosition.top,
            left: tooltipPosition.left,
          }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-5 w-5 text-emerald-500" />
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {step.title}
              </h3>
            </div>
            <button
              onClick={() => setShowSkipConfirm(true)}
              className="p-1 rounded-lg text-gray-400 hover:text-gray-600
                         dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700
                         transition-colors"
              aria-label="Skip tour"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Content */}
          <div className="px-5 py-4">
            <p className="text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
              {step.description}
            </p>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-5 py-4 bg-gray-50 dark:bg-gray-900/50 rounded-b-xl">
            {/* Progress */}
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {currentStep + 1} of {TOUR_STEPS.length}
            </span>

            {/* Navigation */}
            <div className="flex items-center space-x-2">
              {!isFirstStep && (
                <button
                  onClick={handleBack}
                  className="flex items-center px-3 py-1.5 text-sm font-medium
                             text-gray-600 dark:text-gray-300
                             hover:text-gray-900 dark:hover:text-white
                             transition-colors"
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Back
                </button>
              )}

              <button
                onClick={isLastStep ? handleComplete : handleNext}
                className="flex items-center px-4 py-2 text-sm font-medium
                           bg-emerald-600 text-white rounded-lg
                           hover:bg-emerald-700 transition-colors
                           click-feedback"
              >
                {isLastStep ? (
                  <>
                    Finish
                    <Sparkles className="h-4 w-4 ml-1.5" />
                  </>
                ) : (
                  <>
                    Next
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Progress dots */}
          <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 flex space-x-1.5">
            {TOUR_STEPS.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-colors duration-200
                  ${index === currentStep
                    ? 'bg-emerald-500'
                    : index < currentStep
                    ? 'bg-emerald-300'
                    : 'bg-gray-300 dark:bg-gray-600'
                  }`}
              />
            ))}
          </div>
        </div>
      )}

      {/* Skip Confirmation Dialog */}
      {showSkipConfirm && (
        <div className="fixed inset-0 z-[101] flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={handleCancelSkip}
          />
          <div className="relative bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-sm w-full animate-fade-in-up">
            <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Skip the tour?
            </h4>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              You can always replay the tour from the Help menu if you change your mind.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleCancelSkip}
                className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300
                           hover:text-gray-900 dark:hover:text-white transition-colors"
              >
                Continue Tour
              </button>
              <button
                onClick={handleSkip}
                className="px-4 py-2 text-sm font-medium bg-gray-100 dark:bg-gray-700
                           text-gray-700 dark:text-gray-200 rounded-lg
                           hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
              >
                Skip for now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>,
    document.body
  );
}

// Export a function to trigger tour restart (for help menu)
export function restartOnboardingTour() {
  localStorage.removeItem(STORAGE_KEYS.COMPLETED);
  localStorage.removeItem(STORAGE_KEYS.SKIPPED);
  // Dispatch custom event that the component can listen to
  window.dispatchEvent(new CustomEvent('restart-onboarding-tour'));
}
