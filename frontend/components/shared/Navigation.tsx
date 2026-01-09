'use client';

/**
 * Navigation Component
 * Main navigation menu with links to Admin, POS, and Settings pages
 * Includes connected tools dropdown and mobile hamburger menu
 */

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Settings, ChevronDown, Check, Server, Wrench, Menu, X } from 'lucide-react';
import { ROUTES } from '@/lib/constants';
import { getAllTools, SystemTool } from '@/lib/tools-api';
import { getConnectors, Connector } from '@/lib/connectors-api';

export default function Navigation() {
  const pathname = usePathname();
  const [toolsOpen, setToolsOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [systemTools, setSystemTools] = useState<SystemTool[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + '/');
  };

  const linkClasses = (path: string) => {
    const base = 'px-4 py-2 rounded transition-colors';
    return isActive(path)
      ? `${base} bg-primary text-white`
      : `${base} text-gray-700 hover:bg-gray-100`;
  };

  const mobileLinkClasses = (path: string) => {
    const base = 'block px-4 py-3 rounded-lg transition-colors text-base';
    return isActive(path)
      ? `${base} bg-primary text-white`
      : `${base} text-gray-700 hover:bg-gray-100`;
  };

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  // Load tools and connectors
  useEffect(() => {
    async function loadData() {
      try {
        const [tools, conns] = await Promise.all([
          getAllTools().catch(() => []),
          getConnectors(true).catch(() => []), // Only active connectors
        ]);
        setSystemTools(tools.filter(t => t.is_connected || t.auth_type === 'none'));
        setConnectors(conns.filter(c => c.is_verified));
      } catch (err) {
        console.error('Failed to load tools:', err);
      }
    }
    loadData();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setToolsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const connectedCount = systemTools.filter(t => t.is_connected).length + connectors.length;

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-2">
          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>

          {/* Left side - Main navigation (hidden on mobile) */}
          <div className="hidden lg:flex space-x-2">
            <Link href={ROUTES.HOME} className={linkClasses(ROUTES.HOME)}>
              Home
            </Link>
            <Link href={ROUTES.ADMIN} className={linkClasses(ROUTES.ADMIN)}>
              📦 Admin
            </Link>
            <Link href={ROUTES.POS} className={linkClasses(ROUTES.POS)}>
              💳 POS
            </Link>
            <Link href={ROUTES.ANALYTICS} className={linkClasses(ROUTES.ANALYTICS)}>
              📊 Analytics
            </Link>
            <Link href={ROUTES.DB_CONNECT} className={linkClasses(ROUTES.DB_CONNECT)}>
              🔌 Connect DB
            </Link>
          </div>

          {/* Right side - Tools dropdown and Settings */}
          <div className="flex items-center space-x-2">
            {/* Connected Tools Dropdown (hidden on mobile) */}
            <div className="hidden md:block relative" ref={dropdownRef}>
              <button
                onClick={() => setToolsOpen(!toolsOpen)}
                className={`
                  flex items-center px-3 py-2 rounded transition-colors
                  ${toolsOpen ? 'bg-gray-100' : 'hover:bg-gray-100'}
                  text-gray-700
                `}
              >
                <Wrench className="h-4 w-4 mr-2" />
                <span className="hidden sm:inline">Tools</span>
                {connectedCount > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                    {connectedCount}
                  </span>
                )}
                <ChevronDown className={`h-4 w-4 ml-1 transition-transform ${toolsOpen ? 'rotate-180' : ''}`} />
              </button>

              {/* Dropdown Menu */}
              {toolsOpen && (
                <div className="absolute right-0 mt-1 w-64 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
                  {/* System Tools */}
                  <div className="p-2 border-b border-gray-100">
                    <p className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">System Tools</p>
                    {systemTools.length > 0 ? (
                      systemTools.map(tool => (
                        <div
                          key={tool.id}
                          className="flex items-center px-2 py-2 rounded hover:bg-gray-50"
                        >
                          <div className={`
                            w-6 h-6 rounded flex items-center justify-center mr-2
                            ${tool.is_connected ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-500'}
                          `}>
                            {tool.is_connected && <Check className="h-3 w-3" />}
                          </div>
                          <span className="text-sm text-gray-700">{tool.name}</span>
                          {tool.is_connected && (
                            <span className="ml-auto text-xs text-green-600">Connected</span>
                          )}
                        </div>
                      ))
                    ) : (
                      <p className="px-2 py-2 text-sm text-gray-500">No tools connected</p>
                    )}
                  </div>

                  {/* MCP Connectors */}
                  <div className="p-2 border-b border-gray-100">
                    <p className="px-2 py-1 text-xs font-medium text-gray-500 uppercase">My Connectors</p>
                    {connectors.length > 0 ? (
                      connectors.map(conn => (
                        <div
                          key={conn.id}
                          className="flex items-center px-2 py-2 rounded hover:bg-gray-50"
                        >
                          <div className="w-6 h-6 rounded bg-green-100 text-green-600 flex items-center justify-center mr-2">
                            <Server className="h-3 w-3" />
                          </div>
                          <span className="text-sm text-gray-700">{conn.name}</span>
                          <span className="ml-auto text-xs text-gray-500">
                            {conn.tool_count} tools
                          </span>
                        </div>
                      ))
                    ) : (
                      <p className="px-2 py-2 text-sm text-gray-500">No connectors added</p>
                    )}
                  </div>

                  {/* Manage Tools Link */}
                  <div className="p-2">
                    <Link
                      href="/dashboard/settings"
                      className="flex items-center justify-center px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                      onClick={() => setToolsOpen(false)}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Manage Tools & Connectors
                    </Link>
                  </div>
                </div>
              )}
            </div>

            {/* Settings Link */}
            <Link
              href="/dashboard/settings"
              className={`
                flex items-center px-3 py-2 rounded transition-colors
                ${isActive('/dashboard/settings') ? 'bg-primary text-white' : 'text-gray-700 hover:bg-gray-100'}
              `}
            >
              <Settings className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden py-4 border-t border-gray-200">
            <div className="space-y-2">
              <Link href={ROUTES.HOME} className={mobileLinkClasses(ROUTES.HOME)}>
                🏠 Home
              </Link>
              <Link href={ROUTES.ADMIN} className={mobileLinkClasses(ROUTES.ADMIN)}>
                📦 Admin
              </Link>
              <Link href={ROUTES.POS} className={mobileLinkClasses(ROUTES.POS)}>
                💳 POS
              </Link>
              <Link href={ROUTES.ANALYTICS} className={mobileLinkClasses(ROUTES.ANALYTICS)}>
                📊 Analytics
              </Link>
              <Link href={ROUTES.DB_CONNECT} className={mobileLinkClasses(ROUTES.DB_CONNECT)}>
                🔌 Connect DB
              </Link>
              <div className="border-t border-gray-200 mt-3 pt-3">
                <Link href="/dashboard/settings" className={mobileLinkClasses('/dashboard/settings')}>
                  <span className="flex items-center">
                    <Wrench className="h-4 w-4 mr-2" />
                    Tools & Settings
                    {connectedCount > 0 && (
                      <span className="ml-2 px-1.5 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                        {connectedCount}
                      </span>
                    )}
                  </span>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
