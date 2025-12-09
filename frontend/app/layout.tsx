import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/shared/Header';
import Navigation from '@/components/shared/Navigation';
import { APP_METADATA } from '@/lib/constants';

export const metadata: Metadata = {
  title: `${APP_METADATA.NAME} - ${APP_METADATA.SUBTITLE}`,
  description: APP_METADATA.DESCRIPTION,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">
        <Header />
        <Navigation />
        <main className="container mx-auto px-4 py-6">
          {children}
        </main>
        <footer className="bg-gray-100 border-t border-gray-200 mt-8 py-4">
          <div className="container mx-auto px-4 text-center text-sm text-gray-600">
            <p>{APP_METADATA.NAME} v{APP_METADATA.VERSION}</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
