/**
 * Home / Landing Page
 * Simple landing page with navigation to Admin and POS
 */

import Link from 'next/link';
import { ROUTES, APP_METADATA } from '@/lib/constants';

export default function Home() {
  return (
    <div className="max-w-4xl mx-auto py-12">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold mb-2">{APP_METADATA.NAME}</h1>
        <p className="text-xl text-gray-600">{APP_METADATA.DESCRIPTION}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Admin Card */}
        <Link href={ROUTES.ADMIN}>
          <div className="card hover:shadow-lg cursor-pointer transition-shadow">
            <div className="text-4xl mb-4">📦</div>
            <h2 className="text-2xl font-bold mb-2">Inventory Management</h2>
            <p className="text-gray-600">
              Manage your inventory: add items, update prices and stock levels, and search for
              products.
            </p>
            <div className="mt-4 text-primary font-semibold">Go to Admin →</div>
          </div>
        </Link>

        {/* POS Card */}
        <Link href={ROUTES.POS}>
          <div className="card hover:shadow-lg cursor-pointer transition-shadow">
            <div className="text-4xl mb-4">💳</div>
            <h2 className="text-2xl font-bold mb-2">Point of Sale</h2>
            <p className="text-gray-600">
              Process customer purchases: search items, build bills, calculate totals, and generate
              invoices.
            </p>
            <div className="mt-4 text-primary font-semibold">Go to POS →</div>
          </div>
        </Link>
      </div>

      {/* Features Section */}
      <div className="mt-12">
        <h2 className="text-2xl font-bold mb-6 text-center">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-start">
            <div className="text-primary mr-3 text-xl">✓</div>
            <div>
              <h3 className="font-semibold">Real-time Inventory</h3>
              <p className="text-sm text-gray-600">Live stock levels and item management</p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="text-primary mr-3 text-xl">✓</div>
            <div>
              <h3 className="font-semibold">Fast Billing</h3>
              <p className="text-sm text-gray-600">Quick item search and bill generation</p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="text-primary mr-3 text-xl">✓</div>
            <div>
              <h3 className="font-semibold">Automatic Retry</h3>
              <p className="text-sm text-gray-600">Network-resilient with auto-retry logic</p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="text-primary mr-3 text-xl">✓</div>
            <div>
              <h3 className="font-semibold">Printable Invoices</h3>
              <p className="text-sm text-gray-600">Professional receipt generation</p>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      <div className="mt-12 bg-primary bg-opacity-5 rounded-lg p-6">
        <h2 className="text-xl font-bold mb-3">Getting Started</h2>
        <ol className="list-decimal list-inside space-y-2 text-gray-700">
          <li>Navigate to the Admin page to add your inventory items</li>
          <li>Set up product names, categories, prices, and stock levels</li>
          <li>Go to the POS page to start processing customer sales</li>
          <li>Search for items, add them to bills, and generate invoices</li>
          <li>Print invoices for customer receipts</li>
        </ol>
      </div>
    </div>
  );
}
