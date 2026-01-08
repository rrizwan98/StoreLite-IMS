/**
 * useChatKitSession Hook
 * Manages tab-lifetime ChatKit session with persistence
 */

import { useEffect, useState } from 'react';
import { createChatKitSession } from '../chatkit-api';

export function useChatKitSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initializeSession() {
      try {
        // Check sessionStorage first (for page refresh recovery)
        const stored = sessionStorage.getItem('chatkit-session-id');

        if (stored) {
          setSessionId(stored);
          setIsLoading(false);
          return;
        }

        // Create new session
        const session = await createChatKitSession();
        sessionStorage.setItem('chatkit-session-id', session.session_id);
        setSessionId(session.session_id);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setIsLoading(false);
      }
    }

    initializeSession();

    // Cleanup on unmount
    return () => {
      // Session persists until tab closes (per spec)
    };
  }, []);

  return { sessionId, isLoading, error };
}
