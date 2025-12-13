'use client';

import { ReactNode, Component, ErrorInfo } from 'react';

/**
 * Error Boundary Component
 * Catches React component errors and displays fallback UI
 */

interface Props {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to console for debugging
    console.error('Error caught by ErrorBoundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error);
      }

      return (
        <div className="bg-error bg-opacity-10 border border-error text-error rounded-md p-4 m-4">
          <h2 className="font-semibold mb-2">Something went wrong</h2>
          <details className="text-sm">
            <summary>Error details</summary>
            <pre className="mt-2 bg-white p-2 rounded overflow-auto">
              {this.state.error.message}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}
