/**
 * useSessionInit.ts
 *
 * Hook odpalany raz przy starcie aplikacji.
 * Pobiera surowy stan sesji z allauth i zapisuje go w authStore.
 */
import { useEffect } from "react";
import { authService, useAuthStore } from "@core/auth";

export function useSessionInit() {
  const { setSession } = useAuthStore();

  useEffect(() => {
    let cancelled = false;

    async function initSession() {
      try {
        const session = await authService.getSession();
        if (cancelled) return;
        setSession(session);
      } catch {
        if (cancelled) return;
        // Błąd sieciowy — traktuj jak niezalogowany
        setSession(null);
      }
    }

    initSession();

    return () => {
      cancelled = true;
    };
  }, [setSession]);
}
