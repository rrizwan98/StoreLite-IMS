'use client';

/**
 * Navigation Component
 * Main navigation menu with links to Admin and POS pages
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ROUTES } from '@/lib/constants';

export default function Navigation() {
  const pathname = usePathname();

  const isActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + '/');
  };

  const linkClasses = (path: string) => {
    const base = 'px-4 py-2 rounded transition-colors';
    return isActive(path)
      ? `${base} bg-primary text-white`
      : `${base} text-gray-700 hover:bg-gray-100`;
  };

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex space-x-2 py-2">
          <Link href={ROUTES.HOME} className={linkClasses(ROUTES.HOME)}>
            Home
          </Link>
          <Link href={ROUTES.ADMIN} className={linkClasses(ROUTES.ADMIN)}>
            📦 Admin
          </Link>
          <Link href={ROUTES.POS} className={linkClasses(ROUTES.POS)}>
            💳 POS
          </Link>
        </div>
      </div>
    </nav>
  );
}
