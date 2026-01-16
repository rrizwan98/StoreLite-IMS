/**
 * Documentation Modal Component
 *
 * A comprehensive in-app documentation system with:
 * - Sidebar navigation with sections
 * - Screenshot placeholders for visual guides
 * - Search functionality
 * - Dark mode support
 * - Responsive design
 *
 * v1.0: Initial implementation
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import {
  X,
  Search,
  ChevronRight,
  Home,
  LayoutDashboard,
  Bot,
  Database,
  Calendar,
  Plug,
  Settings,
  Keyboard,
  HelpCircle,
  ExternalLink,
  Image as ImageIcon,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Shield,
  Clock,
  Mail,
  FileText,
  Zap,
} from 'lucide-react';

interface DocumentationSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  subsections: {
    id: string;
    title: string;
    content: React.ReactNode;
  }[];
}

interface DocumentationModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialSection?: string;
}

export default function DocumentationModal({
  isOpen,
  onClose,
  initialSection = 'getting-started',
}: DocumentationModalProps) {
  const [activeSection, setActiveSection] = useState(initialSection);
  const [activeSubsection, setActiveSubsection] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  // Scroll to section when changed
  useEffect(() => {
    if (activeSubsection && contentRef.current) {
      const element = contentRef.current.querySelector(`#${activeSubsection}`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  }, [activeSubsection]);

  if (!isOpen) return null;

  const sections: DocumentationSection[] = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: <Home className="h-4 w-4" />,
      subsections: [
        {
          id: 'welcome',
          title: 'Welcome to StoreLite IMS',
          content: <WelcomeSection />,
        },
        {
          id: 'quick-start',
          title: 'Quick Start Guide',
          content: <QuickStartSection />,
        },
        {
          id: 'system-requirements',
          title: 'System Requirements',
          content: <SystemRequirementsSection />,
        },
      ],
    },
    {
      id: 'dashboard',
      title: 'Dashboard',
      icon: <LayoutDashboard className="h-4 w-4" />,
      subsections: [
        {
          id: 'dashboard-overview',
          title: 'Overview',
          content: <DashboardOverviewSection />,
        },
        {
          id: 'kpi-stats',
          title: 'KPI Stats',
          content: <KPIStatsSection />,
        },
        {
          id: 'onboarding-checklist',
          title: 'Onboarding Checklist',
          content: <OnboardingChecklistSection />,
        },
      ],
    },
    {
      id: 'ai-agent',
      title: 'AI Agent',
      icon: <Bot className="h-4 w-4" />,
      subsections: [
        {
          id: 'how-to-ask',
          title: 'How to Ask Questions',
          content: <HowToAskSection />,
        },
        {
          id: 'example-queries',
          title: 'Example Queries',
          content: <ExampleQueriesSection />,
        },
        {
          id: 'understanding-results',
          title: 'Understanding Results',
          content: <UnderstandingResultsSection />,
        },
      ],
    },
    {
      id: 'database',
      title: 'Database Connection',
      icon: <Database className="h-4 w-4" />,
      subsections: [
        {
          id: 'schema-query-mode',
          title: 'Schema-Query-Only Mode',
          content: <SchemaQueryModeSection />,
        },
        {
          id: 'connecting-db',
          title: 'Connecting Your Database',
          content: <ConnectingDBSection />,
        },
      ],
    },
    {
      id: 'scheduler',
      title: 'Scheduler',
      icon: <Calendar className="h-4 w-4" />,
      subsections: [
        {
          id: 'creating-tasks',
          title: 'Creating Tasks',
          content: <CreatingTasksSection />,
        },
        {
          id: 'recurring-schedules',
          title: 'Recurring Schedules',
          content: <RecurringSchedulesSection />,
        },
      ],
    },
    {
      id: 'tools',
      title: 'Connected Tools',
      icon: <Plug className="h-4 w-4" />,
      subsections: [
        {
          id: 'available-integrations',
          title: 'Available Integrations',
          content: <AvailableIntegrationsSection />,
        },
        {
          id: 'connecting-gmail',
          title: 'Connecting Gmail',
          content: <ConnectingGmailSection />,
        },
        {
          id: 'connecting-notion',
          title: 'Connecting Notion',
          content: <ConnectingNotionSection />,
        },
      ],
    },
    {
      id: 'settings',
      title: 'Settings',
      icon: <Settings className="h-4 w-4" />,
      subsections: [
        {
          id: 'user-preferences',
          title: 'User Preferences',
          content: <UserPreferencesSection />,
        },
        {
          id: 'theme-settings',
          title: 'Theme Settings',
          content: <ThemeSettingsSection />,
        },
      ],
    },
    {
      id: 'keyboard-shortcuts',
      title: 'Keyboard Shortcuts',
      icon: <Keyboard className="h-4 w-4" />,
      subsections: [
        {
          id: 'navigation-shortcuts',
          title: 'Navigation',
          content: <NavigationShortcutsSection />,
        },
        {
          id: 'action-shortcuts',
          title: 'Actions',
          content: <ActionShortcutsSection />,
        },
      ],
    },
    {
      id: 'faq',
      title: 'FAQ',
      icon: <HelpCircle className="h-4 w-4" />,
      subsections: [
        {
          id: 'common-questions',
          title: 'Common Questions',
          content: <CommonQuestionsSection />,
        },
        {
          id: 'troubleshooting',
          title: 'Troubleshooting',
          content: <TroubleshootingSection />,
        },
      ],
    },
  ];

  const currentSection = sections.find((s) => s.id === activeSection);

  // Filter sections based on search
  const filteredSections = searchQuery
    ? sections.filter(
        (section) =>
          section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          section.subsections.some((sub) =>
            sub.title.toLowerCase().includes(searchQuery.toLowerCase())
          )
      )
    : sections;

  return (
    <div
      className="fixed inset-0 z-[100] flex bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="flex w-full h-full bg-white dark:bg-gray-900 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sidebar */}
        <aside
          className={`
            ${isSidebarOpen ? 'w-72' : 'w-0'}
            flex-shrink-0 border-r border-gray-200 dark:border-gray-700
            bg-gray-50 dark:bg-gray-800/50 transition-all duration-300 overflow-hidden
            lg:w-72
          `}
        >
          <div className="h-full flex flex-col">
            {/* Sidebar Header */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-emerald-600" />
                  <h2 className="font-semibold text-gray-900 dark:text-white">
                    Documentation
                  </h2>
                </div>
              </div>

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search docs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-sm bg-white dark:bg-gray-800
                           border border-gray-200 dark:border-gray-600 rounded-lg
                           text-gray-900 dark:text-white placeholder-gray-400
                           focus:ring-2 focus:ring-emerald-500 focus:border-transparent outline-none"
                />
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto p-3">
              {filteredSections.map((section) => (
                <div key={section.id} className="mb-1">
                  <button
                    onClick={() => {
                      setActiveSection(section.id);
                      setActiveSubsection(section.subsections[0]?.id || '');
                    }}
                    className={`
                      w-full flex items-center gap-2 px-3 py-2 text-sm rounded-lg
                      transition-colors text-left
                      ${
                        activeSection === section.id
                          ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 font-medium'
                          : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                  >
                    {section.icon}
                    {section.title}
                    <ChevronRight
                      className={`h-4 w-4 ml-auto transition-transform ${
                        activeSection === section.id ? 'rotate-90' : ''
                      }`}
                    />
                  </button>

                  {/* Subsections */}
                  {activeSection === section.id && (
                    <div className="ml-6 mt-1 space-y-0.5">
                      {section.subsections.map((sub) => (
                        <button
                          key={sub.id}
                          onClick={() => setActiveSubsection(sub.id)}
                          className={`
                            w-full text-left px-3 py-1.5 text-sm rounded-md transition-colors
                            ${
                              activeSubsection === sub.id
                                ? 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20'
                                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                            }
                          `}
                        >
                          {sub.title}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>

            {/* Sidebar Footer */}
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                StoreLite IMS v3.0.0
              </p>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
            <div className="flex items-center gap-3">
              {/* Mobile sidebar toggle */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="lg:hidden p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ChevronRight
                  className={`h-5 w-5 transition-transform ${isSidebarOpen ? 'rotate-180' : ''}`}
                />
              </button>

              <div>
                <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {currentSection?.title || 'Documentation'}
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Learn how to use StoreLite IMS
                </p>
              </div>
            </div>

            <button
              onClick={onClose}
              className="p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200
                       hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              aria-label="Close documentation"
            >
              <X className="h-5 w-5" />
            </button>
          </header>

          {/* Content */}
          <div ref={contentRef} className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto px-6 py-8">
              {currentSection?.subsections.map((sub) => (
                <section
                  key={sub.id}
                  id={sub.id}
                  className="mb-12 scroll-mt-8"
                >
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
                    {sub.title}
                  </h2>
                  {sub.content}
                </section>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

// ============================================
// Documentation Section Components
// ============================================

function ScreenshotPlaceholder({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="my-6 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 p-8">
      <div className="flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center mb-4">
          <ImageIcon className="h-8 w-8 text-gray-400 dark:text-gray-500" />
        </div>
        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
          {title}
        </p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

function InfoBox({
  type = 'info',
  title,
  children,
}: {
  type?: 'info' | 'tip' | 'warning';
  title: string;
  children: React.ReactNode;
}) {
  const styles = {
    info: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-800 dark:text-blue-300',
    tip: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300',
    warning:
      'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300',
  };

  const icons = {
    info: <HelpCircle className="h-5 w-5" />,
    tip: <Zap className="h-5 w-5" />,
    warning: <Shield className="h-5 w-5" />,
  };

  return (
    <div className={`my-4 p-4 rounded-lg border ${styles[type]}`}>
      <div className="flex items-start gap-3">
        {icons[type]}
        <div>
          <p className="font-medium mb-1">{title}</p>
          <div className="text-sm opacity-90">{children}</div>
        </div>
      </div>
    </div>
  );
}

function StepList({ steps }: { steps: string[] }) {
  return (
    <ol className="space-y-3 my-4">
      {steps.map((step, index) => (
        <li key={index} className="flex items-start gap-3">
          <span className="flex-shrink-0 w-6 h-6 rounded-full bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 text-sm font-medium flex items-center justify-center">
            {index + 1}
          </span>
          <span className="text-gray-600 dark:text-gray-300">{step}</span>
        </li>
      ))}
    </ol>
  );
}

function ShortcutKey({ keys }: { keys: string[] }) {
  return (
    <span className="inline-flex items-center gap-1">
      {keys.map((key, index) => (
        <span key={index}>
          <kbd className="px-2 py-1 text-xs font-mono bg-gray-100 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300">
            {key}
          </kbd>
          {index < keys.length - 1 && (
            <span className="text-gray-400 mx-0.5">+</span>
          )}
        </span>
      ))}
    </span>
  );
}

// ============================================
// Individual Sections
// ============================================

function WelcomeSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-lg text-gray-600 dark:text-gray-300 leading-relaxed">
        Welcome to <strong>StoreLite IMS</strong> - your AI-powered inventory
        management system. This documentation will help you get the most out of
        our platform.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        <div className="p-4 rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800">
          <Sparkles className="h-8 w-8 text-emerald-600 dark:text-emerald-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            AI-Powered Queries
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Ask questions about your data in natural language
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800">
          <Shield className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Read-Only Security
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Your data is safe - we only read, never modify
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
          <Clock className="h-8 w-8 text-purple-600 dark:text-purple-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Scheduled Tasks
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Automate recurring queries on your schedule
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border border-orange-200 dark:border-orange-800">
          <Plug className="h-8 w-8 text-orange-600 dark:text-orange-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Tool Integrations
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Connect Gmail, Notion, Google Drive and more
          </p>
        </div>
      </div>

      <ScreenshotPlaceholder
        title="Dashboard Overview Screenshot"
        description="Shows the main dashboard with all key features"
      />
    </div>
  );
}

function QuickStartSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Get up and running with StoreLite IMS in just a few minutes.
      </p>

      <StepList
        steps={[
          'Sign up or log in to your account',
          'Connect your database from the Schema Connect page',
          'Wait for schema discovery to complete',
          'Start asking questions to the AI Agent',
          'Optionally connect additional tools like Gmail',
        ]}
      />

      <InfoBox type="tip" title="Pro Tip">
        Use the onboarding checklist on your dashboard to track your progress
        and ensure you have set up all features.
      </InfoBox>

      <ScreenshotPlaceholder
        title="Onboarding Checklist Screenshot"
        description="Shows the step-by-step onboarding process"
      />
    </div>
  );
}

function SystemRequirementsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        StoreLite IMS works on all modern browsers and devices.
      </p>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Supported Browsers
      </h3>
      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Google Chrome (latest 2 versions)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Mozilla Firefox (latest 2 versions)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Microsoft Edge (latest 2 versions)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Safari (latest 2 versions)
        </li>
      </ul>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Database Support
      </h3>
      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          PostgreSQL 12+
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          MySQL 8.0+
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          SQLite 3.x
        </li>
      </ul>
    </div>
  );
}

function DashboardOverviewSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The dashboard is your central hub for managing your inventory data and
        accessing all features.
      </p>

      <ScreenshotPlaceholder
        title="Full Dashboard Screenshot"
        description="Annotated view of all dashboard components"
      />

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Dashboard Components
      </h3>

      <div className="space-y-4">
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            AI Agent Card
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Your primary interface for asking questions about your data. Click
            &quot;Open Chat&quot; to start querying.
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            KPI Stats Row
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Quick overview of your connected tables and tools at a glance.
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Connected Tools
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            View and manage your external integrations like Gmail, Notion, and
            Google Drive.
          </p>
        </div>
      </div>
    </div>
  );
}

function KPIStatsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The KPI Stats row provides a quick summary of your data at a glance.
      </p>

      <ScreenshotPlaceholder
        title="KPI Stats Row Screenshot"
        description="Shows the metrics displayed in the stats row"
      />

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Available Metrics
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>
          <strong>Tables Discovered:</strong> Number of database tables
          connected
        </li>
        <li>
          <strong>Tools Connected:</strong> Number of external integrations
          active
        </li>
        <li>
          <strong>Schema Status:</strong> Current state of your database
          connection
        </li>
      </ul>

      <InfoBox type="info" title="Click to Navigate">
        Click on any stat card to navigate directly to its detail page.
      </InfoBox>
    </div>
  );
}

function OnboardingChecklistSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The onboarding checklist guides you through setting up all features of
        StoreLite IMS.
      </p>

      <ScreenshotPlaceholder
        title="Onboarding Checklist Screenshot"
        description="Shows the checklist with progress tracking"
      />

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Checklist Steps
      </h3>

      <StepList
        steps={[
          'Connect your database - Establish a secure connection',
          'Ask your first AI question - Try the natural language interface',
          'Connect a tool - Add Gmail, Notion, or other integrations',
          'Create a scheduled task - Automate recurring queries',
        ]}
      />

      <InfoBox type="tip" title="Auto-Collapse">
        The checklist automatically collapses once you complete all steps to
        reduce visual clutter.
      </InfoBox>
    </div>
  );
}

function HowToAskSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The AI Agent understands natural language queries about your data. Just
        type your question as you would ask a colleague.
      </p>

      <ScreenshotPlaceholder
        title="AI Agent Chat Interface"
        description="Shows the chat input and response area"
      />

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Tips for Better Results
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>Be specific about what data you want</li>
        <li>Mention table names when relevant</li>
        <li>Specify time ranges for date-based queries</li>
        <li>Ask for summaries, counts, or specific records</li>
      </ul>

      <InfoBox type="warning" title="Read-Only Mode">
        All queries are read-only (SELECT only). The AI cannot modify, delete,
        or insert data into your database.
      </InfoBox>
    </div>
  );
}

function ExampleQueriesSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Here are some example queries to help you get started.
      </p>

      <div className="space-y-4 my-6">
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Show me the top 10 products by sales&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;What items are low in stock?&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;List all customers who ordered last month&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;What is the total revenue this week?&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Show me inventory for the Grocery category&quot;
          </p>
        </div>
      </div>
    </div>
  );
}

function UnderstandingResultsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The AI Agent returns results in a clear, readable format with supporting
        context.
      </p>

      <ScreenshotPlaceholder
        title="Query Results Screenshot"
        description="Shows how results are displayed"
      />

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Result Components
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>
          <strong>Summary:</strong> Natural language explanation of the results
        </li>
        <li>
          <strong>Data Table:</strong> Tabular view of query results (when
          applicable)
        </li>
        <li>
          <strong>SQL Query:</strong> The actual SQL executed (expandable)
        </li>
        <li>
          <strong>Row Count:</strong> Number of records returned
        </li>
      </ul>
    </div>
  );
}

function SchemaQueryModeSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Schema-Query-Only mode allows you to connect your database for read-only
        AI queries without any write operations.
      </p>

      <InfoBox type="warning" title="Security First">
        In this mode, StoreLite IMS can only execute SELECT queries. INSERT,
        UPDATE, DELETE, and DDL operations are blocked at the database level.
      </InfoBox>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        How It Works
      </h3>

      <StepList
        steps={[
          'You provide your database connection string',
          'We create a read-only connection',
          'Schema discovery runs to understand your tables',
          'AI can then query your data safely',
        ]}
      />

      <ScreenshotPlaceholder
        title="Schema Discovery Process"
        description="Shows the schema connection flow"
      />
    </div>
  );
}

function ConnectingDBSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Follow these steps to connect your database to StoreLite IMS.
      </p>

      <StepList
        steps={[
          'Navigate to Schema Connect from your dashboard',
          'Select your database type (PostgreSQL, MySQL, SQLite)',
          'Enter your connection string or individual credentials',
          'Click "Test Connection" to verify',
          'Click "Connect" to start schema discovery',
          'Wait for the discovery process to complete',
        ]}
      />

      <InfoBox type="tip" title="Connection String Format">
        PostgreSQL: postgresql://user:password@host:port/database
        <br />
        MySQL: mysql://user:password@host:port/database
      </InfoBox>

      <ScreenshotPlaceholder
        title="Database Connection Form"
        description="Shows the connection configuration interface"
      />
    </div>
  );
}

function CreatingTasksSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        The Scheduler allows you to create automated tasks that run on a
        schedule.
      </p>

      <ScreenshotPlaceholder
        title="Create Task Interface"
        description="Shows the task creation form"
      />

      <StepList
        steps={[
          'Navigate to Scheduler from the dashboard',
          'Click "Create Task" button',
          'Enter a name and description for your task',
          'Write the query or instruction for the AI',
          'Set the schedule (one-time or recurring)',
          'Configure email notifications if needed',
          'Click "Create" to save the task',
        ]}
      />

      <InfoBox type="info" title="Email Results">
        Enable email delivery to receive task results directly in your inbox
        when scheduled queries complete.
      </InfoBox>
    </div>
  );
}

function RecurringSchedulesSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Set up recurring schedules for tasks that need to run regularly.
      </p>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Schedule Options
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>
          <strong>Hourly:</strong> Run every hour at a specific minute
        </li>
        <li>
          <strong>Daily:</strong> Run every day at a specific time
        </li>
        <li>
          <strong>Weekly:</strong> Run on specific days of the week
        </li>
        <li>
          <strong>Monthly:</strong> Run on specific days of the month
        </li>
        <li>
          <strong>Custom:</strong> Use cron expressions for complex schedules
        </li>
      </ul>

      <ScreenshotPlaceholder
        title="Schedule Configuration"
        description="Shows the recurring schedule options"
      />
    </div>
  );
}

function AvailableIntegrationsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Extend your AI agent&apos;s capabilities by connecting external tools
        and services.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Mail className="h-6 w-6 text-red-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">Gmail</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Search emails, send messages, manage drafts
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <FileText className="h-6 w-6 text-gray-700 dark:text-gray-300 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">Notion</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Access pages, databases, and documents
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Database className="h-6 w-6 text-blue-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">
            Google Drive
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Search and access files from your Drive
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Zap className="h-6 w-6 text-amber-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">
            More Coming
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Slack, Airtable, and more integrations planned
          </p>
        </div>
      </div>
    </div>
  );
}

function ConnectingGmailSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Connect your Gmail account to enable email-related AI capabilities.
      </p>

      <StepList
        steps={[
          'Go to Settings > Connected Tools',
          'Find Gmail in the available integrations',
          'Click "Connect" to start OAuth flow',
          'Sign in with your Google account',
          'Grant the requested permissions',
          'You\'re connected! The AI can now access your emails',
        ]}
      />

      <InfoBox type="info" title="Permissions">
        We only request read access to your emails. We cannot send emails on
        your behalf without explicit action.
      </InfoBox>

      <ScreenshotPlaceholder
        title="Gmail OAuth Flow"
        description="Shows the Google sign-in process"
      />
    </div>
  );
}

function ConnectingNotionSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Connect your Notion workspace to access pages and databases.
      </p>

      <StepList
        steps={[
          'Go to Settings > Connected Tools',
          'Find Notion in the available integrations',
          'Click "Connect" to start OAuth flow',
          'Authorize StoreLite IMS in Notion',
          'Select which pages/databases to share',
          'Complete the connection',
        ]}
      />

      <ScreenshotPlaceholder
        title="Notion Connection"
        description="Shows the Notion authorization process"
      />
    </div>
  );
}

function UserPreferencesSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Customize your StoreLite IMS experience with user preferences.
      </p>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Available Settings
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>
          <strong>File Retention:</strong> How long uploaded files are kept
        </li>
        <li>
          <strong>Default Email:</strong> Pre-filled email for notifications
        </li>
        <li>
          <strong>Dashboard Widgets:</strong> Show/hide and reorder widgets
        </li>
        <li>
          <strong>Notification Preferences:</strong> Email notification settings
        </li>
      </ul>

      <ScreenshotPlaceholder
        title="Settings Page"
        description="Shows the user preferences interface"
      />
    </div>
  );
}

function ThemeSettingsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        StoreLite IMS supports light and dark themes.
      </p>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        Theme Options
      </h3>

      <ul className="space-y-2 text-gray-600 dark:text-gray-300">
        <li>
          <strong>Light:</strong> Clean, bright interface
        </li>
        <li>
          <strong>Dark:</strong> Easy on the eyes in low light
        </li>
        <li>
          <strong>System:</strong> Automatically match your OS preference
        </li>
      </ul>

      <InfoBox type="tip" title="Quick Toggle">
        Use the theme toggle in the header to quickly switch between light and
        dark modes.
      </InfoBox>
    </div>
  );
}

function NavigationShortcutsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Use these keyboard shortcuts to navigate quickly through the
        application.
      </p>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Open documentation
          </span>
          <ShortcutKey keys={['Shift', '/']} />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Show keyboard shortcuts
          </span>
          <ShortcutKey keys={['?']} />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Open command palette
          </span>
          <ShortcutKey keys={['Ctrl', 'K']} />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Close modal/dialog
          </span>
          <ShortcutKey keys={['Esc']} />
        </div>
      </div>
    </div>
  );
}

function ActionShortcutsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300 mb-6">
        Action shortcuts for common tasks.
      </p>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Focus chat input
          </span>
          <ShortcutKey keys={['/']} />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">Send message</span>
          <ShortcutKey keys={['Ctrl', 'Enter']} />
        </div>

        <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <span className="text-gray-700 dark:text-gray-300">
            Navigate between elements
          </span>
          <ShortcutKey keys={['Tab']} />
        </div>
      </div>
    </div>
  );
}

function CommonQuestionsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Is my data secure?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Yes. We use read-only connections and never store your actual data.
            All queries are executed directly against your database through a
            secure connection.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Can the AI modify my data?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            No. The AI can only execute SELECT queries. INSERT, UPDATE, DELETE,
            and DDL operations are blocked at the database level.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            What databases are supported?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Currently we support PostgreSQL, MySQL, and SQLite. More database
            types are planned.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            How do scheduled tasks work?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Scheduled tasks run your queries automatically at specified times.
            Results can be sent to your email or viewed in the task history.
          </p>
        </div>
      </div>
    </div>
  );
}

function TroubleshootingSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Connection timeout errors
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Check that your database is accessible from the internet and that
            your firewall allows connections. Verify your connection string is
            correct.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Schema discovery not completing
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            For large databases, schema discovery may take a few minutes. If it
            fails, try reconnecting or check your database permissions.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            AI not understanding my queries
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Try being more specific with table names and column names. You can
            also refer to the schema view to see exact names.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Gmail connection issues
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Try disconnecting and reconnecting your Gmail account. Ensure
            you&apos;re granting all requested permissions during OAuth.
          </p>
        </div>
      </div>

      <InfoBox type="info" title="Need More Help?">
        Can&apos;t find what you&apos;re looking for? Use the Contact Support
        option in the help menu to submit a ticket.
      </InfoBox>
    </div>
  );
}
