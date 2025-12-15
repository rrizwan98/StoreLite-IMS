import type { Metadata } from 'next';
import './globals.css';
import { APP_METADATA } from '@/lib/constants';
import { AuthProvider } from '@/lib/auth-context';

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
      <head></head>
      <body className="bg-gray-50 min-h-screen">
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
