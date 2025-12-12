/**
 * Admin Layout
 * Layout wrapper for admin pages with admin-specific navigation
 */

export const metadata = {
  title: 'Inventory Management - Admin',
};

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Inventory Management</h1>
          <p className="text-gray-600">Manage your inventory items, prices, and stock levels</p>
        </div>
        {children}
      </div>
    </div>
  );
}
