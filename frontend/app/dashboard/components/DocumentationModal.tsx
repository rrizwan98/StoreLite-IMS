/**
 * Documentation Modal Component
 *
 * A comprehensive in-app documentation system with:
 * - Sidebar navigation with sections
 * - Animated illustrations for visual guides
 * - Search functionality
 * - Dark mode support
 * - Responsive design
 *
 * v1.0: Initial implementation
 * v2.0: Replaced static placeholders with animated illustrations
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

// Import animated illustrations
import {
  DashboardDemo,
  AIAgentDemo,
  SchedulerDemo,
  ConnectedToolsDemo,
  KeyboardShortcutsDemo,
  GettingStartedDemo,
  DatabaseConnectionDemo,
  SettingsDemo,
} from './DocAnimations';

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
      id: 'developer-tools',
      title: 'For Developers',
      icon: <ExternalLink className="h-4 w-4" />,
      subsections: [
        {
          id: 'published-agents',
          title: 'Published Agents',
          content: <PublishedAgentsSection />,
        },
        {
          id: 'api-integration',
          title: 'API Integration',
          content: <APIIntegrationSection />,
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
        Welcome to <strong>StoreLite IMS</strong> - Your personal AI-powered inventory
        assistant that automates your business operations, saving you hours of manual work every day.
      </p>

      <InfoBox type="tip" title="No Personal AI Agent Needed">
        You don&apos;t need to build your own AI solution. IMS provides a pre-configured,
        business-ready assistant that works immediately — no coding, no complex setup.
      </InfoBox>

      {/* Time Savings Highlight */}
      <div className="my-6 p-4 bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-xl border border-emerald-200 dark:border-emerald-800">
        <h3 className="text-lg font-bold text-emerald-700 dark:text-emerald-400 mb-3">
          Estimated Daily Time Saved: 2-4 Hours
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
          <div className="text-center p-2 bg-white/50 dark:bg-gray-800/50 rounded-lg">
            <div className="text-2xl font-bold text-emerald-600">25 min</div>
            <div className="text-gray-600 dark:text-gray-400">Adding Items</div>
          </div>
          <div className="text-center p-2 bg-white/50 dark:bg-gray-800/50 rounded-lg">
            <div className="text-2xl font-bold text-emerald-600">14 min</div>
            <div className="text-gray-600 dark:text-gray-400">Reports</div>
          </div>
          <div className="text-center p-2 bg-white/50 dark:bg-gray-800/50 rounded-lg">
            <div className="text-2xl font-bold text-emerald-600">20 min</div>
            <div className="text-gray-600 dark:text-gray-400">Alerts</div>
          </div>
          <div className="text-center p-2 bg-white/50 dark:bg-gray-800/50 rounded-lg">
            <div className="text-2xl font-bold text-emerald-600">8 min</div>
            <div className="text-gray-600 dark:text-gray-400">Invoicing</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        <div className="p-4 rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 border border-emerald-200 dark:border-emerald-800">
          <Sparkles className="h-8 w-8 text-emerald-600 dark:text-emerald-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Natural Language Commands
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Just say &quot;Add 50 kg rice at Rs. 120&quot; — done!
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800">
          <Shield className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Secure & Private
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Your data stays yours. User isolation & encryption.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 border border-purple-200 dark:border-purple-800">
          <Clock className="h-8 w-8 text-purple-600 dark:text-purple-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Set It & Forget It
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Schedule automated reports, alerts & emails.
          </p>
        </div>

        <div className="p-4 rounded-lg bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/20 dark:to-amber-900/20 border border-orange-200 dark:border-orange-800">
          <Plug className="h-8 w-8 text-orange-600 dark:text-orange-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
            Connect Everything
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Gmail, Drive, Notion + custom MCP servers.
          </p>
        </div>
      </div>

      <div className="my-6">
        <GettingStartedDemo />
      </div>
    </div>
  );
}

function QuickStartSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Get up and running in under 5 minutes!
      </p>

      <StepList
        steps={[
          'Sign up or log in to your account',
          'Choose your connection type (Our Database / Your Database)',
          'Start talking to the AI — try "Show my inventory"',
          'Connect Gmail for automated emails (optional)',
          'Schedule your first automated task (optional)',
        ]}
      />

      {/* Try These First */}
      <div className="my-4 p-4 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg border border-emerald-200 dark:border-emerald-700">
        <h4 className="font-semibold text-emerald-700 dark:text-emerald-400 mb-2">Try These Commands First</h4>
        <div className="space-y-1 text-sm font-mono">
          <p className="text-gray-600 dark:text-gray-400">&quot;Show me my inventory overview&quot;</p>
          <p className="text-gray-600 dark:text-gray-400">&quot;Add a test item: Sample Product, Rs. 100, 10 pcs&quot;</p>
          <p className="text-gray-600 dark:text-gray-400">&quot;What&apos;s my best selling item?&quot;</p>
        </div>
      </div>

      <InfoBox type="tip" title="No Setup for Basic Use">
        Choose &quot;Use Our Database&quot; to start immediately — no database setup needed.
        You can connect your own database later!
      </InfoBox>

      <div className="my-6">
        <DashboardDemo />
      </div>
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

      <div className="my-6">
        <DashboardDemo />
      </div>

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

      <div className="my-6">
        <DashboardDemo />
      </div>

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

      <div className="my-6">
        <GettingStartedDemo />
      </div>

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
        The AI Agent understands natural language — just talk to it like you would to a colleague.
        No special syntax needed!
      </p>

      {/* Time Savings */}
      <div className="my-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-700">
        <h4 className="font-semibold text-blue-700 dark:text-blue-400 mb-2">Time Comparison</h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Manual (20 items):</span>
            <span className="font-bold text-red-600 ml-2">30 min</span>
          </div>
          <div>
            <span className="text-gray-500">With AI Agent:</span>
            <span className="font-bold text-emerald-600 ml-2">5 min</span>
          </div>
        </div>
      </div>

      <div className="my-6">
        <AIAgentDemo />
      </div>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mt-6 mb-3">
        What You Can Do
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-4">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <strong className="text-emerald-600">Inventory:</strong>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Add 50 shirts at Rs. 350&quot;</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <strong className="text-emerald-600">Billing:</strong>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Create bill for Ahmed&quot;</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <strong className="text-emerald-600">Reports:</strong>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Show last week&apos;s sales&quot;</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <strong className="text-emerald-600">Alerts:</strong>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Low stock items?&quot;</span>
        </div>
      </div>

      <InfoBox type="tip" title="Context Awareness">
        The AI remembers your conversation! Say &quot;same for last month&quot; or
        &quot;update that to 100&quot; — it understands context.
      </InfoBox>
    </div>
  );
}

function ExampleQueriesSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Copy these examples to get started quickly!
      </p>

      {/* Inventory Examples */}
      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">
        Inventory Management
      </h4>
      <div className="space-y-2 my-3">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Add 100 Samsung Galaxy cases at Rs. 450 each&quot;
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Update rice stock to 200 kg&quot;
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-emerald-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Show all items under Rs. 500&quot;
          </p>
        </div>
      </div>

      {/* Billing Examples */}
      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">
        Billing & Invoices
      </h4>
      <div className="space-y-2 my-3">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-blue-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Create bill for 5 shirts and 2 pants for Ahmed&quot;
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-blue-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Show today&apos;s bills&quot;
          </p>
        </div>
      </div>

      {/* Analytics Examples */}
      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">
        Reports & Analytics
      </h4>
      <div className="space-y-2 my-3">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-purple-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Show last week&apos;s sales with top items&quot;
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-purple-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Compare this month vs last month revenue&quot;
          </p>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border-l-4 border-purple-500">
          <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
            &quot;Which items haven&apos;t sold in 30 days?&quot;
          </p>
        </div>
      </div>

      {/* Multi-step Examples */}
      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">
        Multi-Step Tasks
      </h4>
      <div className="p-3 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-lg border-l-4 border-amber-500">
        <p className="font-mono text-sm text-gray-700 dark:text-gray-300">
          &quot;Check low stock items, create reorder list, and email to supplier@vendor.com&quot;
        </p>
        <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
          AI executes multiple steps automatically!
        </p>
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

      <div className="my-6">
        <AIAgentDemo />
      </div>

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

      <div className="my-6">
        <DatabaseConnectionDemo />
      </div>
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

      <div className="my-6">
        <DatabaseConnectionDemo />
      </div>
    </div>
  );
}

function CreatingTasksSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Automate repetitive tasks and never forget a report again. Set it once, and IMS handles it forever.
      </p>

      {/* Time Savings */}
      <div className="my-4 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-700">
        <h4 className="font-semibold text-purple-700 dark:text-purple-400 mb-2">Monthly Time Saved</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div className="p-2 bg-white/50 dark:bg-gray-800/50 rounded">
            <div className="text-lg font-bold text-purple-600">25 hrs</div>
            <div className="text-gray-500 text-xs">Daily reports automated</div>
          </div>
          <div className="p-2 bg-white/50 dark:bg-gray-800/50 rounded">
            <div className="text-lg font-bold text-purple-600">6 hrs</div>
            <div className="text-gray-500 text-xs">Weekly tasks automated</div>
          </div>
        </div>
      </div>

      <div className="my-6">
        <SchedulerDemo />
      </div>

      <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-2">Example Automated Tasks</h4>

      <div className="space-y-2 my-3">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <span className="font-semibold text-emerald-600">Daily 8:30 AM:</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Send inventory summary to manager@company.com&quot;</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <span className="font-semibold text-blue-600">Every Monday 9 AM:</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Create restock list and email to supplier&quot;</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
          <span className="font-semibold text-amber-600">Every 4 Hours:</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">&quot;Check for items below 10 units, alert if found&quot;</span>
        </div>
      </div>

      <InfoBox type="tip" title="No Manual Work">
        Once scheduled, tasks run automatically. You&apos;ll receive results
        via email or view them in task history — no daily login needed!
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

      <div className="my-6">
        <SchedulerDemo />
      </div>
    </div>
  );
}

function AvailableIntegrationsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Extend your AI assistant&apos;s capabilities. More tools = more automation = more time saved!
      </p>

      {/* Time Savings with Gmail */}
      <div className="my-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-700">
        <h4 className="font-semibold text-red-700 dark:text-red-400 mb-2">Gmail Integration Saves</h4>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          <span className="font-bold text-red-600">34 min/day</span> — No manual email composing,
          reports auto-sent, invoices delivered instantly
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 my-6">
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Mail className="h-6 w-6 text-red-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">Gmail</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Send reports, invoices, alerts automatically
          </p>
          <p className="text-xs text-emerald-600 font-medium">
            &quot;Email daily report to manager@company.com&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Database className="h-6 w-6 text-blue-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">
            Google Drive
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Backup data, store reports, share files
          </p>
          <p className="text-xs text-emerald-600 font-medium">
            &quot;Save inventory backup to Drive&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <FileText className="h-6 w-6 text-gray-700 dark:text-gray-300 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">Notion</h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Sync inventory, create pages, update databases
          </p>
          <p className="text-xs text-emerald-600 font-medium">
            &quot;Sync inventory to my Notion database&quot;
          </p>
        </div>

        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <Zap className="h-6 w-6 text-amber-500 mb-2" />
          <h4 className="font-medium text-gray-900 dark:text-white">
            Custom MCP Servers
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Add any MCP-compatible service
          </p>
          <p className="text-xs text-emerald-600 font-medium">
            ERP, CRM, Accounting software & more
          </p>
        </div>
      </div>

      <InfoBox type="info" title="No API Coding Needed">
        Connect with OAuth (one-click). The AI automatically discovers
        available tools and uses them in your conversations.
      </InfoBox>

      <div className="my-6">
        <ConnectedToolsDemo />
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

      <div className="my-6">
        <ConnectedToolsDemo />
      </div>
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

      <div className="my-6">
        <ConnectedToolsDemo />
      </div>
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

      <div className="my-6">
        <SettingsDemo />
      </div>
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
      <div className="my-6">
        <KeyboardShortcutsDemo />
      </div>

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
            Do I need to build my own AI agent?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            <strong>No!</strong> IMS provides a pre-configured AI assistant that works immediately.
            Building your own would take 3-6 months and cost Rs. 50,000+/month in API fees.
            With IMS, you get it included.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Is my data secure?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Yes. Your data is completely isolated from other users. We use encryption at rest,
            JWT authentication, and never share your inventory data with anyone.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            How much time will I actually save?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Based on typical operations: <strong>2-4 hours daily</strong>. That&apos;s 60-120 hours per month.
            Adding 20 items takes 5 min vs 30 min manually. Reports are instant vs 15+ min.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            Can I use my existing database?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Yes! Connect your PostgreSQL database and the AI will understand your schema.
            Or use our database to start immediately — no setup required.
          </p>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            What if I&apos;m not technical?
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            Perfect! IMS uses natural language — just type what you need like you&apos;re texting
            a colleague. No coding, no complex menus, no learning curve.
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

// ============================================
// Developer Sections
// ============================================

function PublishedAgentsSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Create AI-powered chat widgets for your customers — without building AI infrastructure!
      </p>

      {/* Time Savings for Developers */}
      <div className="my-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-200 dark:border-indigo-700">
        <h4 className="font-semibold text-indigo-700 dark:text-indigo-400 mb-2">Developer Time Saved</h4>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-500">Build from scratch:</span>
            <span className="font-bold text-red-600 ml-2">10-15 weeks</span>
          </div>
          <div>
            <span className="text-gray-500">With Published Agents:</span>
            <span className="font-bold text-emerald-600 ml-2">15 minutes</span>
          </div>
        </div>
      </div>

      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">What Are Published Agents?</h4>
      <p className="text-gray-600 dark:text-gray-400 text-sm">
        Create AI chat widgets that your customers can use to query their data.
        Embed on any website with a simple code snippet.
      </p>

      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">Features</h4>
      <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Rate limiting (configurable queries/minute)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Domain restrictions (allowed origins)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Table access control (whitelist specific tables)
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Read-only or read-write modes
        </li>
        <li className="flex items-center gap-2">
          <CheckCircle className="h-4 w-4 text-emerald-500" />
          Usage statistics and monitoring
        </li>
      </ul>

      <InfoBox type="tip" title="No AI Expertise Required">
        You don&apos;t need to know ML, LLMs, or AI APIs. Just configure your agent,
        get the embed code, and add it to your website!
      </InfoBox>
    </div>
  );
}

function APIIntegrationSection() {
  return (
    <div className="prose dark:prose-invert max-w-none">
      <p className="text-gray-600 dark:text-gray-300">
        Full REST API for building custom integrations.
      </p>

      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">Available Endpoints</h4>

      <div className="space-y-2 my-3">
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-mono">
          <span className="text-emerald-600">GET</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">/api/items</span>
          <span className="text-gray-500 ml-2">— List inventory</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-mono">
          <span className="text-blue-600">POST</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">/api/items</span>
          <span className="text-gray-500 ml-2">— Create item</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-mono">
          <span className="text-blue-600">POST</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">/api/billing</span>
          <span className="text-gray-500 ml-2">— Create bill</span>
        </div>
        <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-mono">
          <span className="text-emerald-600">GET</span>
          <span className="text-gray-600 dark:text-gray-400 ml-2">/api/analytics/*</span>
          <span className="text-gray-500 ml-2">— Analytics</span>
        </div>
      </div>

      <h4 className="text-md font-semibold text-gray-900 dark:text-white mt-4 mb-2">Authentication</h4>
      <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm font-mono">
        <span className="text-gray-500">Authorization:</span>
        <span className="text-gray-700 dark:text-gray-300 ml-2">Bearer YOUR_JWT_TOKEN</span>
      </div>

      <InfoBox type="info" title="API Documentation">
        Full Swagger documentation available at <code>/docs</code> endpoint.
        OpenAPI spec at <code>/openapi.json</code>.
      </InfoBox>
    </div>
  );
}
