/**
 * Home / Landing Page
 * Public landing page with Login/Signup options
 */

'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ROUTES, APP_METADATA } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';

export default function Home() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  // Redirect to dashboard if already logged in
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push(ROUTES.DASHBOARD);
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2 sm:space-x-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-lg sm:text-xl font-bold">S</span>
            </div>
            <span className="text-lg sm:text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
          </div>
          <div className="flex items-center space-x-2 sm:space-x-4">
            <Link
              href={ROUTES.LOGIN}
              className="text-gray-600 hover:text-gray-900 font-medium text-sm sm:text-base"
            >
              Login
            </Link>
            <Link
              href={ROUTES.SIGNUP}
              className="bg-blue-600 text-white px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm sm:text-base"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12 lg:py-16">
        <div className="text-center mb-10 sm:mb-16">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-gray-900 mb-4 sm:mb-6">
            Smart Inventory Management
            <br />
            <span className="text-blue-600">Powered by AI</span>
          </h1>
          <p className="text-base sm:text-lg lg:text-xl text-gray-600 max-w-3xl mx-auto mb-6 sm:mb-8 px-2">
            {APP_METADATA.DESCRIPTION}. Connect your own database or use our platform -
            manage inventory with natural language queries and AI-powered analytics.
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3 sm:gap-4">
            <Link
              href={ROUTES.SIGNUP}
              className="bg-blue-600 text-white px-6 sm:px-8 py-2.5 sm:py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold text-base sm:text-lg"
            >
              Start Free
            </Link>
            <Link
              href={ROUTES.LOGIN}
              className="border-2 border-gray-300 text-gray-700 px-6 sm:px-8 py-2.5 sm:py-3 rounded-lg hover:border-gray-400 transition-colors font-semibold text-base sm:text-lg"
            >
              Sign In
            </Link>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-10 sm:mb-16">
          <div className="bg-white rounded-xl shadow-md p-5 sm:p-6 hover:shadow-lg transition-shadow">
            <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">🔌</div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2">Connect Your Database</h3>
            <p className="text-gray-600 text-sm sm:text-base">
              Bring your own PostgreSQL database and manage it with our AI-powered tools via MCP.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-5 sm:p-6 hover:shadow-lg transition-shadow">
            <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">📊</div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2">AI Analytics</h3>
            <p className="text-gray-600 text-sm sm:text-base">
              Ask questions in natural language and get smart visualizations from your data.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-5 sm:p-6 hover:shadow-lg transition-shadow">
            <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">📦</div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2">Inventory Management</h3>
            <p className="text-gray-600 text-sm sm:text-base">
              Full inventory tracking with categories, stock levels, and real-time updates.
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-md p-5 sm:p-6 hover:shadow-lg transition-shadow">
            <div className="text-3xl sm:text-4xl mb-3 sm:mb-4">💳</div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2">Point of Sale</h3>
            <p className="text-gray-600 text-sm sm:text-base">
              Fast billing system with searchable products and printable invoices.
            </p>
          </div>
        </div>

        {/* Two Options Section */}
        <div className="bg-white rounded-2xl shadow-lg p-5 sm:p-8 mb-10 sm:mb-16">
          <h2 className="text-2xl sm:text-3xl font-bold text-center mb-6 sm:mb-8">Choose How You Want to Work</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-8">
            {/* Option 1: Own Database */}
            <div className="border-2 border-blue-200 rounded-xl p-4 sm:p-6 bg-blue-50">
              <div className="text-4xl sm:text-5xl mb-3 sm:mb-4 text-center">🔗</div>
              <h3 className="text-xl sm:text-2xl font-semibold text-center mb-3 sm:mb-4">Connect Your Own Database</h3>
              <ul className="space-y-2 sm:space-y-3 text-gray-700 text-sm sm:text-base">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Your data stays in your database
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  MCP Protocol for secure access
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  AI Analytics on YOUR data
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Full control over your schema
                </li>
              </ul>
            </div>

            {/* Option 2: Our Database */}
            <div className="border-2 border-purple-200 rounded-xl p-4 sm:p-6 bg-purple-50">
              <div className="text-4xl sm:text-5xl mb-3 sm:mb-4 text-center">☁️</div>
              <h3 className="text-xl sm:text-2xl font-semibold text-center mb-3 sm:mb-4">Use Our Platform</h3>
              <ul className="space-y-2 sm:space-y-3 text-gray-700 text-sm sm:text-base">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  No database setup required
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Full Admin & POS features
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  AI Analytics included
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  Start managing in seconds
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-3 sm:mb-4">Ready to Get Started?</h2>
          <p className="text-gray-600 mb-4 sm:mb-6 text-sm sm:text-base">
            Create your free account and start managing your inventory today.
          </p>
          <Link
            href={ROUTES.SIGNUP}
            className="inline-block bg-blue-600 text-white px-6 sm:px-8 py-2.5 sm:py-3 rounded-lg hover:bg-blue-700 transition-colors font-semibold text-base sm:text-lg"
          >
            Create Free Account
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t border-gray-200 mt-10 sm:mt-16 py-6 sm:py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-xs sm:text-sm text-gray-600">
          <p>{APP_METADATA.NAME} v{APP_METADATA.VERSION}</p>
          <p className="mt-2">Modern inventory management powered by AI and MCP Protocol</p>
        </div>
      </footer>
    </div>
  );
}
