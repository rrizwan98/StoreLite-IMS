/**
 * Analytics Layout
 * Layout wrapper for analytics dashboard pages
 */

export const metadata = {
  title: 'AI Analytics Dashboard - StoreLite IMS',
  description: 'AI-powered analytics with natural language queries',
};

export default function AnalyticsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">AI Analytics Dashboard</h1>
          <p className="text-gray-600">
            Ask questions about sales, inventory, and business performance in natural language
          </p>
        </div>
        {children}
      </div>
    </div>
  );
}
