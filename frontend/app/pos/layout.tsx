/**
 * POS Layout
 * Layout wrapper for POS pages with POS-specific navigation
 */

export const metadata = {
  title: 'Point of Sale - POS',
};

export default function POSLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Point of Sale</h1>
          <p className="text-gray-600">Process customer purchases and generate invoices</p>
        </div>
        {children}
      </div>
    </div>
  );
}
