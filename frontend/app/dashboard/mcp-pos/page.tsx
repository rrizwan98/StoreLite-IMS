/**
 * MCP POS Page
 * Full Point of Sale for users with their own database (via MCP)
 * Features: Product search, cart management, bill generation
 */

'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ROUTES, APP_METADATA, API_BASE_URL } from '@/lib/constants';
import { useAuth } from '@/lib/auth-context';
import { getAccessToken } from '@/lib/auth-api';

// Types
interface Product {
  id: number;
  name: string;
  category: string;
  unit: string;
  unit_price: number;
  stock_qty: number;
}

interface CartItem extends Product {
  quantity: number;
}

interface GeneratedBill {
  bill_number: string;
  customer_name: string;
  items: CartItem[];
  subtotal: number;
  discount: number;
  tax: number;
  grand_total: number;
  created_at: string;
}

export default function MCPPOSPage() {
  const { user, connectionStatus, logout, isLoading } = useAuth();
  const router = useRouter();

  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [allProducts, setAllProducts] = useState<Product[]>([]); // Cache all products for suggestions
  const [suggestions, setSuggestions] = useState<Product[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [customerName, setCustomerName] = useState('Walk-in Customer');
  const [customerPhone, setCustomerPhone] = useState('');
  const [discount, setDiscount] = useState(0);
  const [tax, setTax] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [notes, setNotes] = useState('');

  const [searching, setSearching] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedBill, setGeneratedBill] = useState<GeneratedBill | null>(null);
  const [error, setError] = useState('');
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Derived state
  const isOwnDatabase = connectionStatus?.connection_type === 'own_database';
  const mcpConnected = connectionStatus?.mcp_status === 'connected';
  const mcpSessionId = connectionStatus?.mcp_session_id;

  // Calculate totals
  const subtotal = cart.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
  const grandTotal = subtotal - discount + tax;

  // Redirect if not own_database user or not connected
  useEffect(() => {
    if (!isLoading) {
      if (!isOwnDatabase) {
        router.push(ROUTES.POS);
      } else if (!mcpConnected || !mcpSessionId) {
        router.push(ROUTES.DB_CONNECT);
      }
    }
  }, [isLoading, isOwnDatabase, mcpConnected, mcpSessionId, router]);

  // Search products - Uses MCP to search user's own database
  const searchProducts = useCallback(async (query: string = '', isInitialLoad: boolean = false) => {
    if (!mcpSessionId) return;

    setSearching(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE_URL}/inventory-agent/pos/search-products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
          query,
          session_id: mcpSessionId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Search failed');
      }

      const fetchedProducts = data.products || [];
      setProducts(fetchedProducts);

      // Cache all products on initial load for suggestions
      if (isInitialLoad && fetchedProducts.length > 0) {
        setAllProducts(fetchedProducts);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
      setProducts([]);
    } finally {
      setSearching(false);
    }
  }, [mcpSessionId]);

  // Filter suggestions based on search query
  const getFilteredSuggestions = useCallback((query: string): Product[] => {
    if (!query.trim() || allProducts.length === 0) return [];

    const lowerQuery = query.toLowerCase();
    return allProducts
      .filter(product =>
        product.name.toLowerCase().includes(lowerQuery) ||
        product.category.toLowerCase().includes(lowerQuery)
      )
      .slice(0, 8); // Limit to 8 suggestions
  }, [allProducts]);

  // Handle search input change with auto-suggestions
  const handleSearchInputChange = (value: string) => {
    setSearchQuery(value);

    if (value.trim()) {
      const filtered = getFilteredSuggestions(value);
      setSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  // Handle suggestion click
  const handleSuggestionClick = (product: Product) => {
    setSearchQuery(product.name);
    setShowSuggestions(false);
    addToCart(product);
  };

  // Handle clicking outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.search-container')) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load products on mount (with isInitialLoad to cache all products for suggestions)
  useEffect(() => {
    if (mcpSessionId && mcpConnected) {
      searchProducts('', true);
    }
  }, [mcpSessionId, mcpConnected, searchProducts]);

  // Add to cart
  const addToCart = (product: Product) => {
    setCart(prev => {
      const existing = prev.find(item => item.id === product.id);
      if (existing) {
        return prev.map(item =>
          item.id === product.id
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      }
      return [...prev, { ...product, quantity: 1 }];
    });
  };

  // Update quantity
  const updateQuantity = (productId: number, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prev =>
      prev.map(item =>
        item.id === productId ? { ...item, quantity } : item
      )
    );
  };

  // Remove from cart
  const removeFromCart = (productId: number) => {
    setCart(prev => prev.filter(item => item.id !== productId));
  };

  // Clear cart
  const clearCart = () => {
    setCart([]);
    setDiscount(0);
    setTax(0);
    setNotes('');
  };

  // Generate bill - Uses fast MCP direct SQL endpoint (saves to user's database, no agent)
  const generateBill = async () => {
    if (cart.length === 0) {
      setError('Cart is empty');
      return;
    }

    if (!mcpSessionId) {
      setError('Not connected to database');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      // Use the fast MCP endpoint (direct SQL to user's database, no agent)
      const response = await fetch(`${API_BASE_URL}/inventory-agent/pos/create-bill`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
          session_id: mcpSessionId,
          customer_name: customerName,
          customer_phone: customerPhone,
          items: cart.map(item => ({
            id: item.id,
            name: item.name,
            quantity: item.quantity,
            unit_price: item.unit_price,
          })),
          discount,
          tax,
          payment_method: paymentMethod,
          notes,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || 'Bill generation failed');
      }

      // Set generated bill for display
      setGeneratedBill({
        bill_number: data.bill_number,
        customer_name: data.customer_name || customerName,
        items: [...cart],
        subtotal,
        discount,
        tax,
        grand_total: data.grand_total || grandTotal,
        created_at: new Date().toISOString(),
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bill generation failed');
    } finally {
      setGenerating(false);
    }
  };

  // Start new bill
  const startNewBill = () => {
    setGeneratedBill(null);
    clearCart();
    setCustomerName('Walk-in Customer');
    setCustomerPhone('');
    searchProducts(); // Refresh products
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!mcpConnected || !mcpSessionId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to your database...</p>
        </div>
      </div>
    );
  }

  // Show invoice if bill generated
  if (generatedBill) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white text-xl font-bold">S</span>
                </div>
                <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
              </Link>
            </div>
            <span className="text-gray-600 text-sm">{user?.email}</span>
          </div>
        </header>

        <main className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-lg p-8">
            {/* Invoice Header */}
            <div className="text-center border-b pb-6 mb-6">
              <h1 className="text-2xl font-bold text-gray-900">{APP_METADATA.NAME}</h1>
              <p className="text-gray-600 mt-1">Invoice / Receipt</p>
              <p className="text-sm text-gray-500 mt-2">
                Bill #: {generatedBill.bill_number}
              </p>
              <p className="text-sm text-gray-500">
                Date: {new Date(generatedBill.created_at).toLocaleString()}
              </p>
            </div>

            {/* Customer Info */}
            <div className="mb-6">
              <p className="text-gray-700">
                <strong>Customer:</strong> {generatedBill.customer_name}
              </p>
              {customerPhone && (
                <p className="text-gray-700">
                  <strong>Phone:</strong> {customerPhone}
                </p>
              )}
            </div>

            {/* Items Table */}
            <table className="w-full mb-6">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Item</th>
                  <th className="text-right py-2">Qty</th>
                  <th className="text-right py-2">Price</th>
                  <th className="text-right py-2">Total</th>
                </tr>
              </thead>
              <tbody>
                {generatedBill.items.map((item, index) => (
                  <tr key={index} className="border-b">
                    <td className="py-2">{item.name}</td>
                    <td className="text-right py-2">{item.quantity}</td>
                    <td className="text-right py-2">${item.unit_price.toFixed(2)}</td>
                    <td className="text-right py-2">${(item.quantity * item.unit_price).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Totals */}
            <div className="border-t pt-4 space-y-2">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>${generatedBill.subtotal.toFixed(2)}</span>
              </div>
              {generatedBill.discount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount:</span>
                  <span>-${generatedBill.discount.toFixed(2)}</span>
                </div>
              )}
              {generatedBill.tax > 0 && (
                <div className="flex justify-between">
                  <span>Tax:</span>
                  <span>${generatedBill.tax.toFixed(2)}</span>
                </div>
              )}
              <div className="flex justify-between text-xl font-bold border-t pt-2">
                <span>Grand Total:</span>
                <span>${generatedBill.grand_total.toFixed(2)}</span>
              </div>
            </div>

            {/* Actions */}
            <div className="mt-8 flex gap-4">
              <button
                onClick={() => window.print()}
                className="flex-1 bg-gray-100 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              >
                Print Invoice
              </button>
              <button
                onClick={startNewBill}
                className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                New Bill
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-6">
            <Link href={ROUTES.DASHBOARD} className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white text-xl font-bold">S</span>
              </div>
              <span className="text-xl font-bold text-gray-900">{APP_METADATA.NAME}</span>
            </Link>
            <nav className="hidden md:flex space-x-4">
              <Link href={ROUTES.MCP_ADMIN} className="text-gray-600 hover:text-gray-900">Admin</Link>
              <Link href={ROUTES.MCP_POS} className="text-blue-600 font-medium">POS</Link>
              <Link href={ROUTES.ANALYTICS} className="text-gray-600 hover:text-gray-900">Analytics</Link>
              <Link href={ROUTES.DB_CONNECT} className="text-gray-600 hover:text-gray-900">Connection</Link>
            </nav>
          </div>
          <div className="flex items-center space-x-4">
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Your Database</span>
            <span className="text-gray-600 text-sm">{user?.email}</span>
            <button onClick={logout} className="text-gray-600 hover:text-gray-900 text-sm">Logout</button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
            <button onClick={() => setError('')} className="float-right text-red-700 hover:text-red-900">&times;</button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Products Section */}
          <div className="lg:col-span-2 space-y-4">
            {/* Search */}
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-xl font-bold mb-4">Search Products</h2>
              <div className="flex gap-2">
                <div className="search-container relative flex-1">
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSearchInputChange(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        setShowSuggestions(false);
                        searchProducts(searchQuery);
                      } else if (e.key === 'Escape') {
                        setShowSuggestions(false);
                      }
                    }}
                    onFocus={() => {
                      if (searchQuery.trim() && suggestions.length > 0) {
                        setShowSuggestions(true);
                      }
                    }}
                    placeholder="Search by name or category..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    autoComplete="off"
                  />

                  {/* Auto-suggestions dropdown */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-64 overflow-y-auto">
                      {suggestions.map((product) => (
                        <button
                          key={product.id}
                          onClick={() => handleSuggestionClick(product)}
                          className="w-full px-4 py-3 text-left hover:bg-blue-50 border-b border-gray-100 last:border-b-0 transition-colors"
                        >
                          <div className="flex justify-between items-center">
                            <div>
                              <span className="font-medium text-gray-900">{product.name}</span>
                              <span className="ml-2 text-sm text-gray-500">({product.category})</span>
                            </div>
                            <div className="text-right">
                              <span className="text-blue-600 font-semibold">${product.unit_price.toFixed(2)}</span>
                              <span className="ml-2 text-xs text-gray-400">Stock: {product.stock_qty}</span>
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => { setShowSuggestions(false); searchProducts(searchQuery); }}
                  disabled={searching}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-400 transition-colors"
                >
                  {searching ? 'Searching...' : 'Search'}
                </button>
                <button
                  onClick={() => { setSearchQuery(''); setShowSuggestions(false); setSuggestions([]); searchProducts(''); }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>

            {/* Products Grid */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-semibold mb-4 text-gray-700">
                {searching ? 'Searching...' : `${products.length} Products Found`}
              </h3>

              {products.length === 0 && !searching ? (
                <div className="text-center py-8 text-gray-500">
                  No products found. Try a different search or add products in Admin.
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {products.map((product) => (
                    <button
                      key={product.id}
                      onClick={() => addToCart(product)}
                      className="p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors text-left"
                    >
                      <div className="font-medium text-gray-900 truncate">{product.name}</div>
                      <div className="text-sm text-gray-500">{product.category}</div>
                      <div className="flex justify-between items-center mt-2">
                        <span className="text-blue-600 font-bold">${product.unit_price.toFixed(2)}</span>
                        <span className="text-xs text-gray-400">Stock: {product.stock_qty}</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Cart Section */}
          <div className="lg:col-span-1 space-y-4">
            {/* Customer Info */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-semibold mb-3">Customer</h3>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Customer Name"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-2 text-sm"
              />
              <input
                type="text"
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                placeholder="Phone (optional)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>

            {/* Cart Items */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-semibold">Cart ({cart.length} items)</h3>
                {cart.length > 0 && (
                  <button
                    onClick={clearCart}
                    className="text-red-600 text-sm hover:text-red-700"
                  >
                    Clear
                  </button>
                )}
              </div>

              {cart.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  Cart is empty. Click products to add.
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {cart.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm truncate">{item.name}</div>
                        <div className="text-xs text-gray-500">${item.unit_price.toFixed(2)} each</div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => updateQuantity(item.id, item.quantity - 1)}
                          className="w-7 h-7 bg-gray-200 rounded-full hover:bg-gray-300 flex items-center justify-center"
                        >
                          -
                        </button>
                        <span className="w-8 text-center font-medium">{item.quantity}</span>
                        <button
                          onClick={() => updateQuantity(item.id, item.quantity + 1)}
                          className="w-7 h-7 bg-gray-200 rounded-full hover:bg-gray-300 flex items-center justify-center"
                        >
                          +
                        </button>
                        <button
                          onClick={() => removeFromCart(item.id)}
                          className="text-red-500 hover:text-red-700 ml-2"
                        >
                          &times;
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Discount & Tax */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Discount ($)</label>
                  <input
                    type="number"
                    value={discount}
                    onChange={(e) => setDiscount(Number(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-600 mb-1">Tax ($)</label>
                  <input
                    type="number"
                    value={tax}
                    onChange={(e) => setTax(Number(e.target.value) || 0)}
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>
              <div className="mt-3">
                <label className="block text-sm text-gray-600 mb-1">Payment Method</label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
                >
                  <option value="cash">Cash</option>
                  <option value="card">Card</option>
                  <option value="upi">UPI</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            {/* Bill Summary */}
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="font-semibold mb-3">Summary</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal:</span>
                  <span>${subtotal.toFixed(2)}</span>
                </div>
                {discount > 0 && (
                  <div className="flex justify-between text-green-600">
                    <span>Discount:</span>
                    <span>-${discount.toFixed(2)}</span>
                  </div>
                )}
                {tax > 0 && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Tax:</span>
                    <span>${tax.toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>Total:</span>
                  <span className="text-blue-600">${grandTotal.toFixed(2)}</span>
                </div>
              </div>
            </div>

            {/* Generate Bill Button */}
            <button
              onClick={generateBill}
              disabled={generating || cart.length === 0}
              className="w-full bg-green-600 text-white py-4 px-4 rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition-colors font-bold text-lg"
            >
              {generating ? 'Generating Bill...' : 'Generate Bill'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
