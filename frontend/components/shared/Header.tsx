'use client';

/**
 * Header Component
 * App title and metadata at top of page
 */

import { APP_METADATA } from '@/lib/constants';

export default function Header() {
  return (
    <header className="bg-primary text-white shadow-md">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{APP_METADATA.NAME}</h1>
            <p className="text-sm text-primary opacity-90">{APP_METADATA.SUBTITLE}</p>
          </div>
          <div className="text-right text-sm">
            <p>v{APP_METADATA.VERSION}</p>
          </div>
        </div>
      </div>
    </header>
  );
}
